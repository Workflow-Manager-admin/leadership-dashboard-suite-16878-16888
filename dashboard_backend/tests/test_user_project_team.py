import pytest

@pytest.mark.asyncio
async def test_user_project_team_listing_and_fetch(async_client, test_user_data):
    # Register and log in
    await async_client.post("/api/auth/register", json=test_user_data)
    resp = await async_client.post(
        "/api/auth/token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List teams/projects (should be empty)
    res1 = await async_client.get("/api/user/teams", headers=headers)
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)
    res2 = await async_client.get("/api/user/projects", headers=headers)
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)
