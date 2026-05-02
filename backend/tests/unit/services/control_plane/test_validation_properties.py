"""
Property-based tests for Control Plane domain validation.

Uses Hypothesis to validate correctness properties from the design spec.

Feature: control-plane-kernel-extraction
**Validates: Requirements 7.1**

Property 4: Board Validation Correctness — validation functions correctly
accept valid inputs and reject invalid inputs.
"""

from __future__ import annotations

import string

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.control_plane.domain.validation import (
    DomainValidationError,
    DuplicateJobIdError,
    require_ascii_text,
    require_ascii_text_list,
    optional_ascii_text,
    best_effort_ascii_text,
    validate_queue_payload_shape,
    validate_queue_entry,
    validate_completion_payload,
    build_closeout_receipt_contract,
    QUEUE_LANGUAGE,
    QUEUE_VOCABULARY_POLICY,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty ASCII printable strings (valid for require_ascii_text)
_ascii_text_st = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
        whitelist_characters=" ",
        max_codepoint=127,
    ),
    min_size=1,
    max_size=80,
).filter(lambda s: s.strip() != "" and s.isascii())

# Non-ASCII strings (contain at least one non-ASCII character)
_non_ascii_text_st = st.text(
    alphabet=st.characters(min_codepoint=128, max_codepoint=1000),
    min_size=1,
    max_size=40,
)

# Whitespace-only strings
_whitespace_st = st.sampled_from(["", " ", "  ", "\t", "\n", "  \t\n  "])

# Non-string values
_non_string_st = st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.booleans(),
    st.lists(st.integers(), max_size=3),
    st.just(None),
)

# Field name for validation error messages
_field_name_st = st.text(
    alphabet=string.ascii_lowercase + "_",
    min_size=1,
    max_size=20,
)


def _valid_queue_entry_st(existing_job_ids: set[str] | None = None):
    """Strategy that produces a valid queue entry dict."""
    job_id = _ascii_text_st.filter(
        lambda s: existing_job_ids is None or s not in existing_job_ids
    )
    return st.fixed_dictionaries({
        "jobId": job_id,
        "title": _ascii_text_st,
        "status": st.just("queued"),
        "priority": st.just("p2"),
        "primaryAgent": _ascii_text_st,
        "supportAgents": st.lists(_ascii_text_st, min_size=0, max_size=3),
        "executionMode": st.just("same-control-plane"),
        "autonomousTrigger": st.just({
            "type": "overnight-window",
            "window": "nightly",
            "enabled": True,
        }),
        "dependsOn": st.just([]),
        "goal": _ascii_text_st,
        "lane": st.fixed_dictionaries({
            "objective": _ascii_text_st,
            "inputs": st.lists(_ascii_text_st, min_size=0, max_size=3),
            "outputs": st.lists(_ascii_text_st, min_size=0, max_size=3),
            "dependencies": st.lists(_ascii_text_st, min_size=0, max_size=3),
            "completion_criteria": st.lists(_ascii_text_st, min_size=1, max_size=3),
        }),
        "successCriteria": st.lists(_ascii_text_st, min_size=1, max_size=3),
        "verification": st.fixed_dictionaries({
            "commands": st.lists(_ascii_text_st, min_size=0, max_size=3),
            "stateRefreshRequired": st.just(True),
        }),
    })


def _valid_queue_payload_st():
    """Strategy that produces a valid queue payload dict."""
    return st.fixed_dictionaries({
        "language": st.just(QUEUE_LANGUAGE),
        "vocabularyPolicy": st.just(QUEUE_VOCABULARY_POLICY),
        "defaults": st.fixed_dictionaries({
            "priority": st.just("p2"),
        }),
        "jobs": st.just([]),
    })


# ---------------------------------------------------------------------------
# Property 4: Board Validation Correctness
# ---------------------------------------------------------------------------


