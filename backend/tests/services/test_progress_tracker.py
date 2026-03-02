
import pytest
from unittest.mock import patch, MagicMock
from app.services.progress_tracker import ProgressTrackerService, load_metrics_json

# Mock data
MOCK_METRICS = {
    "lastUpdated": "2025-01-01",
    "pages": {"total": 10, "functional": 5, "demo": 2, "uiOnly": 3},
    "api": {"totalEndpoints": 50, "brapiEndpoints": 20, "brapiCoverage": 80, "customEndpoints": 30},
    "modules": {
        "total": 2,
        "list": [
            {"name": "Module A", "pages": 5, "endpoints": 25},
            {"name": "Module B", "pages": 5, "endpoints": 25}
        ]
    },
    "techStack": {
        "frontend": ["React"],
        "backend": ["Python"],
        "database": ["Postgres"],
        "compute": ["Rust"]
    }
}

@pytest.fixture
def progress_service():
    return ProgressTrackerService()

@pytest.mark.asyncio
async def test_get_data_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS) as mock_load:
        data = await progress_service.get_data()

        mock_load.assert_called_once()
        assert data["summary"]["total_endpoints"] == 50
        assert data["summary"]["total_pages"] == 10
        assert len(data["divisions"]) == 2
        assert data["divisions"][0]["name"] == "Module A"

@pytest.mark.asyncio
async def test_get_summary_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS):
        summary = await progress_service.get_summary()
        assert summary["total_endpoints"] == 50
        assert summary["total_pages"] == 10
        # Check computed fields
        assert "completed_features" in summary
        assert "divisions_complete" in summary

@pytest.mark.asyncio
async def test_get_divisions_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS):
        divisions = await progress_service.get_divisions()
        assert len(divisions) == 2
        assert divisions[0]["id"] == "div-1"
        assert divisions[0]["name"] == "Module A"

@pytest.mark.asyncio
async def test_get_recent_features_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS):
        # The mock data doesn't have recent_features, so it should default to the hardcoded list in _build_progress_data
        # Wait, _build_progress_data hardcodes recent_features.
        # So I should see the hardcoded ones.
        features = await progress_service.get_recent_features()
        assert len(features) > 0
        assert features[0]["id"] == "feat-myworkspace-complete"

@pytest.mark.asyncio
async def test_add_feature_async(progress_service):
    # add_feature is in-memory only but returns the feature
    feature = await progress_service.add_feature(
        name="New Feature",
        description="Description",
        status="planned"
    )
    assert feature["name"] == "New Feature"
    assert feature["status"] == "planned"
    assert feature["id"].startswith("feat-new-feature")

@pytest.mark.asyncio
async def test_update_feature_status_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS):
        # Since updates are "transient" (re-read from file/mock every time),
        # checking persistence is moot, but we can check the return value.
        # However, update_feature_status tries to find the feature in the loaded data.
        # Since our mock data doesn't have features, and the hardcoded ones are in _build_progress_data...
        # Let's target a hardcoded feature.
        target_id = "feat-myworkspace-complete"
        updated = await progress_service.update_feature_status(target_id, "backlog")
        assert updated is not None
        assert updated["status"] == "backlog"
        assert updated["id"] == target_id

@pytest.mark.asyncio
async def test_update_division_progress_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS):
        # Target first division
        target_id = "div-1"
        updated = await progress_service.update_division_progress(target_id, 50)
        assert updated is not None
        assert updated["progress"] == 50
        assert updated["status"] == "in-progress"

@pytest.mark.asyncio
async def test_update_summary_async(progress_service):
    with patch("app.services.progress_tracker.load_metrics_json", return_value=MOCK_METRICS):
        updated = await progress_service.update_summary(endpoints=100)
        assert updated["total_endpoints"] == 100
        # Should preserve other fields from mock
        assert updated["total_pages"] == 10
