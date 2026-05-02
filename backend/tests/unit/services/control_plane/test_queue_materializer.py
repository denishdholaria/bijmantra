"""
Unit tests for Control Plane queue materializer orchestrator.

Tests queue loading, writing, job ID creation, and status response building
in ``app.control_plane.orchestration.queue_materializer``.

**Validates: Requirements 10.1**
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.control_plane.orchestration.queue_materializer import (
    QueueMaterializer,
    _OVERNIGHT_QUEUE_PATH,
)


# ---------------------------------------------------------------------------
# default_queue_payload
# ---------------------------------------------------------------------------


class TestDefaultQueuePayload:
    """Tests for QueueMaterializer.default_queue_payload."""

    def test_returns_dict_with_expected_keys(self):
        """Default payload has all required top-level keys."""
        payload = QueueMaterializer.default_queue_payload()
        expected_keys = {
            "version",
            "updatedAt",
            "language",
            "vocabularyPolicy",
            "defaults",
            "jobs",
        }
        assert set(payload.keys()) == expected_keys

    def test_version_is_one(self):
        """Default version is 1."""
        payload = QueueMaterializer.default_queue_payload()
        assert payload["version"] == 1

    def test_updated_at_is_none(self):
        """Default updatedAt is None (no writes yet)."""
        payload = QueueMaterializer.default_queue_payload()
        assert payload["updatedAt"] is None

    def test_language_is_en(self):
        """Default language is 'en'."""
        payload = QueueMaterializer.default_queue_payload()
        assert payload["language"] == "en"

    def test_vocabulary_policy(self):
        """Default vocabulary policy is english-technical-only."""
        payload = QueueMaterializer.default_queue_payload()
        assert payload["vocabularyPolicy"] == "english-technical-only"

    def test_jobs_is_empty_list(self):
        """Default jobs list is empty."""
        payload = QueueMaterializer.default_queue_payload()
        assert payload["jobs"] == []

    def test_defaults_has_expected_structure(self):
        """Default 'defaults' sub-object has expected keys and values."""
        payload = QueueMaterializer.default_queue_payload()
        defaults = payload["defaults"]
        assert defaults["window"] == "nightly"
        assert defaults["stateRefreshRequired"] is True
        assert defaults["closeoutCommands"] == ["make update-state"]
        assert defaults["maxJobsPerRun"] == 2

    def test_returns_fresh_dict_each_call(self):
        """Each call returns a new dict (no shared mutable state)."""
        a = QueueMaterializer.default_queue_payload()
        b = QueueMaterializer.default_queue_payload()
        assert a == b
        assert a is not b
        a["jobs"].append({"jobId": "test"})
        assert len(b["jobs"]) == 0


# ---------------------------------------------------------------------------
# queue_sha256
# ---------------------------------------------------------------------------


class TestQueueSha256:
    """Tests for QueueMaterializer.queue_sha256."""

    def test_produces_correct_sha256_hex_digest(self):
        """Hash matches manual SHA-256 of the same canonical serialization."""
        payload = {"version": 1, "jobs": []}
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        expected = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        assert QueueMaterializer.queue_sha256(payload) == expected

    def test_deterministic_same_input_same_output(self):
        """Calling twice with the same payload returns the same hash."""
        payload = {"version": 1, "updatedAt": "2026-04-15", "jobs": []}
        assert QueueMaterializer.queue_sha256(payload) == QueueMaterializer.queue_sha256(payload)

    def test_different_payloads_produce_different_hashes(self):
        """Two distinct payloads produce distinct hashes."""
        a = {"version": 1, "jobs": []}
        b = {"version": 2, "jobs": []}
        assert QueueMaterializer.queue_sha256(a) != QueueMaterializer.queue_sha256(b)

    def test_returns_lowercase_hex_string(self):
        """The digest is a 64-char lowercase hex string."""
        result = QueueMaterializer.queue_sha256({"version": 1})
        assert len(result) == 64
        assert result == result.lower()
        assert all(c in "0123456789abcdef" for c in result)

    def test_key_order_does_not_affect_hash(self):
        """sort_keys=True means key order in the input dict is irrelevant."""
        a = {"b": 2, "a": 1}
        b = {"a": 1, "b": 2}
        assert QueueMaterializer.queue_sha256(a) == QueueMaterializer.queue_sha256(b)


# ---------------------------------------------------------------------------
# load_overnight_queue_payload
# ---------------------------------------------------------------------------


class TestLoadOvernightQueuePayload:
    """Tests for QueueMaterializer.load_overnight_queue_payload."""

    def test_returns_payload_and_true_when_file_exists(self, tmp_path):
        """When the queue file exists with valid JSON, returns (payload, True)."""
        queue_file = tmp_path / "overnight-queue.json"
        payload = {"version": 1, "language": "en", "vocabularyPolicy": "english-technical-only", "jobs": []}
        queue_file.write_text(json.dumps(payload), encoding="utf-8")

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            queue_file,
        ):
            result, exists = QueueMaterializer.load_overnight_queue_payload()

        assert exists is True
        assert result == payload

    def test_returns_default_and_false_when_file_missing(self, tmp_path):
        """When the queue file does not exist, returns (default, False)."""
        missing_file = tmp_path / "nonexistent.json"

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            missing_file,
        ):
            result, exists = QueueMaterializer.load_overnight_queue_payload()

        assert exists is False
        default = QueueMaterializer.default_queue_payload()
        assert result["version"] == default["version"]
        assert result["jobs"] == default["jobs"]

    def test_handles_malformed_json_gracefully(self, tmp_path):
        """When the file contains invalid JSON, returns default with malformed flag."""
        queue_file = tmp_path / "overnight-queue.json"
        queue_file.write_text("not valid json {{{", encoding="utf-8")

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            queue_file,
        ):
            result, exists = QueueMaterializer.load_overnight_queue_payload()

        assert exists is False
        assert result["malformed_artifact"] is True
        assert "error" in result

    def test_handles_non_dict_json_gracefully(self, tmp_path):
        """When the file contains valid JSON but not a dict, returns default with malformed flag."""
        queue_file = tmp_path / "overnight-queue.json"
        queue_file.write_text("[1, 2, 3]", encoding="utf-8")

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            queue_file,
        ):
            result, exists = QueueMaterializer.load_overnight_queue_payload()

        assert exists is False
        assert result["malformed_artifact"] is True
        assert "must be a JSON object" in result["error"]


# ---------------------------------------------------------------------------
# serialize_queue_payload
# ---------------------------------------------------------------------------


class TestSerializeQueuePayload:
    """Tests for QueueMaterializer.serialize_queue_payload."""

    def test_produces_stable_json_with_expected_key_order(self):
        """Serialized output has keys in the canonical order."""
        payload = {
            "jobs": [{"jobId": "j1"}],
            "version": 1,
            "updatedAt": "2026-04-15",
            "language": "en",
            "vocabularyPolicy": "english-technical-only",
            "defaults": {"window": "nightly"},
        }
        result = QueueMaterializer.serialize_queue_payload(payload)
        parsed = json.loads(result)
        keys = list(parsed.keys())
        assert keys == [
            "version",
            "updatedAt",
            "language",
            "vocabularyPolicy",
            "defaults",
            "jobs",
        ]

    def test_ends_with_newline(self):
        """Serialized output ends with a trailing newline."""
        payload = QueueMaterializer.default_queue_payload()
        result = QueueMaterializer.serialize_queue_payload(payload)
        assert result.endswith("\n")

    def test_round_trips_through_json_parse(self):
        """Serialized output can be parsed back to equivalent data."""
        payload = QueueMaterializer.default_queue_payload()
        payload["jobs"] = [{"jobId": "test-job", "title": "Test"}]
        result = QueueMaterializer.serialize_queue_payload(payload)
        parsed = json.loads(result)
        assert parsed["version"] == 1
        assert parsed["jobs"] == [{"jobId": "test-job", "title": "Test"}]

    def test_fills_defaults_for_missing_keys(self):
        """Missing keys in the input are filled with defaults."""
        result = QueueMaterializer.serialize_queue_payload({})
        parsed = json.loads(result)
        assert parsed["version"] == 1
        assert parsed["language"] == "en"
        assert parsed["vocabularyPolicy"] == "english-technical-only"
        assert parsed["jobs"] == []

    def test_deterministic_output(self):
        """Same input produces identical serialized output."""
        payload = {"version": 1, "jobs": [{"jobId": "a"}], "language": "en"}
        a = QueueMaterializer.serialize_queue_payload(payload)
        b = QueueMaterializer.serialize_queue_payload(payload)
        assert a == b


# ---------------------------------------------------------------------------
# write_overnight_queue_payload
# ---------------------------------------------------------------------------


class TestWriteOvernightQueuePayload:
    """Tests for QueueMaterializer.write_overnight_queue_payload."""

    def test_writes_to_filesystem(self, tmp_path):
        """Payload is written to the expected path and is valid JSON."""
        queue_file = tmp_path / "jobs" / "overnight-queue.json"

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            queue_file,
        ):
            payload = QueueMaterializer.default_queue_payload()
            payload["jobs"] = [{"jobId": "write-test"}]
            QueueMaterializer.write_overnight_queue_payload(payload)

        assert queue_file.exists()
        written = json.loads(queue_file.read_text(encoding="utf-8"))
        assert written["version"] == 1
        assert written["jobs"] == [{"jobId": "write-test"}]

    def test_creates_parent_directories(self, tmp_path):
        """Parent directories are created if they don't exist."""
        queue_file = tmp_path / "deep" / "nested" / "overnight-queue.json"

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            queue_file,
        ):
            QueueMaterializer.write_overnight_queue_payload(
                QueueMaterializer.default_queue_payload()
            )

        assert queue_file.exists()

    def test_written_content_matches_serialize(self, tmp_path):
        """Written file content matches serialize_queue_payload output."""
        queue_file = tmp_path / "overnight-queue.json"
        payload = QueueMaterializer.default_queue_payload()

        with patch(
            "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
            queue_file,
        ):
            QueueMaterializer.write_overnight_queue_payload(payload)

        expected = QueueMaterializer.serialize_queue_payload(payload)
        assert queue_file.read_text(encoding="utf-8") == expected


