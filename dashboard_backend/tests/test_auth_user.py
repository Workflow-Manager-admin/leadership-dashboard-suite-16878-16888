import pytest

@pytest.mark.asyncio
async def test_user_registration_and_login(async_client, test_user_data):
    # Register new user
    resp = await async_client.post("/api/auth/register", json=test_user_data)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["email"] == test_user_data["email"]

    # Attempt duplicate registration should fail
    resp2 = await async_client.post("/api/auth/register", json=test_user_data)
    assert resp2.status_code == 400

    # Login
    resp3 = await async_client.post(
        "/api/auth/token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    assert resp3.status_code == 200
    token = resp3.json()["access_token"]
    assert token

    # Verify /api/user/me with JWT
    headers = {"Authorization": f"Bearer {token}"}
    resp4 = await async_client.get("/api/user/me", headers=headers)
    assert resp4.status_code == 200
    data = resp4.json()
    assert data["email"] == test_user_data["email"]

@pytest.mark.asyncio
async def test_superuser_flag_on_admin_register(async_client, test_admin_data):
    # Register admin (will be a regular user, not superuser by default)
    resp = await async_client.post("/api/auth/register", json=test_admin_data)
    assert resp.status_code == 200
    user = resp.json()
    assert user["email"] == test_admin_data["email"]
    assert "is_active" in user
