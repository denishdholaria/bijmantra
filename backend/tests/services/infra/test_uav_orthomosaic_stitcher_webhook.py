import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.core.services.infra.uav_orthomosaic_stitcher_webhook import (
    UAVStitcherWebhookService,
    UAVWebhookPayload,
)
from app.models.spatial import GISLayer


@pytest.mark.asyncio
async def test_process_webhook_completed():
    service = UAVStitcherWebhookService()
    mock_db = AsyncMock()
    mock_db.add = MagicMock() # add is synchronous

    payload = UAVWebhookPayload(
        job_id="job-123",
        status="completed",
        organization_id=1,
        download_url="http://example.com/ortho.tif",
        metadata={"name": "Test Ortho", "resolution": 0.05}
    )

    await service.process_webhook(payload, mock_db)

    # Verify GISLayer added
    assert mock_db.add.called
    added_layer = mock_db.add.call_args[0][0]
    assert isinstance(added_layer, GISLayer)
    assert added_layer.organization_id == 1
    assert added_layer.source_path == "http://example.com/ortho.tif"
    assert added_layer.name == "Test Ortho"
    assert added_layer.resolution == 0.05

    assert mock_db.commit.called
    assert mock_db.refresh.called


@pytest.mark.asyncio
async def test_process_webhook_failed():
    service = UAVStitcherWebhookService()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    payload = UAVWebhookPayload(
        job_id="job-456",
        status="failed",
        organization_id=1
    )

    await service.process_webhook(payload, mock_db)

    # Verify nothing added
    assert not mock_db.add.called
    assert not mock_db.commit.called
