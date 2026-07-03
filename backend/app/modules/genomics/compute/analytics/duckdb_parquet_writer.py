import logging
import uuid
from typing import Any, List, Dict, Optional, Union
from pathlib import Path

try:
    import duckdb
except ImportError:
    duckdb = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import polars as pl
except ImportError:
    pl = None

from .engine import analytics_engine

logger = logging.getLogger(__name__)


class DuckDBParquetWriter:
    """
    Service for writing data to Parquet format using DuckDB.
    Supports writing from SQL queries, DataFrames (Pandas/Polars), and list of records.
    Leverages the shared AnalyticsEngine connection for S3/MinIO access if available.
    """

    def __init__(self, connection=None):
        """
        Initialize the writer.

        Args:
            connection: Optional DuckDB connection. If provided, it will be used.
                        Otherwise, it tries to use the shared analytics_engine connection.
                        If analytics_engine is not initialized, it creates a temporary in-memory connection.
        """
        if connection:
            self.conn = connection
        else:
            # Try to get shared connection, which might have S3 secrets configured
            try:
                self.conn = analytics_engine.get_connection()
            except Exception as e:
                logger.warning(f"Could not get shared analytics connection: {e}. creating new in-memory connection.")
                self.conn = None

            if self.conn is None and duckdb:
                self.conn = duckdb.connect(":memory:")

        if self.conn is None:
            logger.error("DuckDB is not available. DuckDBParquetWriter will fail.")

    def _validate_connection(self):
        if self.conn is None:
            raise RuntimeError("DuckDB connection is not available.")

    def write_query_to_parquet(
        self,
        query: str,
        output_path: str,
        compression: str = "SNAPPY",
        **kwargs
    ) -> str:
        """
        Execute a SQL query and write the result to a Parquet file.

        Args:
            query: SQL query to execute.
            output_path: Path to the output Parquet file (local or s3://).
            compression: Compression codec (SNAPPY, ZSTD, GZIP, UNCOMPRESSED).
            **kwargs: Additional options for COPY command.

        Returns:
            The output path on success.
        """
        self._validate_connection()
        try:
            logger.info(f"Writing query result to {output_path} (compression={compression})")

            # Use COPY ... TO ... (FORMAT PARQUET)
            # We need to wrap the query in parentheses for the COPY command
            copy_cmd = f"""
                COPY ({query})
                TO '{output_path}'
                (FORMAT PARQUET, COMPRESSION '{compression}')
            """
            self.conn.execute(copy_cmd)
            logger.info(f"Successfully wrote to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to write query to parquet: {e}")
            raise

    def write_df_to_parquet(
        self,
        df: Any,
        output_path: str,
        compression: str = "SNAPPY",
        table_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Write a DataFrame (Pandas or Polars) to a Parquet file.

        Args:
            df: Pandas or Polars DataFrame.
            output_path: Path to the output Parquet file.
            compression: Compression codec.
            table_name: Temporary name for the view registration. If None, a unique name is generated.

        Returns:
            The output path.
        """
        self._validate_connection()

        # Generate unique table name if not provided to avoid concurrency issues
        if table_name is None:
            table_name = f"view_{uuid.uuid4().hex}"

        try:
            logger.info(f"Writing DataFrame to {output_path} (compression={compression})")

            # Check type and register
            if pd and isinstance(df, pd.DataFrame):
                self.conn.register(table_name, df)
            elif pl and isinstance(df, pl.DataFrame):
                # Polars can be converted to Arrow or registered if supported
                # DuckDB Python client supports registering Polars DF directly in recent versions
                # If not, convert to Arrow
                try:
                    self.conn.register(table_name, df)
                except Exception:
                    # Fallback to Arrow
                    self.conn.register(table_name, df.to_arrow())
            else:
                # Try to register generic object (e.g. Arrow Table)
                try:
                    self.conn.register(table_name, df)
                except Exception as e:
                    raise ValueError(f"Unsupported DataFrame type: {type(df)}") from e

            # Write
            query = f"SELECT * FROM {table_name}"
            self.write_query_to_parquet(query, output_path, compression, **kwargs)

            # Cleanup view
            self.conn.execute(f"DROP VIEW IF EXISTS {table_name}")
            self.conn.unregister(table_name)

            return output_path
        except Exception as e:
            logger.error(f"Failed to write DataFrame to parquet: {e}")
            raise

    def write_records_to_parquet(
        self,
        records: List[Dict],
        output_path: str,
        compression: str = "SNAPPY",
        **kwargs
    ) -> str:
        """
        Write a list of dictionaries to a Parquet file.

        Args:
            records: List of dictionaries.
            output_path: Path to the output Parquet file.
            compression: Compression codec.

        Returns:
            The output path.
        """
        if not records:
            logger.warning("No records to write.")
            return output_path

        try:
            # Convert to Pandas DataFrame as intermediate (simplest for list of dicts)
            if pd:
                df = pd.DataFrame(records)
                return self.write_df_to_parquet(df, output_path, compression, **kwargs)
            # If no pandas, try polars
            elif pl:
                df = pl.DataFrame(records)
                return self.write_df_to_parquet(df, output_path, compression, **kwargs)
            else:
                raise ImportError("Pandas or Polars is required to write records.")
        except Exception as e:
            logger.error(f"Failed to write records to parquet: {e}")
            raise
