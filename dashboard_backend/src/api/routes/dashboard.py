from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from src.api.models import Dashboard as DashboardORM
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
async def save_dashboard_config(config: DashboardConfig, db: Session = Depends(get_db)):
    db_obj = db.query(DashboardORM).filter_by(dashboard_id=config.dashboard_id).first()
    if db_obj:
        db_obj.config = config.config
    else:
        db_obj = DashboardORM(dashboard_id=config.dashboard_id, config=config.config)
        db.add(db_obj)
    db.commit()
    return config

# PUBLIC_INTERFACE
@router.get("/configs", summary="List dashboards", description="List all dashboard configs (as summaries).", response_model=List[DashboardSummary])
async def list_dashboards(db: Session = Depends(get_db)):
    dashboards = db.query(DashboardORM).all()
    return [
        DashboardSummary(
            dashboard_id=dbdash.dashboard_id,
            title=dbdash.config.get("title", "") if isinstance(dbdash.config, dict) else ""
        )
        for dbdash in dashboards
    ]

# PUBLIC_INTERFACE
@router.get("/config/{dashboard_id}", summary="Get dashboard config", description="Load dashboard config by ID", response_model=DashboardConfig)
async def get_dashboard_config(dashboard_id: str, db: Session = Depends(get_db)):
    db_obj = db.query(DashboardORM).filter_by(dashboard_id=dashboard_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return DashboardConfig(dashboard_id=dashboard_id, config=db_obj.config)
