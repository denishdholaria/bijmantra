"""Unit tests for Stage B: evidence envelope + provenance validator."""

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.reevu_envelope import (
    CalculationStep,
    ClaimTrace,
    EvidenceRef,
    ReevuEnvelope,
    UncertaintyInfo,
)
from app.modules.ai.services.reevu.response_validator import (
    ClaimItem,
    EvidencePack,
    ResponseValidator,
)
from app.modules.ai.services.reevu_provenance_validator import (
    validate_all,
    validate_freshness,
    validate_required_fields,
    validate_resolvable,
)


# ═══════════════════════════════════════════════════════════════════════
# Evidence Envelope Schema
# ═══════════════════════════════════════════════════════════════════════

class TestEvidenceRef:
    def test_defaults(self):
        ref = EvidenceRef(source_type="rag", entity_id="doc-42")
        assert ref.source_type == "rag"
        assert ref.entity_id == "doc-42"
        assert ref.freshness_seconds is None
        assert ref.query_or_method == ""

    def test_frozen(self):
        ref = EvidenceRef(source_type="rag", entity_id="1")
        with pytest.raises(Exception):
            ref.entity_id = "2"  # type: ignore[misc]


class TestReevuEnvelope:
    def test_empty_envelope(self):
        env = ReevuEnvelope()
        assert env.claims == []
        assert env.claim_traces == []
        assert env.evidence_refs == []
        assert env.calculation_steps == []
        assert env.missing_evidence_signals == []
        assert env.policy_flags == []
        assert env.uncertainty.confidence is None

    def test_full_envelope(self):
        env = ReevuEnvelope(
            claims=["claim1"],
            claim_traces=[
                ClaimTrace(statement="claim1", support_type="retrieval_backed", evidence_refs=["ref-1"])
            ],
            evidence_refs=[EvidenceRef(source_type="rag", entity_id="ref-1")],
            calculation_steps=[CalculationStep(step_id="fn:calculate_gdd")],
            uncertainty=UncertaintyInfo(confidence=0.9, missing_data=["gap"]),
            missing_evidence_signals=["missing_calculation_provenance"],
            policy_flags=["stale_evidence:ref-1"],
        )
        d = env.model_dump()
        assert d["claims"] == ["claim1"]
        assert d["claim_traces"][0]["support_type"] == "retrieval_backed"
        assert len(d["evidence_refs"]) == 1
        assert d["uncertainty"]["confidence"] == 0.9
        assert d["missing_evidence_signals"] == ["missing_calculation_provenance"]


# ═══════════════════════════════════════════════════════════════════════
# Provenance Validator
# ═══════════════════════════════════════════════════════════════════════

class TestValidateFreshness:
    def test_fresh_ref(self):
        ref = EvidenceRef(source_type="rag", entity_id="x", freshness_seconds=100.0)
        assert validate_freshness(ref) is None

    def test_stale_ref(self):
        ref = EvidenceRef(source_type="rag", entity_id="y", freshness_seconds=200_000.0)
        assert validate_freshness(ref) == "stale_evidence:y"

    def test_unknown_freshness(self):
        ref = EvidenceRef(source_type="rag", entity_id="z")
        assert validate_freshness(ref) is None

    def test_negative_freshness_is_invalid(self):
        ref = EvidenceRef(source_type="rag", entity_id="neg", freshness_seconds=-1.0)
        assert validate_freshness(ref) == "invalid_freshness:neg"

    def test_invalid_retrieved_at_timestamp(self):
        ref = EvidenceRef(
            source_type="rag",
            entity_id="bad-ts",
            freshness_seconds=None,
            retrieved_at="not-a-timestamp",
        )
        assert validate_freshness(ref) == "invalid_retrieved_at:bad-ts"

    def test_retrieved_at_fallback_detects_stale(self):
        old_iso = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        ref = EvidenceRef(
            source_type="rag",
            entity_id="old-ts",
            freshness_seconds=None,
            retrieved_at=old_iso,
        )
        assert validate_freshness(ref) == "stale_evidence:old-ts"

    def test_retrieved_at_future_timestamp_flagged(self):
        future_iso = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        ref = EvidenceRef(
            source_type="rag",
            entity_id="future-ts",
            freshness_seconds=None,
            retrieved_at=future_iso,
        )
        assert validate_freshness(ref) == "future_evidence_timestamp:future-ts"

    @pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_freshness_is_invalid(self, bad_value: float):
        ref = EvidenceRef(source_type="rag", entity_id="non-finite", freshness_seconds=bad_value)
        assert validate_freshness(ref) == "invalid_freshness:non-finite"