class TestRequireAsciiText:
    """Property 4a: require_ascii_text accepts valid ASCII, rejects invalid."""

    @given(value=_ascii_text_st, field=_field_name_st)
    @settings(max_examples=100)
    def test_accepts_valid_ascii_strings(self, value: str, field: str):
        """**Validates: Requirements 7.1**

        For any non-empty ASCII string, require_ascii_text returns the string.
        """
        result = require_ascii_text(value, field)
        assert result == value

    @given(value=_non_ascii_text_st, field=_field_name_st)
    @settings(max_examples=100)
    def test_rejects_non_ascii_strings(self, value: str, field: str):
        """**Validates: Requirements 7.1**

        For any string containing non-ASCII characters, require_ascii_text
        raises DomainValidationError with status 400.
        """
        with pytest.raises(DomainValidationError) as exc_info:
            require_ascii_text(value, field)
        assert exc_info.value.status_code == 400
        assert field in str(exc_info.value.detail)

    @given(value=_whitespace_st, field=_field_name_st)
    @settings(max_examples=20)
    def test_rejects_empty_or_whitespace(self, value: str, field: str):
        """**Validates: Requirements 7.1**

        Empty or whitespace-only strings are rejected.
        """
        with pytest.raises(DomainValidationError) as exc_info:
            require_ascii_text(value, field)
        assert exc_info.value.status_code == 400

    @given(value=_non_string_st, field=_field_name_st)
    @settings(max_examples=50)
    def test_rejects_non_string_values(self, value, field: str):
        """**Validates: Requirements 7.1**

        Non-string values (int, float, bool, list, None) are rejected.
        """
        with pytest.raises(DomainValidationError) as exc_info:
            require_ascii_text(value, field)
        assert exc_info.value.status_code == 400


class TestRequireAsciiTextList:
    """Property 4b: require_ascii_text_list accepts valid lists, rejects invalid."""

    @given(
        items=st.lists(_ascii_text_st, min_size=0, max_size=10),
        field=_field_name_st,
    )
    @settings(max_examples=100)
    def test_accepts_valid_ascii_lists(self, items: list[str], field: str):
        """**Validates: Requirements 7.1**

        For any list of non-empty ASCII strings, require_ascii_text_list
        returns the list unchanged.
        """
        result = require_ascii_text_list(items, field)
        assert result == items

    @given(
        items=st.lists(_ascii_text_st, min_size=2, max_size=10),
        field=_field_name_st,
    )
    @settings(max_examples=50)
    def test_rejects_list_below_min_items(self, items: list[str], field: str):
        """**Validates: Requirements 7.1**

        When min_items is larger than the list, validation fails.
        """
        min_items = len(items) + 1
        with pytest.raises(DomainValidationError) as exc_info:
            require_ascii_text_list(items, field, min_items=min_items)
        assert exc_info.value.status_code == 400

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False),
            st.booleans(),
            st.just(None),
            st.text(min_size=1, max_size=10),
        ),
        field=_field_name_st,
    )
    @settings(max_examples=50)
    def test_rejects_non_list_values(self, value, field: str):
        """**Validates: Requirements 7.1**

        Non-list values (int, float, bool, None, str) are rejected.
        """
        with pytest.raises(DomainValidationError) as exc_info:
            require_ascii_text_list(value, field)
        assert exc_info.value.status_code == 400

    @given(
        valid_items=st.lists(_ascii_text_st, min_size=0, max_size=3),
        bad_item=_non_ascii_text_st,
        field=_field_name_st,
    )
    @settings(max_examples=50)
    def test_rejects_list_with_non_ascii_item(
        self, valid_items: list[str], bad_item: str, field: str
    ):
        """**Validates: Requirements 7.1**

        A list containing a non-ASCII item is rejected.
        """
        items = valid_items + [bad_item]
        with pytest.raises(DomainValidationError) as exc_info:
            require_ascii_text_list(items, field)
        assert exc_info.value.status_code == 400


class TestOptionalAndBestEffortAscii:
    """Property 4c: optional_ascii_text and best_effort_ascii_text edge cases."""

    @given(value=_ascii_text_st, field=_field_name_st)
    @settings(max_examples=50)
    def test_optional_accepts_valid_ascii(self, value: str, field: str):
        """**Validates: Requirements 7.1**"""
        result = optional_ascii_text(value, field)
        assert result == value

    @given(field=_field_name_st)
    @settings(max_examples=10)
    def test_optional_accepts_none(self, field: str):
        """**Validates: Requirements 7.1**"""
        assert optional_ascii_text(None, field) is None

    @given(value=_ascii_text_st)
    @settings(max_examples=50)
    def test_best_effort_returns_stripped_ascii(self, value: str):
        """**Validates: Requirements 7.1**

        best_effort_ascii_text returns stripped value for valid ASCII.
        """
        result = best_effort_ascii_text(value)
        assert result == value.strip()

    @given(value=_non_ascii_text_st)
    @settings(max_examples=50)
    def test_best_effort_returns_none_for_non_ascii(self, value: str):
        """**Validates: Requirements 7.1**

        best_effort_ascii_text returns None for non-ASCII strings (never raises).
        """
        result = best_effort_ascii_text(value)
        assert result is None

    @given(value=_non_string_st)
    @settings(max_examples=30)
    def test_best_effort_returns_none_for_non_strings(self, value):
        """**Validates: Requirements 7.1**

        best_effort_ascii_text returns None for non-string values (never raises).
        """
        result = best_effort_ascii_text(value)
        assert result is None


