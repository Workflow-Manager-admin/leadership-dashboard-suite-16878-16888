from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class TemplateModel(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=64, description="Unique template identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    config: Dict = Field(..., description="Template dashboard configuration")
    version: Optional[int] = None
    updated_at: Optional[datetime] = None

class TemplateSummary(BaseModel):
    template_id: str
    name: str

# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Create dashboard template",
    description="Save a dashboard template (versioned).",
    response_model=TemplateModel,
)
@rate_limit(5, 60)
async def create_template(
    request: Request,
    template: TemplateModel,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Admin-only for creation to avoid template flooding
    if not current_user.get("is_superuser", False):
        raise HTTPException(status_code=403, detail="Only admin can create templates.")
    prev = await db["templates"].find_one({"template_id": template.template_id})
    next_version = (prev["version"] + 1) if prev and "version" in prev else 1
    # Store in template version history
    await db["template_versions"].insert_one({
        "template_id": template.template_id,
        "name": template.name,
        "config": template.config,
        "version": next_version,
        "updated_at": datetime.utcnow(),
        "updated_by": current_user["email"],
    })
    updated_doc = {
        "template_id": template.template_id,
        "name": template.name,
        "config": template.config,
        "version": next_version,
        "updated_at": datetime.utcnow(),
    }
    await db["templates"].update_one(
        {"template_id": template.template_id},
        {"$set": updated_doc},
        upsert=True,
    )
    return TemplateModel(**updated_doc)

# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List dashboard templates",
    description="Get all saved dashboard templates.",
    response_model=List[TemplateSummary],
)
@rate_limit(20, 60)
async def list_templates(
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    templates = await db["templates"].find({}).to_list(length=100)
    return [TemplateSummary(template_id=t["template_id"], name=t["name"]) for t in templates]
