import asyncio
import os
import shutil
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.compliance import SeedBatchInfo, ComplianceType
from app.modules.core.services.compliance import batch


@pytest.fixture
def mock_output_dir():
    test_dir = "test_generated_certificates"
    os.makedirs(test_dir, exist_ok=True)
    original_dir = batch.OUTPUT_DIR
    batch.OUTPUT_DIR = test_dir
    yield test_dir
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    batch.OUTPUT_DIR = original_dir


@pytest.fixture
def sample_batches():
    return [
        SeedBatchInfo(
            batch_id=f"BATCH-{i}",
            crop="Wheat",
            variety="SuperWheat",
            weight_kg=1000.0,
            germination_percentage=95.0,
            purity_percentage=99.0,
            moisture_percentage=12.0,
            origin_country="India",
        )
        for i in range(5)
    ]


@pytest.mark.asyncio
async def test_process_batch_generation_success(mock_output_dir, sample_batches):
    # Mock dependencies
    with (
        patch("app.modules.core.services.compliance.batch_service.generate_certificate_pdf") as mock_gen_pdf,
        patch("app.modules.core.services.compliance.batch_service.send_email_with_attachment") as mock_email,
    ):
        mock_gen_pdf.return_value = b"%PDF-TestContent"
        mock_email.return_value = True

        progress_calls = []

        def progress_callback(progress, message):
            progress_calls.append((progress, message))

        result = await batch.process_batch_generation(
            compliance_type=ComplianceType.ISTA,
            batches=sample_batches,
            issuer_name="Test Issuer",
            email_to="test@example.com",
            progress_callback=progress_callback,
        )

        # Verify result
        assert result["count"] == 5
        zip_path = result["zip_path"]
        assert os.path.exists(zip_path)
        assert zip_path.endswith(".zip")

        # Verify ZIP content
        with zipfile.ZipFile(zip_path, "r") as zf:
            files = zf.namelist()
            assert len(files) == 5
            for f in files:
                assert f.endswith(".pdf")

        # Verify generate_certificate_pdf was called 5 times
        assert mock_gen_pdf.call_count == 5

        # Verify email was sent
        mock_email.assert_called_once()

        # Verify progress callback was called
        # Should be called at least 5 times + 2 (zip + email) + 1 (done)
        # 5 for batches + 1 for zip + 1 for email + 1 for done = 8 calls minimum.
        assert len(progress_calls) >= 5

        # Check if progress increases
        progress_values = [p[0] for p in progress_calls]
        assert progress_values[-1] == 1.0
        assert sorted(progress_values) == progress_values  # Should be monotonic


@pytest.mark.asyncio
async def test_process_batch_generation_parallel_execution(mock_output_dir, sample_batches):
    # Verify parallelism by adding a delay in mock_gen_pdf and checking total time
    # If sequential: 5 * 0.1s = 0.5s
    # If parallel: ~0.1s

    with (
        patch("app.modules.core.services.compliance.batch_service.generate_certificate_pdf") as mock_gen_pdf,
        patch("app.modules.core.services.compliance.batch_service.send_email_with_attachment") as mock_email,
    ):
        # Simulate delay
        def side_effect(*args, **kwargs):
            import time

            time.sleep(0.1)
            return b"%PDF-TestContent"

        mock_gen_pdf.side_effect = side_effect
        mock_email.return_value = True

        import time

        start_time = time.time()

        await batch.process_batch_generation(
            compliance_type=ComplianceType.ISTA,
            batches=sample_batches,
            issuer_name="Test Issuer",
            email_to="test@example.com",
        )

        end_time = time.time()
        duration = end_time - start_time

        # Should be significantly less than sequential time
        # Sequential: 5 * 0.1 = 0.5s
        # Parallel: max(0.1) + overhead.
        # With 5 batches, it should be fast.

        print(f"Test duration: {duration}s")
        assert duration < 0.4  # Allow some buffer, but clearly less than 0.5s
