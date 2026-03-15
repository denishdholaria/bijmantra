import pytest

from app.api.v2 import genomic_selection


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