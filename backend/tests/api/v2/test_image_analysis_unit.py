
import os
import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi import UploadFile
from fastapi.testclient import TestClient
from app.api.v2.image_analysis import router

# Setup a minimal app for testing
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def mock_tempfile():
    with patch("app.api.v2.image_analysis.tempfile") as mock:
        yield mock

@pytest.fixture
def mock_shutil():
    with patch("app.api.v2.image_analysis.shutil") as mock:
        yield mock

@pytest.fixture
def mock_os():
    with patch("app.api.v2.image_analysis.os") as mock:
        # Mock os.path completely but wire up splitext to real one
        mock.path.splitext.side_effect = os.path.splitext
        yield mock

@pytest.fixture
def mock_spectral():
    with patch("app.api.v2.image_analysis.spectral_indices") as mock:
        yield mock

def test_analyze_spectral_indices_tgi(mock_tempfile, mock_shutil, mock_os, mock_spectral):
    # Mock temp file creation
    mock_fd = 123
    mock_path = "/tmp/test_input.png"
    mock_tempfile.mkstemp.return_value = (mock_fd, mock_path)

    # Mock os.fdopen to return a mock file handle
    mock_file_handle = MagicMock()
    mock_os.fdopen.return_value.__enter__.return_value = mock_file_handle

    # Mock os.path.exists to verify files exist for processing and cleanup
    # Sequence:
    # 1. Processing check (exists=True)
    # 2. Cleanup (exists=True)
    mock_os.path.exists.return_value = True

    # Mock spectral calculation
    mock_spectral.calculate_tgi.return_value = "processed_image_array"

    # Prepare input
    files = {"file": ("input.png", b"fake-image-content", "image/png")}
    data = {"index": "tgi"}

    # Execute
    # We need to mock the reading of the output file too
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = b"processed-content"

        response = client.post("/image-analysis/spectral-indices", files=files, data=data)

    # Verify
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["index"] == "tgi"
    assert "data:image/png;base64," in json_resp["image_data"]

    # Verify blocking I/O was called
    mock_tempfile.mkstemp.assert_called_with(suffix=".png")
    mock_shutil.copyfileobj.assert_called()
    mock_os.fdopen.assert_called_with(mock_fd, "wb")

    # Verify cleanup (remove called for both input and output)
    assert mock_os.remove.call_count >= 2
    mock_os.remove.assert_any_call(mock_path)
    mock_os.remove.assert_any_call(mock_path + "_out.png")

def test_analyze_spectral_indices_cleanup_on_error(mock_tempfile, mock_shutil, mock_os):
    # Simulate error during write
    mock_tempfile.mkstemp.return_value = (123, "/tmp/fail.png")
    mock_os.fdopen.side_effect = Exception("Write failed")
    mock_os.path.exists.return_value = True # For cleanup check

    files = {"file": ("fail.png", b"content", "image/png")}
    data = {"index": "tgi"}

    response = client.post("/image-analysis/spectral-indices", files=files, data=data)

    assert response.status_code == 500
    assert "Write failed" in response.text

    # Verify it attempted to remove the file
    mock_os.remove.assert_called_with("/tmp/fail.png")
