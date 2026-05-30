"""Pure Intelligence Knowledge Graph retrieval policies."""

from collections.abc import Iterable
from typing import Any


def candidate_diagnostic_warnings(
    *,
    matched_edges_without_evidence_count: int,
    low_confidence_edge_count: int,
    missing_confidence_edge_count: int,
) -> list[str]:
    warnings: list[str] = []
    if matched_edges_without_evidence_count:
        warnings.append("matched_edge_missing_evidence")
    if low_confidence_edge_count:
        warnings.append("low_confidence_edges")
    if missing_confidence_edge_count:
        warnings.append("missing_confidence_edges")
    return warnings


def retrieval_readiness(
    *,
    candidate_count: int,
    matched_edges_without_evidence_count: int,
    low_confidence_edge_count: int,
    missing_confidence_edge_count: int,
) -> dict[str, Any]:
    reasons: list[str] = []
    if candidate_count == 0:
        reasons.append("no_candidates")
    if matched_edges_without_evidence_count:
        reasons.append("matched_edge_missing_evidence")
    if low_confidence_edge_count:
        reasons.append("low_confidence_edges")
    if missing_confidence_edge_count:
        reasons.append("missing_confidence_edges")
    status = "ready_for_experimentation" if not reasons else "needs_review"
    return {"status": status, "reasons": reasons}


def candidate_score_factors(
    *,
    match_count: int,
    confidence_values: Iterable[float],
    matched_evidence_ref_count: int,
    evidence_pack_edge_count: int,
) -> dict[str, float]:
    confidence_values = list(confidence_values)
    average_confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    )
    return {
        "match_count": round(min(match_count / 3, 1.0), 3),
        "average_confidence": round(average_confidence, 3),
        "evidence_refs": round(min(matched_evidence_ref_count / 3, 1.0), 3),
        "evidence_pack_edges": round(min(evidence_pack_edge_count / 5, 1.0), 3),
    }


def candidate_retrieval_score(factors: dict[str, float]) -> float:
    score = (
        factors["match_count"] * 0.35
        + factors["average_confidence"] * 0.25
        + factors["evidence_refs"] * 0.25
        + factors["evidence_pack_edges"] * 0.15
    )
    return round(score, 3)
