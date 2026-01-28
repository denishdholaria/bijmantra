import logging
from typing import Optional, Any
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
            use_ssl = "true" if settings.MINIO_USE_SSL else "false"

            self._con.execute(f"SET s3_endpoint='{s3_endpoint}';")
            self._con.execute(f"SET s3_access_key_id='{settings.MINIO_ROOT_USER}';")
            self._con.execute(f"SET s3_secret_access_key='{settings.MINIO_ROOT_PASSWORD}';")
            self._con.execute(f"SET s3_use_ssl={use_ssl};")
            self._con.execute("SET s3_url_style='path';")

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
