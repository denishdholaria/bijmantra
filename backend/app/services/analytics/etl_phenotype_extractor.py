import logging

from app.core.config import settings
from app.services.analytics.etl_service import etl_service


logger = logging.getLogger(__name__)


class PhenotypeExtractor:
    """
    Service for extracting phenotype data from PostgreSQL and syncing to Data Lake (MinIO).
    """

    def run_daily_sync(self) -> dict:
        """
        Run the daily sync job for phenotype data.
        Extracts key tables and uploads them as Parquet files to the Raw Zone.
        """
        tables = [
            "observations",
            "observation_units",
            "observation_variables",
            "samples",
            "images",
            "events",
        ]

        results = {}
        logger.info("Starting daily phenotype data sync...")

        for table in tables:
            try:
                result = etl_service.extract_to_parquet(
                    query=f"SELECT * FROM {table}",
                    bucket=settings.MINIO_BUCKET_RAW,
                    folder=f"phenotype/{table}",
                    filename_prefix=table,
                )
                results[table] = result
            except Exception as e:
                logger.error(f"Error extracting {table}: {e}")
                results[table] = {"status": "error", "message": str(e)}

        logger.info("Daily phenotype data sync completed.")
        return results


phenotype_extractor = PhenotypeExtractor()