class TestValidateQueuePayloadShape:
    """Property 4d: validate_queue_payload_shape accepts valid payloads, rejects malformed."""

    @given(payload=_valid_queue_payload_st())
    @settings(max_examples=100)
    def test_accepts_valid_queue_payloads(self, payload: dict):
        """**Validates: Requirements 7.1**

        For any payload with correct language, vocabularyPolicy, defaults dict,
        and jobs list, validation passes and returns the payload.
        """
        result = validate_queue_payload_shape(payload)
        assert result is payload

    @given(payload=_valid_queue_payload_st())
    @settings(max_examples=30)
    def test_rejects_wrong_language(self, payload: dict):
        """**Validates: Requirements 7.1**"""
        payload["language"] = "fr"
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_payload_shape(payload)
        assert exc_info.value.status_code == 500

    @given(payload=_valid_queue_payload_st())
    @settings(max_examples=30)
    def test_rejects_wrong_vocabulary_policy(self, payload: dict):
        """**Validates: Requirements 7.1**"""
        payload["vocabularyPolicy"] = "any-language"
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_payload_shape(payload)
        assert exc_info.value.status_code == 500

    @given(payload=_valid_queue_payload_st())
    @settings(max_examples=30)
    def test_rejects_non_dict_defaults(self, payload: dict):
        """**Validates: Requirements 7.1**"""
        payload["defaults"] = "not-a-dict"
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_payload_shape(payload)
        assert exc_info.value.status_code == 500

    @given(payload=_valid_queue_payload_st())
    @settings(max_examples=30)
    def test_rejects_non_list_jobs(self, payload: dict):
        """**Validates: Requirements 7.1**"""
        payload["jobs"] = "not-a-list"
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_payload_shape(payload)
        assert exc_info.value.status_code == 500


class TestValidateQueueEntry:
    """Property 4e: validate_queue_entry accepts valid entries, rejects invalid."""

    @given(entry=_valid_queue_entry_st())
    @settings(max_examples=100)
    def test_accepts_valid_queue_entries(self, entry: dict):
        """**Validates: Requirements 7.1**

        For any well-formed queue entry with all required fields and correct
        fixed values, validation passes and returns a validated dict.
        """
        result = validate_queue_entry(entry, existing_job_ids=set())
        assert result["jobId"] == entry["jobId"]
        assert result["status"] == "queued"
        assert result["priority"] == "p2"
        assert result["executionMode"] == "same-control-plane"
        assert result["autonomousTrigger"]["type"] == "overnight-window"
        assert result["verification"]["stateRefreshRequired"] is True

    @given(entry=_valid_queue_entry_st())
    @settings(max_examples=50)
    def test_rejects_duplicate_job_id(self, entry: dict):
        """**Validates: Requirements 7.1**

        When the job ID already exists, DuplicateJobIdError is raised.
        """
        existing = {entry["jobId"]}
        with pytest.raises(DuplicateJobIdError) as exc_info:
            validate_queue_entry(entry, existing_job_ids=existing)
        assert exc_info.value.job_id == entry["jobId"]
        assert exc_info.value.status_code == 409

    @given(
        entry=_valid_queue_entry_st(),
        missing_key=st.sampled_from([
            "jobId", "title", "status", "priority", "primaryAgent",
            "supportAgents", "executionMode", "autonomousTrigger",
            "dependsOn", "goal", "lane", "successCriteria", "verification",
        ]),
    )
    @settings(max_examples=100)
    def test_rejects_missing_required_keys(self, entry: dict, missing_key: str):
        """**Validates: Requirements 7.1**

        Removing any required key causes validation to fail.
        """
        del entry[missing_key]
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_entry(entry, existing_job_ids=set())
        assert exc_info.value.status_code == 400

    @given(entry=_valid_queue_entry_st())
    @settings(max_examples=30)
    def test_rejects_wrong_status(self, entry: dict):
        """**Validates: Requirements 7.1**"""
        entry["status"] = "running"
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_entry(entry, existing_job_ids=set())
        assert exc_info.value.status_code == 400

    @given(entry=_valid_queue_entry_st())
    @settings(max_examples=30)
    def test_rejects_wrong_execution_mode(self, entry: dict):
        """**Validates: Requirements 7.1**"""
        entry["executionMode"] = "remote"
        with pytest.raises(DomainValidationError) as exc_info:
            validate_queue_entry(entry, existing_job_ids=set())
        assert exc_info.value.status_code == 400


