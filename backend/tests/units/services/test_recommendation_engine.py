"""
TDD tests for RecommendationEngine.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1: Data models (RecommendationEntry, EvidenceFactor, RecommendationResult)
- Task 2: Factor extraction (trait_performance, genomic_prediction, disease_resistance, seed_availability)
- Task 3: Weight management (parse, normalize)
- Task 4: Composite scoring and classification
- Task 5: recommend() orchestration
- Task 6: Cross-domain handler wiring (intent detection)
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.modules.ai.services.reevu.recommendation_engine import (
    RecommendationEngine,
    RecommendationEntry,
    EvidenceFactor,
    RecommendationResult,
)
from app.modules.ai.services.reevu.evidence_synthesis_engine import (
    EvidenceSynthesisEngine,
    SynthesisResult,
    EvidenceContradiction,
    EvidenceGap,
)
from app.modules.ai.services.reevu.step_executor import (
    ExecutionOutcome,
    StepResult,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_outcome(step_results: list[StepResult]) -> ExecutionOutcome:
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


def _empty_synthesis() -> SynthesisResult:
    return SynthesisResult(
        primary_conclusion=None,
        confidence=0.7,
        supporting_evidence=[],
        contradictions=[],
        gaps=[],
        caveats=[],
    )


def _analytics_step(rankings: list[dict]) -> StepResult:
    return StepResult(
        step_id="analytics-1", domain="analytics", status="success",
        records={"ranking": {"ranked_germplasm": rankings}},
        entity_ids=[str(r["germplasm_id"]) for r in rankings],
    )


def _genomics_step(entries: list[dict]) -> StepResult:
    return StepResult(
        step_id="genomics-1", domain="genomics", status="success",
        records={"gebv_result": {"entries": entries}},
        entity_ids=[str(e["germplasm_id"]) for e in entries],
    )


def _pest_disease_step(profiles: list[dict]) -> StepResult:
    return StepResult(
        step_id="pd-1", domain="pest_disease", status="success",
        records={"resistance_profiles": profiles, "scouting_records": []},
        entity_ids=[str(p.get("germplasm_id", "")) for p in profiles],
    )


def _seed_ops_step(seedlots: list[dict]) -> StepResult:
    return StepResult(
        step_id="seed-1", domain="seed_ops", status="success",
        records={"seedlots": seedlots, "inventory_summary": {}},
        entity_ids=[str(s.get("germplasm_id", "")) for s in seedlots],
    )


# ── Task 1: Data models ───────────────────────────────────────────────────────

def test_recommendation_entry_has_required_fields():
    entry = RecommendationEntry(
        rank=1,
        germplasm_id="10",
        germplasm_name="IR64",
        composite_score=0.82,
        classification="advance",
        evidence_chain=[],
        caveats=[],
    )
    assert entry.rank == 1
    assert entry.composite_score == 0.82
    assert entry.classification == "advance"


def test_evidence_factor_has_required_fields():
    factor = EvidenceFactor(
        factor_name="trait_performance",
        value=0.9,
        raw_value="4.2 t/ha",
        source_domain="analytics",
        evidence_refs=["analytics-1"],
        weight=0.4,
    )
    assert factor.factor_name == "trait_performance"
    assert factor.value == 0.9
    assert factor.weight == 0.4


def test_recommendation_result_has_required_fields():
    result = RecommendationResult(
        ranked_entries=[],
        classification={"advance": [], "drop": [], "retest": []},
        weights_used={},
        factors_available=[],
        factors_missing=[],
        evidence_refs=[],
    )
    assert isinstance(result.ranked_entries, list)
    assert "advance" in result.classification


def test_engine_has_default_weights_and_thresholds():
    engine = RecommendationEngine()
    assert "trait_performance" in engine.DEFAULT_WEIGHTS
    assert "genomic_prediction" in engine.DEFAULT_WEIGHTS
    assert "disease_resistance" in engine.DEFAULT_WEIGHTS
    assert "seed_availability" in engine.DEFAULT_WEIGHTS
    assert engine.ADVANCE_THRESHOLD == 0.7
    assert engine.DROP_THRESHOLD == 0.3


# ── Task 2: Factor extraction ─────────────────────────────────────────────────

def test_extract_trait_performance_normalizes_to_0_1():
    """Mean values are normalized so the highest = 1.0 and lowest = 0.0."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.0},
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 3.0},
            {"germplasm_id": "30", "name": "MTU7029", "rank": 3, "mean_value": 1.0},
        ])
    ])

    factors = engine._extract_trait_performance(outcome)

    assert factors is not None
    assert abs(factors["10"] - 1.0) < 0.01   # highest → 1.0
    assert abs(factors["30"] - 0.0) < 0.01   # lowest → 0.0
    assert 0.0 < factors["20"] < 1.0          # middle → between


