from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List
from src.api.db import get_database
from src.api.models import UploadEntity
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


class FolderMapping(BaseModel):
    path: str = Field(..., description="Absolute or relative folder path to monitor")
    alias: str = Field(..., description="Custom name/label for the folder")


class UploadResponse(BaseModel):
    filename: str
    status: str

# PUBLIC_INTERFACE
@router.post("/upload", summary="Ingest a file", description="Upload Excel, PowerPoint, PDF, or Word file for ingestion", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Ingest a file (metadata only; actual storage not handled). Track upload in MongoDB.
    """
    upload_doc = UploadEntity(filename=file.filename, status="uploaded")
    await db.uploads.insert_one(upload_doc.model_dump())
    return UploadResponse(filename=file.filename, status="uploaded")


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
