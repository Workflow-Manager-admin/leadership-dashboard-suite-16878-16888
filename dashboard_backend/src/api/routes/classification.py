from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List

from src.api.deps import get_db

router = APIRouter()

class ClassificationInput(BaseModel):
    filename: str = Field(..., description="Filename to classify/tag")
    tags: List[str] = Field(..., description="Manual or rule-based tags")

class ClassificationResult(BaseModel):
    filename: str
    tags: List[str]

# PUBLIC_INTERFACE
@router.post("/tag", summary="Apply manual tags or rules", description="Assign tags or classification rules to a parsed file.", response_model=ClassificationResult)
async def apply_tags(classification: ClassificationInput, db=Depends(get_db)):
    # Remove old tags for this file
    await db["classification_tags"].delete_many({"filename": classification.filename})
    # Add new tags
    docs = [{"filename": classification.filename, "tag": tag} for tag in classification.tags]
    if docs:
        await db["classification_tags"].insert_many(docs)
    return ClassificationResult(filename=classification.filename, tags=classification.tags)
