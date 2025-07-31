from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.routes.auth import get_current_user

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
async def create_template(
    template: TemplateModel,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Save or update template to MongoDB (owned by current user).
    """
    await db.templates.update_one(
        {"template_id": template.template_id, "user_id": str(user["_id"])},
        {"$set": {"template_id": template.template_id, "name": template.name, "config": template.config, "user_id": str(user["_id"])}},
        upsert=True
    )
    return template

# PUBLIC_INTERFACE
@router.get("/", summary="List dashboard templates", description="Get all saved dashboard templates.", response_model=List[TemplateSummary])
async def list_templates(
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Retrieve all saved dashboard templates (owned by user as summaries only).
    """
    cursor = db.templates.find({"user_id": str(user["_id"])})
    result = []
    async for doc in cursor:
        result.append(TemplateSummary(template_id=doc["template_id"], name=doc.get("name", "")))
    return result
