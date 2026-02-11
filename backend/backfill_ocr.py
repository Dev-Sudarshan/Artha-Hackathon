"""Backfill OCR data for existing KYC records"""

from db.database import get_all_items, put_item
from models.citizenship_ocr_model import verify_citizenship_card
import os


def backfill_ocr_data():
    """Run OCR on all existing KYC records that don't have ocr_extracted data"""
    
    all_kyc = get_all_items("kyc")
    
    for user_id, kyc_data in all_kyc.items():
        print(f"\n[BACKFILL] Processing: {user_id}")
        
        # Skip if already has OCR data
        if kyc_data.get("id_documents", {}).get("ocr_extracted"):
            print(f"[BACKFILL] {user_id} already has OCR data, skipping")
            continue
        
        # Check if has ID documents
        id_documents = kyc_data.get("id_documents")
        if not id_documents:
            print(f"[BACKFILL] {user_id} has no ID documents, skipping")
            continue
        
        # Get image paths
        back_image_ref = id_documents.get("id_images", {}).get("back_image_ref")
        if not back_image_ref:
            print(f"[BACKFILL] {user_id} has no back image, skipping")
            continue
        
        # Resolve image path
        if back_image_ref.startswith("static/"):
            back_image_path = back_image_ref
        elif back_image_ref.startswith("/static/"):
            back_image_path = back_image_ref[1:]  # Remove leading /
        else:
            back_image_path = f"static/{back_image_ref}"
        
        # Check if file exists
        if not os.path.isfile(back_image_path):
            print(f"[BACKFILL] {user_id} back image not found at {back_image_path}, skipping")
            continue
        
        # Get user input data for matching
        basic_info = kyc_data.get("basic_info", {})
        full_name = " ".join(
            filter(None, [
                basic_info.get("first_name"),
                basic_info.get("middle_name"),
                basic_info.get("last_name"),
            ])
        )
        dob = basic_info.get("date_of_birth", "")
        citizenship_no = id_documents.get("id_details", {}).get("id_number", "")
        
        print(f"[BACKFILL] Running OCR for {user_id}...")
        print(f"[BACKFILL] Image: {back_image_path}")
        print(f"[BACKFILL] Input: name={full_name}, dob={dob}, cit_no={citizenship_no}")
        
        try:
            # Run OCR
            ocr_result = verify_citizenship_card(
                image_path=back_image_path,
                input_full_name=full_name,
                input_dob=dob,
                input_citizenship_no=citizenship_no,
            )
            
            # Extract the fields
            extracted_fields = ocr_result.get("extracted_fields", {})
            
            if extracted_fields:
                # Save to database
                kyc_data["id_documents"]["ocr_extracted"] = extracted_fields
                put_item("kyc", user_id, kyc_data)
                print(f"[BACKFILL] ✓ Successfully extracted and saved OCR data for {user_id}")
                print(f"[BACKFILL]   - Citizenship: {extracted_fields.get('citizenship_certificate_number')}")
                print(f"[BACKFILL]   - Name: {extracted_fields.get('full_name')}")
                print(f"[BACKFILL]   - DOB: {extracted_fields.get('date_of_birth')}")
            else:
                print(f"[BACKFILL] ✗ No fields extracted for {user_id}")
                
        except Exception as e:
            print(f"[BACKFILL] ✗ OCR failed for {user_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n[BACKFILL] Done!")


if __name__ == "__main__":
    print("=" * 60)
    print("Starting OCR Backfill for Existing KYC Records")
    print("=" * 60)
    backfill_ocr_data()
