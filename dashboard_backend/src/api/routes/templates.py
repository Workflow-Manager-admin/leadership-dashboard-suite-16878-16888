from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, List

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
async def create_template(template: TemplateModel, db=Depends(get_db)):
    await db["templates"].update_one(
        {"template_id": template.template_id},
        {"$set": {"name": template.name, "config": template.config}},
        upsert=True,
    )
    return template

# PUBLIC_INTERFACE
@router.get("/", summary="List dashboard templates", description="Get all saved dashboard templates.", response_model=List[TemplateSummary])
async def list_templates(db=Depends(get_db)):
    templates = await db["templates"].find({}).to_list(length=100)
    return [TemplateSummary(template_id=t["template_id"], name=t["name"]) for t in templates]
