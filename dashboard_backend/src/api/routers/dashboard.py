"""
Dashboard APIs: fetch data, filter, configure KPIs and charts, templates.
"""
from fastapi import APIRouter, Depends
from typing import List, Optional, Any
from pydantic import BaseModel, Field

router = APIRouter()

# === Models ===

class DashboardFilter(BaseModel):
    date_from: Optional[str] = Field(None, description="Start date for data filter")
    date_to: Optional[str] = Field(None, description="End date for data filter")
    project: Optional[str] = Field(None, description="Project filter")
    team: Optional[str] = Field(None, description="Team filter")

class ChartOption(BaseModel):
    chart_id: str
    title: str
    type: str
    kpi: str
    config: dict

class KPIOption(BaseModel):
    kpi_id: str
    name: str
    description: str

class DashboardTemplate(BaseModel):
    template_id: str
    name: str
    config: dict

class DashboardResult(BaseModel):
    dashboard_id: str
    data: Any
    charts: List[ChartOption]
    kpis: List[KPIOption]
    summary: str

# === Endpoints ===

# PUBLIC_INTERFACE
@router.get("/", response_model=List[DashboardResult], summary="Fetch dashboards", description="Fetch list of dashboards, with charts, KPIs, and data.")
async def get_dashboards(filters: DashboardFilter = Depends()):
    """Return available dashboard views filtered by params (stub)."""
    # TODO: Fetch dashboards from DB / compute according to user config and filters
    # Dummy response
    return []

# PUBLIC_INTERFACE
@router.get("/charts", response_model=List[ChartOption], summary="List chart options", description="Lists all chart options and configs.")
async def list_charts():
    return [
        ChartOption(chart_id="1", title="Project Progress", type="bar", kpi="progress", config={}),
    ]

# PUBLIC_INTERFACE
@router.get("/kpis", response_model=List[KPIOption], summary="List KPI options", description="Lists available key performance indicators.")
async def list_kpis():
    return [
        KPIOption(kpi_id="1", name="On Time Delivery", description="Percent of milestones delivered on time."),
    ]

# PUBLIC_INTERFACE
@router.post("/template", response_model=DashboardTemplate, summary="Create dashboard template", description="Creates a reusable dashboard template.")
async def create_template(template: DashboardTemplate):
    # TODO: Persist template in DB
    return template

# PUBLIC_INTERFACE
@router.get("/template", response_model=List[DashboardTemplate], summary="List dashboard templates", description="Lists all templates.")
async def list_templates():
    return []
