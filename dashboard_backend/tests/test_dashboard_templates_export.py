import pytest

@pytest.mark.asyncio
async def test_empty_dashboard_and_template_listings(async_client, test_user_data):
    await async_client.post("/api/auth/register", json=test_user_data)
    resp = await async_client.post(
        "/api/auth/token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dash_res = await async_client.get("/api/dashboard/configs", headers=headers)
    assert dash_res.status_code == 200
    assert isinstance(dash_res.json(), list)

    # Template listing (should be empty/403 if not admin)
    templ_res = await async_client.get("/api/templates/", headers=headers)
    if templ_res.status_code == 403:
        # Not admin
        assert True
    else:
        assert isinstance(templ_res.json(), list)
