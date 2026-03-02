import logging
from typing import Any

from app.core.config import settings


logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Core engine for the Analytical Plane.
    Manages DuckDB connections and integration with MinIO (Parquet).
    """

    def __init__(self):
        self._con = None
        self._initialized = False

    def initialize(self):
        """Initialize DuckDB connection and install extensions."""
        if self._initialized:
            return

        try:
            import duckdb

            # In-memory database for now, or connect to a persistent file if needed
            self._con = duckdb.connect(database=":memory:")

            # Install httpfs for MinIO/S3 access
            self._con.execute("INSTALL httpfs;")
            self._con.execute("LOAD httpfs;")

            # Configure MinIO access
            # Note: We need to handle non-SSL correctly for local MinIO
            s3_endpoint = settings.MINIO_ENDPOINT

            # Use CREATE SECRET for secure configuration (parameterized queries prevent injection)
            self._con.execute(
                """
                CREATE OR REPLACE SECRET minio_secret (
                    TYPE S3,
                    KEY_ID ?,
                    SECRET ?,
                    ENDPOINT ?,
                    USE_SSL ?,
                    URL_STYLE 'path'
                );
                """,
                [
                    settings.MINIO_ROOT_USER,
                    settings.MINIO_ROOT_PASSWORD,
                    s3_endpoint,
                    settings.MINIO_USE_SSL,
                ],
            )

            self._initialized = True
            logger.info("Analytics Engine (DuckDB) initialized successfully.")

        except ImportError:
            logger.warning("DuckDB not installed. Analytics features will be disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Analytics Engine: {e}")

    def get_connection(self) -> Any:
        """Get the raw DuckDB connection."""
        if not self._initialized:
            self.initialize()
        return self._con

    def query(self, sql: str) -> Any:
        """Execute a SQL query and return the result."""
        con = self.get_connection()
        if con:
            return con.execute(sql)
        return None


analytics_engine = AnalyticsEngine()
