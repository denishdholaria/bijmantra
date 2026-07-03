"""
Unit tests for Control Plane execution application service.

Tests closeout receipt loading, response building, contract building,
and contract extraction from response models in
``app.control_plane.application.execution_service.ExecutionService``.

**Validates: Requirements 9.4**
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.control_plane.application.execution_service import ExecutionService
from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneCloseoutArtifactResponse,
    DeveloperControlPlaneCloseoutReceiptResponse,
)


# ---------------------------------------------------------------------------
# load_closeout_receipt — delegates to telemetry_service
# ---------------------------------------------------------------------------


class TestLoadCloseoutReceipt:
    """Tests for ExecutionService.load_closeout_receipt."""

    @patch("app.control_plane.application.execution_service.telemetry_service")
    def test_delegates_to_telemetry_service(self, mock_telemetry):
        receipt_data = {
            "data": {"missionId": "m-1", "status": "completed"},
            "timestamp": "2026-04-20T12:00:00Z",
        }
        mock_telemetry.load_closeout_receipt.return_value = receipt_data

        result = ExecutionService.load_closeout_receipt("job-abc-123")

        mock_telemetry.load_closeout_receipt.assert_called_once()
        call_args = mock_telemetry.load_closeout_receipt.call_args
        assert call_args[0][0] == "job-abc-123"
        assert result is receipt_data

    @patch("app.control_plane.application.execution_service.telemetry_service")
    def test_returns_none_when_no_receipt_exists(self, mock_telemetry):
        mock_telemetry.load_closeout_receipt.return_value = None

        result = ExecutionService.load_closeout_receipt("nonexistent-job")

        assert result is None


# ---------------------------------------------------------------------------
# closeout_receipt_response — builds response via telemetry_service
# ---------------------------------------------------------------------------


class TestCloseoutReceiptResponse:
    """Tests for ExecutionService.closeout_receipt_response."""

    @patch("app.control_plane.application.execution_service.telemetry_service")
    def test_builds_correct_response(self, mock_telemetry):
        mock_telemetry.build_closeout_receipt_response.return_value = {
            "exists": True,
            "queue_job_id": "job-xyz",
            "mission_id": "m-42",
            "producer_key": "agent-alpha",
            "source_lane_id": "lane-1",
            "source_board_concurrency_token": "tok-abc",
            "runtime_profile_id": None,
            "runtime_policy_sha256": None,
            "closeout_status": "completed",
            "state_refresh_required": True,
            "receipt_recorded_at": "2026-04-20T12:00:00Z",
            "started_at": None,
            "finished_at": None,
            "verification_evidence_ref": "ref-123",
            "queue_sha256_at_closeout": "sha-456",
            "closeout_commands": [],
            "artifacts": [],
        }

        receipt = {"data": {"missionId": "m-42"}}
        result = ExecutionService.closeout_receipt_response("job-xyz", receipt)

        assert isinstance(result, DeveloperControlPlaneCloseoutReceiptResponse)
        assert result.exists is True
        assert result.queue_job_id == "job-xyz"
        assert result.mission_id == "m-42"
        assert result.producer_key == "agent-alpha"
        assert result.closeout_status == "completed"
        assert result.state_refresh_required is True
        assert result.verification_evidence_ref == "ref-123"
        assert result.queue_sha256_at_closeout == "sha-456"

        mock_telemetry.build_closeout_receipt_response.assert_called_once()


# ---------------------------------------------------------------------------
# build_closeout_receipt_contract — delegates to domain layer
# ---------------------------------------------------------------------------


class TestBuildCloseoutReceiptContract:
    """Tests for ExecutionService.build_closeout_receipt_contract."""

    def test_builds_correct_dict_with_all_fields(self):
        result = ExecutionService.build_closeout_receipt_contract(
            queue_job_id="job-full",
            artifact_paths=["path/a.txt", "path/b.txt"],
            mission_id="m-100",
            producer_key="agent-beta",
            source_lane_id="lane-7",
            source_board_concurrency_token="tok-999",
            runtime_profile_id="profile-1",
            runtime_policy_sha256="policy-sha",
            closeout_status="completed",
            state_refresh_required=True,
            receipt_recorded_at="2026-04-20T12:00:00Z",
            verification_evidence_ref="evidence-ref",
            queue_sha256_at_closeout="queue-sha",
        )

        assert result["queue_job_id"] == "job-full"
        assert result["artifact_paths"] == ["path/a.txt", "path/b.txt"]
        assert result["mission_id"] == "m-100"
        assert result["producer_key"] == "agent-beta"
        assert result["source_lane_id"] == "lane-7"
        assert result["source_board_concurrency_token"] == "tok-999"
        assert result["runtime_profile_id"] == "profile-1"
        assert result["runtime_policy_sha256"] == "policy-sha"
        assert result["closeout_status"] == "completed"
        assert result["state_refresh_required"] is True
        assert result["receipt_recorded_at"] == "2026-04-20T12:00:00Z"
        assert result["verification_evidence_ref"] == "evidence-ref"
        assert result["queue_sha256_at_closeout"] == "queue-sha"

    def test_omits_none_optional_fields(self):
        result = ExecutionService.build_closeout_receipt_contract(
            queue_job_id="job-minimal",
            artifact_paths=[],
        )

        assert result["queue_job_id"] == "job-minimal"
        assert result["artifact_paths"] == []
        # All optional fields should be absent (not present as None)
        assert "mission_id" not in result
        assert "producer_key" not in result
        assert "source_lane_id" not in result
        assert "source_board_concurrency_token" not in result
        assert "runtime_profile_id" not in result
        assert "runtime_policy_sha256" not in result
        assert "closeout_status" not in result
        assert "state_refresh_required" not in result
        assert "receipt_recorded_at" not in result
        assert "verification_evidence_ref" not in result
        assert "queue_sha256_at_closeout" not in result


# ---------------------------------------------------------------------------
# closeout_receipt_contract_from_response — extracts contract from response
# ---------------------------------------------------------------------------


class TestCloseoutReceiptContractFromResponse:
    """Tests for ExecutionService.closeout_receipt_contract_from_response."""

    def test_extracts_contract_from_response(self):
        response = DeveloperControlPlaneCloseoutReceiptResponse(
            exists=True,
            queue_job_id="job-extract",
            mission_id="m-200",
            producer_key="agent-gamma",
            source_lane_id="lane-3",
            source_board_concurrency_token="tok-extract",
            runtime_profile_id="profile-2",
            runtime_policy_sha256="policy-sha-2",
            closeout_status="completed",
            state_refresh_required=False,
            receipt_recorded_at="2026-04-20T14:00:00Z",
            verification_evidence_ref="ev-ref-2",
            queue_sha256_at_closeout="q-sha-2",
            artifacts=[
                DeveloperControlPlaneCloseoutArtifactResponse(
                    path="artifact/one.txt", exists=True, sha256=None, modified_at=None
                ),
                DeveloperControlPlaneCloseoutArtifactResponse(
                    path="artifact/two.txt", exists=False, sha256=None, modified_at=None
                ),
            ],
        )

        result = ExecutionService.closeout_receipt_contract_from_response(response)

        assert result is not None
        assert result["queue_job_id"] == "job-extract"
        assert result["mission_id"] == "m-200"
        assert result["producer_key"] == "agent-gamma"
        assert result["source_lane_id"] == "lane-3"
        assert result["closeout_status"] == "completed"
        assert result["state_refresh_required"] is False
        # Only artifacts with exists=True are included
        assert result["artifact_paths"] == ["artifact/one.txt"]

    def test_returns_none_when_exists_is_false(self):
        response = DeveloperControlPlaneCloseoutReceiptResponse(
            exists=False,
            queue_job_id="job-missing",
        )

        result = ExecutionService.closeout_receipt_contract_from_response(response)

        assert result is None
