"""
APIs for folder mapping configuration & management.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

router = APIRouter()

class FolderMapping(BaseModel):
    folder_id: str = Field(..., description="Unique ID for folder mapping")
    folder_path: str = Field(..., description="Absolute or virtual folder path")
    mapping_type: str = Field(..., description="Type (local, SMB, OneDrive, etc.)")
    meta: Optional[Dict] = Field({}, description="Other settings/meta")

# In-memory stub
FOLDERS = {}

# PUBLIC_INTERFACE
@router.get("/", response_model=List[FolderMapping], summary="List all folder mappings")
def list_mappings():
    """Return all configured folder mappings."""
    return list(FOLDERS.values())

# PUBLIC_INTERFACE
@router.post("/", response_model=FolderMapping, summary="Create a new folder mapping")
def create_mapping(mapping: FolderMapping):
    FOLDERS[mapping.folder_id] = mapping
    return mapping

# PUBLIC_INTERFACE
@router.delete("/{folder_id}", summary="Delete folder mapping")
def delete_mapping(folder_id: str):
    FOLDERS.pop(folder_id, None)
    return {"deleted": folder_id}
