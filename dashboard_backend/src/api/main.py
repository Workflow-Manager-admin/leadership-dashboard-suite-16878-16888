"""Main FastAPI app for the SLT Leadership Dashboard Backend.

Features:
- Real-time dashboard visualization
- File ingestion, parsing, and classification
- KPI computation and charting
- Folder mapping and management
- Manual tagging and configurable rules
- Dashboard template/config API
- Interactive filters (date, project, team)
- Export endpoints (PDF/PPT/HTML)
- Summary insights API
- Scheduled export/report/email

Framework: FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Import routers and services
from src.api.routers import (
    file_ingest,
    dashboard,
    folder,
    tagging,
    kpi,
    export,
    scheduling,
    websocket_stream,
    file_ingest_list  # NEW: router for /files/list
)

openapi_tags = [
    {"name": "health", "description": "Health check and metadata."},
    {"name": "file-ingest", "description": "Upload, parse, classify, and process files."},
    {"name": "dashboard", "description": "Dashboard endpoints (fetch, filter, configure, chart selection, templates)."},
    {"name": "folder", "description": "Folder mapping and management APIs."},
    {"name": "tagging", "description": "Manual tagging and rule definition endpoints."},
    {"name": "kpi", "description": "Custom KPI computation logic and APIs."},
    {"name": "export", "description": "Export to PDF, PPT, HTML and export logic."},
    {"name": "scheduling", "description": "Scheduling, summary, and email report delivery."},
    {"name": "realtime", "description": "WebSocket streaming for real-time dashboard updates."},
]

app = FastAPI(
    title="SLT Leadership Dashboard Backend",
    description="Backend for file ingestion, parsing, KPI engine, configuration, and dashboard APIs with real-time streaming.",
    version="1.0.0",
    openapi_tags=openapi_tags,
    contact={"name": "SLT Dashboard Team"}
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["health"])
# PUBLIC_INTERFACE
def health_check():
    """Health check endpoint for readiness and monitoring."""
    return {"status": "healthy", "ts": datetime.now().isoformat()}

# API routers
app.include_router(file_ingest.router, prefix="/files", tags=["file-ingest"])
app.include_router(file_ingest_list.router, prefix="/files", tags=["file-ingest"])  # Register /files/list endpoint
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(folder.router, prefix="/folders", tags=["folder"])
app.include_router(tagging.router, prefix="/tagging", tags=["tagging"])
app.include_router(kpi.router, prefix="/kpi", tags=["kpi"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(scheduling.router, prefix="/schedule", tags=["scheduling"])

# Real-time (WebSocket for dashboard push updates)
app.include_router(websocket_stream.router, prefix="/ws", tags=["realtime"])
