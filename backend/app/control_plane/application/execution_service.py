"""Execution application service — closeout receipt operations.

This module is the application-layer home for queue job execution tracking
and closeout receipt production.  It bridges the telemetry service
(infrastructure) and the domain validation layer for closeout receipt
contract building.

Application-layer modules **may** have infrastructure imports (filesystem,
telemetry service) — that is expected for execution tracking.

Extracted from ``backend/app/api/v2/developer_control_plane.py``.

Requirements: 9.4, 9.5, 9.6
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneCloseoutReceiptResponse,
)
from app.control_plane.domain.validation import (
    build_closeout_receipt_contract as _domain_build_closeout_receipt_contract,
)
from app.modules.ai.services.claw_runtime_surface import (
    resolve_runtime_mission_evidence_dir,
)
from app.services.control_plane import telemetry_service


# ---------------------------------------------------------------------------
# Path resolution — mirrors the constants in developer_control_plane.py
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[5]
_MISSION_EVIDENCE_DIR = resolve_runtime_mission_evidence_dir(_REPO_ROOT)


# ---------------------------------------------------------------------------
# ExecutionService — application service class
# ---------------------------------------------------------------------------


class ExecutionService:
    """Application service for queue job execution tracking and closeout
    receipt production.

    All methods are intentionally ``@staticmethod`` so that the class acts
    as a namespace grouping related execution operations.  Infrastructure
    dependencies (filesystem paths, telemetry service) are resolved at
    module level.

    A database session dependency is accepted via the constructor for
    future use when execution tracking requires persistence, but current
    operations are filesystem-based.
    """

    # ------------------------------------------------------------------
    # Closeout receipt loading (filesystem via telemetry service)
    # ------------------------------------------------------------------

    @staticmethod
    def load_closeout_receipt(queue_job_id: str) -> dict[str, Any] | None:
        """Load a closeout receipt for *queue_job_id* from the filesystem.

        Delegates to the telemetry service which reads the receipt JSON
        from the mission evidence directory.

        Returns ``None`` when no receipt exists for the given job ID.
        """
        return telemetry_service.load_closeout_receipt(
            queue_job_id, _MISSION_EVIDENCE_DIR
        )

    # ------------------------------------------------------------------
    # Closeout receipt response building
    # ------------------------------------------------------------------

    @staticmethod
    def closeout_receipt_response(
        queue_job_id: str,
        receipt: dict[str, Any] | None,
    ) -> DeveloperControlPlaneCloseoutReceiptResponse:
        """Build a closeout receipt API response from a raw receipt dict.

        Delegates to the telemetry service for response dict construction,
        then wraps the result in the frozen contract schema.
        """
        response_dict = telemetry_service.build_closeout_receipt_response(
            queue_job_id,
            receipt,
            _MISSION_EVIDENCE_DIR,
            _REPO_ROOT,
        )
        return DeveloperControlPlaneCloseoutReceiptResponse(**response_dict)

    # ------------------------------------------------------------------
    # Closeout receipt contract building
    # ------------------------------------------------------------------

    @staticmethod
    def build_closeout_receipt_contract(
        *,
        queue_job_id: str,
        artifact_paths: list[str],
        mission_id: str | None = None,
        producer_key: str | None = None,
        source_lane_id: str | None = None,
        source_board_concurrency_token: str | None = None,
        runtime_profile_id: str | None = None,
        runtime_policy_sha256: str | None = None,
        closeout_status: str | None = None,
        state_refresh_required: bool | None = None,
        receipt_recorded_at: str | None = None,
        verification_evidence_ref: str | None = None,
        queue_sha256_at_closeout: str | None = None,
    ) -> dict[str, Any]:
        """Build a closeout receipt contract dict from validated fields.

        Delegates to the domain-layer ``build_closeout_receipt_contract``
        which is the canonical pure implementation.
        """
        return _domain_build_closeout_receipt_contract(
            queue_job_id=queue_job_id,
            artifact_paths=artifact_paths,
            mission_id=mission_id,
            producer_key=producer_key,
            source_lane_id=source_lane_id,
            source_board_concurrency_token=source_board_concurrency_token,
            runtime_profile_id=runtime_profile_id,
            runtime_policy_sha256=runtime_policy_sha256,
            closeout_status=closeout_status,
            state_refresh_required=state_refresh_required,
            receipt_recorded_at=receipt_recorded_at,
            verification_evidence_ref=verification_evidence_ref,
            queue_sha256_at_closeout=queue_sha256_at_closeout,
        )

    # ------------------------------------------------------------------
    # Closeout receipt contract from response (convenience)
    # ------------------------------------------------------------------

    @staticmethod
    def closeout_receipt_contract_from_response(
        receipt: DeveloperControlPlaneCloseoutReceiptResponse,
    ) -> dict[str, Any] | None:
        """Extract a closeout receipt contract dict from a response model.

        Returns ``None`` when the receipt does not exist (``exists=False``).
        """
        if not receipt.exists:
            return None

        return ExecutionService.build_closeout_receipt_contract(
            queue_job_id=receipt.queue_job_id,
            artifact_paths=[
                artifact.path
                for artifact in receipt.artifacts
                if artifact.exists
            ],
            mission_id=receipt.mission_id,
            producer_key=receipt.producer_key,
            source_lane_id=receipt.source_lane_id,
            source_board_concurrency_token=receipt.source_board_concurrency_token,
            runtime_profile_id=receipt.runtime_profile_id,
            runtime_policy_sha256=receipt.runtime_policy_sha256,
            closeout_status=receipt.closeout_status,
            state_refresh_required=receipt.state_refresh_required,
            receipt_recorded_at=receipt.receipt_recorded_at,
            verification_evidence_ref=receipt.verification_evidence_ref,
            queue_sha256_at_closeout=receipt.queue_sha256_at_closeout,
        )
