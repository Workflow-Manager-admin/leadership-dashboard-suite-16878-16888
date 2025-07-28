from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class ExportRequest(BaseModel):
    dashboard_id: str = Field(..., description="ID of dashboard to export")
    format: str = Field(..., description="Export format: pdf | ppt | html")

class ExportResult(BaseModel):
    url: str = Field(..., description="Download URL or confirmation")

# PUBLIC_INTERFACE
@router.post("/dashboard", summary="Export dashboard data", description="Export dashboard as PDF, PPT, or HTML (stubbed returns a fake URL)", response_model=ExportResult)
async def export_dashboard(export: ExportRequest):
    url = f"/mock_exports/{export.dashboard_id}.{export.format}"
    return ExportResult(url=url)
