import pytest

@pytest.mark.asyncio
async def test_upload_and_parse_missing_file(async_client, test_user_data):
    # Register/login
    await async_client.post("/api/auth/register", json=test_user_data)
    resp = await async_client.post(
        "/api/auth/token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to parse file that doesn't exist
    resp = await async_client.post("/api/parsing/parse", params={"filename": "nofile.xlsx"}, headers=headers)
    assert resp.status_code == 404
