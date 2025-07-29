"""
Monitoring (Prometheus-compatible metrics), structured logging, and health/liveness probe utilities for backend.

Provides:
- /metrics (Prometheus scrape endpoint)
- /healthz (deep health including MongoDB connectivity)
- Structured, context-rich JSON logging for all API traffic and errors
"""

import time
import logging
import sys
from functools import wraps
from fastapi import Request, status
from starlette.responses import JSONResponse, PlainTextResponse
from prometheus_client import Histogram, Counter, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

from src.api.db import db as mongo_db

# Logging: Structured JSON logs for all API calls and errors
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "funcName": getattr(record, "funcName", None),
            "lineno": record.lineno,
        }
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return str(log_record)

def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

# Prometheus metrics setup (registry is auto-discovered by prometheus_client)
registry = CollectorRegistry()

REQUEST_LATENCY = Histogram(
    "fastapi_request_duration_seconds",
    "Latency of FastAPI requests in seconds",
    ["method", "path", "status_code"],
    registry=registry,
)
REQUEST_COUNT = Counter(
    "fastapi_request_count_total",
    "Total HTTP request count",
    ["method", "path", "status_code"],
    registry=registry,
)
HEALTH_MONGO = Gauge(
    "dashboard_backend_mongo_up",
    "MongoDB health metric (1=healthy, 0=down)",
    registry=registry,
)

def prometheus_metrics_route():
    # Expose all metrics for Prometheus scraper
    return PlainTextResponse(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

def with_metrics(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        start_time = time.time()
        try:
            response = await func(request, *args, **kwargs)
            status_code = getattr(response, "status_code", status.HTTP_200_OK)
        except Exception:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            raise
        # Use the route path pattern if available, otherwise the literal path
        path = request.scope.get("route").path if hasattr(request.scope.get("route"), "path") else request.url.path
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(request.method, path, status_code).observe(latency)
        REQUEST_COUNT.labels(request.method, path, status_code).inc()
        return response
    return wrapper

async def database_healthy():
    try:
        await mongo_db.command("ping")
        return True
    except Exception:
        return False

# PUBLIC_INTERFACE
async def healthz_handler():
    db_healthy = await database_healthy()
    HEALTH_MONGO.set(1 if db_healthy else 0)
    status_val = "ok" if db_healthy else "degraded"
    result = {
        "status": status_val,
        "mongo": "up" if db_healthy else "down"
    }
    return JSONResponse(status_code=200 if db_healthy else 503, content=result)


# PUBLIC_INTERFACE
def add_monitoring_routes(app):
    """
    Add /metrics and /healthz endpoints. /healthz checks database.
    To be called from main.py after app creation.
    """
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus scrape endpoint."""
        return prometheus_metrics_route()

    @app.get("/healthz", tags=["Health"])
    async def healthz():
        """Full health check including DB/service status."""
        return await healthz_handler()

    # Patch structured logging globally
    configure_logging()
    @app.middleware("http")
    async def log_api_requests(request: Request, call_next):
        logger = logging.getLogger("dashboard_backend")
        req_id = request.headers.get("x-request-id") or str(int(time.time() * 1000))
        logger.info({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "request_id": req_id
        })
        try:
            resp = await call_next(request)
        except Exception:
            logger.exception({
                "event": "exception",
                "method": request.method,
                "path": request.url.path,
                "request_id": req_id
            })
            raise
        logger.info({
            "event": "response",
            "method": request.method,
            "path": request.url.path,
            "status_code": resp.status_code,
            "request_id": req_id
        })
        return resp
