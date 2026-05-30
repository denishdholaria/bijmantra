from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_retrieval import (
    candidate_diagnostic_warnings,
    candidate_retrieval_score,
    candidate_score_factors,
    retrieval_readiness,
)


def test_intelligence_knowledge_graph_retrieval_readiness_marks_clean_candidates_ready() -> None:
    assert retrieval_readiness(
        candidate_count=1,
        matched_edges_without_evidence_count=0,
        low_confidence_edge_count=0,
        missing_confidence_edge_count=0,
    ) == {"status": "ready_for_experimentation", "reasons": []}


def test_intelligence_knowledge_graph_retrieval_readiness_explains_review_reasons() -> None:
    assert retrieval_readiness(
        candidate_count=0,
        matched_edges_without_evidence_count=1,
        low_confidence_edge_count=1,
        missing_confidence_edge_count=1,
    ) == {
        "status": "needs_review",
        "reasons": [
            "no_candidates",
            "matched_edge_missing_evidence",
            "low_confidence_edges",
            "missing_confidence_edges",
        ],
    }
    assert candidate_diagnostic_warnings(
        matched_edges_without_evidence_count=1,
        low_confidence_edge_count=1,
        missing_confidence_edge_count=1,
    ) == [
        "matched_edge_missing_evidence",
        "low_confidence_edges",
        "missing_confidence_edges",
    ]


def test_intelligence_knowledge_graph_candidate_score_policy_is_deterministic() -> None:
    factors = candidate_score_factors(
        match_count=1,
        confidence_values=[0.88],
        matched_evidence_ref_count=1,
        evidence_pack_edge_count=1,
    )

    assert factors == {
        "match_count": 0.333,
        "average_confidence": 0.88,
        "evidence_refs": 0.333,
        "evidence_pack_edges": 0.2,
    }
    assert candidate_retrieval_score(factors) == 0.45
