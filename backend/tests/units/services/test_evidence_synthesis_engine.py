"""
TDD tests for EvidenceSynthesisEngine.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1: Data models (SynthesisResult, EvidenceAgreement, EvidenceContradiction, EvidenceGap)
- Task 2: Agreement detection
- Task 3: Contradiction detection
- Task 4: Gap detection
- Task 5: Confidence aggregation and primary conclusion
- Task 6: synthesize() orchestration
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.modules.ai.services.reevu.evidence_synthesis_engine import (
    EvidenceSynthesisEngine,
    SynthesisResult,
    EvidenceAgreement,
    EvidenceContradiction,
    EvidenceGap,
)
from app.modules.ai.services.reevu.step_executor import (
    ExecutionOutcome,
    StepResult,
    EvidenceRef,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_outcome(step_results: list[StepResult]) -> ExecutionOutcome:
    """Build a minimal ExecutionOutcome from a list of StepResults."""
    return ExecutionOutcome(
        step_results=step_results,
        evidence_refs=[],
        total_duration_ms=100.0,
        steps_completed=sum(1 for r in step_results if r.status == "success"),
        steps_failed=sum(1 for r in step_results if r.status == "failed"),
        steps_skipped=0,
        steps_timed_out=0,
        budget_exhausted=False,
    )


def _analytics_step(germplasm_rankings: list[dict]) -> StepResult:
    """Analytics step result with germplasm rankings."""
    return StepResult(
        step_id="analytics-1",
        domain="analytics",
        status="success",
        records={
            "ranking": {
                "ranked_germplasm": germplasm_rankings,
            }
        },
        entity_ids=[str(g["germplasm_id"]) for g in germplasm_rankings],
    )


def _genomics_step(gebv_entries: list[dict]) -> StepResult:
    """Genomics step result with GEBV entries."""
    return StepResult(
        step_id="genomics-1",
        domain="genomics",
        status="success",
        records={
            "gebv_result": {
                "entries": gebv_entries,
            }
        },
        entity_ids=[str(e["germplasm_id"]) for e in gebv_entries],
    )


def _pest_disease_step(resistance_profiles: list[dict]) -> StepResult:
    """Pest/disease step result with resistance profiles."""
    return StepResult(
        step_id="pd-1",
        domain="pest_disease",
        status="success",
        records={"resistance_profiles": resistance_profiles, "scouting_records": []},
        entity_ids=[str(p.get("germplasm_id", "")) for p in resistance_profiles],
    )


def _seed_ops_step(seedlots: list[dict]) -> StepResult:
    """Seed ops step result."""
    return StepResult(
        step_id="seed-1",
        domain="seed_ops",
        status="success",
        records={
            "seedlots": seedlots,
            "inventory_summary": {"availability": "available" if seedlots else "unavailable"},
        },
        entity_ids=[str(s.get("germplasm_id", "")) for s in seedlots],
    )


def _failed_step(domain: str, error_category: str = "missing_service") -> StepResult:
    return StepResult(
        step_id=f"{domain}-1",
        domain=domain,
        status="failed",
        error_category=error_category,
        error_message=f"{domain} service unavailable",
    )


def _empty_step(domain: str) -> StepResult:
    return StepResult(
        step_id=f"{domain}-1",
        domain=domain,
        status="success",
        records={},
        entity_ids=[],
    )


# ── Task 1: Data models ───────────────────────────────────────────────────────

def test_synthesis_result_has_required_fields():
    """SynthesisResult must have all required fields."""
    result = SynthesisResult(
        primary_conclusion="Variety A is top performer",
        confidence=0.8,
        supporting_evidence=[],
        contradictions=[],
        gaps=[],
        caveats=[],
    )
    assert result.primary_conclusion == "Variety A is top performer"
    assert result.confidence == 0.8
    assert isinstance(result.supporting_evidence, list)
    assert isinstance(result.contradictions, list)
    assert isinstance(result.gaps, list)
    assert isinstance(result.caveats, list)


def test_evidence_agreement_has_required_fields():
    agreement = EvidenceAgreement(
        domains=["analytics", "genomics"],
        entity_id="10",
        entity_name="IR64",
        claim="IR64 has highest yield and high GEBV",
        confidence=0.85,
    )
    assert agreement.domains == ["analytics", "genomics"]
    assert agreement.entity_id == "10"
    assert agreement.confidence == 0.85


def test_evidence_contradiction_has_required_fields():
    contradiction = EvidenceContradiction(
        domain_a="analytics",
        domain_b="pest_disease",
        entity_id="10",
        entity_name="IR64",
        claim_a="IR64 ranks #1 for yield",
        claim_b="IR64 is susceptible to blast",
        severity="warning",
    )
    assert contradiction.severity == "warning"
    assert contradiction.domain_a == "analytics"


def test_evidence_gap_has_required_fields():
    gap = EvidenceGap(
        domain="soil",
        entity_id=None,
        description="No soil data for trial locations",
        impact="medium",
        suggestion="Add soil analysis records for trial locations",
    )
    assert gap.impact == "medium"
    assert gap.domain == "soil"


# ── Task 2: Agreement detection ───────────────────────────────────────────────

def test_find_agreements_detects_analytics_genomics_agreement():
    """When analytics ranks germplasm X highest and genomics has high GEBV for X → agreement."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2},
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 4.8},
        ]),
        _genomics_step([
            {"germplasm_id": "10", "gebv": 0.92, "reliability": 0.85},
            {"germplasm_id": "20", "gebv": 0.61, "reliability": 0.70},
        ]),
    ])

    agreements = engine._find_agreements(outcome)

    assert len(agreements) >= 1
    top_agreement = next((a for a in agreements if a.entity_id == "10"), None)
    assert top_agreement is not None
    assert "analytics" in top_agreement.domains
    assert "genomics" in top_agreement.domains


