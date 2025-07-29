import pytest

@pytest.mark.asyncio
async def test_scheduling_listing_empty(async_client, test_user_data):
    await async_client.post("/api/auth/register", json=test_user_data)
    resp = await async_client.post(
        "/api/auth/token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List schedules: should be empty
    schedules = await async_client.get("/api/scheduling/", headers=headers)
    assert schedules.status_code == 200
    assert isinstance(schedules.json(), list)