def test_extract_trait_performance_returns_none_when_no_analytics():
    """Returns None when no analytics step exists."""
    engine = RecommendationEngine()
    outcome = _make_outcome([_genomics_step([{"germplasm_id": "10", "gebv": 0.9}])])

    assert engine._extract_trait_performance(outcome) is None


def test_extract_trait_performance_handles_single_entry():
    """Single entry normalizes to 1.0 (no range to normalize over)."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 4.5}])
    ])

    factors = engine._extract_trait_performance(outcome)

    assert factors is not None
    assert factors["10"] == 1.0


def test_extract_genomic_prediction_normalizes_gebv():
    """GEBV values are normalized to 0-1 within the set."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _genomics_step([
            {"germplasm_id": "10", "gebv": 0.9},
            {"germplasm_id": "20", "gebv": 0.5},
            {"germplasm_id": "30", "gebv": 0.1},
        ])
    ])

    factors = engine._extract_genomic_prediction(outcome)

    assert factors is not None
    assert abs(factors["10"] - 1.0) < 0.01
    assert abs(factors["30"] - 0.0) < 0.01


def test_extract_genomic_prediction_returns_none_when_no_genomics():
    engine = RecommendationEngine()
    outcome = _make_outcome([_analytics_step([{"germplasm_id": "10", "rank": 1, "mean_value": 4.0}])])

    assert engine._extract_genomic_prediction(outcome) is None


def test_extract_disease_resistance_resistant_scores_high():
    """Resistant germplasm scores near 1.0; susceptible scores near 0.0."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _pest_disease_step([
            {"germplasm_id": "10", "resistance_type": "complete", "disease_name": "Blast"},
            {"germplasm_id": "20", "resistance_type": "susceptible", "disease_name": "Blast"},
        ])
    ])

    factors = engine._extract_disease_resistance(outcome)

    assert factors is not None
    assert factors["10"] > factors["20"]
    assert factors["10"] >= 0.5   # resistant → high score
    assert factors["20"] <= 0.5   # susceptible → low score


def test_extract_disease_resistance_returns_none_when_no_pest_disease():
    engine = RecommendationEngine()
    outcome = _make_outcome([_analytics_step([{"germplasm_id": "10", "rank": 1, "mean_value": 4.0}])])

    assert engine._extract_disease_resistance(outcome) is None


def test_extract_seed_availability_binary():
    """Germplasm with stock > 0 → 1.0; no stock → 0.0."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _seed_ops_step([
            {"germplasm_id": "10", "quantity_grams": 500},
            {"germplasm_id": "20", "quantity_grams": 0},
        ])
    ])

    factors = engine._extract_seed_availability(outcome)

    assert factors is not None
    assert factors["10"] == 1.0
    assert factors["20"] == 0.0


def test_extract_seed_availability_returns_none_when_no_seed_ops():
    engine = RecommendationEngine()
    outcome = _make_outcome([_analytics_step([{"germplasm_id": "10", "rank": 1, "mean_value": 4.0}])])

    assert engine._extract_seed_availability(outcome) is None


# ── Task 3: Weight management ─────────────────────────────────────────────────

def test_normalize_weights_sums_to_1():
    """Normalized weights always sum to 1.0."""
    engine = RecommendationEngine()
    weights = {"trait_performance": 0.4, "genomic_prediction": 0.3, "disease_resistance": 0.2, "seed_availability": 0.1}
    available = ["trait_performance", "genomic_prediction", "disease_resistance", "seed_availability"]

    normalized = engine._normalize_weights(weights, available)

    assert abs(sum(normalized.values()) - 1.0) < 1e-9


def test_normalize_weights_excludes_missing_factors():
    """Missing factors are excluded and remaining weights renormalize to 1.0."""
    engine = RecommendationEngine()
    weights = {"trait_performance": 0.4, "genomic_prediction": 0.3, "disease_resistance": 0.2, "seed_availability": 0.1}
    available = ["trait_performance", "disease_resistance"]  # genomic and seed missing

    normalized = engine._normalize_weights(weights, available)

    assert "genomic_prediction" not in normalized
    assert "seed_availability" not in normalized
    assert abs(sum(normalized.values()) - 1.0) < 1e-9
    assert "trait_performance" in normalized
    assert "disease_resistance" in normalized


