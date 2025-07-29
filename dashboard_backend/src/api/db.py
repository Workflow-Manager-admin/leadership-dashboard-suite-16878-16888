"""
MongoDB database initialization for the dashboard_backend using motor.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "dashboard_db")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[MONGODB_DB]
