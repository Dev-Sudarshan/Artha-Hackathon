"""
Quick script to re-run video verification for a specific loan
This will extract and save the video frame
"""

import sys
from db.database import get_item, put_item
from services.loan_verification_service import verify_loan_video_background

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rerun_verification.py <loan_id>")
        print("Example: python rerun_verification.py LN-C01EAF93")
        sys.exit(1)
    
    loan_id = sys.argv[1]
    
    print(f"\n{'='*50}")
    print(f"Re-running verification for loan: {loan_id}")
    print(f"{'='*50}\n")
    
    # Check if loan exists
    loan = get_item("loans", loan_id)
    if not loan:
        print(f"❌ Loan {loan_id} not found!")
        sys.exit(1)
    
    print(f"Current loan status: {loan.get('status')}")
    print(f"Video ref: {loan.get('video_verification_ref')}")
    print(f"KYC selfie ref: {loan.get('kyc_selfie_ref')}")
    print(f"Current frame ref: {loan.get('video_frame_ref', 'NOT SET')}")
    print()
    
    # Reset verification fields so it can be re-run
    loan["status"] = "PENDING_VERIFICATION"
    loan.pop("video_verification_result", None)
    loan.pop("video_frame_ref", None)
    loan.pop("ai_suggestion", None)
    loan.pop("ai_suggestion_reason", None)
    put_item("loans", loan_id, loan)
    
    print("✓ Reset verification fields")
    print("▶ Starting background verification...\n")
    
    # Run verification synchronously for immediate feedback
    verify_loan_video_background(loan_id)
    
    # Check result
    loan = get_item("loans", loan_id)
    print(f"\n{'='*50}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*50}")
    print(f"Status: {loan.get('status')}")
    print(f"AI Suggestion: {loan.get('ai_suggestion')}")
    print(f"Reason: {loan.get('ai_suggestion_reason')}")
    print(f"Video frame ref: {loan.get('video_frame_ref', 'NOT SET')}")
    print(f"\n✅ Done! Refresh admin panel to see updated photos.")
