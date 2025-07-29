from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

class ClassificationInput(BaseModel):
    filename: str = Field(..., description="Filename to classify/tag")
    tags: List[str] = Field(..., description="Manual or rule-based tags")

class ClassificationResult(BaseModel):
    filename: str
    tags: List[str]

# PUBLIC_INTERFACE
@router.post("/tag", summary="Apply manual tags or rules", description="Assign tags or classification rules to a parsed file.", response_model=ClassificationResult)
async def apply_tags(
    classification: ClassificationInput,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Store or update classification/tags for a given file in MongoDB.
    """
    await db.classification.update_one(
        {"filename": classification.filename},
        {"$set": {"filename": classification.filename, "tags": classification.tags}},
        upsert=True
    )
    return ClassificationResult(filename=classification.filename, tags=classification.tags)
