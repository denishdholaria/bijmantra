"""
REEVU Runtime Metrics Collector — Stage D Operations

Lightweight in-process metrics for request counting, latency histograms,
and policy flag tracking.  Thread-safe via ``threading.Lock``.

Use ``ReevuMetrics.get()`` to obtain the singleton and ``record_request()``
after each chat round-trip.  ``get_metrics_snapshot()`` returns a plain dict
suitable for JSON serialisation and can be scraped by any observability backend.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class ReevuMetrics:
    """Singleton runtime metrics collector for REEVU chat pipeline."""

    _instance: ReevuMetrics | None = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> ReevuMetrics:
        """Return the process-wide singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        with cls._lock:
            cls._instance = None

    def __init__(self) -> None:
        self._lock_instance = threading.Lock()
        self._started_at: float = time.monotonic()

        # Counters ─────────────────────────────────────────────────────
        # request count keyed by (domain, function_name, status)
        self._requests: dict[tuple[str, str, str], int] = defaultdict(int)

        # policy flag count keyed by flag type
        self._policy_flags: dict[str, int] = defaultdict(int)

        # Histogram (simple list of values — no external deps) ─────────
        # latency_seconds keyed by stage
        self._latencies: dict[str, list[float]] = defaultdict(list)

        # Provider latency keyed by provider name
        self._provider_latencies: dict[str, list[float]] = defaultdict(list)

        # Safe failures keyed by reason
        self._safe_failures: dict[str, int] = defaultdict(int)

        # Routing decisions keyed by normalized operator-facing label
        self._routing_decisions: dict[str, int] = defaultdict(int)

    # ── recording ─────────────────────────────────────────────────────

    def record_request(
        self,
        *,
        domain: str = "unknown",
        function_name: str = "",
        status: str = "ok",
        latency_seconds: float | None = None,
        stage: str = "total",
        policy_flags: list[str] | None = None,
        provider: str | None = None,
        safe_failure_reason: str | None = None,
        routing_decisions: list[str] | None = None,
    ) -> None:
        """Record a single chat request with associated metrics.

        Parameters
        ----------
        domain : str
            Primary domain tag for the request (e.g. "breeding").
        function_name : str
            Name of the tool/function executed, or empty string.
        status : str
            "ok" | "error" | "safe_failure".
        latency_seconds : float | None
            Round-trip latency for the given *stage*.
        stage : str
            Which stage the latency belongs to (e.g. "plan", "execute", "validate", "total").
        policy_flags : list[str] | None
            Policy flags raised during this request.
        provider : str | None
            Provider selected for the request when known.
        safe_failure_reason : str | None
            Normalized reason for a safe-failure outcome.
        routing_decisions : list[str] | None
            Routing decisions observed for this request.
        """
        with self._lock_instance:
            self._requests[(domain, function_name, status)] += 1

            if latency_seconds is not None:
                self._latencies[stage].append(latency_seconds)
                if provider:
                    self._provider_latencies[provider].append(latency_seconds)

            for flag in policy_flags or []:
                self._policy_flags[flag] += 1

            for decision in routing_decisions or []:
                self._routing_decisions[decision] += 1

            if status == "safe_failure":
                self._safe_failures[safe_failure_reason or "unspecified"] += 1

    # ── snapshot ──────────────────────────────────────────────────────

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of all collected metrics."""
        with self._lock_instance:
            uptime = time.monotonic() - self._started_at

            requests_summary: list[dict[str, Any]] = []
            for (domain, func, status), count in sorted(self._requests.items()):
                requests_summary.append({
                    "domain": domain,
                    "function_name": func,
                    "status": status,
                    "count": count,
                })

            latency_summary: dict[str, dict[str, Any]] = {}
            for stage, values in sorted(self._latencies.items()):
                if values:
                    sorted_vals = sorted(values)
                    n = len(sorted_vals)
                    latency_summary[stage] = {
                        "count": n,
                        "min": round(sorted_vals[0], 6),
                        "max": round(sorted_vals[-1], 6),
                        "mean": round(sum(sorted_vals) / n, 6),
                        "p50": round(sorted_vals[n // 2], 6),
                        "p95": round(sorted_vals[int(n * 0.95)], 6) if n >= 20 else None,
                        "p99": round(sorted_vals[int(n * 0.99)], 6) if n >= 100 else None,
                    }

            flags_summary: list[dict[str, Any]] = [
                {"flag": flag, "count": count}
                for flag, count in sorted(self._policy_flags.items())
            ]

            total_requests = sum(self._requests.values())

            return {
                "uptime_seconds": round(uptime, 2),
                "total_requests": total_requests,
                "requests": requests_summary,
                "latency": latency_summary,
                "policy_flags": flags_summary,
            }

    def get_diagnostics_snapshot(self) -> dict[str, Any]:
        """Return an operator-focused diagnostics snapshot."""
        with self._lock_instance:
            request_status_totals: dict[str, int] = defaultdict(int)
            for (_, _, status), count in self._requests.items():
                request_status_totals[status] += count

            provider_latency_summary: list[dict[str, Any]] = []
            for provider, values in sorted(self._provider_latencies.items()):
                if not values:
                    continue

                sorted_vals = sorted(values)
                n = len(sorted_vals)
                provider_latency_summary.append({
                    "provider": provider,
                    "count": n,
                    "p50": round(sorted_vals[n // 2], 6),
                    "p95": round(sorted_vals[int(n * 0.95)], 6) if n >= 20 else None,
                    "p99": round(sorted_vals[int(n * 0.99)], 6) if n >= 100 else None,
                })

            safe_failure_summary: list[dict[str, Any]] = [
                {"reason": reason, "count": count}
                for reason, count in sorted(self._safe_failures.items())
            ]

            routing_decision_summary: list[dict[str, Any]] = [
                {"decision": decision, "count": count}
                for decision, count in sorted(self._routing_decisions.items())
            ]

            return {
                "request_statuses": [
                    {"status": status, "count": count}
                    for status, count in sorted(request_status_totals.items())
                ],
                "provider_latencies": provider_latency_summary,
                "safe_failures": safe_failure_summary,
                "routing_decisions": routing_decision_summary,
            }