class TestValidateResolvable:
    def test_valid(self):
        ref = EvidenceRef(source_type="rag", entity_id="abc")
        assert validate_resolvable(ref) is None

    def test_empty_entity(self):
        ref = EvidenceRef(source_type="rag", entity_id="  ")
        assert validate_resolvable(ref) == "unresolvable_ref:empty_entity_id"

    def test_function_entity_id_requires_fn_prefix(self):
        ref = EvidenceRef(source_type="function", entity_id="calc-gdd")
        assert (
            validate_resolvable(ref)
            == "unresolvable_ref:function_entity_id_format:calc-gdd"
        )

    def test_function_entity_id_with_fn_prefix_is_valid(self):
        ref = EvidenceRef(source_type="function", entity_id="fn:calculate_gdd")
        assert validate_resolvable(ref) is None

    @pytest.mark.parametrize(
        ("entity_id", "expected_flag"),
        [
            ("trial-123", "unresolvable_ref:database_entity_id_format:trial-123"),
            ("observation-123", "unresolvable_ref:database_entity_id_format:observation-123"),
            ("germplasm-456", "unresolvable_ref:database_entity_id_format:germplasm-456"),
        ],
    )
    def test_database_entity_id_requires_db_prefix(self, entity_id: str, expected_flag: str):
        ref = EvidenceRef(source_type="database", entity_id=entity_id)
        assert (
            validate_resolvable(ref)
            == expected_flag
        )

    def test_database_entity_id_with_db_prefix_is_valid(self):
        ref = EvidenceRef(source_type="database", entity_id="db:trial:trial-123")
        assert validate_resolvable(ref) is None


class TestValidateRequiredFields:
    def test_valid(self):
        ref = EvidenceRef(source_type="rag", entity_id="1")
        assert validate_required_fields(ref) is None

    def test_missing_source_type(self):
        ref = EvidenceRef(source_type="", entity_id="1")
        assert validate_required_fields(ref) == "missing_source_type:1"

    def test_function_source_requires_query_or_method(self):
        ref = EvidenceRef(source_type="function", entity_id="fn-1", query_or_method="")
        assert validate_required_fields(ref) == "missing_query_or_method:fn-1"

    def test_function_source_with_query_or_method_is_valid(self):
        ref = EvidenceRef(source_type="function", entity_id="fn-2", query_or_method="fn:calculate")
        assert validate_required_fields(ref) is None


