"""
Tests for Veena AI Chat Streaming Endpoint

Tests the /api/v2/chat/stream SSE endpoint.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from tests.utils.safe_failure_assertions import assert_actionable_safe_failure_payload


def _extract_sse_payloads(response_text: str) -> list[dict]:
    payloads: list[dict] = []
    for line in response_text.splitlines():
        if not line.startswith("data: "):
            continue
        try:
            payloads.append(json.loads(line[6:]))
        except json.JSONDecodeError:
            continue
    return payloads


def _extract_sse_events(response_text: str, event_type: str, stage: str | None = None) -> list[dict]:
    events = [payload for payload in _extract_sse_payloads(response_text) if payload.get("type") == event_type]
    if stage is not None:
        return [payload for payload in events if payload.get("stage") == stage]
    return events


def _assert_data_execution_stage_events(stage_payloads: list[dict], function_name: str) -> None:
    data_exec_events = [p for p in stage_payloads if p.get("stage") == "data_execution"]
    assert data_exec_events
    assert any(evt.get("status") == "started" for evt in data_exec_events)
    assert any(evt.get("status") == "completed" for evt in data_exec_events)
    assert any(evt.get("function_name") == function_name for evt in data_exec_events)


def _completed_stage_events(events: list[dict]) -> list[dict]:
    return [evt for evt in events if evt.get("status") == "completed"]


STREAM_EVENT_REQUIRED_FIELDS: dict[str, set[str]] = {
    "start": {"type", "request_id", "provider", "model"},
    "chunk": {"type", "request_id", "content"},
    "done": {"type", "request_id"},
    "error": {"type", "request_id", "message", "safe_failure"},
    "summary": {"type", "request_id", "evidence_envelope"},
}
SUMMARY_ENVELOPE_REQUIRED_FIELDS = {"evidence_refs", "calculations", "uncertainty", "policy_flags"}
POLICY_STAGE_REQUIRED_FIELDS = {
    "type",
    "request_id",
    "stage",
    "status",
    "ts",
    "latency_ms",
    "valid",
    "error_count",
    "evidence_count",
    "calculation_count",
}


class _MockFunctionGemmaResponse:
    def __init__(self, generated_text: str):
        self.status_code = 200
        self._generated_text = generated_text

    def json(self):
        return [{"generated_text": self._generated_text}]


class _MockFunctionGemmaClient:
    def __init__(self, generated_text: str):
        self._generated_text = generated_text

    async def post(self, *args, **kwargs):
        return _MockFunctionGemmaResponse(self._generated_text)


def _assert_required_fields(payload: dict, required: set[str], *, label: str) -> None:
    missing = required - set(payload)
    assert not missing, f"Missing required {label} fields: {sorted(missing)}"


def _assert_stream_event_contract(payload: dict, event_type: str) -> None:
    _assert_required_fields(payload, STREAM_EVENT_REQUIRED_FIELDS[event_type], label=f"{event_type} event")


def _assert_summary_execution_trace_contract(
    payload: dict,
    *,
    safe_failure_expected: bool = False,
) -> None:
    """Function-backed summary events should preserve execution-trace structure."""

    retrieval_audit = payload.get("retrieval_audit")
    plan_execution_summary = payload.get("plan_execution_summary")

    assert isinstance(retrieval_audit, dict)
    assert isinstance(retrieval_audit.get("services"), list)
    assert isinstance(retrieval_audit.get("entities"), dict)
    assert isinstance(plan_execution_summary, dict)
    assert isinstance(plan_execution_summary.get("plan_id"), str)
    assert isinstance(plan_execution_summary.get("domains_involved"), list)
    assert isinstance(plan_execution_summary.get("steps"), list)
    assert isinstance(plan_execution_summary.get("total_steps"), int)

    if safe_failure_expected:
        assert isinstance(payload.get("safe_failure"), dict)


def _assert_policy_stage_contract(payload: dict, *, safe_failure_expected: bool) -> None:
    _assert_required_fields(payload, POLICY_STAGE_REQUIRED_FIELDS, label="policy_validation stage")

    assert isinstance(payload["request_id"], str)
    assert isinstance(payload["ts"], str)
    assert isinstance(payload["latency_ms"], int | float)
    assert isinstance(payload["valid"], bool)
    assert isinstance(payload["error_count"], int)
    assert isinstance(payload["evidence_count"], int)
    assert isinstance(payload["calculation_count"], int)

    if safe_failure_expected:
        assert "safe_failure" in payload
    else:
        assert "safe_failure" not in payload


class TestChatStreamingEndpoint:
    """Test cases for the streaming chat endpoint"""

    @pytest.fixture(autouse=True)
    def _apply_service_mocks(self, mock_llm_service, mock_breeding_service):
        """Ensure network and vector dependencies are mocked for all streaming tests."""
        return None

    @pytest.fixture(autouse=True)
    def _disable_quota_limits(self):
        """Prevent env-dependent quota state from causing 429 test flakiness."""
        with patch("app.api.v2.chat.AIQuotaService.check_and_increment_usage", return_value=None):
            yield

    @pytest.fixture
    def client(self, mock_breeding_service):
        """Create test client"""
        from app.api.deps import get_current_user, get_db
        from app.api.v2.chat import get_breeding_service, get_reevu_service, router

        app = FastAPI()
        app.include_router(router, prefix="/api/v2")

        reevu_service = SimpleNamespace()
        db_session = SimpleNamespace()

        async def mock_get_or_create_user_context(*args, **kwargs):
            return {"context": "ok"}

        async def mock_update_interaction_stats(*args, **kwargs):
            return None

        async def mock_save_episodic_memory(*args, **kwargs):
            return None

        reevu_service.get_or_create_user_context = mock_get_or_create_user_context
        reevu_service.update_interaction_stats = mock_update_interaction_stats
        reevu_service.save_episodic_memory = mock_save_episodic_memory
        db_session.rollback = mock_update_interaction_stats

        async def override_current_user():
            # Chat endpoint casts id/org to int during request handling.
            return SimpleNamespace(id=1, organization_id=1, email="test@bijmantra.org", is_demo=False)

        async def override_get_db():
            yield db_session

        async def override_reevu_service():
            return reevu_service

        async def override_breeding_service():
            return mock_breeding_service

        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_reevu_service] = override_reevu_service
        app.dependency_overrides[get_breeding_service] = override_breeding_service

        with TestClient(app) as client:
            yield client

        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_llm_service(self):
        """Mock the LLM service"""
        with patch("app.api.v2.chat.get_llm_service") as mock:
            service = MagicMock()

            # Mock get_status
            async def mock_status():
                return {
                    "active_provider": "template",
                    "active_model": "template-v1",
                    "providers": {"template": {"available": True}},
                }

            service.get_status = mock_status

            # Mock stream_chat as async generator
            async def mock_stream_chat(*args, **kwargs):
                yield "Hello"
                yield " from"
                yield " Veena!"

            service.stream_chat = mock_stream_chat
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_breeding_service(self):
        """Mock the breeding service"""
        with patch("app.api.v2.chat.get_breeding_service") as mock:
            service = MagicMock()

            async def mock_search(*args, **kwargs):
                return []

            service.search_breeding_knowledge = mock_search
            mock.return_value = service
            yield service

    def test_streaming_endpoint_returns_200(self, client):
        """Test that streaming endpoint returns 200 OK"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        assert response.status_code == 200

    def test_streaming_endpoint_returns_sse_content_type(self, client):
        """Test that streaming endpoint returns correct SSE content type"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_streaming_endpoint_has_no_cache_header(self, client):
        """Test that streaming endpoint has proper cache control"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        cache_control = response.headers.get("cache-control", "")
        assert "no-cache" in cache_control or "no-store" in cache_control

    def test_streaming_endpoint_disables_buffering(self, client):
        """Test that streaming endpoint disables nginx buffering"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        assert response.headers.get("x-accel-buffering") == "no"

    def test_streaming_format_has_start_event(self, client):
        """Test that SSE stream starts with a 'start' event"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        # Stage telemetry may precede start; assert start exists in stream.
        assert '"type": "start"' in response.text or '"type":"start"' in response.text

    def test_streaming_format_has_chunk_events(self, client):
        """Test that content is sent as 'chunk' events"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        # Should have chunk events
        assert '"type": "chunk"' in response.text or '"type":"chunk"' in response.text

    def test_streaming_format_has_done_event(self, client):
        """Test that SSE stream ends with a 'done' event"""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        # Last data event should be done
        assert '"type": "done"' in response.text or '"type":"done"' in response.text


    def test_streaming_start_event_includes_request_id(self, client):
        """Start event should carry a request_id for stage telemetry correlation."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        start_events = _extract_sse_events(response.text, event_type="start")
        assert start_events
        payload = start_events[-1]
        assert payload.get("request_id")

    def test_streaming_done_event_includes_request_id(self, client):
        """Done event should include request_id for client-side trace closure."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        done_events = _extract_sse_events(response.text, event_type="done")
        assert done_events
        payload = done_events[-1]
        assert payload.get("request_id")

    def test_streaming_function_path_start_and_done_request_ids_match(self, client):
        """Function-path streams should keep start/done request_id correlation intact."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert start_events
        assert done_events
        start_request_id = start_events[-1].get("request_id")
        done_request_id = done_events[-1].get("request_id")
        assert start_request_id
        assert done_request_id
        assert start_request_id == done_request_id

    def test_streaming_function_path_emits_chunk_before_done(self, client):
        """Function-path streams should emit at least one chunk before done closure."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        payloads = _extract_sse_payloads(response.text)
        chunk_indices = [idx for idx, payload in enumerate(payloads) if payload.get("type") == "chunk"]
        done_indices = [idx for idx, payload in enumerate(payloads) if payload.get("type") == "done"]

        assert chunk_indices
        assert done_indices
        assert chunk_indices[0] < done_indices[-1]

    def test_streaming_function_path_orders_start_chunk_done(self, client):
        """Function-path streams should sequence start -> chunk -> done deterministically."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        payloads = _extract_sse_payloads(response.text)
        start_indices = [idx for idx, payload in enumerate(payloads) if payload.get("type") == "start"]
        chunk_indices = [idx for idx, payload in enumerate(payloads) if payload.get("type") == "chunk"]
        done_indices = [idx for idx, payload in enumerate(payloads) if payload.get("type") == "done"]

        assert start_indices
        assert chunk_indices
        assert done_indices
        assert start_indices[0] < chunk_indices[0]
        assert chunk_indices[0] < done_indices[-1]

    def test_streaming_function_path_start_event_includes_provider_and_model(self, client):
        """Function-path start event should include provider and model metadata."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        assert start_events
        start_payload = start_events[-1]

        assert isinstance(start_payload.get("provider"), str)
        assert start_payload.get("provider")
        assert isinstance(start_payload.get("model"), str)
        assert start_payload.get("model")

    def test_streaming_function_path_request_id_is_consistent_across_events(self, client):
        """Function-path stream should keep one request_id across start, stage, and done events."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        stage_events = _extract_sse_events(response.text, event_type="stage")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert start_events
        assert stage_events
        assert done_events

        request_id = start_events[-1].get("request_id")
        assert request_id
        assert done_events[-1].get("request_id") == request_id
        assert all(evt.get("request_id") == request_id for evt in stage_events)

    def test_streaming_function_path_emits_single_start_and_done_event(self, client):
        """Function-path stream should emit exactly one start and one done lifecycle event."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert len(start_events) == 1
        assert len(done_events) == 1

    def test_streaming_function_path_chunk_request_ids_match_start_and_done(self, client):
        """Function-path chunk events should carry the same request_id as lifecycle events."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert start_events
        assert chunk_events
        assert done_events

        request_id = start_events[-1].get("request_id")
        assert request_id
        assert done_events[-1].get("request_id") == request_id
        assert all(evt.get("request_id") == request_id for evt in chunk_events)

    def test_streaming_emits_stage_telemetry_events(self, client):
        """SSE stream should emit explicit REEVU stage telemetry events."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        stage_payloads = _extract_sse_events(response.text, event_type="stage")
        assert stage_payloads
        assert {payload["stage"] for payload in stage_payloads} >= {
            "intent_scope",
            "plan_generation",
            "answer_synthesis",
            "policy_validation",
            "response_emission",
        }

    def test_streaming_stage_events_include_trace_contract_fields(self, client):
        """Stage events should always include trace contract fields for observability."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        stage_payloads = _extract_sse_events(response.text, event_type="stage")

        assert stage_payloads
        for payload in stage_payloads:
            assert payload.get("request_id")
            assert payload.get("stage")
            assert payload.get("status")
            assert payload.get("ts")

            if payload.get("status") == "completed":
                assert "latency_ms" in payload
                assert payload["latency_ms"] >= 0

    def test_policy_validation_stage_reports_metrics(self, client):
        """Policy validation stage should expose deterministic validation telemetry."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        validation_events = _extract_sse_events(
            response.text,
            event_type="stage",
            stage="policy_validation",
        )

        assert validation_events
        completed = _completed_stage_events(validation_events)
        assert completed
        payload = completed[-1]
        assert "valid" in payload
        assert "error_count" in payload
        assert "evidence_count" in payload
        assert "calculation_count" in payload
        assert "safe_failure" not in payload

    def test_streaming_normal_path_contract_lock_allows_additive_fields(self, client):
        """Lock required SSE event fields for normal path while permitting additive keys."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )

        start_events = _extract_sse_events(response.text, event_type="start")
        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        done_events = _extract_sse_events(response.text, event_type="done")
        summary_events = _extract_sse_events(response.text, event_type="summary")
        validation_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert start_events and chunk_events and done_events and summary_events and validation_events

        _assert_stream_event_contract(start_events[-1], "start")
        _assert_stream_event_contract(chunk_events[0], "chunk")
        _assert_stream_event_contract(done_events[-1], "done")
        _assert_stream_event_contract(summary_events[-1], "summary")

        _assert_required_fields(
            summary_events[-1]["evidence_envelope"],
            SUMMARY_ENVELOPE_REQUIRED_FIELDS,
            label="summary evidence_envelope",
        )
        _assert_policy_stage_contract(_completed_stage_events(validation_events)[-1], safe_failure_expected=False)

    def test_streaming_summary_event_contract_lock_keeps_types_stable(self, client):
        """Summary event key field types should remain stable for downstream parsing."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        summary_events = _extract_sse_events(response.text, event_type="summary")

        assert summary_events
        payload = summary_events[-1]
        envelope = payload["evidence_envelope"]

        assert isinstance(payload["request_id"], str)
        assert isinstance(envelope, dict)
        assert isinstance(envelope["evidence_refs"], list)
        assert isinstance(envelope["calculations"], list)
        assert isinstance(envelope["uncertainty"], dict)
        assert isinstance(envelope["policy_flags"], list)

    def test_streaming_without_context_does_not_emit_unbound_context_error(self, client):
        """Disabled context retrieval should not leave the stream generator with an unbound context_docs closure."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )

        assert response.status_code == 200
        assert "cannot access free variable 'context_docs'" not in response.text

        error_events = _extract_sse_events(response.text, event_type="error")
        assert not any(
            payload.get("message") == "cannot access free variable 'context_docs' where it is not associated with a value in enclosing scope"
            for payload in error_events
        )

    def test_streaming_with_conversation_history(self, client):
        """Test streaming with conversation history"""
        response = client.post(
            "/api/v2/chat/stream",
            json={
                "message": "What about disease resistance?",
                "include_context": False,
                "conversation_history": [
                    {"role": "user", "content": "Tell me about wheat"},
                    {"role": "assistant", "content": "Wheat is a cereal grain..."},
                ],
            },
        )
        assert response.status_code == 200

    def test_streaming_with_preferred_provider(self, client):
        """Test streaming with preferred provider"""
        response = client.post(
            "/api/v2/chat/stream",
            json={"message": "Hello", "include_context": False, "preferred_provider": "ollama"},
        )
        assert response.status_code == 200

    def test_streaming_error_event_includes_safe_failure_payload(self, client, mock_llm_service):
        """Stream error event should include standardized safe-failure metadata."""

        async def failing_stream_chat(*args, **kwargs):
            raise RuntimeError("synthetic stream failure")
            if False:
                yield ""

        mock_llm_service.stream_chat = failing_stream_chat

        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )
        error_events = _extract_sse_events(response.text, event_type="error")
        assert error_events
        payload = error_events[-1]

        _assert_stream_event_contract(payload, "error")
        assert isinstance(payload["request_id"], str)
        assert payload.get("message") == "synthetic stream failure"
        assert_actionable_safe_failure_payload(
            payload.get("safe_failure"),
            error_category="streaming_error",
        )

    def test_streaming_function_path_emits_data_execution_stage(self, client):
        """When a function call is detected, stream should emit data_execution stage events."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_germplasm", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_germplasm",
                "result_type": "germplasm_list",
                "data": {"total": 1, "items": [{"id": "G-001"}]},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice germplasm", "include_context": False}
            )

        stage_payloads = _extract_sse_events(response.text, event_type="stage")
        _assert_data_execution_stage_events(stage_payloads, function_name="search_germplasm")

    def test_streaming_stage_sequence_without_function_path_is_ordered(self, client):
        """Core stage progression should remain deterministic when no function call is used."""
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
        )

        stage_payloads = _extract_sse_events(response.text, event_type="stage")

        # Use first stage appearance order to avoid overfitting to status emission details.
        stage_order = []
        for payload in stage_payloads:
            stage_name = payload.get("stage")
            if stage_name and stage_name not in stage_order:
                stage_order.append(stage_name)

        expected = [
            "intent_scope",
            "plan_generation",
            "answer_synthesis",
            "policy_validation",
            "response_emission",
        ]

        indices = {stage: stage_order.index(stage) for stage in expected}
        assert indices["intent_scope"] < indices["plan_generation"]
        assert indices["plan_generation"] < indices["answer_synthesis"]
        assert indices["answer_synthesis"] < indices["policy_validation"]
        assert indices["policy_validation"] < indices["response_emission"]

    def test_streaming_stage_sequence_with_function_path_is_ordered(self, client):
        """Function-call pipeline should sequence plan -> data_execution -> synthesis deterministically."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        stage_payloads = _extract_sse_events(response.text, event_type="stage")

        plan_completed_idx = next(
            idx
            for idx, payload in enumerate(stage_payloads)
            if payload.get("stage") == "plan_generation" and payload.get("status") == "completed"
        )
        data_exec_started_idx = next(
            idx
            for idx, payload in enumerate(stage_payloads)
            if payload.get("stage") == "data_execution" and payload.get("status") == "started"
        )
        data_exec_completed_idx = next(
            idx
            for idx, payload in enumerate(stage_payloads)
            if payload.get("stage") == "data_execution" and payload.get("status") == "completed"
        )
        synthesis_started_idx = next(
            idx
            for idx, payload in enumerate(stage_payloads)
            if payload.get("stage") == "answer_synthesis" and payload.get("status") == "started"
        )

        assert plan_completed_idx < data_exec_started_idx
        assert data_exec_started_idx < data_exec_completed_idx
        assert data_exec_completed_idx < synthesis_started_idx

    @pytest.mark.parametrize(
        ("function_name", "parameters", "message"),
        [
            ("search_trials", {"crop": "wheat"}, "Show wheat trials"),
            ("search_accessions", {"crop": "rice"}, "List rice accessions"),
            ("search_crosses", {"program": "P1"}, "Find crossing records"),
            ("compare_germplasm", {"entry_a": "IR64", "entry_b": "Swarna"}, "Compare IR64 and Swarna"),
            ("navigate_to", {"page": "/trials"}, "Open trials page"),
            (
                "propose_create_cross",
                {"parent1_id": "IR64", "parent2_id": "Swarna"},
                "Create cross between IR64 and Swarna",
            ),
            (
                "propose_record_observation",
                {"trial_id": "T-102", "date": "today"},
                "Record observation for trial T-102",
            ),
            (
                "get_weather_forecast",
                {"location": "Hyderabad", "days": 7},
                "What is the weather forecast for Hyderabad",
            ),
        ],
    )
    def test_streaming_multiple_function_paths_emit_data_execution_stage(
        self,
        client,
        function_name,
        parameters,
        message,
    ):
        """Representative function paths should all emit data_execution telemetry."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": function_name,
                "result_type": "result",
                "data": {"ok": True},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": message, "include_context": False}
            )

        stage_payloads = _extract_sse_events(response.text, event_type="stage")
        _assert_data_execution_stage_events(stage_payloads, function_name=function_name)

    def test_streaming_function_execution_failure_emits_data_execution_failed_stage(self, client):
        """Function execution failures should emit failed data_execution telemetry plus error chunk."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def failing_execute(*args, **kwargs):
            raise RuntimeError("synthetic function failure")

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=failing_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        stage_payloads = _extract_sse_events(response.text, event_type="stage")
        failed_data_exec = [
            p for p in stage_payloads if p.get("stage") == "data_execution" and p.get("status") == "failed"
        ]

        assert failed_data_exec
        assert failed_data_exec[-1].get("error") == "synthetic function failure"
        assert "Error executing action: synthetic function failure" in response.text

    def test_streaming_function_execution_failure_chunk_request_ids_match_lifecycle(self, client):
        """Function execution failure chunk events should keep request_id correlation."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def failing_execute(*args, **kwargs):
            raise RuntimeError("synthetic function failure")

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=failing_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert start_events
        assert chunk_events
        assert done_events

        request_id = start_events[-1].get("request_id")
        assert request_id
        assert done_events[-1].get("request_id") == request_id
        assert all(evt.get("request_id") == request_id for evt in chunk_events)

    def test_streaming_policy_validation_emits_safe_failure_on_invalid_response(self, client):
        """Invalid validation should attach standardized safe-failure metadata to policy stage."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        invalid_validation = SimpleNamespace(valid=False, errors=["unsupported claim"])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(invalid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        policy_events = _extract_sse_events(
            response.text,
            event_type="stage",
            stage="policy_validation",
        )
        summary_events = _extract_sse_events(response.text, event_type="summary")

        assert policy_events
        completed = _completed_stage_events(policy_events)
        assert completed
        payload = completed[-1]
        _assert_policy_stage_contract(payload, safe_failure_expected=True)
        assert payload.get("valid") is False
        assert payload.get("error_count") == 1
        assert_actionable_safe_failure_payload(
            payload.get("safe_failure"),
            error_category="insufficient_evidence",
        )
        assert summary_events
        summary_payload = summary_events[-1]
        _assert_summary_execution_trace_contract(summary_payload, safe_failure_expected=True)
        assert_actionable_safe_failure_payload(
            summary_payload.get("safe_failure"),
            error_category="insufficient_evidence",
        )

    def test_streaming_summary_event_emits_retrieval_audit_and_executed_plan_summary(self, client):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="cross_domain_query", parameters={"location": "Ludhiana"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "cross_domain_query",
                "result_type": "cross_domain_results",
                "data": {"summary": {"trial_count": 1}},
                "retrieval_audit": {
                    "services": ["trial_search_service.search", "weather_service.get_forecast"],
                    "entities": {
                        "location": "Ludhiana",
                        "resolved_weather_location_id": "LOC-1",
                    },
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": True,
                    "domains_involved": ["trials", "weather"],
                    "steps": [
                        {
                            "step_id": "step-1",
                            "domain": "trials",
                            "description": "Search trials",
                            "prerequisites": [],
                            "deterministic": True,
                            "completed": True,
                        }
                    ],
                },
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show trial weather evidence", "include_context": False}
            )

        summary_events = _extract_sse_events(response.text, event_type="summary")

        assert summary_events
        payload = summary_events[-1]
        _assert_summary_execution_trace_contract(payload)
        assert payload["retrieval_audit"] == {
            "services": ["trial_search_service.search", "weather_service.get_forecast"],
            "entities": {
                "location": "Ludhiana",
                "resolved_weather_location_id": "LOC-1",
            },
        }
        assert payload["plan_execution_summary"]["plan_id"] == "plan-1"
        assert payload["plan_execution_summary"]["steps"][0]["completed"] is True
        assert payload["plan_execution_summary"]["total_steps"] == 2

    def test_streaming_summary_event_includes_regular_chat_trace_when_no_function_runs(self, client):
        response = client.post(
            "/api/v2/chat/stream", json={"message": "Summarize verified yield outcomes", "include_context": False}
        )

        assert response.status_code == 200
        summary_events = _extract_sse_events(response.text, event_type="summary")

        assert summary_events
        payload = summary_events[-1]
        _assert_summary_execution_trace_contract(payload)
        assert payload["retrieval_audit"] == {
            "services": [],
            "entities": {"query": "Summarize verified yield outcomes"},
        }
        assert payload["plan_execution_summary"]["total_steps"] == len(
            payload["plan_execution_summary"]["steps"]
        )

    def test_streaming_function_path_prefers_grounded_function_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "message": "Found the requested rice trials in the current dataset.",
                "retrieval_audit": {
                    "services": ["trial_search_service.search"],
                    "entities": {"crop": "rice"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["trials"],
                    "steps": [],
                },
            }

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when a deterministic function message exists")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Show rice trials", "include_context": False}
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Found the requested rice trials in the current dataset."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_germplasm_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="search_germplasm",
                parameters={"crop": "rice", "query": "blast tolerance", "trait": "yield"},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_germplasm",
                "result_type": "germplasm_list",
                "data": {
                    "total": 1,
                    "items": [{"id": "101", "name": "IR64", "accession": "IR64"}],
                    "message": "Found 1 germplasm records matching 'rice blast tolerance'",
                },
                "retrieval_audit": {
                    "services": ["germplasm_search_service.search"],
                    "entities": {"query": "rice blast tolerance", "trait": "yield"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["germplasm"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when germplasm search data includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find rice germplasm with blast tolerance", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Found 1 germplasm records matching 'rice blast tolerance'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_germplasm_failure_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_germplasm", parameters={"query": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "search_germplasm",
                "result_type": "germplasm_search_error",
                "error": "Germplasm search service not available",
                "message": "Failed to search germplasm database",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when germplasm search failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find rice germplasm", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to search germplasm database"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_trials_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="search_trials",
                parameters={"query": "late sowing", "crop": "rice"},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "trial_list",
                "data": {
                    "total": 1,
                    "items": [{"id": "trial-101", "name": "Ludhiana late sowing trial"}],
                    "message": "Found 1 trials matching 'late sowing'",
                },
                "retrieval_audit": {
                    "services": ["trial_search_service.search"],
                    "entities": {"query": "late sowing", "crop": "rice"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["trials"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when trial search data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find late sowing rice trials", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Found 1 trials matching 'late sowing'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_trials_failure_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_trials", parameters={"query": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "search_trials",
                "result_type": "trial_search_error",
                "error": "trial search offline",
                "message": "Failed to search trials database",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when trial search failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find rice trials", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to search trials database"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_crosses_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_crosses", parameters={"query": "IR64", "program": "P1"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_crosses",
                "result_type": "cross_list",
                "data": {
                    "total": 1,
                    "items": [{"id": "cross-101", "name": "IR64 x Swarna"}],
                    "message": "Found 1 crosses matching 'IR64'",
                },
                "retrieval_audit": {
                    "services": ["cross_search_service.search"],
                    "entities": {"query": "IR64", "program": "P1"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["crosses"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when cross search data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find IR64 crosses in program P1", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Found 1 crosses matching 'IR64'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_crosses_failure_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_crosses", parameters={"query": "IR64"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "search_crosses",
                "result_type": "cross_search_error",
                "error": "cross search offline",
                "message": "Failed to search crosses database",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when cross search failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find IR64 crosses", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to search crosses database"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_accessions_data_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_accessions", parameters={"query": "IR64", "country": "India"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_accessions",
                "result_type": "accession_list",
                "data": {
                    "total": 1,
                    "items": [{"id": "acc-101", "name": "IR64"}],
                    "message": "Found 1 accessions matching 'IR64'",
                },
                "retrieval_audit": {
                    "services": ["germplasm_search_service.search"],
                    "entities": {"query": "IR64", "country": "India"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["germplasm"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when accession search data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find IR64 accessions from India", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Found 1 accessions matching 'IR64'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_search_accessions_failure_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="search_accessions", parameters={"query": "IR64"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "search_accessions",
                "result_type": "accession_search_error",
                "error": "accession search offline",
                "message": "Failed to search accessions database",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when accession search failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Find IR64 accessions", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to search accessions database"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        ("function_name", "parameters", "user_message", "error_message"),
        [
            (
                "predict_harvest_timing",
                {"field_id": 17, "planting_date": "2026-07-01", "crop_name": "maize"},
                "When should maize from field 17 planted on 2026-07-01 be harvested?",
                "Failed to predict harvest timing",
            ),
            (
                "recommend_varieties_by_gdd",
                {"field_id": 17},
                "Recommend varieties for field 17 using GDD",
                "Failed to recommend varieties by GDD",
            ),
            (
                "analyze_planting_windows",
                {"field_id": 23, "crop_name": "maize"},
                "Analyze maize planting windows for field 23",
                "Failed to analyze planting windows",
            ),
            (
                "get_gdd_insights",
                {"field_id": 23, "insight_type": "planting"},
                "Give me GDD planting insights for field 23",
                "Failed to get GDD insights",
            ),
        ],
    )
    def test_streaming_function_path_prefers_gdd_helper_failure_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        error_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "error": "gdd service unavailable",
                "message": error_message,
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when GDD helper failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == error_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        (
            "function_name",
            "parameters",
            "user_message",
            "result_type",
            "item",
            "function_message",
            "service_name",
            "domains_involved",
        ),
        [
            (
                "search_locations",
                {"query": "Ludhiana", "country": "India"},
                "Find locations matching Ludhiana",
                "location_list",
                {"id": "loc-101", "name": "Ludhiana"},
                "Found 1 locations matching 'Ludhiana'",
                "location_search_service.search",
                ["locations"],
            ),
            (
                "search_seedlots",
                {"query": "SL-101", "germplasm_id": "101"},
                "Find seedlots matching SL-101",
                "seedlot_list",
                {"id": "SL-101", "name": "SL-101"},
                "Found 1 seedlots matching 'SL-101'",
                "seedlot_search_service.search",
                ["seedlots"],
            ),
            (
                "search_programs",
                {"query": "rice program", "crop": "rice"},
                "Find rice programs",
                "program_list",
                {"id": "prog-101", "name": "Rice Improvement"},
                "Found 1 programs matching 'rice program'",
                "program_search_service.search",
                ["programs"],
            ),
            (
                "search_traits",
                {"query": "yield", "crop": "rice"},
                "Find yield traits",
                "trait_list",
                {"id": "trait-101", "name": "Yield"},
                "Found 1 traits matching 'yield'",
                "trait_search_service.search",
                ["traits"],
            ),
        ],
    )
    def test_streaming_function_path_prefers_extended_search_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        result_type,
        item,
        function_message,
        service_name,
        domains_involved,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": function_name,
                "result_type": result_type,
                "data": {
                    "total": 1,
                    "items": [item],
                    "message": function_message,
                },
                "retrieval_audit": {
                    "services": [service_name],
                    "entities": parameters,
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": domains_involved,
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when search data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == function_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        ("function_name", "parameters", "user_message", "error_message"),
        [
            (
                "search_locations",
                {"query": "Ludhiana"},
                "Find locations matching Ludhiana",
                "Failed to search locations database",
            ),
            (
                "search_seedlots",
                {"query": "SL-101"},
                "Find seedlots matching SL-101",
                "Failed to search seedlots database",
            ),
            (
                "search_programs",
                {"query": "rice program"},
                "Find rice programs",
                "Failed to search programs database",
            ),
            (
                "search_traits",
                {"query": "yield"},
                "Find yield traits",
                "Failed to search traits database",
            ),
        ],
    )
    def test_streaming_function_path_prefers_extended_search_failure_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        error_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "result_type": "search_error",
                "error": "search service unavailable",
                "message": error_message,
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when search failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == error_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_get_observations_data_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="get_observations", parameters={"trait": "Yield", "study_id": "101"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "get_observations",
                "result_type": "observation_list",
                "data": {
                    "total": 1,
                    "items": [{"observationDbId": "obs-101", "value": 42.0, "trait": "Yield"}],
                    "message": "Found 1 observations for trait 'Yield'",
                },
                "retrieval_audit": {
                    "services": ["observation_search_service.search"],
                    "entities": {"trait": "Yield", "study_id": "101"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["observations"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when observations data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show Yield observations for study 101", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Found 1 observations for trait 'Yield'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_get_observations_failure_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="get_observations", parameters={"trait": "Yield"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "get_observations",
                "result_type": "observation_list_error",
                "error": "observations unavailable",
                "message": "Failed to get observations",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when observations failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show Yield observations", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to get observations"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        ("function_name", "parameters", "user_message", "proposal_title", "domains_involved"),
        [
            (
                "propose_create_trial",
                {"crop": "rice", "location": "IRRI"},
                "Create a rice trial at IRRI",
                "Rice Trial Proposal",
                ["trials"],
            ),
            (
                "propose_create_cross",
                {"parent1": "IR64", "parent2": "Swarna"},
                "Propose a cross between IR64 and Swarna",
                "Cross Proposal",
                ["crosses"],
            ),
            (
                "propose_record_observation",
                {"trait": "Yield", "value": 42.0},
                "Propose recording a Yield observation",
                "Observation Proposal",
                ["observations"],
            ),
        ],
    )
    def test_streaming_function_path_prefers_proposal_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        proposal_title,
        domains_involved,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": function_name,
                "result_type": "proposal_created",
                "data": {
                    "proposal_id": 321,
                    "status": "pending_review",
                    "title": proposal_title,
                    "message": "Proposal created successfully (ID: 321). Pending review.",
                },
                "retrieval_audit": {
                    "services": ["proposal_service.create_proposal"],
                    "entities": parameters,
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": domains_involved,
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when proposal data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        proposal_events = _extract_sse_events(response.text, event_type="proposal_created")
        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert proposal_events
        assert proposal_events[-1]["data"]["proposal_id"] == 321
        assert proposal_events[-1]["data"]["title"] == proposal_title
        assert chunk_events
        assert chunk_events[-1]["content"] == "Proposal created successfully (ID: 321). Pending review."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        ("function_name", "parameters", "user_message"),
        [
            ("propose_create_trial", {"crop": "rice"}, "Create a rice trial"),
            ("propose_create_cross", {"parent1": "IR64", "parent2": "Swarna"}, "Create a cross"),
            (
                "propose_record_observation",
                {"trait": "Yield", "value": 42.0},
                "Record an observation",
            ),
        ],
    )
    def test_streaming_function_path_prefers_proposal_failure_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "result_type": "proposal_error",
                "error": "proposal service unavailable",
                "message": "Failed to create proposal",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when proposal failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        proposal_events = _extract_sse_events(response.text, event_type="proposal_created")
        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert not proposal_events
        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to create proposal"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_weather_forecast_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="get_weather_forecast",
                parameters={"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "get_weather_forecast",
                "result_type": "weather_forecast",
                "data": {
                    "location": "Ludhiana",
                    "days": 3,
                    "summary": "Heat risk may influence current field performance.",
                    "alerts": ["heat_risk"],
                    "impacts_count": 1,
                    "optimal_windows": [],
                    "message": "Weather forecast for Ludhiana (3 days)",
                },
                "retrieval_audit": {
                    "services": ["weather_service.get_forecast"],
                    "entities": {"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["environment"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when weather data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show a 3 day weather forecast for Ludhiana wheat", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Weather forecast for Ludhiana (3 days)"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_weather_forecast_failure_message_over_llm_stream(
        self, client, mock_llm_service
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="get_weather_forecast",
                parameters={"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "get_weather_forecast",
                "result_type": "weather_forecast_error",
                "error": "weather service unavailable",
                "message": "Failed to get weather forecast",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when weather failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show a 3 day weather forecast for Ludhiana wheat", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to get weather forecast"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_cross_domain_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="cross_domain_query", parameters={"trait": "blast resistance"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "cross_domain_query",
                "result_type": "cross_domain_results",
                "data": {
                    "message": "Cross-domain evidence matched the requested breeding and genomics scope.",
                },
                "retrieval_audit": {
                    "services": ["germplasm_search_service.search", "QTLMappingService.list_qtls"],
                    "entities": {"trait": "blast resistance"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": True,
                    "domains_involved": ["breeding", "genomics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when cross-domain results include deterministic data copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Compare blast resistance evidence across breeding and genomics", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == (
            "Cross-domain evidence matched the requested breeding and genomics scope."
        )
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_navigation_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="navigate_to",
                parameters={"page": "/trials", "filters": {"crop": "rice"}},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "navigate_to",
                "result_type": "navigation",
                "data": {
                    "page": "/trials",
                    "filters": {"crop": "rice"},
                    "action": "navigate",
                    "message": "Open /trials with the requested filters.",
                },
                "retrieval_audit": {
                    "services": [],
                    "entities": {"page": "/trials", "filters": {"crop": "rice"}},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["navigation"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when navigation data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Open the rice trials page", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Open /trials with the requested filters."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_export_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="export_data",
                parameters={"data_type": "germplasm", "format": "json", "query": "IR64", "limit": 5},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "export_data",
                "result_type": "data_exported",
                "data": {
                    "data_type": "germplasm",
                    "format": "json",
                    "record_count": 1,
                    "content_preview": '{"items": [{"id": "101"}]}',
                    "content_length": 26,
                    "message": "Exported 1 germplasm records in JSON format",
                },
                "retrieval_audit": {
                    "services": ["germplasm_search_service.search", "data_export_service.export_to_json"],
                    "entities": {"data_type": "germplasm", "format": "json", "query": "IR64"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["navigation"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when export data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Export germplasm records for IR64 as JSON", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Exported 1 germplasm records in JSON format"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_export_failure_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="export_data", parameters={"data_type": "unknown"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "export_data",
                "result_type": "data_export_error",
                "error": "Unknown data type: unknown",
                "message": "Supported types: germplasm, trials, observations, crosses, locations, seedlots, traits, programs",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when export failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Export unknown records", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == (
            "Supported types: germplasm, trials, observations, crosses, locations, seedlots, traits, programs"
        )
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        (
            "function_name",
            "parameters",
            "user_message",
            "result_type",
            "function_message",
            "error_message",
            "safe_failure_payload",
            "retrieval_services",
            "entities",
            "domains_involved",
            "expected_message",
        ),
        [
            (
                "compare_germplasm",
                {"germplasm_ids": ["IR64", "unknown-line"]},
                "Compare IR64 and unknown-line",
                "comparison",
                None,
                "Not enough germplasm found",
                {
                    "error_category": "insufficient_retrieval_scope",
                    "searched": ["phenotype_comparison.compare", "germplasm_search_service"],
                    "missing": ["at least two resolvable germplasm identifiers"],
                    "next_steps": ["Retry with exact accession or germplasm IDs."],
                },
                [
                    "germplasm_search_service.search",
                    "observation_search_service.get_by_germplasm",
                ],
                {
                    "requested_germplasm_ids": ["IR64", "unknown-line"],
                    "resolved_germplasm_ids": ["IR64"],
                },
                ["breeding"],
                (
                    "Not enough germplasm found. "
                    "Missing grounded input: at least two resolvable germplasm identifiers. "
                    "Next step: Retry with exact accession or germplasm IDs."
                ),
            ),
            (
                "calculate_breeding_value",
                {"trait": "yield", "method": "GBLUP", "germplasm_ids": ["IR64", "Swarna"]},
                "Calculate GBLUP breeding values for IR64 and Swarna on yield",
                "breeding_values",
                None,
                "GBLUP requires genotype_matrix or g_matrix together with phenotypes",
                {
                    "error_category": "insufficient_compute_inputs",
                    "missing_inputs": ["phenotypes", "genotype_matrix or g_matrix"],
                    "required_inputs": ["phenotypes", "genotype_matrix or g_matrix"],
                },
                ["calculate_breeding_value.input_validation"],
                {
                    "trait": "yield",
                    "method": "GBLUP",
                    "germplasm_ids": ["IR64", "Swarna"],
                    "study_id": None,
                },
                ["analytics"],
                "GBLUP requires genotype_matrix or g_matrix together with phenotypes.",
            ),
            (
                "get_germplasm_details",
                {"query": "ambiguous"},
                "Show the ambiguous germplasm details",
                "germplasm_details",
                None,
                "Ambiguous germplasm query",
                {
                    "error_category": "ambiguous_retrieval_scope",
                    "searched": ["germplasm_lookup", "germplasm_search_service"],
                    "missing": ["single authoritative germplasm match"],
                    "next_steps": ["Retry with the exact accession or internal germplasm ID."],
                },
                ["germplasm_search_service.search"],
                {"query": "ambiguous", "match_count": 2},
                ["breeding"],
                (
                    "Ambiguous germplasm query. "
                    "Missing grounded input: single authoritative germplasm match. "
                    "Next step: Retry with the exact accession or internal germplasm ID."
                ),
            ),
            (
                "get_trial_results",
                {"query": "Punjab wheat trial"},
                "Show the Punjab wheat trial results",
                "trial_results",
                None,
                "Ambiguous trial query",
                {
                    "error_category": "ambiguous_retrieval_scope",
                    "searched": ["trial_summary", "trial_search_service"],
                    "missing": ["single authoritative trial match"],
                    "next_steps": ["Retry with the exact trial ID."],
                },
                ["trial_search_service.search"],
                {"query": "Punjab wheat trial", "match_count": 2},
                ["trials"],
                (
                    "Ambiguous trial query. "
                    "Missing grounded input: single authoritative trial match. "
                    "Next step: Retry with the exact trial ID."
                ),
            ),
            (
                "get_trait_summary",
                {"germplasm_ids": ["unknown-line"]},
                "Summarize the trait evidence for unknown-line",
                "trait_summary",
                None,
                "Trait summary requires at least one resolvable germplasm",
                {
                    "error_category": "insufficient_retrieval_scope",
                    "searched": ["phenotype_comparison.statistics", "germplasm_search_service"],
                    "missing": ["resolvable germplasm identifiers"],
                    "next_steps": ["Retry with exact accession or germplasm IDs."],
                },
                [
                    "germplasm_search_service.get_by_id",
                    "germplasm_search_service.search",
                ],
                {
                    "requested_germplasm_ids": ["unknown-line"],
                    "resolved_germplasm_ids": [],
                },
                ["breeding"],
                (
                    "Trait summary requires at least one resolvable germplasm. "
                    "Missing grounded input: resolvable germplasm identifiers. "
                    "Next step: Retry with exact accession or germplasm IDs."
                ),
            ),
            (
                "get_marker_associations",
                {"query": "unknown resistance"},
                "What marker associations exist for unknown resistance?",
                "marker_associations",
                None,
                "Unresolvable marker association query",
                {
                    "error_category": "insufficient_retrieval_scope",
                    "searched": ["QTLMappingService.get_traits", "QTLMappingService.get_gwas_results"],
                    "missing": ["single authoritative genomics trait"],
                    "next_steps": [
                        "Retry with the exact trait name used in QTL or GWAS records."
                    ],
                },
                ["QTLMappingService.get_traits"],
                {
                    "requested_trait": "unknown resistance",
                    "candidate_traits": [],
                },
                ["genomics"],
                (
                    "Unresolvable marker association query. "
                    "Missing grounded input: single authoritative genomics trait. "
                    "Next step: Retry with the exact trait name used in QTL or GWAS records."
                ),
            ),
            (
                "cross_domain_query",
                {"query": "Which wheat varieties performed best in trials at Ludhiana under current weather?"},
                "Which wheat varieties performed best in trials at Ludhiana under current weather?",
                "cross_domain_results",
                "The compound query was recognized, but not enough domain evidence was retrieved to produce a grounded joined response.",
                "Cross-domain query could not retrieve requested domains: weather",
                {
                    "error_category": "insufficient_retrieval_scope",
                    "searched": [
                        "germplasm_search_service.search",
                        "trial_search_service.search",
                        "location_search_service.search",
                    ],
                    "missing": ["weather"],
                    "missing_context": [
                        {
                            "domain": "weather",
                            "location_query": "Ludhiana",
                            "reason": "weather service is unavailable",
                        }
                    ],
                    "next_steps": ["Add or enable the missing domain data before retrying."],
                },
                [
                    "germplasm_search_service.search",
                    "trial_search_service.search",
                    "location_search_service.search",
                ],
                {
                    "original_query": "Which wheat varieties performed best in trials at Ludhiana under current weather?",
                    "missing_domains": ["weather"],
                    "resolved_domains": ["breeding", "trials"],
                    "resolved_germplasm_ids": ["IR64"],
                    "resolved_trial_ids": ["TRIAL-1"],
                    "resolved_location_ids": ["LOC-1"],
                },
                ["breeding", "trials", "weather", "analytics"],
                "The compound query was recognized, but not enough domain evidence was retrieved to produce a grounded joined response.",
            ),
        ],
    )
    def test_streaming_function_path_prefers_structured_safe_failure_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        result_type,
        function_message,
        error_message,
        safe_failure_payload,
        retrieval_services,
        entities,
        domains_involved,
        expected_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "result_type": result_type,
                "message": function_message,
                "error": error_message,
                "safe_failure": safe_failure_payload,
                "retrieval_audit": {
                    "services": retrieval_services,
                    "entities": entities,
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": domains_involved,
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when a structured safe_failure can be rendered deterministically"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")
        summary_events = _extract_sse_events(response.text, event_type="summary")

        assert chunk_events
        assert chunk_events[-1]["content"] == expected_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert summary_events
        summary_payload = summary_events[-1]
        _assert_summary_execution_trace_contract(summary_payload, safe_failure_expected=True)
        assert summary_payload["safe_failure"] == safe_failure_payload
        assert summary_payload["retrieval_audit"] == {
            "services": retrieval_services,
            "entities": entities,
        }
        assert summary_payload["plan_execution_summary"]["domains_involved"] == domains_involved

    def test_streaming_function_path_prefers_seedlot_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="check_seed_viability", parameters={"seedlot_id": "SL-1"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "check_seed_viability",
                "result_type": "viability_result",
                "data": {
                    "seedlot_id": "SL-1",
                    "is_viable": True,
                    "message": "Checked viability for seedlot SL-1",
                },
                "retrieval_audit": {
                    "services": ["seedlot_search_service.check_viability"],
                    "entities": {"seedlot_id": "SL-1"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["seedlots"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when seedlot data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Check seedlot SL-1 viability", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Checked viability for seedlot SL-1"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_seedlot_batch_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="check_seed_viability", parameters={"germplasm_id": "101"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "check_seed_viability",
                "result_type": "viability_results",
                "data": {
                    "seedlot_count": 2,
                    "results": [
                        {"seedlot_id": "SL-1", "is_viable": True},
                        {"seedlot_id": "SL-2", "is_viable": True},
                    ],
                    "message": "Checked viability for 2 seedlots",
                },
                "retrieval_audit": {
                    "services": [
                        "seedlot_search_service.get_by_germplasm",
                        "seedlot_search_service.check_viability",
                    ],
                    "entities": {"germplasm_id": "101", "seedlot_count": 2},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["seedlots"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when batch seedlot data includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Check seed viability for germplasm 101", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Checked viability for 2 seedlots"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        ("parameters", "user_message", "error_message", "function_message", "expected_message"),
        [
            (
                {},
                "Check seed viability",
                "seedlot_id or germplasm_id required",
                "Please specify a seedlot ID or germplasm ID",
                "Please specify a seedlot ID or germplasm ID",
            ),
            (
                {"germplasm_id": "101"},
                "Check seed viability for germplasm 101",
                "No seedlots found",
                "No seedlots found for germplasm ID 101",
                "No seedlots found for germplasm ID 101",
            ),
        ],
    )
    def test_streaming_function_path_prefers_seedlot_failure_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        parameters,
        user_message,
        error_message,
        function_message,
        expected_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="check_seed_viability", parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "check_seed_viability",
                "result_type": "viability_error",
                "error": error_message,
                "message": function_message,
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when helper failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == expected_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_diversity_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="calculate_genetic_diversity", parameters={"population_id": "POP-1"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "calculate_genetic_diversity",
                "result_type": "diversity_metrics",
                "data": {
                    "population_id": "POP-1",
                    "sample_size": 12,
                    "loci_analyzed": 48,
                    "metrics": [{"name": "Expected Heterozygosity (He)", "value": 0.42}],
                    "recommendations": ["Maintain the current breeding population breadth."],
                    "message": "Calculated genetic diversity metrics for 12 samples across 48 loci.",
                },
                "retrieval_audit": {
                    "services": ["genetic_diversity_service.calculate_diversity_metrics"],
                    "entities": {"population_id": "POP-1", "sample_size": 12, "loci_analyzed": 48},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["genomics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when diversity data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Calculate genetic diversity for population POP-1", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Calculated genetic diversity metrics for 12 samples across 48 loci."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_diversity_failure_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="calculate_genetic_diversity", parameters={"population_id": "POP-1"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "calculate_genetic_diversity",
                "result_type": "diversity_metrics_error",
                "error": "database unavailable",
                "message": "Failed to calculate genetic diversity",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when diversity failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Calculate genetic diversity for population POP-1", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to calculate genetic diversity"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_predict_cross_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="predict_cross",
                parameters={"parent1_id": "101", "parent2_id": "102", "trait": "Yield", "heritability": 0.5},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "predict_cross",
                "result_type": "cross_prediction",
                "data": {
                    "parent1": {"id": "101", "name": "IR64", "mean_phenotype": 4.0},
                    "parent2": {"id": "102", "name": "Swarna", "mean_phenotype": 6.0},
                    "trait": "Yield",
                    "trait_mean": 5.0,
                    "heritability": 0.5,
                    "prediction": {"expected_mean": 5.0},
                    "message": "Cross prediction: IR64 × Swarna",
                },
                "retrieval_audit": {
                    "services": [
                        "germplasm_search_service.get_by_id",
                        "observation_search_service.get_by_germplasm",
                        "observation_search_service.search",
                    ],
                    "entities": {"parent1_id": "101", "parent2_id": "102", "trait": "Yield"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["breeding", "analytics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when predict_cross data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Predict the cross outcome for IR64 and Swarna on yield", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Cross prediction: IR64 × Swarna"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_predict_cross_failure_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="predict_cross", parameters={"parent1_id": "101"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "predict_cross",
                "result_type": "cross_prediction_error",
                "error": "parent1_id and parent2_id are required",
                "message": "Please specify both parent IDs for cross prediction",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when predict_cross failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Predict the cross outcome for IR64", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Please specify both parent IDs for cross prediction"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_analyze_gxe_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="analyze_gxe", parameters={"trait": "Yield", "method": "AMMI"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "analyze_gxe",
                "result_type": "gxe_analysis",
                "data": {
                    "method": "AMMI",
                    "trait": "Yield",
                    "n_genotypes": 3,
                    "n_environments": 2,
                    "n_observations": 6,
                    "analysis": {"principal_components": [0.62, 0.24], "summary": "ammi-stub"},
                    "message": "AMMI analysis: 3 genotypes × 2 environments for trait 'Yield'",
                },
                "retrieval_audit": {
                    "services": ["observation_search_service.search", "gxe_service.ammi_analysis"],
                    "entities": {"trait": "Yield", "n_observations": 6},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["phenotyping", "analytics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when analyze_gxe data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Analyze GxE for yield", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "AMMI analysis: 3 genotypes × 2 environments for trait 'Yield'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_analyze_gxe_failure_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="analyze_gxe", parameters={"trait": "Yield", "method": "AMMI"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "analyze_gxe",
                "result_type": "gxe_analysis_error",
                "error": "Insufficient data",
                "message": "Need at least 6 observations for G×E analysis. Found 1 for trait 'Yield'",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when analyze_gxe failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Analyze GxE for yield", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Need at least 6 observations for G×E analysis. Found 1 for trait 'Yield'"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_harvest_timing_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="predict_harvest_timing",
                parameters={"field_id": 17, "planting_date": "2026-07-01", "crop_name": "maize"},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "predict_harvest_timing",
                "result_type": "harvest_timing_prediction",
                "data": {
                    "field_id": 17,
                    "crop_name": "maize",
                    "predicted_harvest_date": "2026-11-01",
                    "message": "Predicted harvest timing for maize planted on 2026-07-01.",
                },
                "retrieval_audit": {
                    "services": ["CrossDomainGDDService.predict_harvest_timing"],
                    "entities": {"field_id": 17, "crop_name": "maize", "planting_date": "2026-07-01"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["environment"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when harvest timing data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "When should maize from field 17 planted on 2026-07-01 be harvested?", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Predicted harvest timing for maize planted on 2026-07-01."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_variety_recommendation_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="recommend_varieties_by_gdd", parameters={"field_id": 17})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "recommend_varieties_by_gdd",
                "result_type": "variety_recommendations",
                "data": {
                    "recommendations": [
                        {"variety": "IR64", "score": 0.91, "reason": "Optimal GDD match"}
                    ],
                    "message": "Recommended 1 varieties for field 17 based on GDD suitability.",
                },
                "retrieval_audit": {
                    "services": ["CrossDomainGDDService.recommend_varieties"],
                    "entities": {"field_id": 17, "recommendation_count": 1},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["environment"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when variety recommendations include deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Recommend varieties for field 17 using GDD", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Recommended 1 varieties for field 17 based on GDD suitability."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_planting_window_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="analyze_planting_windows", parameters={"field_id": 23, "crop_name": "maize"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "analyze_planting_windows",
                "result_type": "planting_windows",
                "data": {
                    "planting_windows": [
                        {
                            "start_date": "2026-05-01",
                            "predicted_maturity": "2026-09-15",
                            "days_to_maturity": 137,
                            "suitability_score": 0.72,
                        }
                    ],
                    "message": "Analyzed planting windows for maize in field 23.",
                },
                "retrieval_audit": {
                    "services": ["CrossDomainGDDService.analyze_planting_windows"],
                    "entities": {"field_id": 23, "crop_name": "maize"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["environment"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when planting-window data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Analyze maize planting windows for field 23", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Analyzed planting windows for maize in field 23."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_gdd_insight_data_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="get_gdd_insights", parameters={"field_id": 23, "insight_type": "planting"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "get_gdd_insights",
                "result_type": "gdd_insights",
                "data": {
                    "planting_windows": [
                        {
                            "start_date": "2026-05-01",
                            "predicted_maturity": "2026-09-15",
                            "days_to_maturity": 137,
                            "suitability_score": 0.72,
                        }
                    ],
                    "message": "Generated planting GDD insights for field 23.",
                },
                "retrieval_audit": {
                    "services": ["CrossDomainGDDService.analyze_planting_windows"],
                    "entities": {"field_id": 23, "insight_type": "planting"},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["environment"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when GDD insights include deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Give me GDD planting insights for field 23", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Generated planting GDD insights for field 23."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        (
            "function_name",
            "parameters",
            "user_message",
            "result_type",
            "data_payload",
            "service_name",
            "domains_involved",
            "expected_message",
        ),
        [
            (
                "get_trait_details",
                {"trait_id": "trait-101"},
                "Show trait trait-101 details",
                "trait_details",
                {
                    "trait": {"traitDbId": "trait-101", "name": "Plant Height", "trait_class": "morphological"},
                    "observation_count": 12,
                    "message": "Trait 'Plant Height' (morphological)",
                },
                "trait_search_service.get_by_id",
                ["traits"],
                "Trait 'Plant Height' (morphological)",
            ),
            (
                "get_program_details",
                {"program_id": "program-101"},
                "Show program program-101 details",
                "program_details",
                {
                    "program": {"programDbId": "program-101", "name": "Rice Breeding 2024"},
                    "trial_count": 12,
                    "message": "Program 'Rice Breeding 2024' with 12 trials",
                },
                "program_search_service.get_by_id",
                ["programs"],
                "Program 'Rice Breeding 2024' with 12 trials",
            ),
            (
                "get_location_details",
                {"location_id": "location-101"},
                "Show location location-101 details",
                "location_details",
                {
                    "location": {"locationDbId": "location-101", "name": "Ludhiana", "country": "India"},
                    "message": "Location 'Ludhiana' in India",
                },
                "location_search_service.get_by_id",
                ["locations"],
                "Location 'Ludhiana' in India",
            ),
            (
                "get_seedlot_details",
                {"seedlot_id": "seedlot-101"},
                "Show seedlot seedlot-101 details",
                "seedlot_details",
                {
                    "seedlot": {"seedlotDbId": "seedlot-101", "name": "S-001", "amount": 5000, "units": "seeds"},
                    "viability": {"is_viable": True},
                    "message": "Seedlot 'S-001' - 5000 seeds",
                },
                "seedlot_search_service.get_by_id",
                ["seedlots"],
                "Seedlot 'S-001' - 5000 seeds",
            ),
            (
                "get_cross_details",
                {"cross_id": "cross-101"},
                "Show cross cross-101 details",
                "cross_details",
                {
                    "cross": {"crossDbId": "cross-101", "name": "IR64 x Swarna", "status": "Completed"},
                    "message": "Cross 'IR64 x Swarna' - Completed",
                },
                "cross_search_service.get_by_id",
                ["crosses"],
                "Cross 'IR64 x Swarna' - Completed",
            ),
        ],
    )
    def test_streaming_function_path_prefers_detail_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        result_type,
        data_payload,
        service_name,
        domains_involved,
        expected_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": function_name,
                "result_type": result_type,
                "data": data_payload,
                "retrieval_audit": {
                    "services": [service_name],
                    "entities": parameters,
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": domains_involved,
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when detail data includes deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == expected_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        ("function_name", "parameters", "user_message", "error_message"),
        [
            (
                "get_trait_details",
                {"trait_id": "trait-101"},
                "Show trait trait-101 details",
                "Failed to get trait details",
            ),
            (
                "get_program_details",
                {"program_id": "program-101"},
                "Show program program-101 details",
                "Failed to get program details",
            ),
            (
                "get_location_details",
                {"location_id": "location-101"},
                "Show location location-101 details",
                "Failed to get location details",
            ),
            (
                "get_seedlot_details",
                {"seedlot_id": "seedlot-101"},
                "Show seedlot seedlot-101 details",
                "Failed to get seedlot details",
            ),
            (
                "get_cross_details",
                {"cross_id": "cross-101"},
                "Show cross cross-101 details",
                "Failed to get cross details",
            ),
        ],
    )
    def test_streaming_function_path_prefers_detail_failure_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        error_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "result_type": "details_error",
                "error": "lookup failed",
                "message": error_message,
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when detail failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == error_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_statistics_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="get_statistics", parameters={})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "get_statistics",
                "result_type": "statistics",
                "calculation_ids": ["fn:get_statistics"],
                "data": {
                    "programs": {"total_programs": 3},
                    "germplasm": {"total_germplasm": 21},
                    "trials": {"total_trials": 7},
                    "observations": {"total_observations": 33},
                    "crosses": {"total_crosses": 5},
                    "locations": {"total_locations": 4},
                    "seedlots": {"total_seedlots": 11},
                    "traits": {"total_traits": 9},
                    "message": (
                        "Database contains 3 programs, 21 germplasm, 7 trials, 33 observations, "
                        "11 seedlots, 9 traits"
                    ),
                },
                "retrieval_audit": {
                    "services": [
                        "germplasm_search_service.get_statistics",
                        "trial_search_service.get_statistics",
                        "observation_search_service.get_statistics",
                        "cross_search_service.get_statistics",
                        "location_search_service.get_statistics",
                        "seedlot_search_service.get_statistics",
                        "program_search_service.get_statistics",
                        "trait_search_service.get_statistics",
                    ],
                    "entities": {"organization_id": 1},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": True,
                    "domains_involved": [
                        "programs",
                        "germplasm",
                        "trials",
                        "observations",
                        "crosses",
                        "locations",
                        "seedlots",
                        "traits",
                    ],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when get_statistics includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show overall database statistics", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == (
            "Database contains 3 programs, 21 germplasm, 7 trials, 33 observations, 11 seedlots, 9 traits"
        )
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_statistics_failure_message_over_llm_stream(
        self,
        client,
        mock_llm_service,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="get_statistics", parameters={})

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "get_statistics",
                "error": "statistics temporarily unavailable",
                "message": "Failed to get database statistics",
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when get_statistics failure already includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show overall database statistics", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Failed to get database statistics"
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_comparison_context_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(
                name="compare_germplasm",
                parameters={"germplasm_ids": ["IR64", "Swarna"]},
            )

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "compare_germplasm",
                "result_type": "comparison",
                "data": [
                    {"candidate": "Swarna", "score": 5.5},
                    {"candidate": "IR64", "score": 4.0},
                ],
                "comparison_context": {
                    "message": "Compared IR64 and Swarna using the shared phenotype interpretation contract.",
                },
                "retrieval_audit": {
                    "services": ["observation_search_service.get_by_germplasm"],
                    "entities": {"resolved_germplasm_ids": ["IR64", "Swarna"]},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["breeding", "analytics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM stream should be skipped when comparison_context includes deterministic copy"
            )

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Compare IR64 and Swarna", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == (
            "Compared IR64 and Swarna using the shared phenotype interpretation contract."
        )
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_function_path_prefers_breeding_value_message_over_llm_stream(self, client, mock_llm_service):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="calculate_breeding_value", parameters={"trait": "yield", "method": "GBLUP"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "calculate_breeding_value",
                "result_type": "breeding_values",
                "message": "Calculated deterministic GBLUP breeding values for trait 'yield' across the resolved training population.",
                "data": [
                    {"candidate": "IR64", "score": 0.45},
                    {"candidate": "Swarna", "score": 0.12},
                ],
                "retrieval_audit": {
                    "services": ["compute_engine.compute_gblup"],
                    "entities": {"trait": "yield", "method": "GBLUP", "n_individuals": 2},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["genomics", "analytics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when breeding-value results include deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Calculate breeding values for yield", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == "Calculated deterministic GBLUP breeding values for trait 'yield' across the resolved training population."
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    @pytest.mark.parametrize(
        (
            "function_name",
            "parameters",
            "user_message",
            "result_type",
            "data_payload",
            "retrieval_services",
            "entities",
            "domains_involved",
            "expected_message",
        ),
        [
            (
                "get_germplasm_details",
                {"germplasm_id": "101"},
                "Show me the IR64 germplasm details",
                "germplasm_details",
                {
                    "germplasm": {"id": "101", "name": "IR64"},
                    "observation_count": 3,
                    "observations": [{"observation_db_id": "OBS-1"}],
                    "message": "Germplasm 'IR64' with 3 observations",
                },
                [
                    "germplasm_search_service.get_by_id",
                    "observation_search_service.get_by_germplasm",
                ],
                {"germplasm_id": "101", "germplasm_accession": "IR64"},
                ["breeding"],
                "Germplasm 'IR64' with 3 observations",
            ),
            (
                "get_trial_results",
                {"trial_id": "TRIAL-1"},
                "Show me the Ludhiana trial summary",
                "trial_results",
                {
                    "trial": {"trialDbId": "TRIAL-1", "trialName": "Ludhiana advanced yield trial"},
                    "top_performers": [{"germplasmName": "IR64"}],
                    "trait_summary": [{"trait": "Yield"}],
                    "location_performance": [],
                    "statistics": {"primary_trait": "Yield"},
                    "interpretation": {"contract_version": "phenotyping.interpretation.v1"},
                    "message": "Trial 'Ludhiana advanced yield trial' summary retrieved from database-backed trial surfaces.",
                },
                ["app.api.v2.trial_summary.get_trial_summary"],
                {"trial_id": "TRIAL-1", "trial_db_id": "TRIAL-1"},
                ["trials", "analytics"],
                "Trial 'Ludhiana advanced yield trial' summary retrieved from database-backed trial surfaces.",
            ),
            (
                "get_trait_summary",
                {"germplasm_ids": ["IR64", "Swarna"]},
                "Summarize the trait evidence for IR64 and Swarna",
                "trait_summary",
                {
                    "total_germplasm": 2,
                    "total_traits": 1,
                    "trait_summary": {"yield": {"mean": 4.75}},
                    "interpretation": {"contract_version": "phenotyping.interpretation.v1"},
                    "message": "Trait summary statistics retrieved from database-backed phenotype comparison surfaces.",
                },
                ["app.api.v2.phenotype_comparison.get_comparison_statistics"],
                {
                    "requested_germplasm_ids": ["IR64", "Swarna"],
                    "resolved_germplasm_ids": ["IR64", "Swarna"],
                },
                ["breeding", "analytics"],
                "Trait summary statistics retrieved from database-backed phenotype comparison surfaces.",
            ),
            (
                "get_marker_associations",
                {"query": "blast resistance"},
                "What marker associations exist for blast resistance?",
                "marker_associations",
                {
                    "trait": "Blast Resistance",
                    "qtls": [{"qtl_id": "qtl_blast_1"}],
                    "associations": [{"marker_name": "M123"}],
                    "summary": {"qtl_count": 1, "association_count": 1, "top_marker": "M123"},
                    "message": "Retrieved genomics marker associations for trait 'Blast Resistance' from database-backed QTL and GWAS records.",
                },
                [
                    "QTLMappingService.get_traits",
                    "QTLMappingService.list_qtls",
                    "QTLMappingService.get_gwas_results",
                ],
                {"requested_trait": "blast resistance", "resolved_trait": "Blast Resistance"},
                ["genomics"],
                "Retrieved genomics marker associations for trait 'Blast Resistance' from database-backed QTL and GWAS records.",
            ),
        ],
    )
    def test_streaming_function_path_prefers_trusted_get_data_messages_over_llm_stream(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        result_type,
        data_payload,
        retrieval_services,
        entities,
        domains_involved,
        expected_message,
    ):
        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name=function_name, parameters=parameters)

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": function_name,
                "result_type": result_type,
                "data": data_payload,
                "retrieval_audit": {
                    "services": retrieval_services,
                    "entities": entities,
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": domains_involved,
                    "steps": [],
                    "total_steps": 0,
                },
            }

        valid_validation = SimpleNamespace(valid=True, errors=[])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM stream should be skipped when trusted get_* results include deterministic copy")

        mock_llm_service.stream_chat = fail_if_called

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": user_message, "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        policy_events = _extract_sse_events(response.text, event_type="stage", stage="policy_validation")

        assert chunk_events
        assert chunk_events[-1]["content"] == expected_message
        completed = _completed_stage_events(policy_events)
        assert completed
        _assert_policy_stage_contract(completed[-1], safe_failure_expected=False)
        assert completed[-1]["valid"] is True
        assert completed[-1]["error_count"] == 0

    def test_streaming_template_mode_chunks_include_request_id(self, client, mock_llm_service):
        """Template-mode warning chunks should include request_id for correlation."""

        async def mock_detect_function_call(*args, **kwargs):
            return None

        async def template_unavailable_status():
            return {
                "active_provider": "template",
                "active_model": "template-v1",
                "providers": {"template": {"available": False}},
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ):
            mock_llm_service.get_status = template_unavailable_status
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Hello", "include_context": False}
            )

        start_events = _extract_sse_events(response.text, event_type="start")
        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert start_events
        assert chunk_events
        assert done_events

        request_id = start_events[-1].get("request_id")
        assert request_id
        assert done_events[-1].get("request_id") == request_id
        assert all(evt.get("request_id") == request_id for evt in chunk_events)

    def test_streaming_proposal_created_event_is_emitted(self, client):
        """Proposal function results should surface proposal_created event in SSE stream."""

        async def mock_detect_function_call(*args, **kwargs):
            return SimpleNamespace(name="propose_create_trial", parameters={"crop": "rice"})

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "result_type": "proposal_created",
                "data": {
                    "id": 321,
                    "title": "Create rice trial",
                    "status": "draft",
                },
            }

        with patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat/stream", json={"message": "Create a rice trial", "include_context": False}
            )

        proposal_events = _extract_sse_events(response.text, event_type="proposal_created")
        assert proposal_events
        payload = proposal_events[-1]
        assert payload["type"] == "proposal_created"
        assert payload["data"]["id"] == 321

    def test_streaming_route_uses_request_scoped_registry_metadata(self, client):
        """Streaming start metadata should reflect the request-scoped provider registry selection."""

        registry = SimpleNamespace(active_provider="openai", active_model="gpt-4.1-mini")
        provider_service = SimpleNamespace(
            load_registry=AsyncMock(return_value=registry),
            get_agent_setting=AsyncMock(return_value=None),
        )

        class FakeMultiTierLLMService:
            def __init__(self):
                self.registry = None

            def set_provider_registry(self, registry_to_apply):
                self.registry = registry_to_apply

            async def get_status(self):
                if self.registry is None:
                    return {
                        "active_provider": "template",
                        "active_model": "template-v1",
                        "providers": {"template": {"available": True}},
                    }

                return {
                    "active_provider": self.registry.active_provider,
                    "active_model": self.registry.active_model,
                    "providers": {
                        self.registry.active_provider: {"available": True},
                    },
                }

            async def stream_chat(self, *args, **kwargs):
                yield "Scoped"
                yield " response"

        async def no_function_call(*args, **kwargs):
            return None

        with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
            "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
        ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=no_function_call,
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Hello", "include_context": False},
            )

        assert response.status_code == 200
        start_events = _extract_sse_events(response.text, event_type="start")
        assert start_events
        start_payload = start_events[-1]
        assert start_payload["provider"] == "openai"
        assert start_payload["model"] == "gpt-4.1-mini"
        provider_service.load_registry.assert_awaited_once()
        assert provider_service.load_registry.await_args.args[1] == 1
        assert provider_service.load_registry.await_args.kwargs == {"is_superuser": False}

    def test_streaming_blocked_internal_functiongemma_output_falls_back_without_execution(
        self,
        client,
        mock_llm_service,
    ):
        valid_validation = SimpleNamespace(valid=True, errors=[])
        evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def mock_get_client(self):
            return _MockFunctionGemmaClient(
                '{"function": "get_statistics", "parameters": {}}'
            )

        async def mock_stream_chat(*args, **kwargs):
            yield "Blocked"
            yield " helper"
            yield " prevented."

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "Blocked internal FunctionGemma helper should not execute through the streaming route"
            )

        mock_llm_service.stream_chat = mock_stream_chat

        with patch.dict(
            "os.environ",
            {"HUGGINGFACE_API_KEY": "test-key"},
            clear=False,
        ), patch(
            "app.api.v2.chat.FunctionCallingService._get_client",
            new=mock_get_client,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=fail_if_called,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Show database statistics", "include_context": False},
            )

        chunk_events = _extract_sse_events(response.text, event_type="chunk")
        plan_events = _extract_sse_events(response.text, event_type="stage", stage="plan_generation")
        data_execution_events = _extract_sse_events(response.text, event_type="stage", stage="data_execution")
        start_events = _extract_sse_events(response.text, event_type="start")
        summary_events = _extract_sse_events(response.text, event_type="summary")
        done_events = _extract_sse_events(response.text, event_type="done")

        assert response.status_code == 200
        assert start_events
        assert done_events
        assert summary_events
        assert "".join(event["content"] for event in chunk_events) == "Blocked helper prevented."
        assert data_execution_events == []

        completed_plan_events = _completed_stage_events(plan_events)
        assert completed_plan_events
        assert completed_plan_events[-1].get("function_call_detected") is False
        _assert_stream_event_contract(summary_events[-1], "summary")

    def test_streaming_route_passes_prompt_modes_from_agent_setting(self, client):
        registry = SimpleNamespace(active_provider="openai", active_model="gpt-4.1-mini")
        provider_service = SimpleNamespace(
            load_registry=AsyncMock(return_value=registry),
            get_agent_setting=AsyncMock(
                return_value=SimpleNamespace(
                    capability_overrides=None,
                    tool_policy=None,
                    prompt_mode_capabilities=["environment_mode"],
                    system_prompt_override=None,
                )
            ),
        )

        class FakeMultiTierLLMService:
            instances: list["FakeMultiTierLLMService"] = []

            def __init__(self):
                self.registry = None
                self.stream_calls: list[dict[str, object]] = []
                self.__class__.instances.append(self)

            def set_provider_registry(self, registry_to_apply):
                self.registry = registry_to_apply

            async def get_status(self):
                return {
                    "active_provider": self.registry.active_provider,
                    "active_model": self.registry.active_model,
                    "providers": {self.registry.active_provider: {"available": True}},
                }

            async def stream_chat(self, *args, **kwargs):
                self.stream_calls.append(kwargs)
                yield "Scoped"

        async def no_function_call(*args, **kwargs):
            return None

        base_service = FakeMultiTierLLMService()

        with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
            "app.api.v2.chat.get_llm_service", return_value=base_service
        ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=no_function_call,
        ):
            response = client.post(
                "/api/v2/chat/stream",
                json={"message": "Hello", "include_context": False},
            )

        assert response.status_code == 200
        resolved_service = FakeMultiTierLLMService.instances[-1]
        assert resolved_service.stream_calls[0]["prompt_mode_capabilities"] == ["environment_mode"]


class TestRequestScopedLLMService:
    def test_get_request_llm_service_returns_non_multitier_base_service(self):
        """Non-MultiTier base services should keep the legacy compatibility seam."""
        from app.api.v2.chat import get_request_llm_service

        base_service = object()

        async def run_test():
            with patch("app.api.v2.chat.get_llm_service", return_value=base_service), patch(
                "app.api.v2.chat.get_ai_provider_service"
            ) as mock_provider_service:
                resolved = await get_request_llm_service(
                    db=SimpleNamespace(),
                    current_user=SimpleNamespace(organization_id=7, is_superuser=False),
                )

            assert resolved is base_service
            mock_provider_service.assert_not_called()

        import asyncio

        asyncio.run(run_test())

    def test_get_request_llm_service_loads_org_registry_into_new_multitier_service(self):
        """Request-scoped service should load the org registry into a fresh LLM service instance."""
        from app.api.v2.chat import get_request_llm_service

        registry = SimpleNamespace(active_provider="openai", active_model="gpt-4.1-mini")
        provider_service = SimpleNamespace(load_registry=AsyncMock(return_value=registry))

        class FakeMultiTierLLMService:
            instances: list["FakeMultiTierLLMService"] = []

            def __init__(self):
                self.registry = None
                self.__class__.instances.append(self)

            def set_provider_registry(self, registry_to_apply):
                self.registry = registry_to_apply

        base_service = FakeMultiTierLLMService()
        db = SimpleNamespace(name="db-session")
        user = SimpleNamespace(organization_id=19, is_superuser=True)

        async def run_test():
            with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
                "app.api.v2.chat.get_llm_service", return_value=base_service
            ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
                resolved = await get_request_llm_service(db=db, current_user=user)

            assert resolved is not base_service
            assert isinstance(resolved, FakeMultiTierLLMService)
            assert resolved.registry is registry
            provider_service.load_registry.assert_awaited_once()
            assert provider_service.load_registry.await_args.args == (db, 19)
            assert provider_service.load_registry.await_args.kwargs == {"is_superuser": True}

        import asyncio

        asyncio.run(run_test())

class TestStreamChatMethod:
    """Test the stream_chat method in LLM service"""

    def test_stream_chat_method_exists(self):
        """Test that stream_chat method exists on LLM service"""
        from app.modules.ai.services.engine import MultiTierLLMService

        service = MultiTierLLMService()
        assert hasattr(service, "stream_chat")
        assert callable(service.stream_chat)

    def test_streaming_methods_exist_for_providers(self):
        """Test that provider adapters expose streaming entry points"""
        from app.modules.ai.services.engine import MultiTierLLMService
        from app.modules.ai.services.provider_types import LLMProvider

        service = MultiTierLLMService()

        streaming_providers = [
            LLMProvider.GROQ,
            LLMProvider.GOOGLE,
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
        ]

        for provider in streaming_providers:
            adapter = service._adapters.get(provider)
            assert adapter is not None, f"Missing adapter for provider: {provider.value}"
            assert callable(adapter.stream), f"Missing streaming adapter entry point: {provider.value}"

    def test_compose_system_prompt_appends_prompt_mode_fragments_in_canonical_order(self):
        from app.modules.ai.services.engine import MultiTierLLMService
        from app.modules.ai.services.provider_types import LLMProvider

        service = MultiTierLLMService()
        prompt = service.compose_system_prompt(
            provider=LLMProvider.OPENAI,
            model="gpt-4.1-mini",
            prompt_mode_capabilities=["environment_mode", "breeding_mode"],
        )

        breeding_index = prompt.index("Breeding mode is active.")
        environment_index = prompt.index("Environment mode is active.")
        assert breeding_index < environment_index

    def test_compose_system_prompt_preserves_override_precedence(self):
        from app.modules.ai.services.engine import MultiTierLLMService
        from app.modules.ai.services.provider_types import LLMProvider

        service = MultiTierLLMService()
        prompt = service.compose_system_prompt(
            provider=LLMProvider.OPENAI,
            model="gpt-4.1-mini",
            system_prompt_override="Custom override",
            prompt_mode_capabilities=["breeding_mode"],
        )

        assert prompt == "Custom override"


# Run with: python -m pytest tests/units/api/v2/test_chat_streaming.py -v
