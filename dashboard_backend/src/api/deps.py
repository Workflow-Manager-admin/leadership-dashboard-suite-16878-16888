"""
FastAPI database dependency for SQLAlchemy session.
"""

from .db import SessionLocal

# PUBLIC_INTERFACE
def get_db():
    """Yield a new SQLAlchemy session for a request and close after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
