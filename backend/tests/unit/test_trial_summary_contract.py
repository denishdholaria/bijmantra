from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from datetime import UTC, datetime, timedelta

import pytest

from app.api.v2.trial_summary import (
    _build_trial_evidence_envelope,
    _derive_trial_summary_contract_metadata,
    _load_trial_numeric_records,
    get_trial_summary,
)
from app.schemas.phenotype_interpretation import PhenotypeInterpretation, PhenotypeInterpretationSummary
from app.schemas.trial_summary_contract import (
    TRIAL_SUMMARY_CONTRACT_VERSION,
    TrialSummaryContractMetadata,
)


@pytest.mark.asyncio
async def test_trial_summary_response_includes_trust_contract_metadata():
    trial = SimpleNamespace(
        id=1,
        trial_db_id="TRIAL-1",
        trial_name="Yield Trial",
        program_id=None,
        program=None,
        start_date=None,
        end_date=None,
        additional_info={},
    )
    interpretation = PhenotypeInterpretation(
        scope="trial_summary",
        methodology="database_trial_observation_means_by_germplasm",
        summary=PhenotypeInterpretationSummary(entity_count=0, trait_count=0, observation_count=0),
        evidence_refs=["db:trial:TRIAL-1", "db:study:101"],
        calculation_ids=["calc:trial:yield_mean"],
    )
    db = AsyncMock()
    db.execute.side_effect = [
        SimpleNamespace(scalar_one=lambda: trial),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [SimpleNamespace(id=101)])),
    ]

    with patch(
        "app.api.v2.trial_summary._resolve_trial",
        new=AsyncMock(return_value=trial),
    ), patch(
        "app.api.v2.trial_summary._load_trial_numeric_records",
        new=AsyncMock(return_value=[]),
    ), patch(
        "app.api.v2.trial_summary._build_trial_info",
        return_value={"trialDbId": "TRIAL-1", "trialName": "Yield Trial"},
    ), patch(
        "app.api.v2.trial_summary._build_top_performers_from_interpretation",
        return_value=[],
    ), patch(
        "app.api.v2.trial_summary._build_trait_summary",
        return_value=[],
    ), patch(
        "app.api.v2.trial_summary._build_location_performance",
        return_value=[],
    ), patch(
        "app.api.v2.trial_summary._build_trial_statistics",
        return_value={"grand_mean": 0.0},
    ), patch(
        "app.api.v2.trial_summary._build_trial_interpretation_records",
        return_value=[],
    ), patch(
        "app.api.v2.trial_summary._select_trial_baseline",
        return_value=(None, None, None),
    ), patch(
        "app.api.v2.trial_summary.phenotype_interpretation_service.build_interpretation",
        return_value=interpretation,
    ):
        response = await get_trial_summary(trial_id="TRIAL-1", db=db, organization_id=1)

    assert response.response_contract_version == TRIAL_SUMMARY_CONTRACT_VERSION
    assert response.trust_surface == "trial_summary"
    assert response.data_source == "database"
    assert response.schema_version == "1"
    assert response.confidence_score == 0.45
    assert response.data_age_seconds is None
    assert response.calculation_method_refs == [
        "fn:trial_summary.mean",
        "fn:trial_summary.coefficient_of_variation",
        "fn:trial_summary.baseline_selection",
    ]
    assert response.interpretation.contract_version == "phenotyping.interpretation.v1"
    assert response.evidence_refs == ["db:trial:TRIAL-1", "db:study:101"]
    assert response.calculation_ids == ["calc:trial:yield_mean"]
    assert response.evidence_envelope is not None
    assert response.evidence_envelope.uncertainty.confidence == 0.45
    assert response.evidence_envelope.evidence_refs[0].source_type == "database"


def test_trial_summary_contract_metadata_defaults_are_stable():
    metadata = TrialSummaryContractMetadata()

    assert metadata.response_contract_version == TRIAL_SUMMARY_CONTRACT_VERSION
    assert metadata.trust_surface == "trial_summary"
    assert metadata.data_source == "database"
    assert metadata.schema_version == "1"
    assert metadata.confidence_score is None
    assert metadata.data_age_seconds is None
    assert metadata.calculation_method_refs == []


def test_trial_summary_contract_metadata_derives_freshness_and_method_refs():
    interpretation = PhenotypeInterpretation(
        scope="trial_summary",
        methodology="database_trial_observation_means_by_germplasm",
        summary=PhenotypeInterpretationSummary(entity_count=3, trait_count=2, observation_count=12),
        evidence_refs=["db:trial:TRIAL-1"],
        calculation_ids=["calc:trial:yield_mean"],
    )
    observed_at = datetime.now(UTC) - timedelta(hours=2)

    metadata = _derive_trial_summary_contract_metadata(
        records=[{"observed_at": observed_at.isoformat(), "updated_at": None, "created_at": None}],
        interpretation=interpretation,
    )

    assert metadata.confidence_score == 0.95
    assert metadata.data_age_seconds is not None
    assert 7190 <= metadata.data_age_seconds <= 7210
    assert metadata.calculation_method_refs == [
        "fn:trial_summary.mean",
        "fn:trial_summary.coefficient_of_variation",
        "fn:trial_summary.baseline_selection",
        "fn:trial_summary.anova",
    ]


