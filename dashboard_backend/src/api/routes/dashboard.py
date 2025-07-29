from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class DashboardConfig(BaseModel):
    dashboard_id: str = Field(..., min_length=1, max_length=100, description="Unique dashboard identifier")
    config: Dict[str, Any] = Field(..., description="Dashboard configuration (structure, widgets, filters etc.)")
    version: Optional[int] = Field(default=None, description="Config version (auto-increment)")
    updated_at: Optional[datetime] = None

class DashboardSummary(BaseModel):
    dashboard_id: str
    title: str

# PUBLIC_INTERFACE
@router.post(
    "/config",
    summary="Save dashboard configuration",
    description="Store/update dashboard configuration for user, with versioning.",
    response_model=DashboardConfig,
)
@rate_limit(10, 60)
async def save_dashboard_config(
    request: Request,
    config: DashboardConfig,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    dashboards = db["dashboards"]
    # Only admin or owner can create/update (basic RBAC, extend as needed)
    if not current_user.get("is_superuser", False):
        raise HTTPException(status_code=403, detail="Only admin can update dashboard config.")
    prev_doc = await dashboards.find_one({"dashboard_id": config.dashboard_id})
    next_version = (prev_doc["version"] + 1) if prev_doc and "version" in prev_doc else 1
    # Save to version history too
    await db["dashboard_versions"].insert_one({
        "dashboard_id": config.dashboard_id,
        "config": config.config,
        "version": next_version,
        "updated_at": datetime.utcnow(),
        "updated_by": current_user["email"]
    })
    updated_doc = {
        "dashboard_id": config.dashboard_id,
        "config": config.config,
        "version": next_version,
        "updated_at": datetime.utcnow()
    }
    await dashboards.update_one(
        {"dashboard_id": config.dashboard_id},
        {"$set": updated_doc},
        upsert=True,
    )
    return DashboardConfig(**updated_doc)

# PUBLIC_INTERFACE
@router.get(
    "/configs",
    summary="List dashboards",
    description="List all dashboard configs (as summaries).",
    response_model=List[DashboardSummary],
)
@rate_limit(20, 60)
async def list_dashboards(
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    dashboards = await db["dashboards"].find({}).to_list(length=100)
    summaries = []
    for dash in dashboards:
        config = dash.get("config", {}) if isinstance(dash.get("config", {}), dict) else {}
        title = config.get("title", "") if isinstance(config, dict) else ""
        summaries.append(DashboardSummary(dashboard_id=dash["dashboard_id"], title=title))
    return summaries

# PUBLIC_INTERFACE
@router.get(
    "/config/{dashboard_id}",
    summary="Get dashboard config",
    description="Load dashboard config by ID",
    response_model=DashboardConfig,
)
@rate_limit(20, 60)
async def get_dashboard_config(
    request: Request,
    dashboard_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    doc = await db["dashboards"].find_one({"dashboard_id": dashboard_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return DashboardConfig(
        dashboard_id=dashboard_id,
        config=doc.get("config", {}),
        version=doc.get("version"),
        updated_at=doc.get("updated_at"),
    )
