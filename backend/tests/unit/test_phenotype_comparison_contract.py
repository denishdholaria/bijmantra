from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v2.phenotype_comparison import (
    CompareRequest,
    ObservationsRequest,
    _build_phenotype_evidence_envelope,
    compare_germplasm,
    get_comparison_statistics,
    get_comparison_traits,
    get_germplasm_for_comparison,
    get_observations_for_germplasm,
)
from app.schemas.phenotype_comparison_contract import PHENOTYPE_COMPARISON_CONTRACT_VERSION


@pytest.mark.asyncio
async def test_germplasm_endpoint_includes_contract_metadata():
    germplasm = SimpleNamespace(
        id=7,
        germplasm_db_id="G-7",
        germplasm_name="IR64",
        default_display_name="IR 64",
        species="Oryza sativa",
    )
    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [germplasm]))

    payload = await get_germplasm_for_comparison(db=db, organization_id=1, limit=10)

    assert payload["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["trust_surface"] == "phenotype_comparison"
    assert payload["data_source"] == "database"
    assert payload["source"] == "database"
    assert payload["schema_version"] == "1"
    assert payload["confidence_score"] is None
    assert payload["data_age_seconds"] is None
    assert payload["scope"] == "germplasm"
    assert payload["result"]["data"][0]["germplasmDbId"] == "G-7"


@pytest.mark.asyncio
async def test_observations_endpoint_includes_contract_metadata():
    request = ObservationsRequest(germplasm_ids=["G-7"])
    observation = SimpleNamespace(
        observation_db_id="OBS-1",
        id=1,
        germplasm_id=7,
        value="5.2",
        observation_time_stamp=None,
        observation_variable=SimpleNamespace(
            observation_variable_name="Yield",
            observation_variable_db_id="VAR-1",
        ),
        germplasm=SimpleNamespace(id=7, germplasm_db_id="G-7", germplasm_name="IR64", default_display_name=None),
    )

    with patch(
        "app.api.v2.phenotype_comparison._load_germplasm_by_external_ids",
        new=AsyncMock(return_value=[observation.germplasm]),
    ), patch(
        "app.api.v2.phenotype_comparison._load_observations",
        new=AsyncMock(return_value=[observation]),
    ):
        payload = await get_observations_for_germplasm(request=request, db=AsyncMock(), organization_id=1)

    assert payload["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["data_source"] == "database"
    assert payload["schema_version"] == "1"
    assert payload["scope"] == "observations"
    assert payload["result"]["data"][0]["observationDbId"] == "OBS-1"


@pytest.mark.asyncio
async def test_traits_endpoint_includes_contract_metadata():
    variable = SimpleNamespace(
        id=1,
        observation_variable_db_id="VAR-1",
        observation_variable_name="Yield",
        scale_name="t/ha",
        data_type="numeric",
    )
    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [variable]))

    payload = await get_comparison_traits(db=db, organization_id=1)

    assert payload["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["data_source"] == "database"
    assert payload["schema_version"] == "1"
    assert payload["scope"] == "traits"
    assert payload["data"][0]["id"] == "VAR-1"


@pytest.mark.asyncio
async def test_compare_endpoint_includes_contract_metadata_and_interpretation():
    request = CompareRequest(germplasm_ids=["G-1", "G-2"], check_id="G-1")
    germplasm_rows = [
        SimpleNamespace(id=1, germplasm_db_id="G-1", germplasm_name="Check 1", default_display_name=None),
        SimpleNamespace(id=2, germplasm_db_id="G-2", germplasm_name="Line 2", default_display_name=None),
    ]
    interpretation = SimpleNamespace(
        model_dump=lambda: {"contract_version": "phenotyping.interpretation.v1", "summary": {"entity_count": 2}},
        entities=[
            SimpleNamespace(entity_db_id="G-1", entity_name="Check 1", metrics=[]),
            SimpleNamespace(
                entity_db_id="G-2",
                entity_name="Line 2",
                metrics=[SimpleNamespace(trait_key="yield", mean=5.4, delta_percent_vs_baseline=8.0)],
            ),
        ],
        evidence_refs=["db:germplasm:G-1", "db:germplasm:G-2"],
        calculation_ids=["calc:yield:mean"],
    )

    with patch(
        "app.api.v2.phenotype_comparison._load_germplasm_by_external_ids",
        new=AsyncMock(return_value=germplasm_rows),
    ), patch(
        "app.api.v2.phenotype_comparison._load_observations",
        new=AsyncMock(return_value=[]),
    ), patch(
        "app.api.v2.phenotype_comparison._build_interpretation_records",
        return_value=[],
    ), patch(
        "app.api.v2.phenotype_comparison.phenotype_interpretation_service.build_interpretation",
        return_value=interpretation,
    ):
        payload = await compare_germplasm(request=request, db=AsyncMock(), organization_id=1)

    assert payload["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["data_source"] == "database"
    assert payload["schema_version"] == "1"
    assert payload["scope"] == "compare"
    assert payload["check_id"] == "G-1"
    assert payload["interpretation"]["contract_version"] == "phenotyping.interpretation.v1"
    assert payload["evidence_refs"] == ["db:germplasm:G-1", "db:germplasm:G-2"]
    assert payload["evidence_envelope"]["claims"]
    assert payload["evidence_envelope"]["uncertainty"]["confidence"] == 0.75


@pytest.mark.asyncio
async def test_statistics_endpoint_includes_contract_metadata_and_summary():
    germplasm_rows = [SimpleNamespace(id=1, germplasm_db_id="G-1", germplasm_name="Check 1")]
    interpretation = SimpleNamespace(
        summary=SimpleNamespace(trait_count=1),
        traits=[SimpleNamespace(trait_key="yield", min=4.8, max=5.1, mean=4.95, std=0.15)],
        model_dump=lambda: {"contract_version": "phenotyping.interpretation.v1", "summary": {"trait_count": 1}},
        evidence_refs=["db:germplasm:G-1"],
        calculation_ids=["calc:yield:mean"],
    )

    with patch(
        "app.api.v2.phenotype_comparison._load_germplasm_by_external_ids",
        new=AsyncMock(return_value=germplasm_rows),
    ), patch(
        "app.api.v2.phenotype_comparison._load_observations",
        new=AsyncMock(return_value=[]),
    ), patch(
        "app.api.v2.phenotype_comparison.phenotype_interpretation_service.build_interpretation",
        return_value=interpretation,
    ), patch(
        "app.api.v2.phenotype_comparison.select",
    ):
        payload = await get_comparison_statistics(germplasm_ids="G-1", db=AsyncMock(), organization_id=1)

    assert payload["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert payload["data_source"] == "database"
    assert payload["schema_version"] == "1"
    assert payload["scope"] == "statistics"
    assert payload["total_traits"] == 1
    assert payload["trait_summary"]["yield"]["mean"] == 4.95
    assert payload["evidence_envelope"]["evidence_refs"][0]["entity_id"] == "db:germplasm:G-1"


def test_build_phenotype_evidence_envelope_tracks_observation_refs_and_flags():
    observation = SimpleNamespace(
        id=9,
        observation_db_id="OBS-9",
        observation_time_stamp="2026-03-11T00:00:00+00:00",
    )
    interpretation = SimpleNamespace(
        summary=SimpleNamespace(entity_count=2, trait_count=1, observation_count=3),
        methodology="database_observation_means_by_germplasm",
        evidence_refs=["db:germplasm:G-1"],
        calculation_ids=["calc:yield:mean"],
        ranking=[
            SimpleNamespace(
                entity_name="Line 2",
                entity_db_id="G-2",
                score=5.4,
                score_trait_name="Yield",
                evidence_refs=["OBS-9"],
            )
        ],
        warnings=["baseline_missing_primary_trait"],
    )

    envelope = _build_phenotype_evidence_envelope(
        scope="compare",
        observations=[observation],
        interpretation=interpretation,
    )

    assert any(ref.entity_id == "OBS-9" and ref.source_type == "database" for ref in envelope.evidence_refs)
    assert envelope.calculation_steps[0].step_id == "calc:yield:mean"
    assert "baseline_missing_primary_trait" in envelope.policy_flags
    assert envelope.uncertainty.confidence == 0.9