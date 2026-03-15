"""Tests for shared safe-failure assertion utilities."""

import pytest

from tests.utils.safe_failure_assertions import assert_actionable_safe_failure_payload


def test_assert_actionable_safe_failure_payload_accepts_valid_payload():
    payload = {
        "error_category": "insufficient_evidence",
        "searched": ["retrieved_context"],
        "missing": ["grounded evidence"],
        "next_steps": ["Narrow query scope and retry."],
    }

    assert_actionable_safe_failure_payload(
        payload,
        error_category="insufficient_evidence",
    )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {
            "error_category": "insufficient_evidence",
            "searched": [],
            "missing": ["grounded evidence"],
            "next_steps": ["Retry"],
        },
        {
            "error_category": "insufficient_evidence",
            "searched": ["retrieved_context"],
            "missing": [],
            "next_steps": ["Retry"],
        },
        {
            "error_category": "insufficient_evidence",
            "searched": ["retrieved_context"],
            "missing": ["grounded evidence"],
            "next_steps": [],
        },
        {
            "error_category": "insufficient_evidence",
            "searched": ["retrieved_context"],
            "missing": ["grounded evidence"],
            "next_steps": ["   "],
        },
    ],
)
def test_assert_actionable_safe_failure_payload_rejects_non_actionable_payloads(payload):
    with pytest.raises(AssertionError):
        assert_actionable_safe_failure_payload(
            payload,
            error_category="insufficient_evidence",
        )
