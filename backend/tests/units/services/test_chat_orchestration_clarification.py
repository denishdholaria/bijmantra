from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.services.function_calling_service import (
    ClarificationOption,
    ClarificationResponse,
)
from app.services.chat.orchestration_service import OrchestrationService


@pytest.mark.asyncio
async def test_sync_chat_returns_structured_clarification_response(monkeypatch):
    async def setup_session(self):
        return SimpleNamespace(), SimpleNamespace(), CapabilityRegistry()

    async def noop(self, *args, **kwargs):
        return None

    clarification = ClarificationResponse(
        message=(
            "I can interpret this as: 1. trait summary statistics; "
            "2. germplasm performance comparison. Which would you prefer?"
        ),
        options=[
            ClarificationOption(
                function_name="get_trait_summary",
                description="trait summary statistics",
                confidence=0.75,
            ),
            ClarificationOption(
                function_name="compare_germplasm",
                description="germplasm performance comparison",
                confidence=0.6,
            ),
        ],
    )

    monkeypatch.setattr(OrchestrationService, "_setup_session", setup_session)
    monkeypatch.setattr(OrchestrationService, "_enforce_quota", noop)
    monkeypatch.setattr(OrchestrationService, "_init_user_context", noop)
    monkeypatch.setattr(
        "app.services.chat.orchestration_service.FunctionCallingService.detect_function_call",
        AsyncMock(return_value=clarification),
    )

    service = OrchestrationService(
        db=SimpleNamespace(),
        current_user=SimpleNamespace(id=1, organization_id=1),
        reevu_service=SimpleNamespace(),
    )
    request = SimpleNamespace(
        message="Compare trait summary for IR64 and Swarna",
        conversation_history=None,
        task_context=None,
        user_api_key=None,
        conversation_id="conversation-1",
        include_context=False,
        context_limit=5,
        preferred_provider=None,
        user_model=None,
    )

    response = await service.handle_chat(request)

    assert response.provider == "deterministic_function"
    assert response.model == "function:clarification"
    assert response.message == clarification.message
    assert response.function_call is None
    assert response.suggestions == [
        "trait summary statistics",
        "germplasm performance comparison",
    ]
    assert response.function_result == {
        "result_type": "clarification_required",
        "clarification": clarification.to_dict(),
    }
    assert response.plan_execution_summary == {
        "clarification_required": True,
        "domains_involved": [],
        "is_compound": False,
    }
    assert response.policy_validation["valid"] is True
