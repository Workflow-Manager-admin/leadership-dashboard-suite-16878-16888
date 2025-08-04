import os
import shutil
import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
import sys

# Ensure src root is discoverable for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the FastAPI app for testing.
# The main FastAPI app is in src/api/main.py, named 'app'
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
    # Clean up: remove the entire date directory if it exists (test isolation).
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)

def test_file_upload_creates_dated_folder(cleanup_upload):
    """
    Integration test: file upload is stored in uploads/YYYY-MM-DD/.
    """
    # Dummy file to upload
    file_content = b"Test document content"
    file_name = "test_doc.txt"

    response = client.post(
        "/files/upload",
        files={"file": (file_name, io.BytesIO(file_content), "text/plain")},
    )

    assert response.status_code == 200, "Response code not 200, got: {}".format(response.status_code)
    resp_json = response.json()
    assert resp_json["file_name"] == file_name
    assert "upload_path" in resp_json.get("meta", {})

    # Check path matches uploads/YYYY-MM-DD/filename
    today = datetime.now().strftime("%Y-%m-%d")
    expected_dir = os.path.join("uploads", today)
    expected_path = os.path.join(expected_dir, file_name)
    # Check returned upload_path matches expected
    assert resp_json["meta"]["upload_path"] == expected_path
    # Check file physically exists (integration)
    assert os.path.exists(expected_path), f"File not found at {expected_path}"
