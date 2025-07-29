from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm import Session

from src.api.models import ClassificationTag as ClassificationTagORM
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
async def apply_tags(classification: ClassificationInput, db: Session = Depends(get_db)):
    # Remove old tags for this file
    db.query(ClassificationTagORM).filter_by(filename=classification.filename).delete()
    # Add new tags
    for tag in classification.tags:
        t = ClassificationTagORM(filename=classification.filename, tag=tag)
        db.add(t)
    db.commit()
    return ClassificationResult(filename=classification.filename, tags=classification.tags)
