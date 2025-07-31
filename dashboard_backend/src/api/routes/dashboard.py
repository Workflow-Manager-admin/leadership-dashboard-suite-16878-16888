from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
from src.api.routes.stream import broadcast_dashboard_event  # WebSocket broadcast helper
from src.api.routes.auth import get_current_user
from src.api.models import (
    DashboardConfigEntity,
    DashboardConfigCreateEntity,
    DashboardConfigUpdateEntity,
)

router = APIRouter()

class DashboardSummary(BaseModel):
    dashboard_id: str
    title: str = ""
    description: str = ""

# PUBLIC_INTERFACE
@router.post(
    "/config",
    summary="Save dashboard configuration",
    description="Store a new dashboard configuration for user.",
    response_model=DashboardConfigEntity,
    status_code=201
)
async def create_dashboard_config(
    dashboard: DashboardConfigCreateEntity,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Create a new dashboard config.
    Ensures dashboard_id is unique for this user.
    """
    doc = await db.dashboards.find_one({"dashboard_id": dashboard.dashboard_id, "user_id": str(user["_id"]), "is_archived": {"$ne": True}})
    if doc:
        raise HTTPException(status_code=400, detail="Dashboard with this ID already exists.")
    doc = {
        "dashboard_id": dashboard.dashboard_id,
        "user_id": str(user["_id"]),
        "config": dashboard.config,
        "title": dashboard.title,
        "description": dashboard.description,
        "is_archived": False,
    }
    await db.dashboards.insert_one(doc)
    asyncio.create_task(
        broadcast_dashboard_event("dashboard_create", {"dashboard_id": dashboard.dashboard_id, "config": dashboard.config})
    )
    return DashboardConfigEntity(**doc)

# PUBLIC_INTERFACE
@router.get(
    "/configs",
    summary="List dashboards",
    description="List all dashboard configs (as summaries) owned by current user.",
    response_model=List[DashboardSummary],
)
async def list_dashboards(
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    List all dashboards belonging to the current user.
    Excludes archived dashboards.
    """
    cursor = db.dashboards.find({"user_id": str(user["_id"]), "is_archived": {"$ne": True}})
    result = []
    async for doc in cursor:
        result.append(DashboardSummary(
            dashboard_id=doc["dashboard_id"],
            title=doc.get("title", "") or doc.get("config", {}).get("title", ""),
            description=doc.get("description", "")
        ))
    return result

# PUBLIC_INTERFACE
@router.get(
    "/config/{dashboard_id}",
    summary="Get dashboard config",
    description="Load dashboard config by ID (must be owned by requestor)",
    response_model=DashboardConfigEntity,
)
async def get_dashboard_config(
    dashboard_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Retrieve dashboard config by dashboard_id from MongoDB, only if owned by current user.
    """
    doc = await db.dashboards.find_one({"dashboard_id": dashboard_id, "user_id": str(user["_id"]), "is_archived": {"$ne": True}})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard config not found")
    return DashboardConfigEntity(**doc)

# PUBLIC_INTERFACE
@router.put(
    "/config/{dashboard_id}",
    summary="Update dashboard config",
    description="Update a dashboard configuration for user.",
    response_model=DashboardConfigEntity,
)
async def update_dashboard_config(
    dashboard_id: str,
    update: DashboardConfigUpdateEntity,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user)
):
    """
    Update dashboard config (any or all fields) for a specific dashboard owned by user.
    """
    doc = await db.dashboards.find_one({"dashboard_id": dashboard_id, "user_id": str(user["_id"])})
    if not doc or doc.get("is_archived", False):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    update_data = {}
    if update.config is not None:
        update_data["config"] = update.config
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.is_archived is not None:
        update_data["is_archived"] = update.is_archived
    if update_data:
        await db.dashboards.update_one({"dashboard_id": dashboard_id, "user_id": str(user["_id"])}, {"$set": update_data})
        asyncio.create_task(
            broadcast_dashboard_event("dashboard_update", {"dashboard_id": dashboard_id, "fields": update_data})
        )
    new_doc = await db.dashboards.find_one({"dashboard_id": dashboard_id, "user_id": str(user["_id"])})
    return DashboardConfigEntity(**new_doc)

# PUBLIC_INTERFACE
@router.delete(
    "/config/{dashboard_id}",
    summary="Delete (archive) dashboard config",
    description="Soft-delete (archive) dashboard owned by the current user.",
    status_code=204,
)
async def archive_dashboard_config(
    dashboard_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user=Depends(get_current_user),
):
    """
    Soft-delete a dashboard config. (Retains data but marks `is_archived`=True)
    """
    doc = await db.dashboards.find_one({"dashboard_id": dashboard_id, "user_id": str(user["_id"])})
    if not doc or doc.get("is_archived", False):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    await db.dashboards.update_one({"dashboard_id": dashboard_id, "user_id": str(user["_id"])}, {"$set": {"is_archived": True}})
    asyncio.create_task(
        broadcast_dashboard_event("dashboard_delete", {"dashboard_id": dashboard_id})
    )
    return
