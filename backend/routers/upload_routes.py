from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid

router = APIRouter(tags=["upload"])

# Use absolute path to ensure files are saved in the correct location
# regardless of where uvicorn is started from
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"[UPLOAD] Upload directory: {UPLOAD_DIR}")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Generate unique filename
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[UPLOAD] Saved: {file_path} ({os.path.getsize(file_path)} bytes, exists={os.path.isfile(file_path)})")
            
        # Return a browser-accessible URL (FastAPI serves /static from backend/static)
        return {"url": f"/static/uploads/{filename}", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
