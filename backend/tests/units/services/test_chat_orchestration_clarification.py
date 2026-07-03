import json
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


@pytest.mark.asyncio
async def test_streaming_function_execution_rolls_back_after_context_lookup_failure(monkeypatch):
    class FakeDB:
        failed = False
        rollback_count = 0

        async def rollback(self):
            self.failed = False
            self.rollback_count += 1

    class FailingBreedingService:
        def __init__(self, db):
            self.db = db

        async def search_breeding_knowledge(self, *args, **kwargs):
            self.db.failed = True
            raise RuntimeError("vector context lookup failed")

    class FakeFunctionExecutor:
        def __init__(self, db):
            self.db = db

        async def execute(self, function_name, parameters):
            if self.db.failed:
                return {
                    "success": False,
                    "message": "Failed to search trials database",
                    "error": "current transaction is aborted",
                }
            return {
                "success": True,
                "function": function_name,
                "result_type": "trial_list",
                "data": {
                    "total": 20,
                    "items": [],
                    "message": "Found 20 trials",
                },
            }

    async def setup_session(self):
        llm_service = SimpleNamespace(
            get_status=AsyncMock(
                return_value={
                    "active_provider": "template",
                    "active_model": "template-v1",
                    "providers": {"template": {"available": True}},
                }
            ),
        )
        return llm_service, SimpleNamespace(), CapabilityRegistry()

    async def noop(self, *args, **kwargs):
        return None

    async def fake_plan_summary(*args, **kwargs):
        return {
            "plan_id": "plan-test",
            "is_compound": False,
            "domains_involved": ["trials"],
            "steps": [],
        }

    db = FakeDB()

    monkeypatch.setattr(OrchestrationService, "_setup_session", setup_session)
    monkeypatch.setattr(OrchestrationService, "_enforce_quota", noop)
    monkeypatch.setattr(OrchestrationService, "_init_user_context", noop)
    monkeypatch.setattr(
        OrchestrationService,
        "_build_function_executor",
        lambda self, capability_registry: FakeFunctionExecutor(self.db),
    )
    monkeypatch.setattr(
        "app.services.chat.orchestration_service.SessionService.get_breeding_service",
        AsyncMock(return_value=FailingBreedingService(db)),
    )
    monkeypatch.setattr(
        "app.services.chat.orchestration_service.FunctionCallingService.detect_function_call",
        AsyncMock(return_value=SimpleNamespace(name="search_trials", parameters={})),
    )
    monkeypatch.setattr(
        "app.services.chat.orchestration_service.MessageService.build_plan_summary_async",
        AsyncMock(side_effect=fake_plan_summary),
    )

    service = OrchestrationService(
        db=db,
        current_user=SimpleNamespace(id=1, organization_id=1),
        reevu_service=SimpleNamespace(save_episodic_memory=AsyncMock(return_value=None)),
    )
    request = SimpleNamespace(
        message="Show me active trials",
        conversation_history=None,
        task_context=None,
        user_api_key=None,
        conversation_id="conversation-1",
        include_context=True,
        context_limit=5,
        preferred_provider=None,
        user_model=None,
    )

    stream = await service.handle_stream(request)
    payloads = []
    async for event in stream:
        for line in event.splitlines():
            if line.startswith("data: "):
                payloads.append(json.loads(line[6:]))

    chunks = [payload["content"] for payload in payloads if payload.get("type") == "chunk"]
    assert chunks == ["Found 20 trials"]
    assert db.rollback_count == 1
