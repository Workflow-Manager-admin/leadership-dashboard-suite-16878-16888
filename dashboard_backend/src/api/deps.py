"""
FastAPI dependency for MongoDB database.
"""

from .db import db

# PUBLIC_INTERFACE
def get_db():
    """Yield the MongoDB database handle."""
    yield db
