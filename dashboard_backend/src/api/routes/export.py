from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.deps import get_db

router = APIRouter()

class ExportRequest(BaseModel):
    dashboard_id: str = Field(..., description="ID of dashboard to export")
    format: str = Field(..., description="Export format: pdf | ppt | html")

class ExportResult(BaseModel):
    url: str = Field(..., description="Download URL or confirmation")

# PUBLIC_INTERFACE
@router.post("/dashboard", summary="Export dashboard data", description="Export dashboard as PDF, PPT, or HTML (stubbed returns a fake URL)", response_model=ExportResult)
async def export_dashboard(export: ExportRequest, db=Depends(get_db)):
    dash = await db["dashboards"].find_one({"dashboard_id": export.dashboard_id})
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    # TODO: Build/export report (PDF/PPT/HTML) here
    url = f"/mock_exports/{export.dashboard_id}.{export.format}"
    return ExportResult(url=url)