def test_find_agreements_returns_empty_when_no_overlap():
    """No agreements when steps have no overlapping entity IDs."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _genomics_step([{"germplasm_id": "99", "gebv": 0.9, "reliability": 0.8}]),
    ])

    agreements = engine._find_agreements(outcome)

    assert all(a.entity_id != "10" or "genomics" not in a.domains for a in agreements)


def test_find_agreements_requires_two_or_more_domains():
    """Agreements require the same entity to appear in 2+ domain steps."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
    ])

    agreements = engine._find_agreements(outcome)

    # Single domain — no cross-domain agreement possible
    assert not any(len(a.domains) < 2 for a in agreements)


# ── Task 3: Contradiction detection ──────────────────────────────────────────

def test_find_contradictions_detects_high_rank_plus_susceptibility():
    """Top-ranked germplasm with disease susceptibility → contradiction."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2},
        ]),
        _pest_disease_step([
            {
                "germplasm_id": "10",
                "gene_name": "susceptible",
                "resistance_type": "susceptible",
                "disease_name": "Rice Blast",
            }
        ]),
    ])

    contradictions = engine._find_contradictions(outcome)

    assert len(contradictions) >= 1
    c = next((c for c in contradictions if c.entity_id == "10"), None)
    assert c is not None
    assert c.severity in ("warning", "critical")
    assert "analytics" in (c.domain_a, c.domain_b)
    assert "pest_disease" in (c.domain_a, c.domain_b)


def test_find_contradictions_detects_top_performer_no_seed():
    """Top-ranked germplasm with no seed available → contradiction."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2},
        ]),
        _seed_ops_step([]),  # no seedlots — nothing in stock
    ])

    contradictions = engine._find_contradictions(outcome)

    # seed_ops returned empty — top performer has no seed
    seed_contradiction = next(
        (c for c in contradictions if "seed_ops" in (c.domain_a, c.domain_b)), None
    )
    assert seed_contradiction is not None


def test_find_contradictions_returns_empty_when_no_conflict():
    """No contradictions when all signals are consistent."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2},
        ]),
        _genomics_step([
            {"germplasm_id": "10", "gebv": 0.9, "reliability": 0.85},
        ]),
    ])

    contradictions = engine._find_contradictions(outcome)

    # High rank + high GEBV = no contradiction
    assert not any(c.entity_id == "10" for c in contradictions)


# ── Task 4: Gap detection ─────────────────────────────────────────────────────

def test_find_gaps_detects_failed_step_as_high_impact():
    """A failed step with missing_service → high-impact gap."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _failed_step("soil", error_category="missing_service"),
    ])

    gaps = engine._find_gaps(outcome, {})

    assert len(gaps) >= 1
    soil_gap = next((g for g in gaps if g.domain == "soil"), None)
    assert soil_gap is not None
    assert soil_gap.impact == "high"


