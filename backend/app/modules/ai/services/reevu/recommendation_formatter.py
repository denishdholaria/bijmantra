"""
REEVU Comparative Recommendation Formatter — Stage C

Standardizes ranking/comparison outputs with rationale, evidence refs,
and uncertainty notes for auditable recommendation quality.
"""

from __future__ import annotations

from typing import Any

from app.schemas.reevu_plan import ComparisonResult, RankedItem


class RecommendationFormatter:
    """Format comparative recommendation outputs with deterministic structure."""

    def format_comparison(
        self,
        candidates: list[dict[str, Any]],
        *,
        methodology: str = "",
        domains_used: list[str] | None = None,
    ) -> ComparisonResult:
        """Build a structured comparison result from raw candidate data.

        Each candidate dict should contain at minimum:
        - ``name`` or ``candidate``: identifier
        - ``score``: numeric score (optional)
        - ``rationale``: textual reason (optional)
        - ``evidence_refs``: list of ref ids (optional)
        - ``uncertainty``: note about data gaps (optional)
        """
        items: list[RankedItem] = []

        # Sort by score descending if available, otherwise preserve order.
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.get("score", 0) or 0,
            reverse=True,
        )

        for rank, candidate in enumerate(sorted_candidates, start=1):
            name = candidate.get("candidate") or candidate.get("name", f"item-{rank}")
            items.append(
                RankedItem(
                    candidate=str(name),
                    rank=rank,
                    score=candidate.get("score"),
                    rationale=candidate.get("rationale", ""),
                    evidence_refs=candidate.get("evidence_refs", []),
                    uncertainty_note=candidate.get("uncertainty", ""),
                )
            )

        # Build overall recommendation from top candidate.
        overall = ""
        if items:
            top = items[0]
            overall = (
                f"Recommended: {top.candidate}"
                + (f" (score: {top.score})" if top.score is not None else "")
                + (f". {top.rationale}" if top.rationale else "")
            )

        return ComparisonResult(
            items=items,
            methodology=methodology,
            overall_recommendation=overall,
            domains_used=domains_used or [],
        )
