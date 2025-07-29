from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from src.api.deps import get_db

router = APIRouter()

class DashboardConfig(BaseModel):
    dashboard_id: str = Field(..., description="Unique dashboard identifier")
    config: Dict[str, Any] = Field(..., description="Dashboard configuration (structure, widgets, filters etc.)")

class DashboardSummary(BaseModel):
    dashboard_id: str
    title: str

# PUBLIC_INTERFACE
@router.post("/config", summary="Save dashboard configuration", description="Store/update dashboard configuration for user.", response_model=DashboardConfig)
async def save_dashboard_config(config: DashboardConfig, db=Depends(get_db)):
    dashboards = db["dashboards"]
    await dashboards.update_one(
        {"dashboard_id": config.dashboard_id},
        {"$set": {"config": config.config}},
        upsert=True,
    )
    return config

# PUBLIC_INTERFACE
@router.get("/configs", summary="List dashboards", description="List all dashboard configs (as summaries).", response_model=List[DashboardSummary])
async def list_dashboards(db=Depends(get_db)):
    dashboards = await db["dashboards"].find({}).to_list(length=100)
    summaries = []
    for dash in dashboards:
        config = dash.get("config", {})
        title = config.get("title", "") if isinstance(config, dict) else ""
        summaries.append(DashboardSummary(dashboard_id=dash["dashboard_id"], title=title))
    return summaries

# PUBLIC_INTERFACE
@router.get("/config/{dashboard_id}", summary="Get dashboard config", description="Load dashboard config by ID", response_model=DashboardConfig)
async def get_dashboard_config(dashboard_id: str, db=Depends(get_db)):
    doc = await db["dashboards"].find_one({"dashboard_id": dashboard_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return DashboardConfig(dashboard_id=dashboard_id, config=doc.get("config", {}))
