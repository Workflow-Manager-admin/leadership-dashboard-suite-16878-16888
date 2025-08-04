import os
import shutil
import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
import sys

# Ensure src root is discoverable for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import FastAPI app
from src.api.main import app

client = TestClient(app)

@pytest.fixture(scope="function")
def cleanup_upload():
    """
    Fixture to cleanup created upload folder/files.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    base_dir = "uploads"
    upload_dir = os.path.join(base_dir, today)
    yield upload_dir
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)

@pytest.mark.xfail(
    reason=(
        "Uploading a document does not currently trigger creation of a dashboard entry. "
        "The backend needs to implement logic to create dashboards when files are uploaded. "
        "Currently, /dashboard/ always returns an empty list."
    ),
    strict=True,
)
def test_upload_document_and_dashboard_listing_integration(cleanup_upload):
    """
    INTEGRATION TEST: Upload a test document, then check /dashboard/.
    Expects uploaded file to result in a dashboard entry, but backend does not support this workflow yet.
    """
    file_content = b"Integration test dummy file for dashboard workflow"
    file_name = "test_dashboard_integration.txt"

    # Step 1: Upload a file
    response_upload = client.post(
        "/files/upload",
        files={"file": (file_name, io.BytesIO(file_content), "text/plain")},
    )
    assert response_upload.status_code == 200
    upload_json = response_upload.json()
    assert upload_json["file_name"] == file_name

    # (If processing/hook existed, trigger or wait here...)

    # Step 2: Get dashboards
    response_dashboards = client.get("/dashboard/")
    assert response_dashboards.status_code == 200
    dashboards = response_dashboards.json()

    # Check if uploaded file created a dashboard (expected to fail for stub)
    found_dashboard = False
    for dash in dashboards:
        # Assume there's some trace in dashboard (not defined in stub)
        if isinstance(dash, dict) and (file_name in str(dash.values()) or file_name in str(dash)):
            found_dashboard = True
            break

    assert found_dashboard, (
        "Dashboard list does not include dashboard related to uploaded file. "
        "Backend must implement linking uploaded file to dashboard."
    )
