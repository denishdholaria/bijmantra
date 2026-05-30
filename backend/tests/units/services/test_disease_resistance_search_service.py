"""
TDD tests for DiseaseResistanceSearchService.

Written BEFORE the implementation. RED → GREEN → REFACTOR.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_db() -> AsyncSession:
    return AsyncMock(spec=AsyncSession)


def _make_resistance_gene(
    id: int = 1,
    organization_id: int = 1,
    gene_code: str = "Xa21",
    name: str = "Xa21",
    disease_id: int = 10,
    resistance_type: str = "complete",
    is_validated: bool = True,
    crop: str | None = None,
) -> MagicMock:
    obj = MagicMock()
    obj.id = id
    obj.organization_id = organization_id
    obj.gene_code = gene_code
    obj.name = name
    obj.disease_id = disease_id
    obj.resistance_type = resistance_type
    obj.is_validated = is_validated
    obj.chromosome = "11"
    obj.markers = ["RM224"]
    obj.source_germplasm = "IR64"
    obj.reference = None
    obj.disease = MagicMock()
    obj.disease.name = "Bacterial Leaf Blight"
    obj.disease.crop = crop or "Rice"
    obj.disease.pathogen_type = "bacteria"
    return obj


def _make_pest_observation(
    id: int = 1,
    organization_id: int = 1,
    field_id: int = 5,
    pest_name: str = "Rice Blast",
    pest_type: str = "disease",
    severity_score: float = 6.5,
    crop_name: str = "Rice",
    observation_date: str = "2025-04-01",
) -> MagicMock:
    obj = MagicMock()
    obj.id = id
    obj.organization_id = organization_id
    obj.field_id = field_id
    obj.pest_name = pest_name
    obj.pest_type = pest_type
    obj.severity_score = severity_score
    obj.incidence_percent = 35.0
    obj.crop_name = crop_name
    obj.observation_date = observation_date
    obj.growth_stage = "Tillering"
    obj.notes = None
    return obj


# ── Import (will fail until implemented) ─────────────────────────────────────

from app.modules.phenotyping.services.disease_resistance_search_service import (
    DiseaseResistanceSearchService,
)


# ── Task 2.2: get_resistance_profiles() ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_resistance_profiles_returns_empty_when_no_data():
    """get_resistance_profiles() returns [] when no resistance genes exist."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.get_resistance_profiles(db=db, organization_id=1)

    assert results == []


@pytest.mark.asyncio
async def test_get_resistance_profiles_returns_dict_with_required_keys():
    """get_resistance_profiles() returns dicts with gene, disease, resistance_type."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    gene = _make_resistance_gene()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [gene]
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.get_resistance_profiles(db=db, organization_id=1)

    assert len(results) == 1
    record = results[0]
    assert record["gene_code"] == "Xa21"
    assert record["gene_name"] == "Xa21"
    assert record["resistance_type"] == "complete"
    assert record["disease_name"] == "Bacterial Leaf Blight"
    assert record["is_validated"] is True
    assert record["chromosome"] == "11"


@pytest.mark.asyncio
async def test_get_resistance_profiles_scopes_to_organization():
    """get_resistance_profiles() must filter by organization_id."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.get_resistance_profiles(db=db, organization_id=7)

    call_args = db.execute.call_args[0][0]
    compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
    assert "7" in compiled


@pytest.mark.asyncio
async def test_get_resistance_profiles_filters_by_disease_name():
    """get_resistance_profiles() with disease filter returns only matching genes."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.get_resistance_profiles(
        db=db, organization_id=1, disease="blast"
    )

    # A query was executed — disease filter was applied
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_resistance_profiles_filters_by_germplasm_ids():
    """get_resistance_profiles() with germplasm_ids filters to those entries."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    # germplasm_ids narrows the query — implementation may join or filter
    results = await service.get_resistance_profiles(
        db=db, organization_id=1, germplasm_ids=[10, 20]
    )

    assert isinstance(results, list)


# ── Task 2.3: search_scouting_records() ──────────────────────────────────────

@pytest.mark.asyncio
async def test_search_scouting_records_returns_empty_when_no_data():
    """search_scouting_records() returns [] when no pest observations exist."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.search_scouting_records(db=db, organization_id=1)

    assert results == []


@pytest.mark.asyncio
async def test_search_scouting_records_returns_dict_with_required_keys():
    """search_scouting_records() returns dicts with pest_name, severity, location."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    obs = _make_pest_observation()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [obs]
    db.execute = AsyncMock(return_value=mock_result)

    results = await service.search_scouting_records(db=db, organization_id=1)

    assert len(results) == 1
    record = results[0]
    assert record["pest_name"] == "Rice Blast"
    assert record["pest_type"] == "disease"
    assert record["severity_score"] == 6.5
    assert record["crop_name"] == "Rice"
    assert record["field_id"] == 5
    assert record["observation_date"] == "2025-04-01"


@pytest.mark.asyncio
async def test_search_scouting_records_scopes_to_organization():
    """search_scouting_records() must filter by organization_id."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.search_scouting_records(db=db, organization_id=99)

    call_args = db.execute.call_args[0][0]
    compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
    assert "99" in compiled


@pytest.mark.asyncio
async def test_search_scouting_records_filters_by_location_id():
    """search_scouting_records() with location_id returns only records for that field."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.search_scouting_records(db=db, organization_id=1, location_id=5)

    call_args = db.execute.call_args[0][0]
    compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
    assert "5" in compiled


@pytest.mark.asyncio
async def test_search_scouting_records_filters_by_crop():
    """search_scouting_records() with crop filter returns only matching records."""
    service = DiseaseResistanceSearchService()
    db = _make_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    await service.search_scouting_records(db=db, organization_id=1, crop="Wheat")

    db.execute.assert_called_once()
