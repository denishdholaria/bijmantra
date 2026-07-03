"""
Plan summary building and execution summary extraction.

Extracted from message_service.py — pure functions, no HTTP, no DB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.config import settings
from app.modules.ai.services.reevu import DeterministicRouter, ReevuPlanner

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def _make_planner() -> ReevuPlanner:
    """Construct a ReevuPlanner, injecting DomainEmbeddingService when the feature flag is on."""
    if settings.REEVU_EMBEDDING_DETECTION_ENABLED:
        from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService
        embedding_service = DomainEmbeddingService()
    else:
        embedding_service = None
    return ReevuPlanner(embedding_service=embedding_service)


def build_plan_summary(
    request_message: str,
    *,
    function_call_name: str | None = None,
) -> dict[str, Any]:
    """Build the canonical Stage-C execution plan summary for a chat request."""
    planner = _make_planner()
    plan = planner.build_plan(
        request_message,
        function_call_name=function_call_name,
    )
    plan_summary: dict[str, Any] = {
        "plan_id": plan.plan_id,
        "is_compound": plan.is_compound,
        "domains_involved": plan.domains_involved,
        "total_steps": plan.total_steps,
        "steps": [step.model_dump() for step in plan.steps],
    }
    if plan.metadata:
        plan_summary["metadata"] = dict(plan.metadata)

    routing = DeterministicRouter().get_routing_decision(
        request_message,
        function_call_name=function_call_name,
    )
    if routing.should_route:
        plan_summary["deterministic_routing"] = routing.model_dump()

    return plan_summary


async def build_plan_summary_async(
    request_message: str,
    db: "AsyncSession | None" = None,
    *,
    function_call_name: str | None = None,
) -> dict[str, Any]:
    """Async variant of build_plan_summary.

    When ``REEVU_EMBEDDING_DETECTION_ENABLED`` is True and a database session
    is provided, calls ``planner.build_plan_async()`` so that embedding-based
    domain detection is used.  Falls back to the synchronous ``build_plan()``
    path when the embedding service is not available or ``db`` is None.
    """
    planner = _make_planner()

    if planner._embedding_service is not None and db is not None:
        plan = await planner.build_plan_async(
            request_message,
            db,
            function_call_name=function_call_name,
        )
    else:
        plan = planner.build_plan(
            request_message,
            function_call_name=function_call_name,
        )

    plan_summary: dict[str, Any] = {
        "plan_id": plan.plan_id,
        "is_compound": plan.is_compound,
        "domains_involved": plan.domains_involved,
        "total_steps": plan.total_steps,
        "steps": [step.model_dump() for step in plan.steps],
    }
    if plan.metadata:
        plan_summary["metadata"] = dict(plan.metadata)

    routing = DeterministicRouter().get_routing_decision(
        request_message,
        function_call_name=function_call_name,
    )
    if routing.should_route:
        plan_summary["deterministic_routing"] = routing.model_dump()

    return plan_summary


def extract_plan_execution_summary(
    function_result: dict[str, Any] | None,
    planned_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Merge executed plan summary from function result with the planned summary."""
    executed_summary: dict[str, Any] | None = None
    if isinstance(function_result, dict):
        candidate = function_result.get("plan_execution_summary")
        if isinstance(candidate, dict):
            executed_summary = dict(candidate)

    if executed_summary is None:
        return dict(planned_summary) if planned_summary is not None else None

    if planned_summary:
        for field_name in (
            "deterministic_routing",
            "domains_involved",
            "is_compound",
            "metadata",
            "steps",
            "total_steps",
        ):
            if field_name in planned_summary and field_name not in executed_summary:
                executed_summary[field_name] = planned_summary[field_name]

    if "total_steps" not in executed_summary and isinstance(executed_summary.get("steps"), list):
        executed_summary["total_steps"] = len(executed_summary["steps"])

    return executed_summary


def get_primary_domain(plan_execution_summary: dict[str, Any] | None) -> str:
    """Extract the primary domain from a plan summary for diagnostics and metrics."""
    if isinstance(plan_execution_summary, dict):
        domains_involved = plan_execution_summary.get("domains_involved")
        if isinstance(domains_involved, list):
            for domain_name in domains_involved:
                if isinstance(domain_name, str) and domain_name.strip():
                    return domain_name.strip()
    return "unknown"
