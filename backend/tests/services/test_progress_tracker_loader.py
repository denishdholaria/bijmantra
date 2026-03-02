import pytest
from unittest.mock import patch, mock_open
import json
from pathlib import Path
from app.services.progress_tracker import load_metrics_json_sync, FALLBACK_METRICS, METRICS_PATHS

# Mock data
VALID_METRICS = {
    "lastUpdated": "2025-01-01",
    "pages": {"total": 10},
    "api": {"totalEndpoints": 50},
    "modules": {"total": 2, "list": []},
    "techStack": {}
}

def test_load_metrics_json_sync_success():
    """Test loading metrics when file exists and is valid (Happy Path)"""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(VALID_METRICS))):

        result = load_metrics_json_sync()
        assert result == VALID_METRICS

def test_load_metrics_json_sync_file_not_found():
    """Test loading metrics when file does not exist (fallback)"""
    with patch("pathlib.Path.exists", return_value=False):
        result = load_metrics_json_sync()
        assert result == FALLBACK_METRICS

def test_load_metrics_json_sync_invalid_json():
    """Test loading metrics when file contains invalid JSON"""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="invalid json")):

        result = load_metrics_json_sync()
        assert result == FALLBACK_METRICS

def test_load_metrics_json_sync_os_error():
    """Test loading metrics when file open raises OSError"""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", side_effect=OSError("Read error")):

        result = load_metrics_json_sync()
        assert result == FALLBACK_METRICS

def test_load_metrics_json_sync_first_fails_second_succeeds():
    """Test when first path fails (missing), second succeeds"""
    # Verify we have at least 2 paths to test
    if len(METRICS_PATHS) < 2:
        pytest.skip("Not enough metrics paths to test fallback chain")

    def side_effect_exists(path_instance):
        # Check against the actual Path objects in METRICS_PATHS
        if str(path_instance) == str(METRICS_PATHS[0]):
            return False
        if str(path_instance) == str(METRICS_PATHS[1]):
            return True
        return False

    with patch("pathlib.Path.exists", autospec=True, side_effect=side_effect_exists), \
         patch("builtins.open", mock_open(read_data=json.dumps(VALID_METRICS))):

        result = load_metrics_json_sync()
        assert result == VALID_METRICS