@pytest.mark.asyncio
async def test_load_trial_numeric_records_uses_safe_float_for_numeric_rows():
    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                observation_id=11,
                observation_db_id="OBS-11",
                value="4.2",
                germplasm_id=101,
                entry_type="check",
                observation_variable_name="Grain Yield",
                trait_name="Grain Yield",
                trait_db_id="TRT-1",
                trait_unit="t/ha",
                trait_data_type="numeric",
                germplasm_name="IR64",
                germplasm_db_id="IR64",
                study_id=9,
                location_id=3,
                location_name="Ludhiana",
                observation_time_stamp=datetime(2026, 4, 1, tzinfo=UTC),
                updated_at=None,
                created_at=None,
            )
        ]
    )

    records = await _load_trial_numeric_records(db, organization_id=1, trial_internal_id=9)

    assert len(records) == 1
    assert records[0]["value"] == 4.2
    assert records[0]["trait_name"] == "Grain Yield"
    assert records[0]["germplasm_key"] == "IR64"


def test_trial_summary_evidence_envelope_builds_claims_and_steps():
    interpretation = PhenotypeInterpretation(
        scope="trial_summary",
        methodology="database_trial_observation_means_by_germplasm",
        primary_trait_name="Yield",
        summary=PhenotypeInterpretationSummary(entity_count=4, trait_count=2, observation_count=16),
        evidence_refs=["db:trial:TRIAL-9", "db:study:301"],
        calculation_ids=["calc:trial:yield_mean"],
    )
    contract_metadata = TrialSummaryContractMetadata(
        confidence_score=0.92,
        data_age_seconds=3600,
        calculation_method_refs=[
            "fn:trial_summary.mean",
            "fn:trial_summary.coefficient_of_variation",
            "fn:trial_summary.baseline_selection",
            "fn:trial_summary.anova",
        ],
    )
    envelope = _build_trial_evidence_envelope(
        trial_info=SimpleNamespace(
            trialName="Kharif Yield Trial",
            observations=16,
            entries=4,
            locations=2,
            completionRate=92.5,
        ),
        top_performers=[
            SimpleNamespace(
                germplasmName="IR64",
                yield_value=5.2,
                change_percent="+12.1%",
            )
        ],
        statistics={
            "primary_trait": "yield",
            "grand_mean": 4.6,
            "overall_cv": 8.2,
            "heritability": 0.71,
            "anova": {"df_between": 3, "df_within": 12, "ms_between": 1.2, "ms_within": 0.4},
        },
        records=[
            {
                "observation_ref": "db:observation:1001",
                "observed_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                "updated_at": None,
                "created_at": None,
            }
        ],
        interpretation=interpretation,
        contract_metadata=contract_metadata,
    )

    assert envelope.claims
    assert envelope.claims[0].startswith("Trial Kharif Yield Trial includes 16 numeric observations")
    assert envelope.calculation_steps[0].step_id == "fn:trial_summary.mean"
    assert envelope.uncertainty.confidence == 0.92
    assert "incomplete_observation_matrix" in envelope.uncertainty.missing_data


def test_trial_summary_evidence_envelope_flags_stale_evidence():
    interpretation = PhenotypeInterpretation(
        scope="trial_summary",
        methodology="database_trial_observation_means_by_germplasm",
        summary=PhenotypeInterpretationSummary(entity_count=2, trait_count=1, observation_count=2),
        evidence_refs=["db:trial:TRIAL-11"],
        calculation_ids=[],
        warnings=["Baseline entity has no observations for the primary trait."],
    )
    contract_metadata = TrialSummaryContractMetadata(
        confidence_score=0.55,
        data_age_seconds=91 * 24 * 3600,
        calculation_method_refs=["fn:trial_summary.mean"],
    )

    envelope = _build_trial_evidence_envelope(
        trial_info=SimpleNamespace(
            trialName="Old Trial",
            observations=2,
            entries=2,
            locations=1,
            completionRate=50.0,
        ),
        top_performers=[],
        statistics={"primary_trait": None, "grand_mean": None, "anova": None},
        records=[],
        interpretation=interpretation,
        contract_metadata=contract_metadata,
    )

    assert "stale_evidence" in envelope.policy_flags
    assert "low_entity_count" in envelope.policy_flags
    assert any(flag.startswith("interpretation_warning:") for flag in envelope.policy_flags)