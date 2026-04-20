from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.import_job import ImportJob
from app.modules.phenotyping.services.phenomic_selection_service import PhenomicSelectionService


@pytest.mark.asyncio
async def test_create_upload_receipt_persists_import_job():
    db = AsyncMock()
    db.add = MagicMock(side_effect=lambda job: setattr(job, "id", 42))

    service = PhenomicSelectionService()
    result = await service.create_upload_receipt(
        db=db,
        organization_id=7,
        user_id=9,
        filename="spectra.csv",
        content_type="text/csv",
        size_bytes=2048,
        dataset_name="NIRS Batch 1",
        crop="wheat",
        platform="NIRS",
    )

    added_job = db.add.call_args.args[0]
    assert isinstance(added_job, ImportJob)
    assert added_job.organization_id == 7
    assert added_job.user_id == 9
    assert added_job.import_type == "phenomic_selection"
    assert added_job.status == "queued"
    assert added_job.report["upload"] == {
        "dataset_name": "NIRS Batch 1",
        "crop": "wheat",
        "platform": "NIRS",
        "content_type": "text/csv",
        "size_bytes": 2048,
    }

    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(added_job)

    assert result == {
        "success": True,
        "job_id": 42,
        "status": "queued",
        "filename": "spectra.csv",
        "size_bytes": 2048,
        "dataset_name": "NIRS Batch 1",
        "crop": "wheat",
        "platform": "NIRS",
        "message": "Spectral upload receipt created and queued against a persistent import job.",
    }