class TestValidateAll:
    def test_clean_envelope(self):
        env = ReevuEnvelope(
            claims=["A"],
            evidence_refs=[EvidenceRef(source_type="rag", entity_id="r1")],
        )
        assert validate_all(env) == []

    def test_no_evidence_with_claims(self):
        env = ReevuEnvelope(claims=["A"])
        flags = validate_all(env)
        assert "no_evidence_for_claims" in flags

    def test_stale_flagged(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="s1", freshness_seconds=999_999.0),
            ],
        )
        flags = validate_all(env)
        assert "stale_evidence:s1" in flags

    def test_duplicate_evidence_ref_flagged(self):
        env = ReevuEnvelope(
            claims=["A"],
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-1"),
                EvidenceRef(source_type="rag", entity_id="doc-1"),
            ],
        )
        flags = validate_all(env)
        assert "duplicate_evidence_ref:doc-1" in flags

    def test_duplicate_evidence_ref_normalized(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id=" Doc-2 "),
                EvidenceRef(source_type="rag", entity_id="doc-2"),
            ],
        )
        flags = validate_all(env)
        assert "duplicate_evidence_ref:doc-2" in flags

    def test_conflicting_source_type_flagged(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-3"),
                EvidenceRef(source_type="api", entity_id="doc-3"),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_source_type:doc-3" in flags

    def test_conflicting_source_type_uses_normalized_values(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type=" RAG ", entity_id=" Doc-4 "),
                EvidenceRef(source_type="rag", entity_id="doc-4"),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_source_type:doc-4" not in flags

    def test_validate_all_includes_invalid_retrieved_at_flag(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(
                    source_type="rag",
                    entity_id="doc-5",
                    freshness_seconds=None,
                    retrieved_at="bad-ts",
                )
            ],
        )
        flags = validate_all(env)
        assert "invalid_retrieved_at:doc-5" in flags

    def test_validate_all_includes_missing_query_or_method_for_function(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="function", entity_id="fn-3", query_or_method=""),
            ],
        )
        flags = validate_all(env)
        assert "missing_query_or_method:fn-3" in flags

    def test_validate_all_includes_invalid_database_entity_id_format(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(
                    source_type="database",
                    entity_id="trial-7",
                    query_or_method="trial_search_service.search",
                ),
            ],
        )
        flags = validate_all(env)
        assert "unresolvable_ref:database_entity_id_format:trial-7" in flags

    def test_validate_all_includes_future_timestamp_flag(self):
        future_iso = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(
                    source_type="rag",
                    entity_id="doc-6",
                    freshness_seconds=None,
                    retrieved_at=future_iso,
                )
            ],
        )
        flags = validate_all(env)
        assert "future_evidence_timestamp:doc-6" in flags

    def test_validate_all_includes_function_entity_id_format_flag(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id="calculate_gdd",
                    query_or_method="fn:calculate_gdd",
                )
            ],
        )
        flags = validate_all(env)
        assert "unresolvable_ref:function_entity_id_format:calculate_gdd" in flags

    def test_validate_all_flags_conflicting_query_method_same_entity_source(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-7", query_or_method="search:yield"),
                EvidenceRef(source_type="rag", entity_id="doc-7", query_or_method="search:soil"),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_query_method:doc-7:rag" in flags

    def test_validate_all_does_not_flag_same_query_method_with_case_diff(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="RAG", entity_id=" Doc-8 ", query_or_method="Search:Yield"),
                EvidenceRef(source_type="rag", entity_id="doc-8", query_or_method="search:yield"),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_query_method:doc-8:rag" not in flags

    def test_validate_all_flags_conflicting_retrieved_at_same_entity_source(self):
        base = datetime.now(timezone.utc) - timedelta(minutes=20)
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-9", retrieved_at=base.isoformat()),
                EvidenceRef(
                    source_type="rag",
                    entity_id="doc-9",
                    retrieved_at=(base + timedelta(minutes=3)).isoformat(),
                ),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_retrieved_at:doc-9:rag" in flags

    def test_validate_all_allows_small_retrieved_at_clock_drift(self):
        base = datetime.now(timezone.utc) - timedelta(minutes=20)
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-10", retrieved_at=base.isoformat()),
                EvidenceRef(
                    source_type="rag",
                    entity_id="doc-10",
                    retrieved_at=(base + timedelta(seconds=30)).isoformat(),
                ),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_retrieved_at:doc-10:rag" not in flags

    def test_validate_all_flags_conflicting_freshness_seconds_same_entity_source(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-11", freshness_seconds=30.0),
                EvidenceRef(source_type="rag", entity_id="doc-11", freshness_seconds=200.0),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_freshness_seconds:doc-11:rag" in flags

    def test_validate_all_allows_small_freshness_drift(self):
        env = ReevuEnvelope(
            evidence_refs=[
                EvidenceRef(source_type="rag", entity_id="doc-12", freshness_seconds=100.0),
                EvidenceRef(source_type="rag", entity_id="doc-12", freshness_seconds=140.0),
            ],
        )
        flags = validate_all(env)
        assert "conflicting_freshness_seconds:doc-12:rag" not in flags


# ═══════════════════════════════════════════════════════════════════════
# Anti-hallucination checks (Stage B additions to ResponseValidator)
# ═══════════════════════════════════════════════════════════════════════

class TestCitationMismatch:
    def test_no_citations(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"1", "2"})
        assert v.check_citation_mismatch("Hello world", pack) == []

    def test_matched_citation(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"1"})
        assert v.check_citation_mismatch("According to [1]", pack) == []

    def test_unmatched_citation(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"1"})
        flags = v.check_citation_mismatch("See [1] and [3]", pack)
        assert "citation_mismatch:[3]" in flags

    def test_unmatched_ref_tag(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"doc-1"})
        flags = v.check_citation_mismatch("Based on [[ref:doc-1]] and [[ref:doc-9]]", pack)
        assert "citation_mismatch:[[ref:doc-9]]" in flags

    def test_case_and_whitespace_normalized_matching(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"  Doc-7  "})
        flags = v.check_citation_mismatch("Source [[ref:doc-7]]", pack)
        assert flags == []

    def test_comma_separated_numeric_citations(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"1"})
        flags = v.check_citation_mismatch("As shown in [1, 3]", pack)
        assert "citation_mismatch:[3]" in flags
        assert "citation_mismatch:[1]" not in flags

    def test_numeric_citation_range(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"1", "2"})
        flags = v.check_citation_mismatch("See references [1-3]", pack)
        assert "citation_mismatch:[3]" in flags
        assert "citation_mismatch:[1]" not in flags
        assert "citation_mismatch:[2]" not in flags

    def test_semicolon_and_mixed_numeric_citations(self):
        v = ResponseValidator()
        pack = EvidencePack(evidence_refs={"1", "2", "4"})
        flags = v.check_citation_mismatch("See references [1;2,4-5]", pack)
        assert "citation_mismatch:[5]" in flags
        assert "citation_mismatch:[1]" not in flags
        assert "citation_mismatch:[2]" not in flags
        assert "citation_mismatch:[4]" not in flags


