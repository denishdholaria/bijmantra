import pytest
from app.services.analytics.engine import AnalyticsEngine

def test_analytics_engine_initialization_security():
    """
    Test that the Analytics Engine initializes securely using CREATE SECRET
    instead of potentially vulnerable SET commands.
    """
    engine = AnalyticsEngine()

    # Initialize the engine
    # This might require duckdb to be installed. The engine handles ImportError gracefully,
    # but for this test we expect it to be installed.
    engine.initialize()

    con = engine.get_connection()
    if con is None:
        pytest.skip("DuckDB not installed or failed to initialize")

    # Verify that the secret was created
    # Query duckdb_secrets() table/function
    try:
        result = con.execute("SELECT name, type FROM duckdb_secrets() WHERE type='s3'").fetchall()
    except Exception as e:
         pytest.fail(f"Failed to query duckdb_secrets: {e}")

    assert len(result) > 0, "No S3 secret found in DuckDB"

    secret_name, secret_type = result[0]

    # Check if the secret name matches what we used (minio_secret)
    assert secret_name == 'minio_secret'
    assert secret_type == 's3'