# ---------------------------------------------------------------------------
# create_lane_queue_job_id
# ---------------------------------------------------------------------------


class TestCreateLaneQueueJobId:
    """Tests for QueueMaterializer.create_lane_queue_job_id."""

    def test_produces_expected_format(self):
        """Job ID has the format overnight-lane-{lane_id}-{token_suffix}."""
        result = QueueMaterializer.create_lane_queue_job_id(
            "lane-alpha", "AbCd1234XyZ"
        )
        assert result.startswith("overnight-lane-lane-alpha-")
        assert result == "overnight-lane-lane-alpha-abcd1234"

    def test_token_suffix_is_lowercase_alphanumeric(self):
        """Token suffix strips non-alphanumeric chars and lowercases."""
        result = QueueMaterializer.create_lane_queue_job_id(
            "lane-1", "A-B_C!D@2#3$4%5"
        )
        # Only alphanumeric chars kept: ABCD2345 -> abcd2345
        assert result == "overnight-lane-lane-1-abcd2345"

    def test_token_suffix_truncated_to_eight_chars(self):
        """Token suffix is at most 8 characters."""
        result = QueueMaterializer.create_lane_queue_job_id(
            "lane-x", "abcdefghijklmnop"
        )
        assert result == "overnight-lane-lane-x-abcdefgh"

    def test_empty_token_uses_fallback(self):
        """When the token produces no alphanumeric chars, uses 'unknown000'."""
        result = QueueMaterializer.create_lane_queue_job_id(
            "lane-y", "---!!!---"
        )
        assert result == "overnight-lane-lane-y-unknown000"

    def test_deterministic_for_same_inputs(self):
        """Same lane ID and token always produce the same job ID."""
        a = QueueMaterializer.create_lane_queue_job_id("lane-z", "token123")
        b = QueueMaterializer.create_lane_queue_job_id("lane-z", "token123")
        assert a == b

    def test_different_lanes_produce_different_ids(self):
        """Different lane IDs produce different job IDs."""
        a = QueueMaterializer.create_lane_queue_job_id("lane-a", "token")
        b = QueueMaterializer.create_lane_queue_job_id("lane-b", "token")
        assert a != b


