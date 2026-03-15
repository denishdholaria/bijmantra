"""Unit tests for REEVU chat policy validation helpers."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.api.v2.chat import (
    _build_evidence_pack,
    _build_safe_failure_payload,
    _extract_claims_for_validation,
    _validate_response_content,
    get_veena_service,
)
from tests.utils.safe_failure_assertions import assert_actionable_safe_failure_payload


CHAT_RESPONSE_REQUIRED_FIELDS = {
    "message",
    "provider",
    "model",
    "model_confirmed",
    "context",
    "conversation_id",
    "suggestions",
    "cached",
    "latency_ms",
    "policy_validation",
    "evidence_envelope",
}
POLICY_VALIDATION_REQUIRED_FIELDS = {
    "valid",
    "error_count",
    "errors",
    "evidence_count",
    "calculation_count",
}


def _assert_chat_contract_fields(payload: dict) -> None:
    """Lock required top-level chat fields while allowing additive fields."""

    missing = CHAT_RESPONSE_REQUIRED_FIELDS - set(payload)
    assert not missing, f"Missing required chat response fields: {sorted(missing)}"


def _assert_chat_contract_types(payload: dict) -> None:
    """Lock key chat field types that clients parse downstream."""

    assert isinstance(payload["message"], str)
    assert isinstance(payload["provider"], str)
    assert isinstance(payload["model"], str)
    assert isinstance(payload["model_confirmed"], bool)
    assert payload["context"] is None or isinstance(payload["context"], list)
    assert payload["conversation_id"] is None or isinstance(payload["conversation_id"], str)
    assert payload["suggestions"] is None or isinstance(payload["suggestions"], list)
    assert isinstance(payload["cached"], bool)
    assert payload["latency_ms"] is None or isinstance(payload["latency_ms"], int | float)
    assert isinstance(payload["policy_validation"], dict)
    assert isinstance(payload["evidence_envelope"], dict)


def _assert_policy_validation_contract(validation_payload: dict, *, safe_failure_expected: bool) -> None:
    """Lock required policy_validation contract fields without overconstraining extras."""

    missing = POLICY_VALIDATION_REQUIRED_FIELDS - set(validation_payload)
    assert not missing, f"Missing required policy_validation fields: {sorted(missing)}"

    assert isinstance(validation_payload["valid"], bool)
    assert isinstance(validation_payload["error_count"], int)
    assert isinstance(validation_payload["errors"], list)
    assert isinstance(validation_payload["evidence_count"], int)
    assert isinstance(validation_payload["calculation_count"], int)

    if safe_failure_expected:
        assert "safe_failure" in validation_payload
    else:
        assert "safe_failure" not in validation_payload


def test_build_evidence_pack_collects_context_and_function_artifacts():
    docs = [
        SimpleNamespace(doc_id="doc-1", source_id="src-1"),
        SimpleNamespace(doc_id="doc-2", source_id=None),
    ]
    function_result = {
        "evidence_refs": ["ev-1"],
        "calculation_ids": ["calc-1"],
        "data": [{"id": 99, "doc_id": "doc-3", "source_id": "src-3"}],
    }

    evidence_pack = _build_evidence_pack(
        context_docs=docs,
        function_call_name="calculate_gain",
        function_result=function_result,
    )

    assert {"doc-1", "doc-2", "doc-3", "src-1", "src-3", "ev-1", "99"}.issubset(
        evidence_pack.evidence_refs
    )
    assert {"calc-1", "fn:calculate_gain"}.issubset(evidence_pack.calculation_ids)


def test_extract_claims_parses_ref_and_calc_tags():
    content = "Result [[ref:doc-1]] shows gain [[calc:fn:calculate_gain]]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    claim_types = [c.claim_type for c in claims]
    assert "reference" in claim_types
    assert "quantitative" in claim_types


def test_extract_claims_parses_numeric_citation_style_refs():
    content = "This recommendation is supported by [7]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(c.claim_type == "reference" and c.evidence_refs == ("7",) for c in claims)


def test_extract_claims_parses_comma_separated_numeric_citations():
    content = "Recommendation is supported by [7, 8]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(c.claim_type == "reference" and c.evidence_refs == ("7",) for c in claims)
    assert any(c.claim_type == "reference" and c.evidence_refs == ("8",) for c in claims)


def test_extract_claims_parses_numeric_citation_range():
    content = "Recommendation is supported by [7-9]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(c.claim_type == "reference" and c.evidence_refs == ("7",) for c in claims)
    assert any(c.claim_type == "reference" and c.evidence_refs == ("8",) for c in claims)
    assert any(c.claim_type == "reference" and c.evidence_refs == ("9",) for c in claims)


def test_extract_claims_parses_semicolon_and_mixed_citation_groups():
    content = "Recommendation is supported by [7;8,10-11]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(c.claim_type == "reference" and c.evidence_refs == ("7",) for c in claims)
    assert any(c.claim_type == "reference" and c.evidence_refs == ("8",) for c in claims)
    assert any(c.claim_type == "reference" and c.evidence_refs == ("10",) for c in claims)
    assert any(c.claim_type == "reference" and c.evidence_refs == ("11",) for c in claims)


def test_extract_claims_dedupes_repeated_numeric_citations():
    content = "Supported by [7] and again [7]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    repeated_refs = [
        c for c in claims if c.claim_type == "reference" and c.evidence_refs == ("7",)
    ]
    assert len(repeated_refs) == 1


def test_extract_claims_ignores_year_like_bracketed_numbers():
    content = "The trial was conducted in [2024] under controlled settings."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert not any(c.claim_type == "reference" and c.evidence_refs == ("2024",) for c in claims)


def test_extract_claims_parses_percentage_as_quantitative_claim():
    content = "Yield improved by 42% under trial conditions."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(
        c.claim_type == "quantitative" and "missing_calculation" in c.calculation_ids
        for c in claims
    )


def test_extract_claims_dedupes_repeated_percentage_phrases():
    content = "Yield improved by 42% yield; repeat signal 42% yield."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    repeated_percentages = [
        c
        for c in claims
        if c.claim_type == "quantitative" and c.statement.lower() == "quantitative:42% yield"
    ]
    assert len(repeated_percentages) == 1


def test_extract_claims_dedupes_percentage_phrases_with_case_variation():
    content = "Observed 42% Yield change and repeated 42% yield change."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    repeated_percentages = [
        c
        for c in claims
        if c.claim_type == "quantitative" and c.statement.lower() == "quantitative:42% yield"
    ]
    assert len(repeated_percentages) == 1


def test_extract_claims_percentage_uses_inline_calc_tag_in_same_sentence():
    content = "Yield improved by 42% yield [[calc:fn:calculate_gain]]."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(
        c.claim_type == "quantitative"
        and c.statement.startswith("quantitative:42%")
        and "fn:calculate_gain" in c.calculation_ids
        and "missing_calculation" not in c.calculation_ids
        for c in claims
    )


def test_extract_claims_percentage_not_backed_by_calc_tag_in_other_sentence():
    content = "Yield improved by 42% yield. [[calc:fn:calculate_gain]] supports another metric."
    evidence_pack = _build_evidence_pack(context_docs=[])

    claims = _extract_claims_for_validation(content, evidence_pack)

    assert any(
        c.claim_type == "quantitative"
        and c.statement.startswith("quantitative:42%")
        and "missing_calculation" in c.calculation_ids
        for c in claims
    )


def test_validate_response_flags_numeric_density_without_evidence():
    validation, evidence_pack = _validate_response_content(
        content="Yield improved from 10 to 18 and confidence is 95%.",
        context_docs=[],
    )

    assert not validation.valid
    assert len(validation.errors) > 0
    assert len(evidence_pack.evidence_refs) == 0


def test_validate_response_ignores_year_only_numeric_density():
    validation, _ = _validate_response_content(
        content="Season windows were 2022, 2023, and 2024 across baseline trials.",
        context_docs=[],
    )

    assert validation.valid
    assert not any("quantitative-claim-without-evidence" in err for err in validation.errors)


def test_validate_response_ignores_non_claim_percentage_numeric_density():
    validation, _ = _validate_response_content(
        content="Uncertainty bounds are 95% CI, 90% CI, and 85% CI for the cohort.",
        context_docs=[],
    )

    assert validation.valid
    assert not any("quantitative-claim-without-evidence" in err for err in validation.errors)


def test_validate_response_flags_unmatched_numeric_citation():
    validation, _ = _validate_response_content(
        content="Recommendation is supported by [1].",
        context_docs=[],
    )

    assert not validation.valid
    assert any(err.startswith("citation_mismatch:") for err in validation.errors)


def test_validate_response_flags_unmatched_numeric_citation_in_comma_list():
    validation, _ = _validate_response_content(
        content="Recommendation is supported by [1, 3].",
        context_docs=[SimpleNamespace(doc_id="1", source_id=None)],
    )

    assert not validation.valid
    assert "citation_mismatch:[3]" in validation.errors


def test_validate_response_flags_unmatched_numeric_citation_in_range():
    validation, _ = _validate_response_content(
        content="Recommendation is supported by [1-3].",
        context_docs=[SimpleNamespace(doc_id="1", source_id=None)],
    )

    assert not validation.valid
    assert "citation_mismatch:[2]" in validation.errors
    assert "citation_mismatch:[3]" in validation.errors


def test_validate_response_flags_unmatched_numeric_citation_in_mixed_group():
    validation, _ = _validate_response_content(
        content="Recommendation is supported by [1;2,4-5].",
        context_docs=[SimpleNamespace(doc_id="1", source_id=None), SimpleNamespace(doc_id="2", source_id=None)],
    )

    assert not validation.valid
    assert "citation_mismatch:[4]" in validation.errors
    assert "citation_mismatch:[5]" in validation.errors


def test_validate_response_does_not_flag_year_like_bracketed_number_as_citation():
    validation, _ = _validate_response_content(
        content="The trial season in [2024] had normal rainfall patterns.",
        context_docs=[],
    )

    assert validation.valid
    assert not any(err.startswith("citation_mismatch:") for err in validation.errors)


def test_validate_response_flags_percentage_without_calc_ids():
    validation, _ = _validate_response_content(
        content="Achieved 95% yield improvement in comparative trials.",
        context_docs=[],
    )

    assert not validation.valid
    assert any(err.startswith("percentage_without_calc:") for err in validation.errors)


def test_validate_response_does_not_flag_ci_percentage_without_calc_ids():
    validation, _ = _validate_response_content(
        content="Estimated interval is 95% CI for the observed trend.",
        context_docs=[],
    )

    assert validation.valid
    assert not any(err.startswith("percentage_without_calc:") for err in validation.errors)


def test_build_safe_failure_payload_defaults_to_empty_lists():
    payload = _build_safe_failure_payload(error_category="insufficient_evidence")

    assert payload["error_category"] == "insufficient_evidence"
    assert payload["searched"] == []
    assert payload["missing"] == []
    assert payload["next_steps"] == []


def test_build_safe_failure_payload_preserves_actionable_next_steps_content():
    payload = _build_safe_failure_payload(
        error_category="insufficient_evidence",
        searched=["retrieved_context"],
        missing=["grounded evidence"],
        next_steps=["Narrow query scope and retry."],
    )

    assert len(payload["next_steps"]) > 0
    assert all(isinstance(step, str) and step.strip() for step in payload["next_steps"])
    assert len(payload["searched"]) > 0
    assert len(payload["missing"]) > 0


def test_build_safe_failure_payload_preserves_custom_fields():
    payload = _build_safe_failure_payload(
        error_category="policy_blocked",
        searched=["trial_records", "weather_history"],
        missing=["authorized_scope"],
        next_steps=["Request access and retry."],
    )

    assert payload == {
        "error_category": "policy_blocked",
        "searched": ["trial_records", "weather_history"],
        "missing": ["authorized_scope"],
        "next_steps": ["Request access and retry."],
    }


class TestChatPolicyValidationEndpoint:
    """Contract tests for non-stream /chat policy-validation payloads."""

    @pytest.fixture
    def client(self):
        from app.api.deps import get_current_user
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
        with patch("app.api.v2.chat.get_llm_service") as mock:
            service = SimpleNamespace()

            async def mock_chat(*args, **kwargs):
                return SimpleNamespace(
                    content="Yield improved from 10 to 18 and confidence is 95%.",
                    provider=SimpleNamespace(value="template"),
                    model="template-v1",
                    model_confirmed=True,
                    cached=False,
                    latency_ms=1.23,
                )

            service.chat = mock_chat
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_breeding_service(self):
        with patch("app.api.v2.chat.get_breeding_service") as mock:
            service = SimpleNamespace()

            async def mock_search(*args, **kwargs):
                return []

            service.search_breeding_knowledge = mock_search
            mock.return_value = service
            yield service

    @pytest.fixture(autouse=True)
    def _apply_service_mocks(self, mock_llm_service, mock_breeding_service):
        return None

    def test_chat_policy_validation_emits_actionable_safe_failure_on_invalid_response(self, client):
        invalid_validation = SimpleNamespace(valid=False, errors=["unsupported claim"])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def mock_detect_function_call(*args, **kwargs):
            return None

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(invalid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Summarize recent yield changes", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=True)
        assert validation_payload.get("valid") is False
        assert validation_payload.get("error_count") == 1
        assert_actionable_safe_failure_payload(
            validation_payload.get("safe_failure"),
            error_category="insufficient_evidence",
        )

    def test_chat_function_path_policy_validation_emits_actionable_safe_failure(self, client):
        function_call = SimpleNamespace(
            name="search_trials",
            parameters={"crop": "rice"},
            to_dict=lambda: {"name": "search_trials", "parameters": {"crop": "rice"}},
        )
        invalid_validation = SimpleNamespace(valid=False, errors=["unsupported claim"])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
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
                "/api/v2/chat",
                json={"message": "Show rice trials", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}
        safe_failure = validation_payload.get("safe_failure")

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=True)
        assert payload.get("function_call", {}).get("name") == "search_trials"
        assert payload.get("function_result", {}).get("success") is True
        assert validation_payload.get("valid") is False
        assert_actionable_safe_failure_payload(
            safe_failure,
            error_category="insufficient_evidence",
        )

    def test_chat_policy_validation_omits_safe_failure_when_response_is_valid(self, client):
        valid_validation = SimpleNamespace(valid=True, errors=[])
        evidence_pack = SimpleNamespace(evidence_refs={"doc-1"}, calculation_ids=set())

        async def mock_detect_function_call(*args, **kwargs):
            return None

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Summarize verified yield outcomes", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_valid_policy_keeps_llm_message_and_omits_safe_failure(self, client):
        function_call = SimpleNamespace(
            name="search_trials",
            parameters={"crop": "rice"},
            to_dict=lambda: {"name": "search_trials", "parameters": {"crop": "rice"}},
        )
        valid_validation = SimpleNamespace(valid=True, errors=[])
        evidence_pack = SimpleNamespace(evidence_refs={"doc-1"}, calculation_ids=set())

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
            }

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ), patch(
            "app.api.v2.chat._validate_response_content",
            return_value=(valid_validation, evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show rice trials", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("function_call", {}).get("name") == "search_trials"
        assert payload.get("function_result", {}).get("success") is True
        assert payload.get("message") == "Yield improved from 10 to 18 and confidence is 95%."
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload
