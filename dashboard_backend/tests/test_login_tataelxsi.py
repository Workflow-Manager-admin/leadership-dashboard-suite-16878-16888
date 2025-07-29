import pytest

@pytest.mark.asyncio
async def test_login_tataelxsi_email(async_client):
    # Try logging in with user that does not exist (should fail with 401 after passing domain check)
    valid_email = "john.doe@tataelxsi.co.in"
    valid_password = "secret123"

    resp = await async_client.post(
        "/api/auth/token",
        data={"username": valid_email, "password": valid_password}
    )
    # The API will check the domain first (email passes), then fail on user/password mismatch
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"

    # Register a valid @tataelxsi.co.in user
    register_payload = {
        "email": valid_email,
        "password": valid_password,
        "full_name": "John Doe"
    }
    resp2 = await async_client.post("/api/auth/register", json=register_payload)
    assert resp2.status_code == 200
    res_json = resp2.json()
    assert res_json["email"] == valid_email

    # Now login with correct credentials (should succeed)
    resp3 = await async_client.post(
        "/api/auth/token",
        data={"username": valid_email, "password": valid_password}
    )
    assert resp3.status_code == 200
    token_resp = resp3.json()
    assert "access_token" in token_resp
    assert token_resp["token_type"] == "bearer"

    # Try bad password (should fail)
    resp4 = await async_client.post(
        "/api/auth/token",
        data={"username": valid_email, "password": "wrongpass"}
    )
    assert resp4.status_code == 401
    assert resp4.json()["detail"] == "Incorrect email or password"

    # Try invalid domain (should reject before password even checked)
    resp5 = await async_client.post(
        "/api/auth/token",
        data={"username": "someone@example.com", "password": valid_password}
    )
    assert resp5.status_code == 401
    assert resp5.json()["detail"].startswith("Login restricted")

    # Optionally: Try registering with a non-tataelxsi email (should be rejected)
    bad_reg = {
        "email": "bad.user@example.com",
        "password": "irrelevant",
        "full_name": "Bad Guy"
    }
    resp6 = await async_client.post("/api/auth/register", json=bad_reg)
    assert resp6.status_code == 400
    assert "only '@tataelxsi.co.in'" in resp6.json()["detail"]

