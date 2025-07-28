from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()

# In-memory storage for uploaded files and folder mappings
FILES = []
FOLDER_MAPPINGS = {}

class FolderMapping(BaseModel):
    path: str = Field(..., description="Absolute or relative folder path to monitor")
    alias: str = Field(..., description="Custom name/label for the folder")

class UploadResponse(BaseModel):
    filename: str
    status: str

# PUBLIC_INTERFACE
@router.post("/upload", summary="Ingest a file", description="Upload Excel, PowerPoint, PDF, or Word file for ingestion", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # For now, just track filename in memory
    FILES.append(file.filename)
    return UploadResponse(filename=file.filename, status="uploaded")

# PUBLIC_INTERFACE
@router.post("/folders", summary="Map a folder for ingestion", description="Add a new folder to be monitored/mapped for ingestion.", response_model=FolderMapping)
async def map_folder(mapping: FolderMapping):
    FOLDER_MAPPINGS[mapping.alias] = mapping.path
    return mapping

# PUBLIC_INTERFACE
@router.get("/folders", summary="List all mapped folders", description="Get all currently mapped/monitored folders.", response_model=List[FolderMapping])
async def list_mapped_folders():
    return [FolderMapping(path=path, alias=alias) for alias, path in FOLDER_MAPPINGS.items()]