class TestPercentageWithoutCalc:
    def test_percentage_with_calcs(self):
        v = ResponseValidator()
        pack = EvidencePack(calculation_ids={"fn:calc"})
        assert v.check_percentage_without_calc("95% yield improvement", pack) == []

    def test_percentage_without_calcs(self):
        v = ResponseValidator()
        pack = EvidencePack()
        flags = v.check_percentage_without_calc("Achieved 95% yield improvement", pack)
        assert len(flags) >= 1
        assert "percentage_without_calc" in flags[0]

    def test_confidence_percentage_not_flagged(self):
        v = ResponseValidator()
        pack = EvidencePack()
        flags = v.check_percentage_without_calc("Model reported 95% confidence in this answer", pack)
        assert flags == []

    def test_ci_percentage_not_flagged(self):
        v = ResponseValidator()
        pack = EvidencePack()
        flags = v.check_percentage_without_calc("Result reported as 95% CI across replications", pack)
        assert flags == []

    def test_no_percentages(self):
        v = ResponseValidator()
        pack = EvidencePack()
        assert v.check_percentage_without_calc("No numbers here", pack) == []


class TestValidateClaims:
    def test_reference_claim_requires_evidence_refs(self):
        v = ResponseValidator()
        claims = [
            ClaimItem(statement="claim", claim_type="reference", evidence_refs=()),
        ]
        result = v.validate_claims(claims, EvidencePack(evidence_refs={"r1"}))
        assert result.valid is False
        assert "reference claim is missing evidence refs" in result.errors[0]

    def test_reference_claim_normalized_ref_match(self):
        v = ResponseValidator()
        claims = [
            ClaimItem(statement="claim", claim_type="reference", evidence_refs=("Doc-1",)),
        ]
        result = v.validate_claims(claims, EvidencePack(evidence_refs={" doc-1 "}))
        assert result.valid is True
