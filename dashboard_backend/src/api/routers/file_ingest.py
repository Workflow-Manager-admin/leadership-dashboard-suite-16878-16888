"""
File ingestion and parsing endpoints.
"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import Dict, Any
from pydantic import BaseModel, Field
import uuid

router = APIRouter()

class FileProcessResponse(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the processed file")
    file_name: str = Field(..., description="Original file name")
    status: str = Field(..., description="Processing status")
    detected_type: str = Field(..., description="Detected document type")
    meta: Dict[str, Any] = Field({}, description="Additional metadata extracted during ingestion")

import os
from datetime import datetime

# Import dashboard creation logic to link file uploads and dashboards
from src.api.routers.dashboard import add_dashboard

# PUBLIC_INTERFACE
@router.post("/upload", response_model=FileProcessResponse, summary="Upload file for ingestion", description="Upload and process supported files (xlsx, pptx, pdf, docx).")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Accepts and stores a file for backend ingestion/parsing. 
    Triggers async parsing and detection pipeline.
    Stores the uploaded file in 'uploads/YYYY-MM-DD/', creating the folder if needed.
    Returns file_id and classification.
    Automatically creates a dashboard entry for the uploaded file.
    """
    # Generate file and detect type
    file_id = str(uuid.uuid4())
    file_name = file.filename
    detected_type = "unknown"
    # Parse content type
    if file_name.lower().endswith(".xlsx"):
        detected_type = "excel"
    elif file_name.lower().endswith(".pptx"):
        detected_type = "ppt"
    elif file_name.lower().endswith(".pdf"):
        detected_type = "pdf"
    elif file_name.lower().endswith(".docx"):
        detected_type = "doc"
    else:
        detected_type = "other"

    # Determine today's date and the upload directory
    today = datetime.now().strftime("%Y-%m-%d")
    base_upload_dir = "uploads"
    dated_upload_dir = os.path.join(base_upload_dir, today)
    os.makedirs(dated_upload_dir, exist_ok=True)
    save_path = os.path.join(dated_upload_dir, file_name)

    # Save uploaded file to the correct directory
    with open(save_path, "wb") as out_file:
        content = await file.read()
        out_file.write(content)

    status_str = "processing"
    meta = {"upload_path": save_path}

    # Automatically create dashboard entry linked to upload
    dashboard_id = file_id  # Use file UUID as dashboard UUID
    add_dashboard(
        dashboard_id=dashboard_id,
        file_name=file_name,
        file_id=file_id,
        upload_path=save_path,
        detected_type=detected_type,
        meta=meta,
    )

    return FileProcessResponse(
        file_id=file_id,
        file_name=file_name,
        status=status_str,
        detected_type=detected_type,
        meta=meta
    )
