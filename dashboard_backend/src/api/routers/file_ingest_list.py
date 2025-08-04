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

import hashlib

def _list_uploaded_files_in_upload_dir() -> List[FileMetaResponse]:
    """
    Scans the uploads/ directory and constructs file metadata for all found files.
    Ensures that returned file_id is unique across all time by combining hashed full path.
    """
    files: List[FileMetaResponse] = []
    upload_base = "uploads"
    if not os.path.exists(upload_base):
        return files

    # Walk through all date folders
    for dirpath, dirnames, filenames in os.walk(upload_base):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # Use *hash* of relative file path as file_id, to ensure uniqueness on multi-upload/dates
            rel_path = os.path.relpath(file_path, upload_base)
            file_id = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()
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
