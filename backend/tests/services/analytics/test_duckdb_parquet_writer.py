import pytest
import os
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

from app.services.analytics.duckdb_parquet_writer import DuckDBParquetWriter

# Skip all tests if duckdb is not installed
pytestmark = pytest.mark.skipif(duckdb is None, reason="duckdb not installed")

@pytest.fixture
def writer():
    # Use a fresh in-memory connection for each test
    conn = duckdb.connect(":memory:")
    return DuckDBParquetWriter(connection=conn)

def test_init_with_connection(writer):
    assert writer.conn is not None

def test_write_query_to_parquet(writer, tmp_path):
    output_file = tmp_path / "test_query.parquet"
    query = "SELECT 1 as id, 'test' as name"

    result_path = writer.write_query_to_parquet(query, str(output_file))

    assert os.path.exists(output_file)
    assert str(output_file) == result_path

    # Read back to verify
    con = duckdb.connect(":memory:")
    df = con.execute(f"SELECT * FROM '{output_file}'").fetchdf()
    assert len(df) == 1
    assert df.iloc[0]['id'] == 1
    assert df.iloc[0]['name'] == 'test'

@pytest.mark.skipif(pd is None, reason="pandas not installed")
def test_write_pandas_df_to_parquet(writer, tmp_path):
    output_file = tmp_path / "test_pandas.parquet"
    df = pd.DataFrame({'id': [1, 2], 'val': [10.5, 20.5]})

    writer.write_df_to_parquet(df, str(output_file), table_name="test_pd")

    assert os.path.exists(output_file)

    # Read back
    con = duckdb.connect(":memory:")
    res = con.execute(f"SELECT * FROM '{output_file}'").fetchdf()
    assert len(res) == 2
    assert res.iloc[0]['val'] == 10.5

@pytest.mark.skipif(pd is None, reason="pandas not installed")
def test_write_pandas_df_default_name(writer, tmp_path):
    output_file = tmp_path / "test_pandas_default.parquet"
    df = pd.DataFrame({'id': [5], 'val': [50.5]})

    # Should generate unique name internally
    writer.write_df_to_parquet(df, str(output_file))

    assert os.path.exists(output_file)
    con = duckdb.connect(":memory:")
    res = con.execute(f"SELECT * FROM '{output_file}'").fetchdf()
    assert len(res) == 1

@pytest.mark.skipif(pl is None, reason="polars not installed")
def test_write_polars_df_to_parquet(writer, tmp_path):
    output_file = tmp_path / "test_polars.parquet"
    df = pl.DataFrame({'id': [3, 4], 'val': [30.5, 40.5]})

    writer.write_df_to_parquet(df, str(output_file), table_name="test_pl")

    assert os.path.exists(output_file)

    # Read back (using DuckDB to read parquet is standard)
    con = duckdb.connect(":memory:")
    res = con.execute(f"SELECT * FROM '{output_file}'").fetchdf()
    assert len(res) == 2
    assert res.iloc[0]['val'] == 30.5

def test_write_records_to_parquet(writer, tmp_path):
    if pd is None and pl is None:
        pytest.skip("Neither pandas nor polars installed")

    output_file = tmp_path / "test_records.parquet"
    records = [{'id': 1, 'name': 'A'}, {'id': 2, 'name': 'B'}]

    writer.write_records_to_parquet(records, str(output_file))

    assert os.path.exists(output_file)

    con = duckdb.connect(":memory:")
    res = con.execute(f"SELECT * FROM '{output_file}'").fetchdf()
    assert len(res) == 2
    assert res.iloc[0]['name'] == 'A'

def test_write_empty_records(writer, tmp_path):
    output_file = tmp_path / "empty.parquet"
    writer.write_records_to_parquet([], str(output_file))
    # Should not create file or just return path without error
    # The implementation returns path but logs warning
    assert not os.path.exists(output_file)
