"""Unit tests for cross-contract REEVU envelope integration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.api.v2.chat import _build_reevu_envelope, _validate_response_content
from app.api.v2.trial_summary import _build_trial_evidence_envelope
from app.modules.ai.services.reevu_provenance_validator import validate_all
from app.schemas.compute_contract import ComputeInputSummary, ComputeProvenance
from app.schemas.phenotype_interpretation import (
    PhenotypeInterpretation,
    PhenotypeInterpretationRankingItem,
    PhenotypeInterpretationSummary,
)
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, ReevuEnvelope
from app.schemas.trial_summary_contract import TrialSummaryContractMetadata


class TestCrossContractEnvelopeIntegration:
    def test_compute_provenance_is_portable_to_reevu_envelope(self):
        provenance = ComputeProvenance(
            routine="gblup",
            output_kind="breeding_values",
            backend="numpy",
            execution_mode="sync",
            input_summary=ComputeInputSummary(n_individuals=3, n_markers=4, heritability=0.18),
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id="fn:compute.gblup",
                    query_or_method="compute_engine.compute_gblup",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id="fn:compute.gblup",
                    formula="GEBV = G * u",
                    inputs={"n_individuals": 3, "n_markers": 4},
                )
            ],
            policy_flags=["low_heritability"],
        )

        envelope = ReevuEnvelope(
            claims=["GBLUP breeding values were generated for the submitted genotype matrix."],
            evidence_refs=provenance.evidence_refs,
            calculation_steps=provenance.calculation_steps,
            policy_flags=provenance.policy_flags,
        )

        assert validate_all(envelope) == []
        assert envelope.policy_flags == ["low_heritability"]
        assert envelope.evidence_refs[0].entity_id == "fn:compute.gblup"

    def test_trial_envelope_propagates_ranking_observation_refs(self):
        interpretation = PhenotypeInterpretation(
            scope="trial_summary",
            methodology="database_trial_observation_means_by_germplasm",
            summary=PhenotypeInterpretationSummary(entity_count=2, trait_count=1, observation_count=4),
            evidence_refs=["db:trial:TRIAL-X"],
            ranking=[
                PhenotypeInterpretationRankingItem(
                    rank=1,
                    entity_db_id="E1",
                    entity_name="Entry 1",
                    role="candidate",
                    score_trait_key="yield",
                    score_trait_name="Yield",
                    score=5.5,
                    evidence_refs=["db:observation:101", "db:observation:102"],
                ),
                PhenotypeInterpretationRankingItem(
                    rank=2,
                    entity_db_id="E2",
                    entity_name="Entry 2",
                    role="candidate",
                    score_trait_key="yield",
                    score_trait_name="Yield",
                    score=4.2,
                    evidence_refs=["db:observation:103"],
                ),
            ],
        )

        envelope = _build_trial_evidence_envelope(
            trial_info=SimpleNamespace(
                trialName="Cross-Contract Trial",
                observations=4,
                entries=2,
                locations=1,
                completionRate=100.0,
            ),
            top_performers=[],
            statistics={"primary_trait": "yield", "grand_mean": 4.85, "anova": None},
            records=[
                {"observation_ref": "db:observation:101", "observed_at": datetime.now(UTC).isoformat(), "updated_at": None, "created_at": None},
                {"observation_ref": "db:observation:102", "observed_at": datetime.now(UTC).isoformat(), "updated_at": None, "created_at": None},
                {"observation_ref": "db:observation:103", "observed_at": datetime.now(UTC).isoformat(), "updated_at": None, "created_at": None},
            ],
            interpretation=interpretation,
            contract_metadata=TrialSummaryContractMetadata(confidence_score=0.82, data_age_seconds=3600),
        )

        envelope_ref_ids = [ref.entity_id for ref in envelope.evidence_refs]
        assert "db:observation:101" in envelope_ref_ids
        assert "db:observation:102" in envelope_ref_ids
        assert "db:observation:103" in envelope_ref_ids
        assert "db:trial:TRIAL-X" in envelope_ref_ids

    def test_chat_validation_accepts_compute_contract_artifacts(self):
        validation, evidence_pack = _validate_response_content(
            content="Computed genomic breeding values with grounded evidence and [[calc:calc:compute:gblup]].",
            context_docs=None,
            function_call_name="calculate_gblup",
            function_result={
                "evidence_refs": ["fn:compute.gblup", "db:trial:TRIAL-9"],
                "calculation_ids": ["calc:compute:gblup"],
                "data": [{"id": "job-88", "source_id": "db:compute_job:job-88"}],
            },
        )

        assert validation.valid is True
        assert "fn:compute.gblup" in evidence_pack.evidence_refs
        assert "db:compute_job:job-88" in evidence_pack.evidence_refs
        assert "calc:compute:gblup" in evidence_pack.calculation_ids
        assert "fn:calculate_gblup" in evidence_pack.calculation_ids

    def test_chat_envelope_accepts_trial_summary_contract_artifacts(self):
        validation, evidence_pack = _validate_response_content(
            content="Trial mean improved by 12.4% with supporting observations and [[calc:trial_summary.mean]].",
            context_docs=None,
            function_call_name="analyze_trial_summary",
            function_result={
                "evidence_refs": ["db:trial:TRIAL-22", "db:observation:1001"],
                "calculation_ids": ["calc:trial:yield_mean"],
            },
        )

        envelope = _build_reevu_envelope(
            content="Trial mean improved by 12.4% with supporting observations and [[calc:trial_summary.mean]].",
            evidence_pack=evidence_pack,
            validation=validation,
            context_docs=None,
            function_call_name="analyze_trial_summary",
        )

        assert envelope["claims"]
        assert any(ref["entity_id"] == "db:trial:TRIAL-22" for ref in envelope["evidence_refs"])
        assert any(ref["entity_id"] == "db:observation:1001" for ref in envelope["evidence_refs"])
        assert any(step["step_id"] == "calc:trial:yield_mean" for step in envelope["calculation_steps"])
        assert "no_evidence_for_claims" not in envelope["policy_flags"]

    def test_compute_and_trial_refs_share_validator_expectations(self):
        old_ref = EvidenceRef(
            source_type="database",
            entity_id="db:trial:TRIAL-OLD",
            freshness_seconds=(timedelta(days=3).total_seconds()),
            query_or_method="trial_summary.query",
        )
        compute_ref = EvidenceRef(
            source_type="function",
            entity_id="fn:compute.grm",
            query_or_method="compute_engine.compute_grm",
        )
        envelope = ReevuEnvelope(
            claims=["Compute-supported trial ranking was produced."],
            evidence_refs=[old_ref, compute_ref],
        )

        flags = validate_all(envelope)
        assert "stale_evidence:db:trial:TRIAL-OLD" in flags
        assert "unresolvable_ref:function_entity_id_format:fn:compute.grm" not in flags