# ---------------------------------------------------------------------------
# find_queue_job
# ---------------------------------------------------------------------------


class TestFindQueueJob:
    """Tests for QueueMaterializer.find_queue_job."""

    def test_finds_matching_job(self):
        """Returns the job dict when a matching jobId is found."""
        payload = {
            "jobs": [
                {"jobId": "job-1", "title": "First"},
                {"jobId": "job-2", "title": "Second"},
            ]
        }
        result = QueueMaterializer.find_queue_job(payload, "job-2")
        assert result is not None
        assert result["title"] == "Second"

    def test_returns_none_when_not_found(self):
        """Returns None when no job matches the given ID."""
        payload = {"jobs": [{"jobId": "job-1"}]}
        result = QueueMaterializer.find_queue_job(payload, "nonexistent")
        assert result is None

    def test_returns_none_for_empty_jobs(self):
        """Returns None when the jobs list is empty."""
        payload = {"jobs": []}
        result = QueueMaterializer.find_queue_job(payload, "any-id")
        assert result is None

    def test_returns_none_when_jobs_key_missing(self):
        """Returns None when the payload has no 'jobs' key."""
        payload = {}
        result = QueueMaterializer.find_queue_job(payload, "any-id")
        assert result is None

    def test_skips_non_dict_entries(self):
        """Non-dict entries in the jobs list are safely skipped."""
        payload = {
            "jobs": [
                "not-a-dict",
                42,
                {"jobId": "valid-job", "title": "Valid"},
            ]
        }
        result = QueueMaterializer.find_queue_job(payload, "valid-job")
        assert result is not None
        assert result["title"] == "Valid"

    def test_returns_first_match(self):
        """When multiple jobs share the same ID, returns the first match."""
        payload = {
            "jobs": [
                {"jobId": "dup", "title": "First"},
                {"jobId": "dup", "title": "Second"},
            ]
        }
        result = QueueMaterializer.find_queue_job(payload, "dup")
        assert result["title"] == "First"