def test_parse_user_weights_boosts_disease_resistance():
    """'prioritize disease resistance' doubles the disease_resistance weight."""
    engine = RecommendationEngine()
    weights = engine._parse_user_weights("prioritize disease resistance for this selection")

    assert weights["disease_resistance"] > engine.DEFAULT_WEIGHTS["disease_resistance"]


def test_parse_user_weights_boosts_yield():
    """'yield is most important' doubles the trait_performance weight."""
    engine = RecommendationEngine()
    weights = engine._parse_user_weights("yield is most important for our program")

    assert weights["trait_performance"] > engine.DEFAULT_WEIGHTS["trait_performance"]


def test_parse_user_weights_returns_defaults_for_neutral_query():
    """Neutral query returns default weights unchanged."""
    engine = RecommendationEngine()
    weights = engine._parse_user_weights("which varieties should I advance?")

    assert weights == engine.DEFAULT_WEIGHTS


# ── Task 4: Composite scoring and classification ──────────────────────────────

def test_compute_composite_score_weighted_sum():
    """Composite score is the weighted sum of factor values."""
    engine = RecommendationEngine()
    factors = {"trait_performance": 0.8, "genomic_prediction": 0.6}
    weights = {"trait_performance": 0.6, "genomic_prediction": 0.4}

    score = engine._compute_composite_score(factors, weights)

    expected = 0.8 * 0.6 + 0.6 * 0.4
    assert abs(score - expected) < 1e-9


def test_classify_advance_when_score_above_threshold():
    engine = RecommendationEngine()
    assert engine._classify(0.75) == "advance"
    assert engine._classify(0.70) == "advance"


def test_classify_drop_when_score_below_threshold():
    engine = RecommendationEngine()
    assert engine._classify(0.25) == "drop"
    assert engine._classify(0.0) == "drop"


def test_classify_retest_when_score_in_middle():
    engine = RecommendationEngine()
    assert engine._classify(0.5) == "retest"
    assert engine._classify(0.3) == "retest"
    assert engine._classify(0.69) == "retest"


@given(
    scores=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=20),
    weights_raw=st.lists(st.floats(min_value=0.01, max_value=1.0), min_size=1, max_size=4),
)
@settings(max_examples=100)
def test_property_ranking_order_and_classification(scores, weights_raw):
    """Entries are sorted descending by composite_score; classification matches thresholds."""
    engine = RecommendationEngine()

    # Build a minimal outcome with analytics rankings
    rankings = [
        {"germplasm_id": str(i), "name": f"G{i}", "rank": i + 1, "mean_value": s * 10}
        for i, s in enumerate(scores)
    ]
    outcome = _make_outcome([_analytics_step(rankings)])
    synthesis = _empty_synthesis()

    result = engine.recommend(outcome, synthesis, "which varieties should I advance?")

    # Entries must be sorted descending
    for i in range(len(result.ranked_entries) - 1):
        assert result.ranked_entries[i].composite_score >= result.ranked_entries[i + 1].composite_score

    # Classification must match thresholds
    for entry in result.ranked_entries:
        if entry.composite_score >= engine.ADVANCE_THRESHOLD:
            assert entry.classification == "advance"
        elif entry.composite_score < engine.DROP_THRESHOLD:
            assert entry.classification == "drop"
        else:
            assert entry.classification == "retest"

    # Weights must sum to 1.0
    if result.weights_used:
        assert abs(sum(result.weights_used.values()) - 1.0) < 1e-6


# ── Task 5: recommend() orchestration ────────────────────────────────────────

def test_recommend_returns_recommendation_result():
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.0},
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 3.0},
        ])
    ])
    result = engine.recommend(outcome, _empty_synthesis(), "which varieties should I advance?")

    assert isinstance(result, RecommendationResult)
    assert len(result.ranked_entries) == 2
    assert result.ranked_entries[0].rank == 1
    assert result.ranked_entries[0].composite_score >= result.ranked_entries[1].composite_score


