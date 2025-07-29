from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List
import shutil
import os

from src.api.deps import get_db

router = APIRouter()

class FolderMapping(BaseModel):
    path: str = Field(..., description="Absolute or relative folder path to monitor")
    alias: str = Field(..., description="Custom name/label for the folder")

class UploadResponse(BaseModel):
    filename: str
    status: str

# PUBLIC_INTERFACE
@router.post("/upload", summary="Ingest a file", description="Upload Excel, PowerPoint, PDF, or Word file for ingestion", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), db=Depends(get_db)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Upsert the uploaded file record
    await db["uploaded_files"].update_one(
        {"filename": file.filename},
        {"$setOnInsert": {"filename": file.filename}},
        upsert=True,
    )
    return UploadResponse(filename=file.filename, status="uploaded")

# PUBLIC_INTERFACE
@router.post("/folders", summary="Map a folder for ingestion", description="Add a new folder to be monitored/mapped for ingestion.", response_model=FolderMapping)
async def map_folder(mapping: FolderMapping, db=Depends(get_db)):
    await db["folder_mappings"].update_one(
        {"alias": mapping.alias},
        {"$set": {"path": mapping.path, "alias": mapping.alias}},
        upsert=True,
    )
    return FolderMapping(alias=mapping.alias, path=mapping.path)

# PUBLIC_INTERFACE
@router.get("/folders", summary="List all mapped folders", description="Get all currently mapped/monitored folders.", response_model=List[FolderMapping])
async def list_mapped_folders(db=Depends(get_db)):
    folders = await db["folder_mappings"].find({}).to_list(length=100)
    return [FolderMapping(path=f["path"], alias=f["alias"]) for f in folders]
