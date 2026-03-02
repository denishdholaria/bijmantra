"""
Tests for Veena AI Chat Streaming Endpoint

Tests the /api/v2/chat/stream SSE endpoint.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
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


def _assert_required_fields(payload: dict, required: set[str], *, label: str) -> None:
    missing = required - set(payload)
    assert not missing, f"Missing required {label} fields: {sorted(missing)}"


def _assert_stream_event_contract(payload: dict, event_type: str) -> None:
    _assert_required_fields(payload, STREAM_EVENT_REQUIRED_FIELDS[event_type], label=f"{event_type} event")


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
    def client(self):
        """Create test client"""
        from app.api.deps import get_current_user
        from app.api.v2.chat import get_veena_service
        from app.main import app

        veena_service = SimpleNamespace()

        async def mock_get_or_create_user_context(*args, **kwargs):
            return {"context": "ok"}

        async def mock_update_interaction_stats(*args, **kwargs):
            return None

        async def mock_save_episodic_memory(*args, **kwargs):
            return None

        veena_service.get_or_create_user_context = mock_get_or_create_user_context
        veena_service.update_interaction_stats = mock_update_interaction_stats
        veena_service.save_episodic_memory = mock_save_episodic_memory

        async def override_current_user():
            # Chat endpoint casts id/org to int during request handling.
            return SimpleNamespace(id=1, organization_id=1, email="test@bijmantra.org", is_demo=False)

        async def override_veena_service():
            return veena_service

        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_veena_service] = override_veena_service

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


class TestStreamChatMethod:
    """Test the stream_chat method in LLM service"""

    def test_stream_chat_method_exists(self):
        """Test that stream_chat method exists on LLM service"""
        from app.services.ai.engine import MultiTierLLMService

        service = MultiTierLLMService()
        assert hasattr(service, "stream_chat")
        assert callable(service.stream_chat)

    def test_streaming_methods_exist_for_providers(self):
        """Test that streaming methods exist for all supported providers"""
        from app.services.ai.engine import MultiTierLLMService

        service = MultiTierLLMService()

        streaming_methods = [
            "_stream_groq",
            "_stream_google",
            "_stream_openai",
            "_stream_anthropic",
        ]

        for method in streaming_methods:
            assert hasattr(service, method), f"Missing streaming method: {method}"


# Run with: python -m pytest tests/units/api/v2/test_chat_streaming.py -v
