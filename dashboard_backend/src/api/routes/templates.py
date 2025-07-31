from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.routes.auth import get_current_user
from src.api.models import (
    TemplateEntity,
    TemplateCreateEntity,
    TemplateUpdateEntity,
)

router = APIRouter()

class TemplateSummaryOut(BaseModel):
    template_id: str
    name: str
    description: str = ""

# PUBLIC_INTERFACE
@router.post(
    "/",
    summary="Create dashboard template",
    description="Save a new dashboard template for current user.",
    response_model=TemplateEntity,
    status_code=201
)
async def create_template(
    template: TemplateCreateEntity,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Save a new dashboard template, ensure template_id is unique for user.
    """
    exists = await db.templates.find_one({"template_id": template.template_id, "user_id": str(user["_id"]), "is_archived": {"$ne": True}})
    if exists:
        raise HTTPException(status_code=400, detail="Template with this ID already exists.")
    doc = {
        "template_id": template.template_id,
        "name": template.name,
        "config": template.config,
        "user_id": str(user["_id"]),
        "description": template.description or "",
        "is_archived": False,
    }
    await db.templates.insert_one(doc)
    return TemplateEntity(**doc)

# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="List dashboard templates",
    description="Get all saved dashboard templates (user only, not archived).",
    response_model=List[TemplateSummaryOut]
)
async def list_templates(
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Retrieve all dashboard templates owned by user, excluding archived.
    """
    cursor = db.templates.find({"user_id": str(user["_id"]), "is_archived": {"$ne": True}})
    result = []
    async for doc in cursor:
        result.append(TemplateSummaryOut(
            template_id=doc["template_id"],
            name=doc.get("name", ""),
            description=doc.get("description", "")
        ))
    return result

# PUBLIC_INTERFACE
@router.get(
    "/{template_id}",
    summary="Get dashboard template by id",
    description="Get dashboard template if owned by user.",
    response_model=TemplateEntity,
)
async def get_template(
    template_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    doc = await db.templates.find_one({"template_id": template_id, "user_id": str(user["_id"]), "is_archived": {"$ne": True}})
    if not doc:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateEntity(**doc)

# PUBLIC_INTERFACE
@router.put(
    "/{template_id}",
    summary="Update dashboard template",
    description="Update dashboard template by id for current user.",
    response_model=TemplateEntity,
)
async def update_template(
    template_id: str,
    update: TemplateUpdateEntity,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    doc = await db.templates.find_one({"template_id": template_id, "user_id": str(user["_id"])})
    if not doc or doc.get("is_archived", False):
        raise HTTPException(status_code=404, detail="Template not found")
    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.config is not None:
        update_data["config"] = update.config
    if update.description is not None:
        update_data["description"] = update.description
    if update.is_archived is not None:
        update_data["is_archived"] = update.is_archived
    if update_data:
        await db.templates.update_one({"template_id": template_id, "user_id": str(user["_id"])}, {"$set": update_data})
    new_doc = await db.templates.find_one({"template_id": template_id, "user_id": str(user["_id"])})
    return TemplateEntity(**new_doc)

# PUBLIC_INTERFACE
@router.delete(
    "/{template_id}",
    summary="Archive (delete) dashboard template",
    description="Soft-delete (archive) a dashboard template owned by current user.",
    status_code=204,
)
async def archive_template(
    template_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    doc = await db.templates.find_one({"template_id": template_id, "user_id": str(user["_id"])})
    if not doc or doc.get("is_archived", False):
        raise HTTPException(status_code=404, detail="Template not found")
    await db.templates.update_one({"template_id": template_id, "user_id": str(user["_id"])}, {"$set": {"is_archived": True}})
    return
