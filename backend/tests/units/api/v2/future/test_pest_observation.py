"""Unit tests for Pest Observation API route handlers and CRUD query wiring."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v2.future.pest_observation import (
    create_pest_observation,
    delete_pest_observation,
    get_field_pest_observations,
    get_high_severity_observations,
    get_pest_observation,
    list_pest_observations,
    update_pest_observation,
)
from app.crud.future import pest_observation as pest_crud
from app.crud.future.pest_observation import CRUDPestObservation
from app.models.future.pest_observation import PestObservation as PestObservationModel
from app.schemas.future.crop_protection import PestObservationCreate, PestObservationUpdate


class TestPestObservationApi:
    """Test suite for Pest Observation API route functions."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_db = AsyncMock()
        self.mock_user = SimpleNamespace(id=1, organization_id=1, is_active=True)

    @staticmethod
    def _record(**overrides):
        base = {
            "id": 1,
            "organization_id": 1,
            "field_id": 11,
            "study_id": None,
            "observation_date": date(2026, 3, 24),
            "observation_time": datetime(2026, 3, 24, 9, 30, tzinfo=UTC),
            "observer_name": "Scout A",
            "pest_name": "Brown planthopper",
            "pest_type": "insect",
            "pest_stage": "adult",
            "crop_name": "Rice",
            "growth_stage": "Tillering",
            "plant_part_affected": "Leaf sheath",
            "severity_score": 7.0,
            "incidence_percent": 42.0,
            "count_per_plant": 8.0,
            "count_per_trap": None,
            "area_affected_percent": 18.0,
            "sample_location": "North block",
            "lat": None,
            "lon": None,
            "weather_conditions": None,
            "image_urls": None,
            "notes": "Action threshold exceeded",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @pytest.mark.asyncio
    async def test_list_pest_observations_returns_records(self, monkeypatch):
        records = [self._record(id=1), self._record(id=2, pest_name="Stem borer")]
        monkeypatch.setattr(
            pest_crud.pest_observation,
            "get_multi",
            AsyncMock(return_value=(records, len(records))),
        )

        result = await list_pest_observations(skip=0, limit=100, db=self.mock_db, org_id=1)

        assert len(result) == 2
        assert result[1].pest_name == "Stem borer"

    @pytest.mark.asyncio
    async def test_get_pest_observation_returns_record(self, monkeypatch):
        record = self._record(id=7)
        monkeypatch.setattr(pest_crud.pest_observation, "get", AsyncMock(return_value=record))

        result = await get_pest_observation(id=7, db=self.mock_db, org_id=1)

        assert result.id == 7
        assert result.crop_name == "Rice"

    @pytest.mark.asyncio
    async def test_get_pest_observation_raises_404_for_other_org(self, monkeypatch):
        monkeypatch.setattr(
            pest_crud.pest_observation,
            "get",
            AsyncMock(return_value=self._record(organization_id=9)),
        )

        with pytest.raises(HTTPException) as exc:
            await get_pest_observation(id=3, db=self.mock_db, org_id=1)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_pest_observation_persists_and_refreshes(self, monkeypatch):
        record_in = PestObservationCreate(
            field_id=11,
            observation_date=date(2026, 3, 24),
            pest_name="Brown planthopper",
            pest_type="insect",
            crop_name="Rice",
            severity_score=7.0,
            incidence_percent=42.0,
            area_affected_percent=18.0,
        )
        created = self._record(id=9)
        monkeypatch.setattr(
            pest_crud.pest_observation,
            "create",
            AsyncMock(return_value=created),
        )

        result = await create_pest_observation(record_in=record_in, db=self.mock_db, current_user=self.mock_user)

        assert result.id == 9
        self.mock_db.commit.assert_awaited_once()
        self.mock_db.refresh.assert_awaited_once_with(created)

    @pytest.mark.asyncio
    async def test_update_pest_observation_persists_and_refreshes(self, monkeypatch):
        existing = self._record(id=5, severity_score=5.0)
        updated = self._record(id=5, severity_score=8.5, notes="Escalated after follow-up")
        monkeypatch.setattr(pest_crud.pest_observation, "get", AsyncMock(return_value=existing))
        update_mock = AsyncMock(return_value=updated)
        monkeypatch.setattr(pest_crud.pest_observation, "update", update_mock)
        payload = PestObservationUpdate(severity_score=8.5, notes="Escalated after follow-up")

        result = await update_pest_observation(
            id=5,
            record_in=payload,
            db=self.mock_db,
            current_user=self.mock_user,
        )

        assert result.severity_score == 8.5
        update_mock.assert_awaited_once_with(self.mock_db, db_obj=existing, obj_in=payload)
        self.mock_db.commit.assert_awaited_once()
        self.mock_db.refresh.assert_awaited_once_with(updated)

    @pytest.mark.asyncio
    async def test_update_pest_observation_raises_404_for_missing_record(self, monkeypatch):
        monkeypatch.setattr(pest_crud.pest_observation, "get", AsyncMock(return_value=None))

        with pytest.raises(HTTPException) as exc:
            await update_pest_observation(
                id=404,
                record_in=PestObservationUpdate(notes="noop"),
                db=self.mock_db,
                current_user=self.mock_user,
            )

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_pest_observation_returns_none(self, monkeypatch):
        record = self._record(id=5)
        monkeypatch.setattr(pest_crud.pest_observation, "get", AsyncMock(return_value=record))
        delete_mock = AsyncMock(return_value=None)
        monkeypatch.setattr(pest_crud.pest_observation, "delete", delete_mock)

        result = await delete_pest_observation(id=5, db=self.mock_db, org_id=1)

        assert result is None
        delete_mock.assert_awaited_once_with(self.mock_db, id=5)
        self.mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_field_and_high_severity_observations(self, monkeypatch):
        field_records = [self._record(id=1, field_id=44), self._record(id=2, field_id=44, severity_score=9.0)]
        severe_records = [self._record(id=2, severity_score=9.0)]
        monkeypatch.setattr(
            pest_crud.pest_observation,
            "get_by_field",
            AsyncMock(return_value=field_records),
        )
        monkeypatch.setattr(
            pest_crud.pest_observation,
            "get_by_severity",
            AsyncMock(return_value=severe_records),
        )

        by_field = await get_field_pest_observations(field_id=44, db=self.mock_db, org_id=1)
        high = await get_high_severity_observations(min_severity=8, db=self.mock_db, org_id=1)

        assert len(by_field) == 2
        assert len(high) == 1
        assert high[0].severity_score >= 8


class TestPestObservationCrud:
    """Focused CRUD tests for query construction regressions."""

    @pytest.mark.asyncio
    async def test_get_by_severity_uses_severity_score_column(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])))
        crud = CRUDPestObservation(PestObservationModel)

        await crud.get_by_severity(db, min_severity=6, org_id=1)

        stmt = db.execute.await_args.args[0]
        compiled = str(stmt)
        assert "severity_score" in compiled
        assert "pest_observations" in compiled
