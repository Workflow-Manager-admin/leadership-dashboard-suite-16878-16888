from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from .response_envelope import APIErrorEnvelope

async def http_error_handler(request: Request, exc: HTTPException):
    content = APIErrorEnvelope(
        success=False,
        error={"code": str(exc.status_code), "message": exc.detail or "HTTP error"},
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)

async def generic_error_handler(request: Request, exc: Exception):
    content = APIErrorEnvelope(
        success=False,
        error={
            "code": "internal_server_error",
            "message": str(exc) or "Internal Server Error"
        }
    ).model_dump()
    return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=content)

def init_error_handlers(app):
    """Register global error and exception handlers with FastAPI app."""
    from fastapi.exceptions import RequestValidationError
    from fastapi.exception_handlers import request_validation_exception_handler

    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, generic_error_handler)
