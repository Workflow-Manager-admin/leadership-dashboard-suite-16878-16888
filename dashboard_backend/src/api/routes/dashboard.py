from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

from src.api.routes.stream import broadcast_dashboard_event  # WebSocket broadcast helper

router = APIRouter()


class DashboardConfig(BaseModel):
    dashboard_id: str = Field(..., description="Unique dashboard identifier")
    config: Dict[str, Any] = Field(..., description="Dashboard configuration (structure, widgets, filters etc.)")


class DashboardSummary(BaseModel):
    dashboard_id: str
    title: str

# PUBLIC_INTERFACE
@router.post(
    "/config", summary="Save dashboard configuration", description="Store/update dashboard configuration for user.", response_model=DashboardConfig
)
async def save_dashboard_config(
    config: DashboardConfig,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Save or update dashboard config by dashboard_id to MongoDB.
    """
    await db.dashboards.update_one(
        {"dashboard_id": config.dashboard_id},
        {"$set": config.dict()},
        upsert=True,
    )
    # Broadcast to all connected websocket clients (fire-and-forget)
    asyncio.create_task(
        broadcast_dashboard_event("dashboard_update", {"dashboard_id": config.dashboard_id, "config": config.config})
    )
    return config

# PUBLIC_INTERFACE
@router.get(
    "/configs", summary="List dashboards", description="List all dashboard configs (as summaries).", response_model=List[DashboardSummary]
)
async def list_dashboards(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all dashboards with basic summary information.
    """
    cursor = db.dashboards.find()
    result = []
    async for doc in cursor:
        title = ""
        if doc["config"] and isinstance(doc["config"], dict):
            title = doc["config"].get("title", "")
        result.append(DashboardSummary(dashboard_id=doc["dashboard_id"], title=title))
    return result

# PUBLIC_INTERFACE
@router.get(
    "/config/{dashboard_id}", summary="Get dashboard config", description="Load dashboard config by ID", response_model=DashboardConfig
)
async def get_dashboard_config(
    dashboard_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Retrieve dashboard config by dashboard_id from MongoDB.
    """
    doc = await db.dashboards.find_one({"dashboard_id": dashboard_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard config not found")
    return DashboardConfig(dashboard_id=doc["dashboard_id"], config=doc["config"])
