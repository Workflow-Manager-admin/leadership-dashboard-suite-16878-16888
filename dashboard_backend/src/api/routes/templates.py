from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, List

router = APIRouter()

TEMPLATES = {}

class TemplateModel(BaseModel):
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    config: Dict = Field(..., description="Template dashboard configuration")

class TemplateSummary(BaseModel):
    template_id: str
    name: str

# PUBLIC_INTERFACE
@router.post("/", summary="Create dashboard template", description="Save a dashboard template.", response_model=TemplateModel)
async def create_template(template: TemplateModel):
    TEMPLATES[template.template_id] = template
    return template

# PUBLIC_INTERFACE
@router.get("/", summary="List dashboard templates", description="Get all saved dashboard templates.", response_model=List[TemplateSummary])
async def list_templates():
    return [TemplateSummary(template_id=tid, name=tmpl.name) for tid, tmpl in TEMPLATES.items()]
