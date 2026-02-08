import io
import logging
from datetime import datetime, timezone
import polars as pl
from sqlalchemy import create_engine
from app.core.config import settings
from .storage import storage_service

logger = logging.getLogger(__name__)

class ETLService:
    """
    ETL Service for the Analytical Plane.
    Extracts data from PostgreSQL, transforms to Parquet, and loads into MinIO.
    """

    def __init__(self):
        # Polars requires a sync engine or connection string for read_database
        # We replace the async driver (asyncpg) with the sync driver (psycopg2) usually implicit in 'postgresql://'
        # or explicitly 'postgresql+psycopg2://'
        self.db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        self._engine = None

    def _get_engine(self):
        """Get or create sync SQLAlchemy engine."""
        if not self._engine:
            try:
                self._engine = create_engine(self.db_url)
            except Exception as e:
                logger.error(f"Failed to create sync DB engine: {e}")
                raise
        return self._engine

    def extract_to_parquet(
        self,
        query: str,
        bucket: str,
        folder: str,
        filename_prefix: str
    ) -> dict:
        """
        Execute SQL query, convert to Parquet, and upload to Data Lake.

        Args:
            query: SQL select query string.
            bucket: Target MinIO bucket.
            folder: Folder path within bucket (e.g., 'raw/yield_prediction').
            filename_prefix: Prefix for the filename.

        Returns:
            Dict with job status and metadata.
        """
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{folder}/{filename_prefix}_{timestamp}.parquet"

            logger.info(f"Starting extraction for {filename}...")

            # 1. Extract (Read from DB)
            # using read_database with connection string is most robust for Polars
            df = pl.read_database(query, self.db_url)

            if df.is_empty():
                logger.warning("Query returned no data.")
                return {"status": "skipped", "reason": "empty_result", "rows": 0}

            # 2. Transform (Convert to Parquet bytes)
            buffer = io.BytesIO()
            df.write_parquet(buffer)
            data = buffer.getvalue()

            # 3. Load (Upload to MinIO)
            success = storage_service.upload_data(bucket, filename, data)

            if success:
                return {
                    "status": "success",
                    "rows": len(df),
                    "bucket": bucket,
                    "file": filename,
                    "size_bytes": len(data)
                }
            else:
                return {"status": "failed", "reason": "upload_failed"}

        except Exception as e:
            logger.error(f"ETL Job Failed: {e}")
            return {"status": "error", "message": str(e)}

    def run_nightly_etl(self):
        """
        Run the standard nightly ETL jobs.
        Currently focuses on Yield Prediction data.
        """
        # Example 1: Yield Predictions
        # We assume the table name is 'yield_prediction' based on API code
        result = self.extract_to_parquet(
            query="SELECT * FROM yield_prediction",
            bucket=settings.MINIO_BUCKET_RAW,
            folder="phenotype/yield_prediction",
            filename_prefix="yield_pred"
        )
        return {"yield_prediction": result}

etl_service = ETLService()
