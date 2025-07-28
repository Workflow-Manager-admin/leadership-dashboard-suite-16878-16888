from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()

TAGS = {}

class ClassificationInput(BaseModel):
    filename: str = Field(..., description="Filename to classify/tag")
    tags: List[str] = Field(..., description="Manual or rule-based tags")

class ClassificationResult(BaseModel):
    filename: str
    tags: List[str]

# PUBLIC_INTERFACE
@router.post("/tag", summary="Apply manual tags or rules", description="Assign tags or classification rules to a parsed file.", response_model=ClassificationResult)
async def apply_tags(classification: ClassificationInput):
    TAGS[classification.filename] = classification.tags
    return ClassificationResult(filename=classification.filename, tags=classification.tags)
