from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import List

from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class ClassificationInput(BaseModel):
    filename: str = Field(..., min_length=1, max_length=128, description="Filename to classify/tag")
    tags: List[str] = Field(..., min_items=1, max_items=20, description="Manual or rule-based tags")

class ClassificationResult(BaseModel):
    filename: str
    tags: List[str]

# PUBLIC_INTERFACE
@router.post(
    "/tag",
    summary="Apply manual tags or rules",
    description="Assign tags or classification rules to a parsed file.",
    response_model=ClassificationResult,
)
@rate_limit(10, 60)
async def apply_tags(
    request: Request,
    classification: ClassificationInput,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    # Remove old tags for this file
    await db["classification_tags"].delete_many({"filename": classification.filename})
    # Add new tags
    docs = [{"filename": classification.filename, "tag": tag} for tag in classification.tags]
    if docs:
        await db["classification_tags"].insert_many(docs)
    return ClassificationResult(filename=classification.filename, tags=classification.tags)
