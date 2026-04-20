"""
Message service for REEVU chat.

Handles message processing, suggestion generation, and function call orchestration.
Extracted from backend/app/api/v2/chat.py.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message processing and suggestion generation."""

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

        # Default suggestions
        return ["Tell me more", "Search germplasm", "Show active trials"]

    @staticmethod
    def extract_function_response_message(function_result: dict[str, Any] | None) -> str | None:
        """
        Extract deterministic response message from function execution result.

        Prefers executor-provided copy over LLM rewrite when available.
        """
        if not isinstance(function_result, dict):
            return None

        # Try multiple message locations in priority order
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

        # Handle safe_failure scenarios
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
                    (
                        str(step).strip().rstrip(".")
                        for step in next_steps
                        if str(step).strip()
                    ),
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

        # Handle generic failure
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
        import json

        result_summary = json.dumps(function_result, indent=2)
        prompt = f"""The user asked: \"{request_message}\"

I executed the function: {function_name}
With parameters: {json.dumps(function_parameters)}

Result:
{result_summary}

Please provide a natural, friendly response to the user explaining what was found.
CRITICAL: Base your answer STRICTLY on the 'Result' data provided above. Do not hallucinate additional varieties or traits not present in the data.
If the result is empty, clearly state that no matching records were found in the database.
When citing concrete evidence IDs from records, annotate using [[ref:<id>]].
When presenting computed values derived from execution, annotate using [[calc:fn:{function_name}]]."""
        return prompt
