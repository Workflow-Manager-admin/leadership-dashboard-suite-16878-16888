from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.ingestion import router as ingestion_router
from src.api.routes.parsing import router as parsing_router
from src.api.routes.classification import router as classification_router
from src.api.routes.kpi import router as kpi_router
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.export import router as export_router
from src.api.routes.templates import router as templates_router
from src.api.routes.scheduling import router as scheduling_router

# --- DB: Create ORM tables at app startup ---
from src.api.db import Base, engine

# Ensure models are imported for table creation
import src.api.models  # noqa: F401
import src.api.models_auth  # noqa: F401

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SLT Dashboard Backend",
    description="Backend API for SLT configurable dashboards, file ingestion (Excel/PPT/PDF/Word), parsing, manual tagging, KPI/dashboards, templates, exports, and report scheduling.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Ingestion", "description": "File and folder ingestion/mapping APIs"},
        {"name": "Parsing", "description": "File parsing APIs"},
        {"name": "Classification", "description": "Data classification/tagging APIs"},
        {"name": "KPI", "description": "KPIs, analytics, and calculations"},
        {"name": "Dashboard", "description": "Dashboard configuration and data APIs"},
        {"name": "Export", "description": "Data and dashboard export APIs"},
        {"name": "Templates", "description": "Dashboard template management"},
        {"name": "Scheduling", "description": "Report scheduling API endpoints"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint for SLT Dashboard Backend."""
    return {"message": "Healthy"}


# Register routers for each domain
app.include_router(ingestion_router, prefix="/api/ingestion", tags=["Ingestion"])
app.include_router(parsing_router, prefix="/api/parsing", tags=["Parsing"])
app.include_router(classification_router, prefix="/api/classification", tags=["Classification"])
app.include_router(kpi_router, prefix="/api/kpi", tags=["KPI"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(export_router, prefix="/api/export", tags=["Export"])
app.include_router(templates_router, prefix="/api/templates", tags=["Templates"])
app.include_router(scheduling_router, prefix="/api/scheduling", tags=["Scheduling"])

from src.api.routes.auth import router as auth_router
from src.api.routes.user import router as user_router
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/user", tags=["User"])
