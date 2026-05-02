"""
Property-based tests for Queue Hash Determinism.

Uses Hypothesis to validate that the SHA256 hash computed by
QueueMaterializer.queue_sha256 is deterministic, unique with high
probability, key-order independent, and always a valid 64-character
lowercase hex string.

Feature: control-plane-kernel-extraction
Property 3: Queue Hash Determinism

**Validates: Requirements 6.3**
"""

from __future__ import annotations

import hashlib
import json
import re
import string

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.control_plane.orchestration.queue_materializer import QueueMaterializer


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Scalar JSON values (no containers)
_json_scalar_st = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**31), max_value=2**31),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(
        alphabet=st.characters(max_codepoint=127, whitelist_categories=("L", "N", "P", "S", "Z")),
        min_size=0,
        max_size=40,
    ),
)

# Recursive JSON-like structures (dicts with string keys, lists, scalars)
_json_value_st = st.recursive(
    _json_scalar_st,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(
            st.text(
                alphabet=string.ascii_letters + string.digits + "_-",
                min_size=1,
                max_size=20,
            ),
            children,
            max_size=5,
        ),
    ),
    max_leaves=15,
)

# Queue-shaped payloads (closer to real queue structure)
_queue_payload_st = st.fixed_dictionaries({
    "version": st.just(1),
    "updatedAt": st.one_of(
        st.none(),
        st.text(
            alphabet=st.characters(max_codepoint=127, whitelist_categories=("L", "N", "P", "S", "Z")),
            min_size=1,
            max_size=30,
        ),
    ),
    "language": st.just("en"),
    "vocabularyPolicy": st.just("bijmantra-v1"),
    "defaults": st.fixed_dictionaries({
        "window": st.sampled_from(["nightly", "weekly", "manual"]),
        "stateRefreshRequired": st.booleans(),
        "closeoutCommands": st.lists(
            st.text(
                alphabet=st.characters(max_codepoint=127, whitelist_categories=("L", "N", "P", "S")),
                min_size=1,
                max_size=30,
            ),
            min_size=0,
            max_size=3,
        ),
        "maxJobsPerRun": st.integers(min_value=1, max_value=10),
    }),
    "jobs": st.lists(
        st.fixed_dictionaries({
            "jobId": st.text(
                alphabet=string.ascii_lowercase + string.digits + "-",
                min_size=1,
                max_size=30,
            ).filter(lambda s: s.strip() != ""),
            "title": st.text(
                alphabet=st.characters(max_codepoint=127, whitelist_categories=("L", "N", "P", "S")),
                min_size=1,
                max_size=40,
            ),
            "status": st.sampled_from(["queued", "running", "completed", "failed"]),
        }),
        min_size=0,
        max_size=3,
    ),
})

# Arbitrary dict payloads for general hash properties
_arbitrary_dict_st = st.dictionaries(
    st.text(
        alphabet=string.ascii_letters + string.digits + "_-",
        min_size=1,
        max_size=20,
    ),
    _json_value_st,
    min_size=0,
    max_size=8,
)


# ---------------------------------------------------------------------------
# Hex format regex
# ---------------------------------------------------------------------------

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# Property 3: Queue Hash Determinism
# ---------------------------------------------------------------------------


class TestQueueHashDeterminism:
    """Property 3a: Same payload always produces the same hash.

    **Validates: Requirements 6.3**
    """

    @given(payload=_queue_payload_st)
    @settings(max_examples=100)
    def test_same_queue_payload_produces_same_hash(self, payload: dict):
        """**Validates: Requirements 6.3**

        For any queue payload, calling queue_sha256 twice with the same
        payload SHALL produce identical hashes (determinism).
        """
        hash_1 = QueueMaterializer.queue_sha256(payload)
        hash_2 = QueueMaterializer.queue_sha256(payload)
        assert hash_1 == hash_2, (
            f"Determinism violated: same payload produced '{hash_1}' and '{hash_2}'"
        )

    @given(payload=_arbitrary_dict_st)
    @settings(max_examples=100)
    def test_same_arbitrary_dict_produces_same_hash(self, payload: dict):
        """**Validates: Requirements 6.3**

        For any arbitrary JSON-serializable dict, calling queue_sha256
        twice SHALL produce identical hashes.
        """
        hash_1 = QueueMaterializer.queue_sha256(payload)
        hash_2 = QueueMaterializer.queue_sha256(payload)
        assert hash_1 == hash_2


