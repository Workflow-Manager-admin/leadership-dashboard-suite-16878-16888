from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List
import shutil
import os

from src.api.models import FolderMapping as FolderMappingORM, UploadedFile as UploadedFileORM
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
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    db_file = db.query(UploadedFileORM).filter_by(filename=file.filename).first()
    if db_file is None:
        db_file = UploadedFileORM(filename=file.filename)
        db.add(db_file)
        db.commit()
    return UploadResponse(filename=file.filename, status="uploaded")

# PUBLIC_INTERFACE
@router.post("/folders", summary="Map a folder for ingestion", description="Add a new folder to be monitored/mapped for ingestion.", response_model=FolderMapping)
async def map_folder(mapping: FolderMapping, db: Session = Depends(get_db)):
    # Upsert by alias
    db_mapping = db.query(FolderMappingORM).filter_by(alias=mapping.alias).first()
    if db_mapping:
        db_mapping.path = mapping.path
    else:
        db_mapping = FolderMappingORM(alias=mapping.alias, path=mapping.path)
        db.add(db_mapping)
    db.commit()
    return FolderMapping(alias=db_mapping.alias, path=db_mapping.path)

# PUBLIC_INTERFACE
@router.get("/folders", summary="List all mapped folders", description="Get all currently mapped/monitored folders.", response_model=List[FolderMapping])
async def list_mapped_folders(db: Session = Depends(get_db)):
    folders = db.query(FolderMappingORM).all()
    return [FolderMapping(path=f.path, alias=f.alias) for f in folders]
