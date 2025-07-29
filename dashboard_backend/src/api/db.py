import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "dashboard_db")

# Single shared Mongo client for the app
class MongoDB:
    """Initialize and manage MongoDB connection."""

    _client: AsyncIOMotorClient = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(MONGODB_URI)
        return cls._client

    @classmethod
    def get_db(cls):
        return cls.get_client()[MONGO_DB_NAME]

# Convenience function to get database
def get_database():
    return MongoDB.get_db()
