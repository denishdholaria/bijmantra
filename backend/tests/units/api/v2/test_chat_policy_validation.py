"""Unit tests for REEVU chat policy validation helpers."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.v2.chat import (
    _build_evidence_pack,
    _build_safe_failure_payload,
    _extract_claims_for_validation,
    _validate_response_content,
    get_reevu_service,
)
from tests.utils.safe_failure_assertions import assert_actionable_safe_failure_payload


CHAT_RESPONSE_REQUIRED_FIELDS = {
    "request_id",
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
    assert isinstance(payload["request_id"], str)
    assert payload["context"] is None or isinstance(payload["context"], list)
    assert payload["conversation_id"] is None or isinstance(payload["conversation_id"], str)
    assert payload["suggestions"] is None or isinstance(payload["suggestions"], list)
    assert isinstance(payload["cached"], bool)
    assert payload["latency_ms"] is None or isinstance(payload["latency_ms"], int | float)
    assert isinstance(payload["policy_validation"], dict)
    assert isinstance(payload["evidence_envelope"], dict)


def _assert_function_chat_trace_contract(payload: dict) -> None:
    """Function-backed chat responses should keep execution-trace fields stable."""

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


def test_build_evidence_pack_collects_nested_contract_refs_and_steps():
    function_result = {
        "calculation_method_refs": ["fn:trial_summary.mean"],
        "evidence_envelope": {
            "evidence_refs": [
                {"entity_id": "db:trial:TRIAL-22"},
                {"entity_id": "db:observation:OBS-1"},
            ],
            "calculation_steps": [
                {"step_id": "fn:trial_summary.mean"},
                {"step_id": "calc:trial:yield_mean"},
            ],
        },
    }

    evidence_pack = _build_evidence_pack(context_docs=[], function_result=function_result)

    assert {"db:trial:TRIAL-22", "db:observation:OBS-1"}.issubset(evidence_pack.evidence_refs)
    assert {"fn:trial_summary.mean", "calc:trial:yield_mean"}.issubset(
        evidence_pack.calculation_ids
    )


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


def test_validate_response_accepts_trial_summary_contract_method_refs_and_nested_refs():
    validation, evidence_pack = _validate_response_content(
        content=(
            "Trial mean improved by 12.4% yield [[calc:fn:trial_summary.mean]] "
            "with supporting trial evidence [[ref:db:trial:TRIAL-22]]."
        ),
        context_docs=None,
        function_call_name="get_trial_results",
        function_result={
            "calculation_method_refs": ["fn:trial_summary.mean"],
            "evidence_envelope": {
                "evidence_refs": [{"entity_id": "db:trial:TRIAL-22"}],
                "calculation_steps": [{"step_id": "fn:trial_summary.mean"}],
            },
        },
    )

    assert validation.valid is True
    assert validation.errors == ()
    assert "fn:trial_summary.mean" in evidence_pack.calculation_ids
    assert "db:trial:TRIAL-22" in evidence_pack.evidence_refs


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
    def client(self, mock_breeding_service):
        from app.api.deps import get_current_user, get_db
        from app.api.v2.chat import get_breeding_service, router

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
        invalid_validation = SimpleNamespace(valid=False, errors=["claim[0] has no supporting evidence"])
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
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=True)
        assert payload.get("retrieval_audit") == {
            "services": [],
            "entities": {"query": "Summarize recent yield changes"},
        }
        assert payload["plan_execution_summary"]["total_steps"] == len(
            payload["plan_execution_summary"]["steps"]
        )
        assert validation_payload.get("valid") is False
        assert validation_payload.get("error_count") == 1
        assert "missing_evidence" in payload["evidence_envelope"]["policy_flags"]
        assert "missing_evidence" in payload["evidence_envelope"]["missing_evidence_signals"]
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
        invalid_validation = SimpleNamespace(valid=False, errors=["claim[0] has no supporting evidence"])
        empty_evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "search_trials",
                "result_type": "result",
                "data": {"total": 2},
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
        assert payload.get("retrieval_audit") == {
            "services": ["trial_search_service.search"],
            "entities": {"crop": "rice"},
        }
        assert payload.get("plan_execution_summary", {}).get("plan_id") == "plan-1"
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
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("function_call", {}).get("name") == "search_trials"
        assert payload.get("function_result", {}).get("success") is True
        assert payload.get("retrieval_audit") == {
            "services": ["trial_search_service.search"],
            "entities": {"crop": "rice"},
        }
        assert payload.get("plan_execution_summary", {}).get("plan_id") == "plan-1"
        assert payload.get("message") == "Yield improved from 10 to 18 and confidence is 95%."
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert payload["evidence_envelope"]["missing_evidence_signals"] == []
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_grounded_function_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="cross_domain_query",
            parameters={"trait": "blast resistance"},
            to_dict=lambda: {"name": "cross_domain_query", "parameters": {"trait": "blast resistance"}},
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                },
            }

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when a deterministic function message exists")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Compare blast resistance evidence across breeding and genomics", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Cross-domain evidence matched the requested breeding and genomics scope."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:cross_domain_query"
        assert payload.get("function_call", {}).get("name") == "cross_domain_query"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_germplasm_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_germplasm",
            parameters={"crop": "rice", "query": "blast tolerance", "trait": "yield"},
            to_dict=lambda: {
                "name": "search_germplasm",
                "parameters": {"crop": "rice", "query": "blast tolerance", "trait": "yield"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when germplasm search data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find rice germplasm with blast tolerance", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Found 1 germplasm records matching 'rice blast tolerance'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_germplasm"
        assert payload.get("function_call", {}).get("name") == "search_germplasm"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_germplasm_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_germplasm",
            parameters={"query": "rice"},
            to_dict=lambda: {
                "name": "search_germplasm",
                "parameters": {"query": "rice"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when germplasm search failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find rice germplasm", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to search germplasm database"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_germplasm"
        assert payload.get("function_call", {}).get("name") == "search_germplasm"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_trials_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_trials",
            parameters={"query": "late sowing", "crop": "rice"},
            to_dict=lambda: {
                "name": "search_trials",
                "parameters": {"query": "late sowing", "crop": "rice"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when trial search data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find late sowing rice trials", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Found 1 trials matching 'late sowing'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_trials"
        assert payload.get("function_call", {}).get("name") == "search_trials"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_trials_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_trials",
            parameters={"query": "rice"},
            to_dict=lambda: {
                "name": "search_trials",
                "parameters": {"query": "rice"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when trial search failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find rice trials", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to search trials database"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_trials"
        assert payload.get("function_call", {}).get("name") == "search_trials"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_crosses_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_crosses",
            parameters={"query": "IR64", "program": "P1"},
            to_dict=lambda: {
                "name": "search_crosses",
                "parameters": {"query": "IR64", "program": "P1"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when cross search data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find IR64 crosses in program P1", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Found 1 crosses matching 'IR64'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_crosses"
        assert payload.get("function_call", {}).get("name") == "search_crosses"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_crosses_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_crosses",
            parameters={"query": "IR64"},
            to_dict=lambda: {
                "name": "search_crosses",
                "parameters": {"query": "IR64"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when cross search failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find IR64 crosses", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to search crosses database"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_crosses"
        assert payload.get("function_call", {}).get("name") == "search_crosses"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_accessions_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="search_accessions",
            parameters={"query": "IR64", "country": "India"},
            to_dict=lambda: {
                "name": "search_accessions",
                "parameters": {"query": "IR64", "country": "India"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when accession search data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find IR64 accessions from India", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Found 1 accessions matching 'IR64'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_accessions"
        assert payload.get("function_call", {}).get("name") == "search_accessions"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_search_accessions_failure_message_over_llm_rewrite(
        self, client, mock_llm_service
    ):
        function_call = SimpleNamespace(
            name="search_accessions",
            parameters={"query": "IR64"},
            to_dict=lambda: {
                "name": "search_accessions",
                "parameters": {"query": "IR64"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when accession search failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Find IR64 accessions", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to search accessions database"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:search_accessions"
        assert payload.get("function_call", {}).get("name") == "search_accessions"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_extended_search_message_over_llm_rewrite(
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
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when search data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == function_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_extended_search_failure_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        error_message,
    ):
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when search failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == error_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_get_observations_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="get_observations",
            parameters={"trait": "Yield", "study_id": "101"},
            to_dict=lambda: {
                "name": "get_observations",
                "parameters": {"trait": "Yield", "study_id": "101"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when observations data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show Yield observations for study 101", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Found 1 observations for trait 'Yield'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_observations"
        assert payload.get("function_call", {}).get("name") == "get_observations"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_get_observations_failure_message_over_llm_rewrite(
        self, client, mock_llm_service
    ):
        function_call = SimpleNamespace(
            name="get_observations",
            parameters={"trait": "Yield"},
            to_dict=lambda: {
                "name": "get_observations",
                "parameters": {"trait": "Yield"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when observations failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show Yield observations", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to get observations"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_observations"
        assert payload.get("function_call", {}).get("name") == "get_observations"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_proposal_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        proposal_title,
        domains_involved,
    ):
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when proposal data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Proposal created successfully (ID: 321). Pending review."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_proposal_failure_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
    ):
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when proposal failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to create proposal"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_weather_forecast_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="get_weather_forecast",
            parameters={"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
            to_dict=lambda: {
                "name": "get_weather_forecast",
                "parameters": {"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when weather data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show a 3 day weather forecast for Ludhiana wheat", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Weather forecast for Ludhiana (3 days)"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_weather_forecast"
        assert payload.get("function_call", {}).get("name") == "get_weather_forecast"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_weather_forecast_failure_message_over_llm_rewrite(
        self, client, mock_llm_service
    ):
        function_call = SimpleNamespace(
            name="get_weather_forecast",
            parameters={"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
            to_dict=lambda: {
                "name": "get_weather_forecast",
                "parameters": {"location": "LOC-1", "location_name": "Ludhiana", "days": 3, "crop": "wheat"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
                "LLM rewrite should be skipped when weather failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show a 3 day weather forecast for Ludhiana wheat", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to get weather forecast"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_weather_forecast"
        assert payload.get("function_call", {}).get("name") == "get_weather_forecast"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_navigation_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="navigate_to",
            parameters={"page": "/trials", "filters": {"crop": "rice"}},
            to_dict=lambda: {
                "name": "navigate_to",
                "parameters": {"page": "/trials", "filters": {"crop": "rice"}},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when navigation data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Open the rice trials page", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Open /trials with the requested filters."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:navigate_to"
        assert payload.get("function_call", {}).get("name") == "navigate_to"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_export_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="export_data",
            parameters={"data_type": "germplasm", "format": "json", "query": "IR64", "limit": 5},
            to_dict=lambda: {
                "name": "export_data",
                "parameters": {"data_type": "germplasm", "format": "json", "query": "IR64", "limit": 5},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when export data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Export germplasm records for IR64 as JSON", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Exported 1 germplasm records in JSON format"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:export_data"
        assert payload.get("function_call", {}).get("name") == "export_data"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_export_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="export_data",
            parameters={"data_type": "unknown"},
            to_dict=lambda: {
                "name": "export_data",
                "parameters": {"data_type": "unknown"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when export failure already includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Export unknown records", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == (
            "Supported types: germplasm, trials, observations, crosses, locations, seedlots, traits, programs"
        )
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:export_data"
        assert payload.get("function_call", {}).get("name") == "export_data"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_seedlot_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="check_seed_viability",
            parameters={"seedlot_id": "SL-1"},
            to_dict=lambda: {
                "name": "check_seed_viability",
                "parameters": {"seedlot_id": "SL-1"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when seedlot data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Check seedlot SL-1 viability", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Checked viability for seedlot SL-1"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:check_seed_viability"
        assert payload.get("function_call", {}).get("name") == "check_seed_viability"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_seedlot_batch_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="check_seed_viability",
            parameters={"germplasm_id": "101"},
            to_dict=lambda: {
                "name": "check_seed_viability",
                "parameters": {"germplasm_id": "101"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when batch seedlot data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Check seed viability for germplasm 101", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Checked viability for 2 seedlots"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:check_seed_viability"
        assert payload.get("function_call", {}).get("name") == "check_seed_viability"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_seedlot_failure_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
        parameters,
        user_message,
        error_message,
        function_message,
        expected_message,
    ):
        function_call = SimpleNamespace(
            name="check_seed_viability",
            parameters=parameters,
            to_dict=lambda: {
                "name": "check_seed_viability",
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when helper failure already includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == expected_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:check_seed_viability"
        assert payload.get("function_call", {}).get("name") == "check_seed_viability"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_diversity_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="calculate_genetic_diversity",
            parameters={"population_id": "POP-1"},
            to_dict=lambda: {
                "name": "calculate_genetic_diversity",
                "parameters": {"population_id": "POP-1"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when diversity data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Calculate genetic diversity for population POP-1", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Calculated genetic diversity metrics for 12 samples across 48 loci."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:calculate_genetic_diversity"
        assert payload.get("function_call", {}).get("name") == "calculate_genetic_diversity"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_diversity_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="calculate_genetic_diversity",
            parameters={"population_id": "POP-1"},
            to_dict=lambda: {
                "name": "calculate_genetic_diversity",
                "parameters": {"population_id": "POP-1"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when diversity failure already includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Calculate genetic diversity for population POP-1", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to calculate genetic diversity"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:calculate_genetic_diversity"
        assert payload.get("function_call", {}).get("name") == "calculate_genetic_diversity"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_predict_cross_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="predict_cross",
            parameters={"parent1_id": "101", "parent2_id": "102", "trait": "Yield", "heritability": 0.5},
            to_dict=lambda: {
                "name": "predict_cross",
                "parameters": {
                    "parent1_id": "101",
                    "parent2_id": "102",
                    "trait": "Yield",
                    "heritability": 0.5,
                },
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when predict_cross data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Predict the cross outcome for IR64 and Swarna on yield", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Cross prediction: IR64 × Swarna"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:predict_cross"
        assert payload.get("function_call", {}).get("name") == "predict_cross"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_predict_cross_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="predict_cross",
            parameters={"parent1_id": "101"},
            to_dict=lambda: {
                "name": "predict_cross",
                "parameters": {"parent1_id": "101"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when predict_cross failure already includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Predict the cross outcome for IR64", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Please specify both parent IDs for cross prediction"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:predict_cross"
        assert payload.get("function_call", {}).get("name") == "predict_cross"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_analyze_gxe_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="analyze_gxe",
            parameters={"trait": "Yield", "method": "AMMI"},
            to_dict=lambda: {
                "name": "analyze_gxe",
                "parameters": {"trait": "Yield", "method": "AMMI"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when analyze_gxe data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Analyze GxE for yield", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "AMMI analysis: 3 genotypes × 2 environments for trait 'Yield'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:analyze_gxe"
        assert payload.get("function_call", {}).get("name") == "analyze_gxe"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_analyze_gxe_failure_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="analyze_gxe",
            parameters={"trait": "Yield", "method": "AMMI"},
            to_dict=lambda: {
                "name": "analyze_gxe",
                "parameters": {"trait": "Yield", "method": "AMMI"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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
            raise AssertionError("LLM rewrite should be skipped when analyze_gxe failure already includes deterministic copy")

        mock_llm_service.chat = fail_if_called

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
            return_value=(valid_validation, empty_evidence_pack),
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Analyze GxE for yield", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Need at least 6 observations for G×E analysis. Found 1 for trait 'Yield'"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:analyze_gxe"
        assert payload.get("function_call", {}).get("name") == "analyze_gxe"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_harvest_timing_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="predict_harvest_timing",
            parameters={"field_id": 17, "planting_date": "2026-07-01", "crop_name": "maize"},
            to_dict=lambda: {
                "name": "predict_harvest_timing",
                "parameters": {"field_id": 17, "planting_date": "2026-07-01", "crop_name": "maize"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when harvest timing data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "When should maize from field 17 planted on 2026-07-01 be harvested?", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Predicted harvest timing for maize planted on 2026-07-01."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:predict_harvest_timing"
        assert payload.get("function_call", {}).get("name") == "predict_harvest_timing"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_variety_recommendation_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="recommend_varieties_by_gdd",
            parameters={"field_id": 17},
            to_dict=lambda: {
                "name": "recommend_varieties_by_gdd",
                "parameters": {"field_id": 17},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when variety recommendations include deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Recommend varieties for field 17 using GDD", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Recommended 1 varieties for field 17 based on GDD suitability."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:recommend_varieties_by_gdd"
        assert payload.get("function_call", {}).get("name") == "recommend_varieties_by_gdd"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_planting_window_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="analyze_planting_windows",
            parameters={"field_id": 23, "crop_name": "maize"},
            to_dict=lambda: {
                "name": "analyze_planting_windows",
                "parameters": {"field_id": 23, "crop_name": "maize"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when planting-window data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Analyze maize planting windows for field 23", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Analyzed planting windows for maize in field 23."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:analyze_planting_windows"
        assert payload.get("function_call", {}).get("name") == "analyze_planting_windows"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_gdd_insight_data_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="get_gdd_insights",
            parameters={"field_id": 23, "insight_type": "planting"},
            to_dict=lambda: {
                "name": "get_gdd_insights",
                "parameters": {"field_id": 23, "insight_type": "planting"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when GDD insights include deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Give me GDD planting insights for field 23", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Generated planting GDD insights for field 23."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_gdd_insights"
        assert payload.get("function_call", {}).get("name") == "get_gdd_insights"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_gdd_helper_failure_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        error_message,
    ):
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "error": "gdd service unavailable",
                "message": error_message,
            }

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM rewrite should be skipped when GDD helper failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == error_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_detail_message_over_llm_rewrite(
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
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when detail data includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == expected_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_detail_failure_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
        function_name,
        parameters,
        user_message,
        error_message,
    ):
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {
                "name": function_name,
                "parameters": parameters,
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": function_name,
                "result_type": "details_error",
                "error": "lookup failed",
                "message": error_message,
            }

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM rewrite should be skipped when detail failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == error_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_statistics_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="get_statistics",
            parameters={},
            to_dict=lambda: {
                "name": "get_statistics",
                "parameters": {},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM rewrite should be skipped when get_statistics includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show overall database statistics", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == (
            "Database contains 3 programs, 21 germplasm, 7 trials, 33 observations, 11 seedlots, 9 traits"
        )
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_statistics"
        assert payload.get("function_call", {}).get("name") == "get_statistics"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_statistics_failure_message_over_llm_rewrite(
        self,
        client,
        mock_llm_service,
    ):
        function_call = SimpleNamespace(
            name="get_statistics",
            parameters={},
            to_dict=lambda: {
                "name": "get_statistics",
                "parameters": {},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": False,
                "function": "get_statistics",
                "error": "statistics temporarily unavailable",
                "message": "Failed to get database statistics",
            }

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM rewrite should be skipped when get_statistics failure already includes deterministic copy"
            )

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Show overall database statistics", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Failed to get database statistics"
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:get_statistics"
        assert payload.get("function_call", {}).get("name") == "get_statistics"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_comparison_context_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="compare_germplasm",
            parameters={"germplasm_ids": ["IR64", "Swarna"]},
            to_dict=lambda: {
                "name": "compare_germplasm",
                "parameters": {"germplasm_ids": ["IR64", "Swarna"]},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when comparison_context includes deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Compare IR64 and Swarna", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Compared IR64 and Swarna using the shared phenotype interpretation contract."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:compare_germplasm"
        assert payload.get("function_call", {}).get("name") == "compare_germplasm"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_function_path_prefers_breeding_value_message_over_llm_rewrite(self, client, mock_llm_service):
        function_call = SimpleNamespace(
            name="calculate_breeding_value",
            parameters={"trait": "yield", "method": "BLUP"},
            to_dict=lambda: {
                "name": "calculate_breeding_value",
                "parameters": {"trait": "yield", "method": "BLUP"},
            },
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

        async def mock_execute(*args, **kwargs):
            return {
                "success": True,
                "function": "calculate_breeding_value",
                "result_type": "breeding_values",
                "message": "Calculated heuristic BLUP breeding values for 3 individuals on trait 'yield' from 3 database observations.",
                "data": {
                    "method": "BLUP (Heuristic Approximation)",
                    "trait": "yield",
                    "n_individuals": 3,
                    "top_10": [
                        {"individual_id": "IR64", "ebv": 0.42, "reliability": 0.09},
                        {"individual_id": "Swarna", "ebv": 0.18, "reliability": 0.09},
                    ],
                },
                "retrieval_audit": {
                    "services": [
                        "observation_search_service.search",
                        "breeding_value_service.estimate_blup",
                    ],
                    "entities": {"trait": "yield", "method": "BLUP", "n_individuals": 3},
                },
                "plan_execution_summary": {
                    "plan_id": "plan-1",
                    "is_compound": False,
                    "domains_involved": ["analytics"],
                    "steps": [],
                    "total_steps": 0,
                },
            }

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when breeding-value results include deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": "Calculate breeding values for yield", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == "Calculated heuristic BLUP breeding values for 3 individuals on trait 'yield' from 3 database observations."
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == "function:calculate_breeding_value"
        assert payload.get("function_call", {}).get("name") == "calculate_breeding_value"
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_trusted_get_data_messages_over_llm_rewrite(
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
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {"name": function_name, "parameters": parameters},
        )

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM rewrite should be skipped when trusted get_* results include deterministic copy")

        mock_llm_service.chat = fail_if_called

        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            side_effect=mock_detect_function_call,
        ), patch(
            "app.api.v2.chat.FunctionExecutor.execute",
            side_effect=mock_execute,
        ):
            response = client.post(
                "/api/v2/chat",
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("message") == expected_message
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

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
    def test_chat_function_path_prefers_structured_safe_failure_over_llm_rewrite(
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
        function_call = SimpleNamespace(
            name=function_name,
            parameters=parameters,
            to_dict=lambda: {"name": function_name, "parameters": parameters},
        )
        valid_validation = SimpleNamespace(valid=True, errors=[])
        evidence_pack = SimpleNamespace(evidence_refs=set(), calculation_ids=set())

        async def mock_detect_function_call(*args, **kwargs):
            return function_call

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

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "LLM rewrite should be skipped when a structured safe_failure can be rendered deterministically"
            )

        mock_llm_service.chat = fail_if_called

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
                json={"message": user_message, "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_function_chat_trace_contract(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("provider") == "deterministic_function"
        assert payload.get("model") == f"function:{function_name}"
        assert payload.get("function_call", {}).get("name") == function_name
        assert payload.get("message") == expected_message
        assert payload.get("function_result", {}).get("safe_failure", {}).get("error_category") == (
            safe_failure_payload["error_category"]
        )
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
        assert "safe_failure" not in validation_payload

    def test_chat_blocked_internal_functiongemma_output_falls_back_without_execution(
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

        async def mock_chat(*args, **kwargs):
            return SimpleNamespace(
                content="Fallback response after blocked internal helper.",
                provider=SimpleNamespace(value="template"),
                model="template-v1",
                model_confirmed=True,
                cached=False,
                latency_ms=1.23,
            )

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "Blocked internal FunctionGemma helper should not execute through the chat route"
            )

        mock_llm_service.chat = mock_chat

        with patch.dict(
            "os.environ",
            {"HUGGINGFACE_API_KEY": "test-key"},
            clear=False,
        ), patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            return_value=None,
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
                "/api/v2/chat",
                json={"message": "Show database statistics", "include_context": False},
            )

        assert response.status_code == 200
        payload = response.json()
        validation_payload = payload.get("policy_validation") or {}

        _assert_chat_contract_fields(payload)
        _assert_chat_contract_types(payload)
        _assert_policy_validation_contract(validation_payload, safe_failure_expected=False)
        assert payload.get("provider") == "template"
        assert payload.get("model") == "template-v1"
        assert payload.get("message") == "Fallback response after blocked internal helper."
        assert payload.get("function_call") is None
        assert payload.get("function_result") is None
        assert validation_payload.get("valid") is True
        assert validation_payload.get("error_count") == 0
