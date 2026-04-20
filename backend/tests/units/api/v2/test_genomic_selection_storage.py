import pytest
import numpy as np

from app.api.v2 import genomic_selection
from app.services.compute_engine import BLUPResult


@pytest.mark.asyncio
async def test_gs_storage_rejects_local_fallback_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = type("FakeRedis", (), {"is_available": False})()

    monkeypatch.setattr(genomic_selection, "_get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(genomic_selection.settings, "ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="Redis-backed genomic selection result storage is unavailable"):
        await genomic_selection._store_result("analysis-1", {"gebv": [1.0]})

    with pytest.raises(RuntimeError, match="Redis-backed genomic selection result storage is unavailable"):
        await genomic_selection._load_result("analysis-1")


@pytest.mark.asyncio
async def test_gs_storage_uses_local_fallback_outside_production(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = type("FakeRedis", (), {"is_available": False})()

    monkeypatch.setattr(genomic_selection, "_get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(genomic_selection.settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(genomic_selection, "_local_fallback", {})

    payload = {"gebv": [1.0], "reliability": [0.9]}
    await genomic_selection._store_result("analysis-2", payload)

    assert await genomic_selection._load_result("analysis-2") == payload


@pytest.mark.asyncio
async def test_run_gblup_uses_compute_engine_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_compute_gblup_from_grm(*, phenotypes, grm, heritability):
        captured["phenotypes"] = phenotypes.tolist()
        captured["grm"] = grm.tolist()
        captured["heritability"] = heritability
        return BLUPResult(
            fixed_effects=np.array([12.0]),
            breeding_values=np.array([-1.0, 0.0, 1.0]),
            reliability=np.array([0.5, 0.5, 0.5]),
            accuracy=np.array([0.70710678, 0.70710678, 0.70710678]),
            genetic_variance=2.0 / 3.0,
            error_variance=2.0 / 3.0,
            converged=True,
        )

    stored_payload: dict[str, object] = {}

    async def fake_store_result(analysis_id: str, data: dict) -> None:
        stored_payload["analysis_id"] = analysis_id
        stored_payload["data"] = data

    monkeypatch.setattr(genomic_selection.compute_engine, "compute_gblup_from_grm", fake_compute_gblup_from_grm)
    monkeypatch.setattr(genomic_selection, "_store_result", fake_store_result)

    response = await genomic_selection.run_gblup(
        genomic_selection.GBLUPRequest(
            phenotypes=[10.0, 12.0, 14.0],
            g_matrix=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            heritability=0.5,
        )
    )

    assert captured == {
        "phenotypes": [10.0, 12.0, 14.0],
        "grm": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "heritability": 0.5,
    }
    assert response.gebv == [-1.0, 0.0, 1.0]
    assert response.reliability == [0.5, 0.5, 0.5]
    assert response.mean == 12.0
    assert stored_payload["data"] == response.model_dump()