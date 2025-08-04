"""
Endpoint for listing all uploaded files and their metadata.
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import os

router = APIRouter()

class FileMetaResponse(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the processed file")
    file_name: str = Field(..., description="Original file name")
    status: str = Field(..., description="Processing status")
    detected_type: str = Field(..., description="Detected document type")
    meta: Dict[str, Any] = Field({}, description="Additional metadata extracted during ingestion")

def _list_uploaded_files_in_upload_dir() -> List[FileMetaResponse]:
    """
    Scans the uploads/ directory and constructs file metadata for all found files.
    """
    files: List[FileMetaResponse] = []
    upload_base = "uploads"
    if not os.path.exists(upload_base):
        return files

    # Walk through all date folders
    for dirpath, dirnames, filenames in os.walk(upload_base):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # Generate a deterministic file_id using the relative path (for simplicity)
            file_id = os.path.splitext(filename)[0] + "_" + os.path.basename(dirpath)
            detected_type = "other"
            if filename.lower().endswith(".xlsx"):
                detected_type = "excel"
            elif filename.lower().endswith(".pptx"):
                detected_type = "ppt"
            elif filename.lower().endswith(".pdf"):
                detected_type = "pdf"
            elif filename.lower().endswith(".docx"):
                detected_type = "doc"
            upload_path = file_path
            meta = {
                "upload_path": upload_path,
                "date_folder": os.path.basename(dirpath)
            }
            files.append(
                FileMetaResponse(
                    file_id=file_id,
                    file_name=filename,
                    status="uploaded",
                    detected_type=detected_type,
                    meta=meta
                )
            )
    return sorted(files, key=lambda x: x.meta.get("date_folder", ""), reverse=True)

# PUBLIC_INTERFACE
@router.get("/list", response_model=List[FileMetaResponse], summary="List all uploaded files", description="Returns all uploaded files with meta info.", tags=["file-ingest"])
async def list_uploaded_files():
    """
    Returns a list of all uploaded files and their known metadata.
    """
    return _list_uploaded_files_in_upload_dir()
