from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List
from src.api.db import get_database
from src.api.models import UploadEntity
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.routes.parsing import extract_structured_data  # Import parsing logic

import os
import tempfile

router = APIRouter()


class FolderMapping(BaseModel):
    path: str = Field(..., description="Absolute or relative folder path to monitor")
    alias: str = Field(..., description="Custom name/label for the folder")


class UploadResponse(BaseModel):
    filename: str
    status: str

# PUBLIC_INTERFACE
@router.post("/upload", summary="Ingest a file", description="Upload Excel, PowerPoint, PDF, or Word file for ingestion (parses and stores structured data)",
             response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Ingest a file, parse its structured data, and track upload in MongoDB.
    The file is parsed immediately after upload.
    """
    # Save to temp location
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Extract data using the parsing utilities
        try:
            structured_data = await extract_structured_data(tmp_path, file.filename)
        except Exception as e:
            structured_data = {"error": str(e)}

        # Upload record (status="parsed" if parsed else "error")
        status = "parsed" if "error" not in structured_data else "error"
        upload_doc = UploadEntity(filename=file.filename, status=status)
        await db.uploads.insert_one(upload_doc.model_dump())

        # Store parsed content (even if error, for debugging/feedback)
        await db.parsed.update_one(
            {"filename": file.filename},
            {"$set": {"filename": file.filename, "parsed_content": structured_data}},
            upsert=True
        )
        return UploadResponse(filename=file.filename, status=status)
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


# PUBLIC_INTERFACE
@router.post("/folders", summary="Map a folder for ingestion", description="Add a new folder to be monitored/mapped for ingestion.", response_model=FolderMapping)
async def map_folder(
    mapping: FolderMapping,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Map a folder for ingestion. If alias exists, update it; otherwise insert new.
    """
    # Upsert mapping (by alias)
    await db.folders.update_one(
        {"alias": mapping.alias},
        {"$set": mapping.dict()},
        upsert=True
    )
    return mapping

# PUBLIC_INTERFACE
@router.get("/folders", summary="List all mapped folders", description="Get all currently mapped/monitored folders.", response_model=List[FolderMapping])
async def list_mapped_folders(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Retrieve all mapped/monitored folders from MongoDB.
    """
    docs = db.folders.find()
    result = []
    async for doc in docs:
        result.append(FolderMapping(**doc))
    return result
