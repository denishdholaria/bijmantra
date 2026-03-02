"""Unit tests for Crop Suitability API route handlers."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v2.future.crop_suitability import (
    create_crop_suitability,
    delete_crop_suitability,
    get_crop_suitability,
    get_suitable_locations,
    get_suitability_by_crop,
    get_suitability_by_location,
    list_crop_suitability,
)
from app.crud.future import crop_suitability as suitability_crud
from app.schemas.future.crop_intelligence import CropSuitabilityCreate


class TestCropSuitabilityApi:
    """Test suite for Crop Suitability API route functions."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_db = AsyncMock()
        self.mock_user = SimpleNamespace(id=1, organization_id=1, is_active=True)

    @staticmethod
    def _assessment(**overrides):
        base = {
            "id": 1,
            "organization_id": 1,
            "location_id": 10,
            "crop_name": "wheat",
            "variety": "HD-2967",
            "suitability_class": "S1",
            "suitability_score": 86.0,
            "climate_score": 80.0,
            "soil_score": 85.0,
            "terrain_score": 88.0,
            "water_score": 90.0,
            "limiting_factors": ["none"],
            "recommendations": ["maintain current management"],
            "assessment_method": "fao_rule_based",
            "confidence_level": 0.92,
            "notes": "baseline",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @pytest.mark.asyncio
    async def test_list_crop_suitability_returns_records(self, monkeypatch):
        records = [self._assessment(id=1), self._assessment(id=2, crop_name="rice")]
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get_multi",
            AsyncMock(return_value=(records, len(records))),
        )

        result = await list_crop_suitability(skip=0, limit=100, db=self.mock_db, org_id=1)

        assert len(result) == 2
        assert result[0].crop_name == "wheat"

    @pytest.mark.asyncio
    async def test_get_crop_suitability_returns_record(self, monkeypatch):
        record = self._assessment(id=7)
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get",
            AsyncMock(return_value=record),
        )

        result = await get_crop_suitability(id=7, db=self.mock_db, org_id=1)

        assert result.id == 7
        assert result.suitability_class == "S1"

    @pytest.mark.asyncio
    async def test_get_crop_suitability_raises_404_for_other_org(self, monkeypatch):
        record = self._assessment(id=3, organization_id=999)
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get",
            AsyncMock(return_value=record),
        )

        with pytest.raises(HTTPException) as exc:
            await get_crop_suitability(id=3, db=self.mock_db, org_id=1)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_crop_suitability_persists_and_refreshes(self, monkeypatch):
        assessment_in = CropSuitabilityCreate(
            location_id=11,
            crop_name="wheat",
            variety="HD-2967",
            suitability_class="S2",
            suitability_score=74.5,
            climate_score=70.0,
            soil_score=75.0,
            terrain_score=76.0,
            water_score=78.0,
            limiting_factors=["minor drainage constraints"],
            recommendations=["improve drainage"],
            assessment_method="fao_rule_based",
            confidence_level=0.9,
            notes="created in unit test",
        )
        created = self._assessment(id=9, location_id=11, suitability_class="S2", suitability_score=74.5)
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "create",
            AsyncMock(return_value=created),
        )

        result = await create_crop_suitability(
            assessment_in=assessment_in,
            db=self.mock_db,
            current_user=self.mock_user,
        )

        assert result.id == 9
        self.mock_db.commit.assert_awaited_once()
        self.mock_db.refresh.assert_awaited_once_with(created)

    @pytest.mark.asyncio
    async def test_delete_crop_suitability_returns_none(self, monkeypatch):
        record = self._assessment(id=5)
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get",
            AsyncMock(return_value=record),
        )
        delete_mock = AsyncMock(return_value=None)
        monkeypatch.setattr(suitability_crud.crop_suitability, "delete", delete_mock)

        result = await delete_crop_suitability(id=5, db=self.mock_db, org_id=1)

        assert result is None
        delete_mock.assert_awaited_once_with(self.mock_db, id=5)
        self.mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_suitability_by_location(self, monkeypatch):
        records = [self._assessment(id=1, location_id=15), self._assessment(id=2, location_id=15)]
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get_by_location",
            AsyncMock(return_value=records),
        )

        result = await get_suitability_by_location(location_id=15, db=self.mock_db, org_id=1)

        assert len(result) == 2
        assert all(r.location_id == 15 for r in result)

    @pytest.mark.asyncio
    async def test_get_suitability_by_crop_and_suitable_locations(self, monkeypatch):
        crop_records = [self._assessment(id=1, crop_name="wheat"), self._assessment(id=2, crop_name="wheat")]
        suitable_records = [self._assessment(id=3, crop_name="wheat", suitability_score=82.0)]

        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get_by_crop",
            AsyncMock(return_value=crop_records),
        )
        monkeypatch.setattr(
            suitability_crud.crop_suitability,
            "get_suitable_locations",
            AsyncMock(return_value=suitable_records),
        )

        by_crop = await get_suitability_by_crop(crop_name="wheat", db=self.mock_db, org_id=1)
        suitable = await get_suitable_locations(
            crop_name="wheat",
            min_score=80.0,
            db=self.mock_db,
            org_id=1,
        )

        assert len(by_crop) == 2
        assert len(suitable) == 1
        assert suitable[0].suitability_score >= 80.0
