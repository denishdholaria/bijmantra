"""
REEVU Runtime Metrics Collector — Stage D Operations

Lightweight in-process metrics for request counting, latency histograms,
and policy flag tracking.  Thread-safe via ``threading.Lock``.

Use ``ReevuMetrics.get()`` to obtain the singleton and ``record_request()``
after each chat round-trip.  ``get_metrics_snapshot()`` returns a plain dict
suitable for JSON serialisation and can be scraped by any observability backend.
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from typing import Any


def _normalize_diagnostic_key(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"

    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "unknown"


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

        # Retrieval execution trace summary keyed by function, domain, and service
        self._retrieval_functions: dict[str, int] = defaultdict(int)
        self._retrieval_domains: dict[str, int] = defaultdict(int)
        self._retrieval_services: dict[str, int] = defaultdict(int)
        self._traced_requests: int = 0
        self._compound_requests: int = 0
        self._step_trace_statuses: dict[str, int] = defaultdict(int)
        self._step_trace_domain_statuses: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._step_trace_domain_durations_ms: dict[str, list[float]] = defaultdict(list)
        self._retrieval_outcomes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._narrowing_effectiveness: dict[str, int] = defaultdict(int)
        self._narrowing_by_domain: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._safe_failure_domains: dict[str, int] = defaultdict(int)
        self._safe_failure_categories_by_domain: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

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
        retrieval_audit: dict[str, Any] | None = None,
        plan_execution_summary: dict[str, Any] | None = None,
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
        retrieval_audit : dict[str, Any] | None
            Retrieval execution audit metadata attached to the response.
        plan_execution_summary : dict[str, Any] | None
            Planner execution summary attached to the response.
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

            if isinstance(retrieval_audit, dict):
                self._traced_requests += 1
                for service in retrieval_audit.get("services") or []:
                    if isinstance(service, str) and service.strip():
                        self._retrieval_services[service.strip()] += 1

            if function_name.strip():
                self._retrieval_functions[function_name.strip()] += 1

            if isinstance(plan_execution_summary, dict):
                for domain_name in plan_execution_summary.get("domains_involved") or []:
                    if isinstance(domain_name, str) and domain_name.strip():
                        self._retrieval_domains[domain_name.strip()] += 1

                if bool(plan_execution_summary.get("is_compound")):
                    self._compound_requests += 1

            plan_steps_by_id: dict[str, dict[str, Any]] = {}
            if isinstance(plan_execution_summary, dict):
                for step in plan_execution_summary.get("steps") or []:
                    if not isinstance(step, dict):
                        continue
                    step_id = str(step.get("step_id") or "").strip()
                    if step_id:
                        plan_steps_by_id[step_id] = step

            trace_by_step_id: dict[str, dict[str, Any]] = {}
            if isinstance(retrieval_audit, dict):
                for trace_entry in retrieval_audit.get("step_execution_trace") or []:
                    if not isinstance(trace_entry, dict):
                        continue

                    domain = str(trace_entry.get("domain") or "").strip()
                    status_value = str(trace_entry.get("status") or "unknown").strip() or "unknown"
                    step_id = str(trace_entry.get("step_id") or "").strip()

                    if domain:
                        self._step_trace_statuses[status_value] += 1
                        self._step_trace_domain_statuses[domain][status_value] += 1

                        duration_ms = trace_entry.get("duration_ms")
                        if isinstance(duration_ms, (int, float)):
                            self._step_trace_domain_durations_ms[domain].append(float(duration_ms))

                    if step_id:
                        trace_by_step_id[step_id] = trace_entry

            for step_id, step in plan_steps_by_id.items():
                domain = str(step.get("domain") or "").strip()
                if not domain:
                    continue

                trace_entry = trace_by_step_id.get(step_id, {})
                trace_status = str(trace_entry.get("status") or "").strip()
                actual_outputs = step.get("actual_outputs")
                has_outputs = bool(actual_outputs)

                if step.get("status") == "completed":
                    self._retrieval_outcomes[domain]["success"] += 1
                elif trace_status == "skipped":
                    continue
                elif has_outputs:
                    self._retrieval_outcomes[domain]["partial"] += 1
                else:
                    self._retrieval_outcomes[domain]["failure"] += 1

                trace_metadata = trace_entry.get("metadata")
                if isinstance(trace_metadata, dict):
                    if trace_metadata.get("narrowing_applied") is True:
                        narrowing_bucket = "applied_non_empty" if has_outputs else "applied_empty"
                        self._narrowing_effectiveness[narrowing_bucket] += 1
                        self._narrowing_by_domain[domain][narrowing_bucket] += 1
                    elif trace_metadata.get("narrowing_skipped") is True:
                        self._narrowing_effectiveness["fell_back_to_unnarrowed"] += 1
                        self._narrowing_by_domain[domain]["fell_back_to_unnarrowed"] += 1

            if status == "safe_failure":
                self._safe_failures[safe_failure_reason or "unspecified"] += 1
                if isinstance(plan_execution_summary, dict):
                    steps_by_domain = {
                        str(step.get("domain") or "").strip(): step
                        for step in plan_execution_summary.get("steps") or []
                        if isinstance(step, dict) and str(step.get("domain") or "").strip()
                    }
                    for domain_name in plan_execution_summary.get("missing_domains") or []:
                        if not isinstance(domain_name, str) or not domain_name.strip():
                            continue
                        domain_key = domain_name.strip()
                        step = steps_by_domain.get(domain_key)
                        if step is None:
                            continue

                        step_id = str(step.get("step_id") or "").strip()
                        trace_entry = trace_by_step_id.get(step_id, {})
                        if str(trace_entry.get("status") or "").strip() == "skipped":
                            continue

                        self._safe_failure_domains[domain_key] += 1
                        category = (
                            trace_entry.get("error_category")
                            or safe_failure_reason
                            or step.get("missing_reason")
                            or "unknown"
                        )
                        self._safe_failure_categories_by_domain[domain_key][
                            _normalize_diagnostic_key(category)
                        ] += 1

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

            retrieval_execution_summary = {
                "traced_requests": self._traced_requests,
                "compound_requests": self._compound_requests,
                "functions": [
                    {"function_name": function_name, "count": count}
                    for function_name, count in sorted(self._retrieval_functions.items())
                ],
                "domains": [
                    {"domain": domain_name, "count": count}
                    for domain_name, count in sorted(self._retrieval_domains.items())
                ],
                "services": [
                    {"service": service_name, "count": count}
                    for service_name, count in sorted(self._retrieval_services.items())
                ],
            }

            step_trace_summary = {
                "total_steps_observed": sum(self._step_trace_statuses.values()),
                "status_distribution": [
                    {"status": status_name, "count": count}
                    for status_name, count in sorted(self._step_trace_statuses.items())
                ],
                "domain_breakdown": [],
            }
            for domain_name in sorted(self._step_trace_domain_statuses):
                status_counts = self._step_trace_domain_statuses[domain_name]
                durations_ms = sorted(self._step_trace_domain_durations_ms.get(domain_name, []))
                total_domain_steps = sum(status_counts.values())
                p50_duration_ms = durations_ms[len(durations_ms) // 2] if durations_ms else 0.0
                avg_duration_ms = (
                    round(sum(durations_ms) / len(durations_ms), 3) if durations_ms else 0.0
                )
                step_trace_summary["domain_breakdown"].append(
                    {
                        "domain": domain_name,
                        "count": total_domain_steps,
                        "avg_duration_ms": avg_duration_ms,
                        "p50_duration_ms": round(p50_duration_ms, 3) if durations_ms else 0.0,
                        "success": status_counts.get("success", 0),
                        "failed": status_counts.get("failed", 0),
                        "skipped": status_counts.get("skipped", 0),
                        "timed_out": status_counts.get("timed_out", 0),
                    }
                )

            retrieval_outcomes_summary = [
                {
                    "domain": domain_name,
                    "success": self._retrieval_outcomes[domain_name].get("success", 0),
                    "partial": self._retrieval_outcomes[domain_name].get("partial", 0),
                    "failure": self._retrieval_outcomes[domain_name].get("failure", 0),
                }
                for domain_name in sorted(self._retrieval_outcomes)
            ]

            narrowing_effectiveness_summary = {
                "applied_non_empty": self._narrowing_effectiveness.get("applied_non_empty", 0),
                "applied_empty": self._narrowing_effectiveness.get("applied_empty", 0),
                "fell_back_to_unnarrowed": self._narrowing_effectiveness.get(
                    "fell_back_to_unnarrowed", 0
                ),
                "domain_breakdown": [
                    {
                        "domain": domain_name,
                        "applied_non_empty": counts.get("applied_non_empty", 0),
                        "applied_empty": counts.get("applied_empty", 0),
                        "fell_back_to_unnarrowed": counts.get("fell_back_to_unnarrowed", 0),
                    }
                    for domain_name, counts in sorted(self._narrowing_by_domain.items())
                ],
            }

            safe_failure_distribution_summary = [
                {
                    "domain": domain_name,
                    "count": self._safe_failure_domains.get(domain_name, 0),
                    "categories": [
                        {"error_category": error_category, "count": count}
                        for error_category, count in sorted(
                            self._safe_failure_categories_by_domain[domain_name].items()
                        )
                    ],
                }
                for domain_name in sorted(self._safe_failure_domains)
            ]

            return {
                "request_statuses": [
                    {"status": status, "count": count}
                    for status, count in sorted(request_status_totals.items())
                ],
                "provider_latencies": provider_latency_summary,
                "safe_failures": safe_failure_summary,
                "routing_decisions": routing_decision_summary,
                "retrieval_execution": retrieval_execution_summary,
                "step_execution_traces": step_trace_summary,
                "narrowing_effectiveness": narrowing_effectiveness_summary,
                "retrieval_outcomes": retrieval_outcomes_summary,
                "safe_failure_distribution": safe_failure_distribution_summary,
            }