def test_find_gaps_detects_empty_step_as_medium_impact():
    """A successful step with empty records → medium-impact gap."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _empty_step("genomics"),
    ])

    gaps = engine._find_gaps(outcome, {})

    genomics_gap = next((g for g in gaps if g.domain == "genomics"), None)
    assert genomics_gap is not None
    assert genomics_gap.impact == "medium"


def test_find_gaps_includes_description_and_suggestion():
    """Each gap must have a non-empty description and suggestion."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _failed_step("weather"),
        _empty_step("soil"),
    ])

    gaps = engine._find_gaps(outcome, {})

    for gap in gaps:
        assert gap.description, f"Gap for {gap.domain} has no description"
        assert gap.suggestion, f"Gap for {gap.domain} has no suggestion"


def test_find_gaps_returns_empty_when_all_steps_succeed_with_data():
    """No gaps when all steps succeed and return data."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _genomics_step([{"germplasm_id": "10", "gebv": 0.9, "reliability": 0.85}]),
    ])

    gaps = engine._find_gaps(outcome, {})

    assert gaps == []


# ── Task 5: Confidence aggregation ───────────────────────────────────────────

def test_compute_confidence_returns_value_between_0_1_and_1_0():
    """Confidence must always be in [0.1, 1.0]."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
    ])
    agreements = engine._find_agreements(outcome)
    contradictions = engine._find_contradictions(outcome)
    gaps = engine._find_gaps(outcome, {})

    confidence = engine._compute_confidence(outcome, agreements, contradictions, gaps)

    assert 0.1 <= confidence <= 1.0


def test_compute_confidence_decreases_with_contradictions():
    """More contradictions → lower confidence."""
    engine = EvidenceSynthesisEngine()
    outcome_clean = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _genomics_step([{"germplasm_id": "10", "gebv": 0.9, "reliability": 0.85}]),
    ])
    outcome_conflict = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _pest_disease_step([{
            "germplasm_id": "10", "resistance_type": "susceptible", "disease_name": "Blast"
        }]),
    ])

    conf_clean = engine._compute_confidence(
        outcome_clean,
        engine._find_agreements(outcome_clean),
        engine._find_contradictions(outcome_clean),
        engine._find_gaps(outcome_clean, {}),
    )
    conf_conflict = engine._compute_confidence(
        outcome_conflict,
        engine._find_agreements(outcome_conflict),
        engine._find_contradictions(outcome_conflict),
        engine._find_gaps(outcome_conflict, {}),
    )

    assert conf_conflict <= conf_clean


def test_compute_confidence_increases_with_agreements():
    """More agreements → higher confidence than no agreements."""
    engine = EvidenceSynthesisEngine()
    outcome_no_agree = _make_outcome([
        _failed_step("genomics"),
    ])
    outcome_agree = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _genomics_step([{"germplasm_id": "10", "gebv": 0.9, "reliability": 0.85}]),
    ])

    conf_no = engine._compute_confidence(
        outcome_no_agree, [], [], engine._find_gaps(outcome_no_agree, {})
    )
    conf_yes = engine._compute_confidence(
        outcome_agree,
        engine._find_agreements(outcome_agree),
        [],
        [],
    )

    assert conf_yes >= conf_no


def test_derive_primary_conclusion_uses_top_ranked_germplasm():
    """_derive_primary_conclusion returns a string mentioning the top-ranked entity."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2},
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 4.8},
        ]),
    ])

    conclusion = engine._derive_primary_conclusion(outcome, [])

    assert conclusion is not None
    assert "IR64" in conclusion or "10" in conclusion


def test_derive_primary_conclusion_returns_none_when_no_data():
    """_derive_primary_conclusion returns None when no analytics data exists."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([_failed_step("analytics")])

    conclusion = engine._derive_primary_conclusion(outcome, [])

    assert conclusion is None


