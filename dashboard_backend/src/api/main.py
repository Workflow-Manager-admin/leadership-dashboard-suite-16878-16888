from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import new error handler initialization and API envelope
from src.api.utils.error_handlers import init_error_handlers
from src.api.utils.response_envelope import api_response

# from src.api.db import get_database  # (Removed, import was unused)
from src.api.routes.ingestion import router as ingestion_router
from src.api.routes.parsing import router as parsing_router
from src.api.routes.classification import router as classification_router
from src.api.routes.kpi import router as kpi_router
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.export import router as export_router
from src.api.routes.templates import router as templates_router
from src.api.routes.scheduling import router as scheduling_router
from src.api.routes.auth import router as auth_router
from src.api.utils.scheduler_utils import start_scheduler_once

from src.api.routes.stream import router as stream_router  # <-- WebSocket API
from src.api.routes.insights import router as insights_router  # <-- Insights API

app = FastAPI(
    title="SLT Dashboard Backend",
    description=(
        "Backend API for SLT configurable dashboards, file ingestion (Excel/PPT/PDF/Word), "
        "parses uploaded documents for structured data using openpyxl (Excel), python-pptx (PowerPoint), PyMuPDF (PDF), and python-docx (Word).\n\n"
        "APIs:\n"
        "- /api/ingestion/upload: Upload and parse Excel, PPTX, PDF, or Word files. Extracted tabular/textual data is stored in MongoDB.\n"
        "- /api/parsing/parse: Retrieve parsed content by filename. "
        "Supported file types: .xlsx, .xls, .pptx, .ppt, .pdf, .docx, .doc.\n"
        "See responses in openapi docs for details of structured output per file type."
    ),
    version="0.1.0",
    openapi_tags=[
        {"name": "Ingestion", "description": "File and folder ingestion/mapping APIs. Upload an Excel, PPTX, PDF, or Word file and its structured data will be parsed and stored."},
        {"name": "Parsing", "description": "File parsing APIs. Retrieve structured data for previously ingested files. Supported: Excel, PowerPoint, PDF, Word."},
        {"name": "Classification", "description": "Data classification/tagging APIs"},
        {"name": "KPI", "description": "KPIs, analytics, and calculations"},
        {"name": "Dashboard", "description": "Dashboard configuration and data APIs"},
        {"name": "Export", "description": "Data and dashboard export APIs"},
        {"name": "Templates", "description": "Dashboard template management"},
        {"name": "Scheduling", "description": "Report scheduling API endpoints"}
    ]
)

# Robust CORS setup for development and deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # "*" for dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handler middleware
init_error_handlers(app)

@app.on_event("startup")
async def on_startup():
    # Ensure that the background scheduler for scheduled report sending is started.
    start_scheduler_once()

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint for SLT Dashboard Backend."""
    return api_response(message="Healthy")

# Register routers for each domain
app.include_router(ingestion_router, prefix="/api/ingestion", tags=["Ingestion"])
app.include_router(parsing_router, prefix="/api/parsing", tags=["Parsing"])
app.include_router(classification_router, prefix="/api/classification", tags=["Classification"])
app.include_router(kpi_router, prefix="/api/kpi", tags=["KPI"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(export_router, prefix="/api/export", tags=["Export"])
app.include_router(templates_router, prefix="/api/templates", tags=["Templates"])
app.include_router(scheduling_router, prefix="/api/scheduling", tags=["Scheduling"])
app.include_router(insights_router, prefix="/api/insights", tags=["Insights"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Explicit WebSocket API registration & documentation
app.include_router(stream_router, tags=["Streaming"])

@app.get(
    "/api/stream/docs",
    tags=["Streaming"],
    summary="WebSocket Streaming API usage",
    description=(
        "This endpoint describes how to use the real-time data streaming WebSocket API.<br><br>"
        "**WebSocket Endpoint:** `/ws/dashboards`<br>"
        "- Connect using a WebSocket client to `ws://<backend>/ws/dashboards`.<br>"
        "- On data changes (dashboard, kpi, etc.) backend will push JSON: `{event: <event_type>, payload: <...>}`.<br>"
        "- Events: `dashboard_update`, `kpi_update`, ...<br>"
        "- To keep connection alive, send periodic 'ping' messages (receive 'pong')."
    ),
    response_model=None
)
def get_streaming_docs():
    """
    REST helper endpoint explaining the usage of streaming WebSocket API.
    """
    return {
        "websocket_endpoint": "/ws/dashboards",
        "purpose": "Real-time dashboard/data updates",
        "push_format": {"event": "<event_type>", "payload": "dict (details depend on event_type)"},
        "usage_notes": (
            "Connect with a WebSocket client (Browser, JS, Python, etc.). "
            "On dashboard or KPI data changes, the server will send push notifications. "
            "Send 'ping' for keep-alive."
        )
    }