# ---------------------------------------------------------------------------
# overnight_queue_status_response
# ---------------------------------------------------------------------------


class TestOvernightQueueStatusResponse:
    """Tests for QueueMaterializer.overnight_queue_status_response."""

    @patch(
        "app.control_plane.orchestration.queue_materializer.telemetry_service"
    )
    @patch(
        "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
    )
    @patch(
        "app.control_plane.orchestration.queue_materializer._REPO_ROOT",
    )
    def test_builds_correct_response_when_queue_exists(
        self, mock_repo_root, mock_queue_path, mock_telemetry
    ):
        """Returns a valid status response when the queue file exists."""
        tmp = Path("/tmp/test-repo")
        mock_repo_root.__truediv__ = tmp.__truediv__
        mock_queue_path.exists.return_value = True
        mock_queue_path.read_text.return_value = json.dumps({
            "version": 1,
            "language": "en",
            "vocabularyPolicy": "english-technical-only",
            "defaults": {"window": "nightly"},
            "jobs": [{"jobId": "j1"}],
            "updatedAt": "2026-04-15",
        })

        mock_telemetry.build_overnight_queue_status_response.return_value = {
            "queue_path": ".agent/jobs/overnight-queue.json",
            "queue_sha256": "abc123",
            "exists": True,
            "job_count": 1,
            "updated_at": "2026-04-15",
        }

        response = QueueMaterializer.overnight_queue_status_response()

        assert response.exists is True
        assert response.job_count == 1
        assert response.queue_sha256 == "abc123"
        mock_telemetry.build_overnight_queue_status_response.assert_called_once()

    @patch(
        "app.control_plane.orchestration.queue_materializer.telemetry_service"
    )
    @patch(
        "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
    )
    @patch(
        "app.control_plane.orchestration.queue_materializer._REPO_ROOT",
    )
    def test_builds_correct_response_when_queue_missing(
        self, mock_repo_root, mock_queue_path, mock_telemetry
    ):
        """Returns a valid status response when the queue file is missing."""
        mock_queue_path.exists.return_value = False

        mock_telemetry.build_overnight_queue_status_response.return_value = {
            "queue_path": ".agent/jobs/overnight-queue.json",
            "queue_sha256": "def456",
            "exists": False,
            "job_count": 0,
            "updated_at": None,
        }

        response = QueueMaterializer.overnight_queue_status_response()

        assert response.exists is False
        assert response.job_count == 0
        mock_telemetry.build_overnight_queue_status_response.assert_called_once()

    @patch(
        "app.control_plane.orchestration.queue_materializer.telemetry_service"
    )
    @patch(
        "app.control_plane.orchestration.queue_materializer._OVERNIGHT_QUEUE_PATH",
    )
    @patch(
        "app.control_plane.orchestration.queue_materializer._REPO_ROOT",
    )
    def test_passes_sha256_to_telemetry_service(
        self, mock_repo_root, mock_queue_path, mock_telemetry
    ):
        """The computed SHA256 is passed to the telemetry service."""
        mock_queue_path.exists.return_value = False

        mock_telemetry.build_overnight_queue_status_response.return_value = {
            "queue_path": "path",
            "queue_sha256": "hash",
            "exists": False,
            "job_count": 0,
            "updated_at": None,
        }

        QueueMaterializer.overnight_queue_status_response()

        call_args = mock_telemetry.build_overnight_queue_status_response.call_args
        # Third positional arg is the sha256
        sha256_arg = call_args[0][2]
        assert isinstance(sha256_arg, str)
        assert len(sha256_arg) == 64
