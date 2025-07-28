from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, List

router = APIRouter()

DASHBOARDS = {}

class DashboardConfig(BaseModel):
    dashboard_id: str = Field(..., description="Unique dashboard identifier")
    config: Dict[str, Any] = Field(..., description="Dashboard configuration (structure, widgets, filters etc.)")

class DashboardSummary(BaseModel):
    dashboard_id: str
    title: str

# PUBLIC_INTERFACE
@router.post("/config", summary="Save dashboard configuration", description="Store/update dashboard configuration for user.", response_model=DashboardConfig)
async def save_dashboard_config(config: DashboardConfig):
    DASHBOARDS[config.dashboard_id] = config.config
    return config

# PUBLIC_INTERFACE
@router.get("/configs", summary="List dashboards", description="List all dashboard configs (as summaries).", response_model=List[DashboardSummary])
async def list_dashboards():
    return [DashboardSummary(dashboard_id=did, title=conf.get("title", "")) for did, conf in DASHBOARDS.items()]

# PUBLIC_INTERFACE
@router.get("/config/{dashboard_id}", summary="Get dashboard config", description="Load dashboard config by ID", response_model=DashboardConfig)
async def get_dashboard_config(dashboard_id: str):
    conf = DASHBOARDS.get(dashboard_id, {})
    return DashboardConfig(dashboard_id=dashboard_id, config=conf)
