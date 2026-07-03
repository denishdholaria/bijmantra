"""
Retrieval audit helpers and safe-failure payload construction.

Extracted from message_service.py — pure functions, no HTTP, no DB.
"""

from __future__ import annotations

from typing import Any


def build_safe_failure_payload(
    error_category: str,
    searched: list[str] | None = None,
    missing: list[str] | None = None,
    next_steps: list[str] | None = None,
    missing_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a standardized safe-failure payload for user-facing AI failures."""
    payload: dict[str, Any] = {
        "error_category": error_category,
        "searched": searched or [],
        "missing": missing or [],
        "next_steps": next_steps or [],
    }
    if missing_context:
        payload["missing_context"] = missing_context
    return payload


def extract_retrieval_audit(function_result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Extract retrieval audit dict from a function result if present."""
    if isinstance(function_result, dict):
        retrieval_audit = function_result.get("retrieval_audit")
        if isinstance(retrieval_audit, dict):
            return retrieval_audit
    return None


def extract_summary_safe_failure(
    function_result: dict[str, Any] | None,
    validation: Any | None,
) -> dict[str, Any] | None:
    """Extract or synthesize a summary-level safe-failure payload."""
    if isinstance(function_result, dict):
        safe_failure = function_result.get("safe_failure")
        if isinstance(safe_failure, dict):
            return safe_failure

    if validation is not None and getattr(validation, "valid", True) is False:
        return build_safe_failure_payload(
            error_category="insufficient_evidence",
            searched=["stream_response", "retrieved_context", "response_validation"],
            missing=["grounded evidence for one or more claims"],
            next_steps=[
                "Narrow the query by crop, trial, location, or season.",
                "Request cited record IDs and verify before decisions.",
            ],
        )

    return None


def build_response_retrieval_audit(
    *,
    request_message: str,
    function_result: dict[str, Any] | None = None,
    context_retrieval_attempted: bool = False,
    context_doc_ids: list[str] | None = None,
) -> dict[str, Any] | None:
    """Build the additive retrieval audit exposed on the canonical chat contract."""
    function_retrieval_audit = extract_retrieval_audit(function_result)
    if function_retrieval_audit is not None:
        return function_retrieval_audit

    entities: dict[str, Any] = {"query": request_message}
    services: list[str] = []
    if context_retrieval_attempted:
        services.append("breeding_service.search_breeding_knowledge")
        entities["context_doc_ids"] = list(context_doc_ids or [])
        entities["context_doc_count"] = len(context_doc_ids or [])

    return {
        "services": services,
        "entities": entities,
    }
