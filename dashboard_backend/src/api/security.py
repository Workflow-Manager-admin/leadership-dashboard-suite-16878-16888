"""
Core security, RBAC, rate limiting, and exceptionhandler utilities for the dashboard_backend.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
from functools import wraps
import time

# Simple in-memory rate limiting: Not production-grade, but works per-process.
rate_limit_storage = {}

def get_user_roles(user: dict) -> List[str]:
    return user.get("roles", ["user"]) if user else ["anonymous"]

# PUBLIC_INTERFACE
def require_roles(roles: List[str]):
    """
    Decorator for FastAPI dependencies to enforce RBAC for endpoint access.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if user is None:
                # Try positional find
                for v in args:
                    if isinstance(v, dict) and "email" in v and "is_active" in v:
                        user = v
                        break
            user_roles = get_user_roles(user)
            if not any(role in user_roles for role in roles):
                raise HTTPException(status_code=403, detail="Insufficient privileges")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# PUBLIC_INTERFACE
def rate_limit(limit: int, period_sec: int = 60):
    """
    Simple rate limiting decorator.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            ip = request.client.host
            now = int(time.time())
            key = f"{func.__name__}:{ip}"
            counts, last_window = rate_limit_storage.get(key, (0, now))
            if now - last_window > period_sec:
                counts = 0
                last_window = now
            if counts >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {limit} requests every {period_sec} seconds.",
                )
            rate_limit_storage[key] = (counts + 1, last_window)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# PUBLIC_INTERFACE
def register_global_exception_handlers(app):
    """
    Register generic exception handlers (HTTPException, ValidationError, 500s).
    """
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Log error here if logging configured.
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )

