from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Literal
from src.api.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.utils import export_utils
import tempfile
import os
import uuid

router = APIRouter()

EXPORT_DIR = os.path.join(tempfile.gettempdir(), "dashboard_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

class ExportRequest(BaseModel):
    dashboard_id: str = Field(..., description="ID of dashboard to export")
    format: Literal['pdf', 'ppt', 'html'] = Field(..., description="Export format: pdf | ppt | html")

class ExportResult(BaseModel):
    url: str = Field(..., description="Download URL for exported file")

def _get_export_file_path(dashboard_id: str, fmt: str) -> str:
    return os.path.join(EXPORT_DIR, f"{dashboard_id}_{uuid.uuid4()}.{fmt}")

def _cleanup_file_later(path: str):
    # Schedule file for deletion after 5min (or when system cleans up temp files)
    pass  # For demo, just rely on tempfs

# PUBLIC_INTERFACE
@router.post(
    "/dashboard",
    summary="Export dashboard data",
    description="Export dashboard as PDF, PPT, or HTML (actual file, downloadable)",
    response_model=ExportResult,
    tags=["Export"]
)
async def export_dashboard(
    export: ExportRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Exports the dashboard config in the requested format, generates file, and returns download URL.
    Supported formats: pdf, ppt, html.
    """
    # Load dashboard config by ID
    doc = await db.dashboards.find_one({"dashboard_id": export.dashboard_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Dashboard {export.dashboard_id} not found")
    config = doc["config"]

    # Generate export file
    fmt = export.format.lower()
    tmpfile = _get_export_file_path(export.dashboard_id, fmt)

    if fmt == "html":
        html = export_utils.dashboard_to_html(config)
        with open(tmpfile, "w", encoding="utf-8") as f:
            f.write(html)
    elif fmt == "pdf":
        html = export_utils.dashboard_to_html(config)
        export_utils.generate_pdf_from_html(html, tmpfile)
    elif fmt == "ppt":
        export_utils.generate_ppt_from_dashboard(config, tmpfile)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {fmt}")

    # File will be available at download API endpoint below
    filename = f"{export.dashboard_id}_export.{fmt}"
    url = f"/api/export/download?file={os.path.basename(tmpfile)}&filename={filename}"
    return ExportResult(url=url)

# PUBLIC_INTERFACE
@router.get(
    "/download",
    summary="Download exported dashboard file",
    description="Download endpoint for exported PDF, PPT, or HTML file. Use the URL provided by /api/export/dashboard.",
    tags=["Export"]
)
async def download_exported_file(
    file: str = Query(..., description="Temporary file ID (as provided in the export URL)"),
    filename: str = Query(..., description="Suggested download filename for the user")
):
    """
    Returns the requested exported dashboard file for download.
    """
    export_path = os.path.join(EXPORT_DIR, file)
    if not os.path.isfile(export_path):
        raise HTTPException(status_code=404, detail="Export file not found - try exporting again.")
    # Use FileResponse to allow file download
    return FileResponse(export_path, filename=filename, media_type="application/octet-stream")