class TestValidateCompletionPayload:
    """Property 4f: validate_completion_payload accepts valid payloads, rejects invalid."""

    @given(
        source_lane_id=_ascii_text_st,
        queue_job_id=_ascii_text_st,
        closure_summary=_ascii_text_st,
        evidence=st.lists(_ascii_text_st, min_size=1, max_size=5),
    )
    @settings(max_examples=100)
    def test_accepts_valid_completion_payloads(
        self,
        source_lane_id: str,
        queue_job_id: str,
        closure_summary: str,
        evidence: list[str],
    ):
        """**Validates: Requirements 7.1**

        For any valid completion payload with ASCII fields and at least one
        evidence item, validation passes and returns a validated dict.
        """

        class FakePayload:
            pass

        payload = FakePayload()
        payload.source_lane_id = source_lane_id
        payload.queue_job_id = queue_job_id
        payload.closure_summary = closure_summary
        payload.evidence = evidence
        payload.closeout_receipt = None

        result = validate_completion_payload(payload)
        assert result["source_lane_id"] == source_lane_id
        assert result["queue_job_id"] == queue_job_id
        assert result["closure_summary"] == closure_summary
        assert result["evidence"] == evidence
        assert result["closeout_receipt"] is None

    @given(
        source_lane_id=_ascii_text_st,
        queue_job_id=_ascii_text_st,
        closure_summary=_ascii_text_st,
    )
    @settings(max_examples=50)
    def test_rejects_empty_evidence_list(
        self,
        source_lane_id: str,
        queue_job_id: str,
        closure_summary: str,
    ):
        """**Validates: Requirements 7.1**

        Completion payload with empty evidence list is rejected (min_items=1).
        """

        class FakePayload:
            pass

        payload = FakePayload()
        payload.source_lane_id = source_lane_id
        payload.queue_job_id = queue_job_id
        payload.closure_summary = closure_summary
        payload.evidence = []
        payload.closeout_receipt = None

        with pytest.raises(DomainValidationError) as exc_info:
            validate_completion_payload(payload)
        assert exc_info.value.status_code == 400

    @given(
        queue_job_id=_ascii_text_st,
        closure_summary=_ascii_text_st,
        evidence=st.lists(_ascii_text_st, min_size=1, max_size=3),
        bad_lane_id=_non_ascii_text_st,
    )
    @settings(max_examples=50)
    def test_rejects_non_ascii_source_lane_id(
        self,
        queue_job_id: str,
        closure_summary: str,
        evidence: list[str],
        bad_lane_id: str,
    ):
        """**Validates: Requirements 7.1**

        Non-ASCII source_lane_id is rejected.
        """

        class FakePayload:
            pass

        payload = FakePayload()
        payload.source_lane_id = bad_lane_id
        payload.queue_job_id = queue_job_id
        payload.closure_summary = closure_summary
        payload.evidence = evidence
        payload.closeout_receipt = None

        with pytest.raises(DomainValidationError) as exc_info:
            validate_completion_payload(payload)
        assert exc_info.value.status_code == 400

    @given(
        source_lane_id=_ascii_text_st,
        queue_job_id=_ascii_text_st,
        closure_summary=_ascii_text_st,
        evidence=st.lists(_ascii_text_st, min_size=1, max_size=3),
        receipt_job_id=_ascii_text_st,
        artifact_paths=st.lists(_ascii_text_st, min_size=0, max_size=3),
    )
    @settings(max_examples=100)
    def test_accepts_valid_completion_with_closeout_receipt(
        self,
        source_lane_id: str,
        queue_job_id: str,
        closure_summary: str,
        evidence: list[str],
        receipt_job_id: str,
        artifact_paths: list[str],
    ):
        """**Validates: Requirements 7.1**

        Completion payload with a valid closeout_receipt is accepted.
        """

        class FakeReceipt:
            pass

        class FakePayload:
            pass

        receipt = FakeReceipt()
        receipt.queue_job_id = receipt_job_id
        receipt.artifact_paths = artifact_paths
        receipt.mission_id = None
        receipt.producer_key = None
        receipt.source_lane_id = None
        receipt.source_board_concurrency_token = None
        receipt.runtime_profile_id = None
        receipt.runtime_policy_sha256 = None
        receipt.closeout_status = None
        receipt.state_refresh_required = None
        receipt.receipt_recorded_at = None
        receipt.verification_evidence_ref = None
        receipt.queue_sha256_at_closeout = None

        payload = FakePayload()
        payload.source_lane_id = source_lane_id
        payload.queue_job_id = queue_job_id
        payload.closure_summary = closure_summary
        payload.evidence = evidence
        payload.closeout_receipt = receipt

        result = validate_completion_payload(payload)
        assert result["closeout_receipt"] is not None
        assert result["closeout_receipt"]["queue_job_id"] == receipt_job_id
        assert result["closeout_receipt"]["artifact_paths"] == artifact_paths