class TestQueueHashUniqueness:
    """Property 3b: Different payloads produce different hashes (with high probability).

    **Validates: Requirements 6.3**
    """

    @given(
        payload_a=_queue_payload_st,
        payload_b=_queue_payload_st,
    )
    @settings(max_examples=100)
    def test_different_payloads_produce_different_hashes(
        self, payload_a: dict, payload_b: dict
    ):
        """**Validates: Requirements 6.3**

        For any two queue payloads that serialize to different JSON,
        queue_sha256 SHALL produce different hashes.
        """
        serialized_a = json.dumps(payload_a, sort_keys=True, separators=(",", ":"))
        serialized_b = json.dumps(payload_b, sort_keys=True, separators=(",", ":"))
        assume(serialized_a != serialized_b)

        hash_a = QueueMaterializer.queue_sha256(payload_a)
        hash_b = QueueMaterializer.queue_sha256(payload_b)
        assert hash_a != hash_b, (
            f"Collision: different payloads produced same hash '{hash_a}'"
        )


class TestQueueHashKeyOrderIndependence:
    """Property 3c: Key ordering in the payload does not affect the hash.

    **Validates: Requirements 6.3**
    """

    @given(payload=_arbitrary_dict_st)
    @settings(max_examples=100)
    def test_key_order_does_not_affect_hash(self, payload: dict):
        """**Validates: Requirements 6.3**

        For any dict payload, reversing the key order SHALL produce the
        same hash, because queue_sha256 serializes with sort_keys=True.
        """
        reversed_payload = dict(reversed(list(payload.items())))
        hash_original = QueueMaterializer.queue_sha256(payload)
        hash_reversed = QueueMaterializer.queue_sha256(reversed_payload)
        assert hash_original == hash_reversed, (
            f"Key order affected hash: '{hash_original}' vs '{hash_reversed}'"
        )

    @given(
        keys=st.lists(
            st.text(
                alphabet=string.ascii_letters + string.digits,
                min_size=1,
                max_size=10,
            ),
            min_size=2,
            max_size=8,
            unique=True,
        ),
        values=st.lists(
            _json_scalar_st,
            min_size=2,
            max_size=8,
        ),
    )
    @settings(max_examples=100)
    def test_shuffled_keys_produce_same_hash(
        self, keys: list[str], values: list[str]
    ):
        """**Validates: Requirements 6.3**

        For any set of key-value pairs, constructing the dict in different
        key orders SHALL produce the same hash.
        """
        # Trim to same length
        n = min(len(keys), len(values))
        keys = keys[:n]
        values = values[:n]
        assume(n >= 2)

        payload_forward = dict(zip(keys, values))
        payload_backward = dict(zip(reversed(keys), reversed(values)))

        hash_forward = QueueMaterializer.queue_sha256(payload_forward)
        hash_backward = QueueMaterializer.queue_sha256(payload_backward)
        assert hash_forward == hash_backward


class TestQueueHashFormat:
    """Property 3d: The hash is always a valid 64-character lowercase hex string.

    **Validates: Requirements 6.3**
    """

    @given(payload=_queue_payload_st)
    @settings(max_examples=100)
    def test_hash_is_valid_sha256_hex(self, payload: dict):
        """**Validates: Requirements 6.3**

        For any queue payload, queue_sha256 SHALL return a 64-character
        lowercase hexadecimal string (valid SHA-256 digest).
        """
        result = QueueMaterializer.queue_sha256(payload)
        assert _SHA256_HEX_RE.match(result), (
            f"Hash '{result}' is not a valid 64-char lowercase hex string"
        )

    @given(payload=_arbitrary_dict_st)
    @settings(max_examples=100)
    def test_hash_format_for_arbitrary_dicts(self, payload: dict):
        """**Validates: Requirements 6.3**

        For any arbitrary JSON-serializable dict, queue_sha256 SHALL
        return a valid SHA-256 hex digest.
        """
        result = QueueMaterializer.queue_sha256(payload)
        assert len(result) == 64, f"Hash length is {len(result)}, expected 64"
        assert result == result.lower(), "Hash must be lowercase"
        assert all(c in string.hexdigits.lower() for c in result), (
            f"Hash contains non-hex characters: '{result}'"
        )

    @given(payload=_queue_payload_st)
    @settings(max_examples=50)
    def test_hash_matches_manual_sha256_computation(self, payload: dict):
        """**Validates: Requirements 6.3**

        For any queue payload, queue_sha256 SHALL produce the same result
        as manually computing SHA-256 over the sorted-keys compact JSON.
        """
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        expected = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        actual = QueueMaterializer.queue_sha256(payload)
        assert actual == expected, (
            f"Hash mismatch: expected '{expected}', got '{actual}'"
        )
