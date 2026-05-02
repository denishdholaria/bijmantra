"""
Message service for REEVU chat — thin orchestrator and backward-compat facade.

The 808-line monolith has been split into focused modules:

  message_evidence.py  — evidence pack assembly, claim extraction, REEVU envelope
  message_plan.py      — plan summary building and execution summary extraction
  message_retrieval.py — retrieval audit helpers and safe-failure payloads

This file re-exports everything so existing callers (orchestration_service.py,
streaming_service.py, tests) continue to work without changes.

New code should import directly from the focused modules.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.modules.ai.services.memory import SearchResult
from app.modules.ai.services.reevu import (
    ClaimItem,
    EvidencePack,
    RecommendationFormatter,
    ValidationResult,
)
from app.schemas.reevu_envelope import ClaimTrace

# ── Focused module imports (canonical locations) ──────────────────────────────
from app.services.chat.message_evidence import (
    build_evidence_pack,
    build_reevu_envelope,
    extract_claim_traces,
    extract_claims_for_validation,
    validate_response_content,
    # Regex patterns re-exported for any callers that patch them in tests
    _CLAIM_SENTENCE_SPLIT_RE,
    _REF_TAG_CAPTURE_RE,
    _CALC_TAG_CAPTURE_RE,
    _INLINE_TRACE_TAG_RE,
    _PERCENTAGE_PHRASE_RE,
)
from app.services.chat.message_plan import (
    build_plan_summary,
    extract_plan_execution_summary,
    get_primary_domain,
)
from app.services.chat.message_retrieval import (
    build_response_retrieval_audit,
    build_safe_failure_payload,
    extract_retrieval_audit,
    extract_summary_safe_failure,
)

logger = logging.getLogger(__name__)


class MessageService:
    """
    Backward-compatible static-method facade over the focused message modules.

    All methods delegate to the module-level functions above.
    New code should call those functions directly.
    """

    # ── Suggestion generation ─────────────────────────────────────────────────

    @staticmethod
    def generate_suggestions(user_message: str, assistant_response: str) -> list[str]:
        """Generate follow-up suggestions based on conversation context."""
        message_lower = user_message.lower()

        if "germplasm" in message_lower or "variety" in message_lower:
            return [
                "Show me similar varieties",
                "What are the key traits?",
                "Find disease-resistant options",
            ]
        if "trial" in message_lower:
            return [
                "Show trial results",
                "Compare with other trials",
                "What's the best performer?",
            ]
        if "cross" in message_lower or "breeding" in message_lower:
            return [
                "Suggest optimal parents",
                "Calculate genetic distance",
                "Show pedigree information",
            ]
        if "disease" in message_lower or "resistance" in message_lower:
            return [
                "List resistance genes",
                "Show screening protocols",
                "Find resistant varieties",
            ]
        return ["Tell me more", "Search germplasm", "Show active trials"]

    # ── Function call helpers ─────────────────────────────────────────────────

    @staticmethod
    def extract_function_response_message(function_result: dict[str, Any] | None) -> str | None:
        """Extract deterministic response message from function execution result."""
        if not isinstance(function_result, dict):
            return None

        for candidate in (
            function_result.get("message"),
            (function_result.get("data") or {}).get("message")
            if isinstance(function_result.get("data"), dict)
            else None,
            (function_result.get("comparison_context") or {}).get("message")
            if isinstance(function_result.get("comparison_context"), dict)
            else None,
        ):
            if isinstance(candidate, str):
                normalized = candidate.strip()
                if normalized:
                    return normalized

        safe_failure = function_result.get("safe_failure")
        if isinstance(safe_failure, dict):
            message_parts: list[str] = []

            error = function_result.get("error")
            if isinstance(error, str):
                normalized_error = error.strip().rstrip(".")
                if normalized_error:
                    message_parts.append(f"{normalized_error}.")

            missing = safe_failure.get("missing")
            if isinstance(missing, list):
                missing_preview = [str(item).strip() for item in missing if str(item).strip()]
                if missing_preview:
                    message_parts.append(
                        f"Missing grounded input: {', '.join(missing_preview[:2])}."
                    )

            next_steps = safe_failure.get("next_steps")
            if isinstance(next_steps, list):
                first_step = next(
                    (str(step).strip().rstrip(".") for step in next_steps if str(step).strip()),
                    None,
                )
                if first_step:
                    message_parts.append(f"Next step: {first_step}.")

            if message_parts:
                return " ".join(message_parts)

            error_category = safe_failure.get("error_category")
            if isinstance(error_category, str):
                normalized_category = error_category.strip().replace("_", " ")
                if normalized_category:
                    return (
                        "I could not complete this request because REEVU hit "
                        f"{normalized_category}."
                    )

            return "I could not complete this request with grounded evidence."

        if function_result.get("success") is False:
            error = function_result.get("error")
            if isinstance(error, str):
                normalized_error = error.strip()
                if normalized_error:
                    return normalized_error

        return None

    @staticmethod
    def build_function_explanation_prompt(
        *,
        request_message: str,
        function_name: str,
        function_parameters: dict[str, Any],
        function_result: dict[str, Any],
    ) -> str:
        """Build LLM prompt for explaining function execution results."""
        result_summary = json.dumps(function_result, indent=2)
        return (
            f'The user asked: "{request_message}"\n\n'
            f"I executed the function: {function_name}\n"
            f"With parameters: {json.dumps(function_parameters)}\n\n"
            f"Result:\n{result_summary}\n\n"
            "Please provide a natural, friendly response to the user explaining what was found.\n"
            "CRITICAL: Base your answer STRICTLY on the 'Result' data provided above. "
            "Do not hallucinate additional varieties or traits not present in the data.\n"
            "If the result is empty, clearly state that no matching records were found in the database.\n"
            "When citing concrete evidence IDs from records, annotate using [[ref:<id>]].\n"
            f"When presenting computed values derived from execution, annotate using [[calc:fn:{function_name}]]."
        )

    # ── Delegating wrappers ───────────────────────────────────────────────────

    @staticmethod
    def build_evidence_pack(
        context_docs: list[SearchResult] | None,
        function_call_name: str | None = None,
        function_result: dict[str, Any] | None = None,
    ) -> EvidencePack:
        return build_evidence_pack(context_docs, function_call_name, function_result)

    @staticmethod
    def extract_claims_for_validation(
        content: str, evidence_pack: EvidencePack
    ) -> list[ClaimItem]:
        return extract_claims_for_validation(content, evidence_pack)

    @staticmethod
    def extract_claim_traces(
        content: str, evidence_pack: EvidencePack
    ) -> list[ClaimTrace]:
        return extract_claim_traces(content, evidence_pack)

    @staticmethod
    def validate_response_content(
        content: str,
        context_docs: list[SearchResult] | None,
        function_call_name: str | None = None,
        function_result: dict[str, Any] | None = None,
    ) -> tuple[ValidationResult, EvidencePack]:
        return validate_response_content(content, context_docs, function_call_name, function_result)

    @staticmethod
    def build_safe_failure_payload(
        error_category: str,
        searched: list[str] | None = None,
        missing: list[str] | None = None,
        next_steps: list[str] | None = None,
        missing_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return build_safe_failure_payload(error_category, searched, missing, next_steps, missing_context)

    @staticmethod
    def extract_retrieval_audit(
        function_result: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        return extract_retrieval_audit(function_result)

    @staticmethod
    def extract_summary_safe_failure(
        function_result: dict[str, Any] | None,
        validation: Any | None,
    ) -> dict[str, Any] | None:
        return extract_summary_safe_failure(function_result, validation)

    @staticmethod
    def build_response_retrieval_audit(
        *,
        request_message: str,
        function_result: dict[str, Any] | None = None,
        context_retrieval_attempted: bool = False,
        context_doc_ids: list[str] | None = None,
    ) -> dict[str, Any] | None:
        return build_response_retrieval_audit(
            request_message=request_message,
            function_result=function_result,
            context_retrieval_attempted=context_retrieval_attempted,
            context_doc_ids=context_doc_ids,
        )

    @staticmethod
    def build_plan_summary(
        request_message: str,
        *,
        function_call_name: str | None = None,
    ) -> dict[str, Any]:
        return build_plan_summary(request_message, function_call_name=function_call_name)

    @staticmethod
    def extract_plan_execution_summary(
        function_result: dict[str, Any] | None,
        planned_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return extract_plan_execution_summary(function_result, planned_summary)

    @staticmethod
    def get_primary_domain(plan_execution_summary: dict[str, Any] | None) -> str:
        return get_primary_domain(plan_execution_summary)

    @staticmethod
    def build_reevu_envelope(
        content: str,
        evidence_pack: EvidencePack,
        validation: ValidationResult,
        context_docs: list[SearchResult] | None = None,
        function_call_name: str | None = None,
    ) -> dict[str, Any]:
        return build_reevu_envelope(content, evidence_pack, validation, context_docs, function_call_name)

    @staticmethod
    def maybe_format_comparison(
        function_result: dict[str, Any] | None,
        function_call_name: str | None = None,
        domains_involved: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """If the function result contains rankable candidates, format a structured comparison."""
        if not function_result:
            return None

        data = function_result.get("data")
        candidate_data: list[dict[str, Any]] | None = None
        top_level_calculation_method_refs = function_result.get("calculation_method_refs", [])

        if isinstance(data, list) and len(data) > 0:
            candidate_data = data
        elif function_call_name == "cross_domain_query" and isinstance(data, dict):
            recommendations = data.get("recommendations")
            if isinstance(recommendations, list) and recommendations:
                candidate_data = recommendations
        elif function_call_name == "get_trial_results" and isinstance(data, dict):
            interpretation = data.get("interpretation")
            if isinstance(interpretation, dict):
                ranking = interpretation.get("ranking", [])
                if isinstance(ranking, list) and ranking:
                    candidate_data = [
                        {
                            "candidate": (
                                item.get("entity_name")
                                or item.get("germplasmName")
                                or f"ranked-item-{idx}"
                            ),
                            "score": item.get("score"),
                            "rationale": item.get("rationale", ""),
                            "evidence_refs": item.get("evidence_refs", []),
                            "calculation_method_refs": top_level_calculation_method_refs,
                            "uncertainty": (
                                f"Change vs baseline: {item.get('delta_percent_vs_baseline'):.2f}%"
                                if isinstance(item.get("delta_percent_vs_baseline"), (int, float))
                                else ""
                            ),
                        }
                        for idx, item in enumerate(ranking, start=1)
                        if isinstance(item, dict)
                    ]

            if not candidate_data:
                top_performers = data.get("top_performers", [])
                if isinstance(top_performers, list) and top_performers:
                    candidate_data = [
                        {
                            "candidate": item.get("germplasmName") or f"top-performer-{idx}",
                            "score": item.get("yield_value"),
                            "calculation_method_refs": top_level_calculation_method_refs,
                            "rationale": (
                                f"Change vs baseline: {item.get('change_percent')}"
                                if item.get("change_percent")
                                else ""
                            ),
                        }
                        for idx, item in enumerate(top_performers, start=1)
                        if isinstance(item, dict)
                    ]

        if not candidate_data:
            return None

        _RANK_KEYS = {"score", "name", "candidate"}
        if not all(isinstance(item, dict) for item in candidate_data):
            return None
        if not any(_RANK_KEYS & set(item.keys()) for item in candidate_data):
            return None

        formatter = RecommendationFormatter()
        methodology = f"function:{function_call_name}" if function_call_name else ""
        result = formatter.format_comparison(
            candidate_data,
            methodology=methodology,
            domains_used=domains_involved,
            calculation_method_refs=top_level_calculation_method_refs,
        )
        return result.model_dump()