def test_recommend_uses_all_available_factors():
    """When multiple domain steps exist, all factors are used in scoring."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.0},
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 3.0},
        ]),
        _genomics_step([
            {"germplasm_id": "10", "gebv": 0.9},
            {"germplasm_id": "20", "gebv": 0.4},
        ]),
        _seed_ops_step([
            {"germplasm_id": "10", "quantity_grams": 500},
        ]),
    ])

    result = engine.recommend(outcome, _empty_synthesis(), "which varieties should I advance?")

    assert "trait_performance" in result.factors_available
    assert "genomic_prediction" in result.factors_available
    assert "seed_availability" in result.factors_available
    assert len(result.ranked_entries) == 2


def test_recommend_lists_missing_factors():
    """Factors with no data appear in factors_missing."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.0}])
    ])

    result = engine.recommend(outcome, _empty_synthesis(), "which varieties should I advance?")

    assert "genomic_prediction" in result.factors_missing
    assert "disease_resistance" in result.factors_missing
    assert "seed_availability" in result.factors_missing


def test_recommend_attaches_caveats_from_synthesis_contradictions():
    """Entries with contradictions in SynthesisResult have non-empty caveats."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.0}])
    ])
    synthesis = SynthesisResult(
        primary_conclusion="IR64 is top performer",
        confidence=0.7,
        supporting_evidence=[],
        contradictions=[
            EvidenceContradiction(
                domain_a="analytics", domain_b="pest_disease",
                entity_id="10", entity_name="IR64",
                claim_a="IR64 ranks #1 for yield",
                claim_b="IR64 is susceptible to blast",
                severity="warning",
            )
        ],
        gaps=[],
        caveats=["Caution: IR64 ranks #1 for yield, but IR64 is susceptible to blast"],
    )

    result = engine.recommend(outcome, synthesis, "which varieties should I advance?")

    ir64_entry = next((e for e in result.ranked_entries if e.germplasm_id == "10"), None)
    assert ir64_entry is not None
    assert len(ir64_entry.caveats) >= 1


def test_recommend_classification_dict_groups_entries():
    """classification dict groups germplasm names by advance/drop/retest."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([
            {"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 10.0},  # will be advance
            {"germplasm_id": "20", "name": "Swarna", "rank": 2, "mean_value": 5.0},  # retest
            {"germplasm_id": "30", "name": "MTU7029", "rank": 3, "mean_value": 0.0},  # will be drop
        ])
    ])

    result = engine.recommend(outcome, _empty_synthesis(), "which varieties should I advance?")

    all_classified = (
        result.classification["advance"]
        + result.classification["drop"]
        + result.classification["retest"]
    )
    assert len(all_classified) == 3


def test_recommend_evidence_chain_contains_factor_entries():
    """Each RecommendationEntry has at least one EvidenceFactor in its evidence_chain."""
    engine = RecommendationEngine()
    outcome = _make_outcome([
        _analytics_step([{"germplasm_id": "10", "name": "IR64", "rank": 1, "mean_value": 5.0}])
    ])

    result = engine.recommend(outcome, _empty_synthesis(), "which varieties should I advance?")

    for entry in result.ranked_entries:
        assert len(entry.evidence_chain) >= 1
        for factor in entry.evidence_chain:
            assert isinstance(factor, EvidenceFactor)
            assert factor.factor_name
            assert 0.0 <= factor.value <= 1.0


def test_recommend_returns_empty_when_no_germplasm_data():
    """Returns empty ranked_entries when no domain steps have germplasm data."""
    engine = RecommendationEngine()
    outcome = _make_outcome([])

    result = engine.recommend(outcome, _empty_synthesis(), "which varieties should I advance?")

    assert result.ranked_entries == []
    assert result.factors_available == []


# ── Task 6: Intent detection ──────────────────────────────────────────────────

def test_recommendation_intent_detected_for_advance_query():
    """_is_recommendation_query() returns True for advancement queries."""
    engine = RecommendationEngine()
    for query in [
        "which varieties should I advance?",
        "recommend the best germplasm for release",
        "select top entries for next season",
        "which varieties should I drop?",
        "should I advance IR64?",
    ]:
        assert engine._is_recommendation_query(query), f"Expected True for: {query}"


def test_recommendation_intent_not_detected_for_data_queries():
    """_is_recommendation_query() returns False for data retrieval queries."""
    engine = RecommendationEngine()
    for query in [
        "show me trial results for wheat",
        "what is the yield of IR64?",
        "list all germplasm in program P1",
    ]:
        assert not engine._is_recommendation_query(query), f"Expected False for: {query}"
