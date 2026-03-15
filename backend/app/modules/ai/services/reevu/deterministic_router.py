"""
REEVU Deterministic Computation Router — Stage C

Routes applicable requests to deterministic computation paths
before LLM synthesis to ensure numeric accuracy and auditability.
"""

from __future__ import annotations

import re

from app.schemas.reevu_plan import RoutingDecision

# ── routing criteria ─────────────────────────────────────────────────

# Function prefixes that always trigger deterministic routing.
DETERMINISTIC_FUNCTION_PREFIXES: tuple[str, ...] = (
    "calculate_",
    "analyze_",
    "predict_",
    "compute_",
    "estimate_",
)

# Message-level heuristics: keywords indicating numeric computation need.
NUMERIC_KEYWORDS: list[str] = [
    "calculate", "compute", "formula", "equation",
    "how many", "what percentage", "sum of", "total of",
    "average", "mean", "median", "standard deviation",
    "correlation", "regression", "gdd", "growing degree days",
    "yield prediction", "yield gap", "cost analysis",
]

# Threshold for numeric token density (tokens with digits / total words).
NUMERIC_DENSITY_THRESHOLD: float = 0.15

_NUMERIC_TOKEN_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")


class DeterministicRouter:
    """Route requests to deterministic computation when criteria match."""

    def get_routing_decision(
        self,
        message: str,
        *,
        function_call_name: str | None = None,
    ) -> RoutingDecision:
        """Evaluate whether a request should go through deterministic computation.

        Returns a ``RoutingDecision`` with matched criteria.
        """
        criteria: list[str] = []

        # 1. Function prefix match.
        if function_call_name and function_call_name.startswith(DETERMINISTIC_FUNCTION_PREFIXES):
            criteria.append(f"function_prefix:{function_call_name}")

        # 2. Message keyword match.
        message_lower = message.lower()
        for kw in NUMERIC_KEYWORDS:
            if kw in message_lower:
                criteria.append(f"keyword:{kw}")
                break  # one is enough

        # 3. Numeric density heuristic.
        words = message.split()
        if words:
            numeric_count = len(_NUMERIC_TOKEN_RE.findall(message))
            density = numeric_count / len(words)
            if density >= NUMERIC_DENSITY_THRESHOLD:
                criteria.append(f"numeric_density:{density:.2f}")

        should_route = len(criteria) > 0

        reason = (
            f"Deterministic routing triggered by: {', '.join(criteria)}"
            if should_route
            else "No deterministic routing criteria matched"
        )

        return RoutingDecision(
            should_route=should_route,
            reason=reason,
            matched_criteria=criteria,
        )

    def should_route(
        self,
        message: str,
        *,
        function_call_name: str | None = None,
    ) -> bool:
        """Convenience shorthand: True if deterministic routing should apply."""
        return self.get_routing_decision(
            message, function_call_name=function_call_name
        ).should_route
