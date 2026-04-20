import json

import pytest

import app.api.v2.metrics as metrics_api


@pytest.mark.asyncio
async def test_metrics_api_backfills_explicit_brapi_counts(
    superuser_client,
    tmp_path,
    monkeypatch,
):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "lastUpdated": "2026-03-23",
                "updatedBy": "test",
                "session": 0,
                "api": {
                    "totalEndpoints": 300,
                    "brapiEndpoints": 248,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(metrics_api, "METRICS_PATHS", [metrics_path])

    response = await superuser_client.get("/api/v2/metrics/api")

    assert response.status_code == 200
    assert response.json() == {
        "totalEndpoints": 300,
        "brapiEndpoints": 248,
        "brapiPublishedEndpoints": 201,
        "brapiExposedEndpoints": 248,
        "brapiCoverage": 100,
        "customEndpoints": 52,
    }