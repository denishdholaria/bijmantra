from types import SimpleNamespace

import pytest

from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.services.tools import FunctionExecutor
from app.modules.ai.services.tools import FunctionExecutionError


class GermplasmSearchStub:
    async def get_by_id(self, db, organization_id, germplasm_id):
        records = {
            "101": {"id": "101", "name": "IR64", "accession": "IR64", "traits": ["yield"]},
            "102": {"id": "102", "name": "Swarna", "accession": "Swarna", "traits": ["yield"]},
        }
        return records.get(str(germplasm_id))

    async def search(self, db, organization_id, query=None, trait=None, limit=5):
        mapping = {
            "ir64": [{"id": "101", "name": "IR64", "accession": "IR64", "traits": ["yield"]}],
            "swarna": [{"id": "102", "name": "Swarna", "accession": "Swarna", "traits": ["yield"]}],
        }
        return mapping.get((query or "").lower(), [])


class TrialSearchStub:
    async def get_by_id(self, db, organization_id, trial_id):
        return {
            "id": str(trial_id),
            "trial_db_id": "TRIAL-1",
            "name": "Yield Trial",
            "studies": [{"id": "11", "name": "Study 11", "type": "FIELD"}],
        }


@pytest.mark.asyncio
async def test_compare_germplasm_returns_shared_interpretation(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=100):
        if germplasm_id == 101:
            return [
                {
                    "id": "obs-1",
                    "observation_db_id": "OBS-1",
                    "value": "4.0",
                    "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                    "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
                },
            ]
        return [
            {
                "id": "obs-2",
                "observation_db_id": "OBS-2",
                "value": "5.5",
                "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                "germplasm": {"id": "102", "name": "Swarna", "accession": "Swarna"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "compare_germplasm",
        {"organization_id": 1, "germplasm_ids": ["IR64", "Swarna"]},
    )

    assert result["success"] is True
    assert result["result_type"] == "comparison"
    assert isinstance(result["data"], list)
    assert result["comparison_context"]["interpretation"]["contract_version"] == "phenotyping.interpretation.v1"
    assert result["data"][0]["candidate"] == "Swarna"
    assert result["calculation_ids"]


@pytest.mark.asyncio
async def test_get_trial_results_includes_interpretation(monkeypatch):
    async def fake_get_by_study(db, organization_id, study_id, limit=100):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "value": "4.2",
                "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            },
            {
                "id": "obs-2",
                "observation_db_id": "OBS-2",
                "value": "5.1",
                "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                "germplasm": {"id": "102", "name": "Swarna", "accession": "Swarna"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_study",
        fake_get_by_study,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        trial_search_service=TrialSearchStub(),
    )

    result = await executor.execute(
        "get_trial_results",
        {"organization_id": 1, "trial_id": "1"},
    )

    assert result["success"] is True
    assert result["result_type"] == "trial_results"
    assert result["data"]["interpretation"]["contract_version"] == "phenotyping.interpretation.v1"
    assert result["data"]["top_performers"][0]["candidate"] == "Swarna"
    assert result["evidence_refs"]


@pytest.mark.asyncio
async def test_function_executor_rejects_disallowed_tool_before_dispatch():
    capability_registry = CapabilityRegistry(
        capability_overrides=["search_germplasm"],
    )
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        capability_registry=capability_registry,
        trial_search_service=TrialSearchStub(),
    )

    with pytest.raises(FunctionExecutionError, match="not permitted"):
        await executor.execute("get_trial_results", {"organization_id": 1, "trial_id": "1"})
