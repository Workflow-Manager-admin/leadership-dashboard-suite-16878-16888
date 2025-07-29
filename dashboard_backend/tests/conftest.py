import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from src.api.main import app
import asyncio

# Use a test-specific MongoDB (test isolation)
TEST_MONGODB_URL = os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017")
TEST_MONGODB_DB = os.getenv("TEST_MONGODB_DB", "dashboard_db_test")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def mongo_client():
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    yield client
    client.close()

@pytest.fixture(scope="function", autouse=True)
async def clear_test_db(mongo_client):
    # Clear database before each test function
    db = mongo_client[TEST_MONGODB_DB]
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})
    yield

@pytest.fixture(scope="module")
def sync_test_client():
    # For fastapi websocket sync API
    return TestClient(app)

@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture()
def test_user_data():
    return {
        "email": "testuser@example.com",
        "password": "secretpass",
        "full_name": "Test User"
    }

@pytest.fixture()
def test_admin_data():
    return {
        "email": "admin@example.com",
        "password": "supersecret",
        "full_name": "Admin User"
    }