def test_build_caveats_converts_contradictions_to_strings():
    """_build_caveats returns non-empty strings for each contradiction."""
    engine = EvidenceSynthesisEngine()
    contradictions = [
        EvidenceContradiction(
            domain_a="analytics", domain_b="pest_disease",
            entity_id="10", entity_name="IR64",
            claim_a="IR64 ranks #1 for yield",
            claim_b="IR64 is susceptible to blast",
            severity="warning",
        )
    ]

    caveats = engine._build_caveats(contradictions, [])

    assert len(caveats) == 1
    assert isinstance(caveats[0], str)
    assert len(caveats[0]) > 10


# ── Task 5.4: Property test — confidence bounds ───────────────────────────────

@given(
    n_agreements=st.integers(min_value=0, max_value=10),
    n_contradictions=st.integers(min_value=0, max_value=10),
    n_high_gaps=st.integers(min_value=0, max_value=5),
    steps_completed=st.integers(min_value=0, max_value=10),
    total_steps=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_confidence_always_in_bounds(
    n_agreements, n_contradictions, n_high_gaps, steps_completed, total_steps
):
    """Confidence is always between 0.1 and 1.0 for any input combination."""
    engine = EvidenceSynthesisEngine()

    agreements = [
        EvidenceAgreement(
            domains=["a", "b"], entity_id=str(i), entity_name=f"G{i}",
            claim="test", confidence=0.8,
        )
        for i in range(n_agreements)
    ]
    contradictions = [
        EvidenceContradiction(
            domain_a="a", domain_b="b", entity_id=str(i), entity_name=f"G{i}",
            claim_a="high", claim_b="low", severity="warning",
        )
        for i in range(n_contradictions)
    ]
    gaps = [
        EvidenceGap(domain="soil", entity_id=None, description="no data",
                    impact="high", suggestion="add data")
        for _ in range(n_high_gaps)
    ]

    outcome = ExecutionOutcome(
        step_results=[],
        evidence_refs=[],
        total_duration_ms=0.0,
        steps_completed=min(steps_completed, total_steps),
        steps_failed=0,
        steps_skipped=0,
        steps_timed_out=0,
        budget_exhausted=False,
    )

    confidence = engine._compute_confidence(outcome, agreements, contradictions, gaps)

    assert 0.1 <= confidence <= 1.0, f"Confidence {confidence} out of bounds"


# ── Task 6: synthesize() orchestration ───────────────────────────────────────

def test_synthesize_returns_synthesis_result():
    """synthesize() returns a SynthesisResult with all required fields."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _genomics_step([{"germplasm_id": "10", "gebv": 0.9, "reliability": 0.85}]),
    ])

    result = engine.synthesize(outcome, "which variety is best for yield?", {})

    assert isinstance(result, SynthesisResult)
    assert 0.1 <= result.confidence <= 1.0
    assert isinstance(result.supporting_evidence, list)
    assert isinstance(result.contradictions, list)
    assert isinstance(result.gaps, list)
    assert isinstance(result.caveats, list)


def test_synthesize_detects_agreement_in_full_flow():
    """synthesize() detects analytics+genomics agreement for same top entity."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2},
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 4.8},
        ]),
        _genomics_step([
            {"germplasm_id": "10", "gebv": 0.92, "reliability": 0.85},
        ]),
    ])

    result = engine.synthesize(outcome, "which variety is best?", {})

    assert len(result.supporting_evidence) >= 1
    assert result.primary_conclusion is not None


def test_synthesize_detects_contradiction_in_full_flow():
    """synthesize() detects contradiction between analytics rank and disease susceptibility."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _pest_disease_step([{
            "germplasm_id": "10",
            "resistance_type": "susceptible",
            "disease_name": "Rice Blast",
        }]),
    ])

    result = engine.synthesize(outcome, "which variety should I advance?", {})

    assert len(result.contradictions) >= 1
    assert len(result.caveats) >= 1


def test_synthesize_detects_gap_for_failed_step():
    """synthesize() detects gap when a domain step failed."""
    engine = EvidenceSynthesisEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.2}]),
        _failed_step("soil"),
    ])

    result = engine.synthesize(outcome, "why did yield differ across locations?", {})

    assert any(g.domain == "soil" for g in result.gaps)
