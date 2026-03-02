import pytest
from unittest.mock import MagicMock, patch

from app.services.analytics.etl_phenotype_extractor import PhenotypeExtractor
from app.core.config import settings

@pytest.fixture
def phenotype_extractor():
    return PhenotypeExtractor()

@patch("app.services.analytics.etl_phenotype_extractor.etl_service")
def test_run_daily_sync(mock_etl_service, phenotype_extractor):
    # Setup mock return value
    mock_etl_service.extract_to_parquet.return_value = {
        "status": "success",
        "rows": 100,
        "bucket": settings.MINIO_BUCKET_RAW,
        "file": "test.parquet",
        "size_bytes": 1024
    }

    # Run the sync
    results = phenotype_extractor.run_daily_sync()

    # Verify calls
    assert mock_etl_service.extract_to_parquet.call_count == 6

    tables = [
        "observations",
        "observation_units",
        "observation_variables",
        "samples",
        "images",
        "events",
    ]

    for table in tables:
        mock_etl_service.extract_to_parquet.assert_any_call(
            query=f"SELECT * FROM {table}",
            bucket=settings.MINIO_BUCKET_RAW,
            folder=f"phenotype/{table}",
            filename_prefix=table
        )

    # Verify results
    assert len(results) == 6
    for table in tables:
        assert results[table]["status"] == "success"

@patch("app.services.analytics.etl_phenotype_extractor.etl_service")
def test_run_daily_sync_failure(mock_etl_service, phenotype_extractor):
    # Setup mock to raise exception for one table
    def side_effect(query, bucket, folder, filename_prefix):
        if "observations" in query:
            raise Exception("DB Error")
        return {"status": "success"}

    mock_etl_service.extract_to_parquet.side_effect = side_effect

    # Run the sync
    results = phenotype_extractor.run_daily_sync()

    # Verify results
    assert results["observations"]["status"] == "error"
    assert "DB Error" in results["observations"]["message"]
    assert results["observation_units"]["status"] == "success"
