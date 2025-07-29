from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, List
from sqlalchemy.orm import Session

from src.api.models import Template as TemplateORM
from src.api.deps import get_db

router = APIRouter()

class TemplateModel(BaseModel):
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    config: Dict = Field(..., description="Template dashboard configuration")

class TemplateSummary(BaseModel):
    template_id: str
    name: str

# PUBLIC_INTERFACE
@router.post("/", summary="Create dashboard template", description="Save a dashboard template.", response_model=TemplateModel)
async def create_template(template: TemplateModel, db: Session = Depends(get_db)):
    db_template = db.query(TemplateORM).filter_by(template_id=template.template_id).first()
    if db_template:
        db_template.name = template.name
        db_template.config = template.config
    else:
        db_template = TemplateORM(template_id=template.template_id, name=template.name, config=template.config)
        db.add(db_template)
    db.commit()
    return template

# PUBLIC_INTERFACE
@router.get("/", summary="List dashboard templates", description="Get all saved dashboard templates.", response_model=List[TemplateSummary])
async def list_templates(db: Session = Depends(get_db)):
    templates = db.query(TemplateORM).all()
    return [TemplateSummary(template_id=t.template_id, name=t.name) for t in templates]
