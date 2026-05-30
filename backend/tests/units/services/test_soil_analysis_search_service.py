"""
TDD tests for SoilAnalysisSearchService.

Written BEFORE the implementation. Each test defines the contract the service
must satisfy. Run these first — they should all fail (RED). Then implement the
service until they all pass (GREEN).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_db() -> AsyncSession:
    """Return a mock async DB session."""
    return AsyncMock(spec=AsyncSession)


def _make_soil_test(
    id: int = 1,
    organization_id: int = 1,
    field_id: int = 10,
    ph: float = 6.5,
    organic_matter_percent: float = 2.8,
    n_ppm: float = 45.0,
    p_ppm: float = 22.0,
    k_ppm: float = 130.0,
    sample_id: str = "ST-001",
    sample_date: str = "2025-03-01",
) -> MagicMock:
    """Return a mock SoilTest ORM object."""
    obj = MagicMock()
    obj.id = id
    obj.organization_id = organization_id
    obj.field_id = field_id
    obj.sample_id = sample_id
    obj.sample_date = sample_date
    obj.ph = ph
    obj.organic_matter_percent = organic_matter_percent
    obj.n_ppm = n_ppm
    obj.p_ppm = p_ppm
    obj.k_ppm = k_ppm
    obj.ca_ppm = None
    obj.mg_ppm = None
    obj.s_ppm = None
    obj.zn_ppm = None
    obj.texture_class = "Clay Loam"
    obj.notes = None
    return obj


# ── Import the service (will fail until implemented) ─────────────────────────

from app.modules.environment.services.soil_analysis_search_service import (
    SoilAnalysisSearchService,
)


# ── Task 1.2: search() ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_returns_empty_list_when_no_records():
    """search() returns [] when the DB has no matching soil tests."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.search(db=db, organization_id=1)

    assert results == []


@pytest.mark.asyncio
async def test_search_returns_dict_list_with_required_keys():
    """search() returns dicts with id, field_id, ph, organic_matter_percent, nutrients."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    soil_test = _make_soil_test()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [soil_test]
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.search(db=db, organization_id=1)

    assert len(results) == 1
    record = results[0]
    assert record["id"] == "1"
    assert record["field_id"] == 10
    assert record["ph"] == 6.5
    assert record["organic_matter_percent"] == 2.8
    assert record["n_ppm"] == 45.0
    assert record["p_ppm"] == 22.0
    assert record["k_ppm"] == 130.0
    assert record["texture_class"] == "Clay Loam"


@pytest.mark.asyncio
async def test_search_scopes_to_organization_id():
    """search() must filter by organization_id (tenant isolation)."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.search(db=db, organization_id=42)

    # Verify a DB query was executed (tenant filter applied)
    db.execute.assert_called_once()
    call_args = db.execute.call_args[0][0]
    # The compiled query should reference organization_id = 42
    compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
    assert "42" in compiled


@pytest.mark.asyncio
async def test_search_filters_by_location_id():
    """search() with location_id only returns tests for that field."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    matching = _make_soil_test(id=1, field_id=10)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [matching]
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.search(db=db, organization_id=1, location_id=10)

    assert len(results) == 1
    assert results[0]["field_id"] == 10


@pytest.mark.asyncio
async def test_search_respects_limit():
    """search() passes limit to the DB query."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.search(db=db, organization_id=1, limit=5)

    call_args = db.execute.call_args[0][0]
    compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
    assert "5" in compiled


# ── Task 1.3: get_nutrient_summary() ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_nutrient_summary_returns_aggregated_nutrients():
    """get_nutrient_summary() returns mean N, P, K, pH, organic_matter for a location."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    tests = [
        _make_soil_test(id=1, ph=6.0, n_ppm=40.0, p_ppm=20.0, k_ppm=120.0, organic_matter_percent=2.5),
        _make_soil_test(id=2, ph=7.0, n_ppm=50.0, p_ppm=24.0, k_ppm=140.0, organic_matter_percent=3.1),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = tests
    db.execute = AsyncMock(return_value=mock_result)

    summary = await service.get_nutrient_summary(db=db, organization_id=1, location_id=10)

    assert summary["location_id"] == 10
    assert summary["sample_count"] == 2
    assert abs(summary["mean_ph"] - 6.5) < 0.01
    assert abs(summary["mean_n_ppm"] - 45.0) < 0.01
    assert abs(summary["mean_p_ppm"] - 22.0) < 0.01
    assert abs(summary["mean_k_ppm"] - 130.0) < 0.01
    assert abs(summary["mean_organic_matter_percent"] - 2.8) < 0.01


@pytest.mark.asyncio
async def test_get_nutrient_summary_returns_empty_when_no_tests():
    """get_nutrient_summary() returns a safe empty summary when no tests exist."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    summary = await service.get_nutrient_summary(db=db, organization_id=1, location_id=99)

    assert summary["location_id"] == 99
    assert summary["sample_count"] == 0
    assert summary["mean_ph"] is None
    assert summary["mean_n_ppm"] is None


@pytest.mark.asyncio
async def test_get_nutrient_summary_includes_soil_health_indicators():
    """get_nutrient_summary() includes soil_health_indicators with pH and OM flags."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    # Acidic soil (pH < 5.5) and low organic matter (< 2%)
    tests = [_make_soil_test(ph=5.0, organic_matter_percent=1.5, n_ppm=30.0, p_ppm=10.0, k_ppm=80.0)]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = tests
    db.execute = AsyncMock(return_value=mock_result)

    summary = await service.get_nutrient_summary(db=db, organization_id=1, location_id=10)

    indicators = summary["soil_health_indicators"]
    assert "ph_status" in indicators
    assert indicators["ph_status"] == "acidic"
    assert "organic_matter_status" in indicators
    assert indicators["organic_matter_status"] == "low"


@pytest.mark.asyncio
async def test_get_nutrient_summary_handles_none_nutrient_values():
    """get_nutrient_summary() skips None values when computing means."""
    service = SoilAnalysisSearchService()
    db = _make_db()

    t1 = _make_soil_test(id=1, ph=6.0, n_ppm=40.0, p_ppm=None, k_ppm=120.0)
    t1.p_ppm = None
    t2 = _make_soil_test(id=2, ph=7.0, n_ppm=50.0, p_ppm=24.0, k_ppm=140.0)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [t1, t2]
    db.execute = AsyncMock(return_value=mock_result)

    summary = await service.get_nutrient_summary(db=db, organization_id=1, location_id=10)

    # p_ppm mean should only use t2's value (t1 is None)
    assert abs(summary["mean_p_ppm"] - 24.0) < 0.01
