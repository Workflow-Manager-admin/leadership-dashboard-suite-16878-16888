def test_websocket_connect_and_ack(sync_test_client):
    with sync_test_client.websocket_connect("/ws/dashboard/updates") as websocket:
        websocket.send_json({"event": "subscribe", "dashboard_id": "DASH1"})
        response = websocket.receive_json()
        assert response["event"] == "subscription_ack"
        assert response["dashboard_id"] == "DASH1"
