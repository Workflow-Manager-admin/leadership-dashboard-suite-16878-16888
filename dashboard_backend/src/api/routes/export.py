from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Literal

from src.api.deps import get_db
from src.api.routes.auth import get_current_active_user
from src.api.security import rate_limit

router = APIRouter()

class ExportRequest(BaseModel):
    dashboard_id: str = Field(..., min_length=1, max_length=100, description="ID of dashboard to export")
    format: Literal["pdf", "ppt", "html"] = Field(..., description="Export format: pdf | ppt | html")

class ExportResult(BaseModel):
    url: str = Field(..., description="Download URL or confirmation")

# PUBLIC_INTERFACE
@router.post(
    "/dashboard",
    summary="Export dashboard data",
    description="Export dashboard as PDF, PPT, or HTML (stubbed returns a fake URL)",
    response_model=ExportResult
)
@rate_limit(10, 60)
async def export_dashboard(
    request: Request,
    export: ExportRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    dash = await db["dashboards"].find_one({"dashboard_id": export.dashboard_id})
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    # TODO: Build/export report (PDF/PPT/HTML) here
    url = f"/mock_exports/{export.dashboard_id}.{export.format}"
    return ExportResult(url=url)
