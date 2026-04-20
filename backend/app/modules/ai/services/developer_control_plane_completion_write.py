from __future__ import annotations

from typing import Any, Iterable, Mapping


COMPLETION_DRAFT_SOURCE_QUEUE_SNAPSHOT = "queue-snapshot"
COMPLETION_DRAFT_SOURCE_STABLE_CLOSEOUT_RECEIPT = "stable-closeout-receipt"


def _read_payload_field(
    payload: Mapping[str, Any] | object,
    snake_case: str,
    camel_case: str | None = None,
) -> Any:
    if isinstance(payload, Mapping):
        if snake_case in payload:
            return payload.get(snake_case)
        if camel_case is not None and camel_case in payload:
            return payload.get(camel_case)
        return None

    if hasattr(payload, snake_case):
        return getattr(payload, snake_case)
    if camel_case is not None and hasattr(payload, camel_case):
        return getattr(payload, camel_case)
    return None


def _read_optional_text(
    payload: Mapping[str, Any] | object,
    snake_case: str,
    camel_case: str | None = None,
) -> str | None:
    value = _read_payload_field(payload, snake_case, camel_case)
    if isinstance(value, str) and value:
        return value
    return None


def _read_mapping(
    payload: Mapping[str, Any] | object,
    snake_case: str,
    camel_case: str | None = None,
) -> Mapping[str, Any] | None:
    value = _read_payload_field(payload, snake_case, camel_case)
    if isinstance(value, Mapping):
        return value
    return None


def _existing_artifact_paths(closeout_receipt: Mapping[str, Any] | None) -> list[str]:
    if closeout_receipt is None:
        return []

    artifacts = closeout_receipt.get("artifacts")
    if not isinstance(artifacts, list):
        return []

    return [
        artifact["path"]
        for artifact in artifacts
        if isinstance(artifact, dict)
        and artifact.get("exists") is True
        and isinstance(artifact.get("path"), str)
        and artifact["path"]
    ]


def build_developer_control_plane_completion_closeout_receipt_payload(
    closeout_receipt: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if closeout_receipt is None or closeout_receipt.get("exists") is not True:
        return None

    return {
        "queue_job_id": closeout_receipt.get("queue_job_id"),
        "artifact_paths": _existing_artifact_paths(closeout_receipt),
        "mission_id": closeout_receipt.get("mission_id"),
        "producer_key": closeout_receipt.get("producer_key"),
        "source_lane_id": closeout_receipt.get("source_lane_id"),
        "source_board_concurrency_token": closeout_receipt.get(
            "source_board_concurrency_token"
        ),
        "runtime_profile_id": closeout_receipt.get("runtime_profile_id"),
        "runtime_policy_sha256": closeout_receipt.get("runtime_policy_sha256"),
        "closeout_status": closeout_receipt.get("closeout_status"),
        "state_refresh_required": closeout_receipt.get("state_refresh_required"),
        "receipt_recorded_at": closeout_receipt.get("receipt_recorded_at"),
        "verification_evidence_ref": closeout_receipt.get("verification_evidence_ref"),
        "queue_sha256_at_closeout": closeout_receipt.get("queue_sha256_at_closeout"),
    }


def _build_fallback_completion_draft(
    *,
    source_lane_id: str,
    queue_job_id: str,
    source_board_concurrency_token: str,
    expected_queue_sha256: str,
    queue_updated_at: str | None,
) -> dict[str, Any]:
    summary = (
        "Reviewed platform-runtime closeout after queue completion and canonical queue refresh."
        if source_lane_id == "platform-runtime"
        else f"Reviewed closeout for lane {source_lane_id} after queue completion and canonical queue refresh."
    )
    evidence = [
        f"Reviewed queue job {queue_job_id} before explicit board write-back.",
        f"Queue snapshot hash at reviewed closeout: {expected_queue_sha256}.",
        f"Board token used for reviewed closeout: {source_board_concurrency_token}.",
        (
            f"Queue status reviewed at {queue_updated_at}."
            if queue_updated_at
            else "Queue status was refreshed in the control-plane before write-back."
        ),
    ]

    return {
        "draft_source": COMPLETION_DRAFT_SOURCE_QUEUE_SNAPSHOT,
        "closure_summary": summary,
        "evidence": evidence,
    }


def build_developer_control_plane_completion_write_preparation(
    *,
    source_lane_id: str,
    source_board_concurrency_token: str,
    expected_queue_sha256: str,
    queue_updated_at: str | None,
    queue_job_id: str,
    closeout_receipt: Mapping[str, Any] | None,
    operator_intent: str,
) -> dict[str, Any]:
    fallback_draft = _build_fallback_completion_draft(
        source_lane_id=source_lane_id,
        queue_job_id=queue_job_id,
        source_board_concurrency_token=source_board_concurrency_token,
        expected_queue_sha256=expected_queue_sha256,
        queue_updated_at=queue_updated_at,
    )

    closeout_receipt_payload = build_developer_control_plane_completion_closeout_receipt_payload(
        closeout_receipt
    )
    if closeout_receipt_payload is None:
        return {
            "draft_source": fallback_draft["draft_source"],
            "prepared_request": {
                "source_board_concurrency_token": source_board_concurrency_token,
                "expected_queue_sha256": expected_queue_sha256,
                "operator_intent": operator_intent,
                "completion": {
                    "source_lane_id": source_lane_id,
                    "queue_job_id": queue_job_id,
                    "closure_summary": fallback_draft["closure_summary"],
                    "evidence": fallback_draft["evidence"],
                },
            },
        }

    receipt_status = closeout_receipt_payload.get("closeout_status") or "unknown"
    receipt_recorded_at = closeout_receipt_payload.get("receipt_recorded_at")
    queue_sha256_at_closeout = closeout_receipt_payload.get("queue_sha256_at_closeout")
    runtime_profile_id = closeout_receipt_payload.get("runtime_profile_id")
    verification_evidence_ref = closeout_receipt_payload.get("verification_evidence_ref")
    artifact_paths = closeout_receipt_payload.get("artifact_paths") or []

    summary = (
        "Reviewed platform-runtime closeout receipt "
        f"({receipt_status}) after watchdog completion and canonical queue refresh."
        if source_lane_id == "platform-runtime"
        else (
            f"Reviewed closeout receipt for lane {source_lane_id} ({receipt_status}) "
            "after watchdog completion and canonical queue refresh."
        )
    )
    evidence = [
        f"Reviewed queue job {queue_job_id} using watchdog closeout receipt before explicit board write-back.",
        (
            f"Watchdog closeout queue hash: {queue_sha256_at_closeout}."
            if isinstance(queue_sha256_at_closeout, str) and queue_sha256_at_closeout
            else f"Queue snapshot hash at reviewed closeout: {expected_queue_sha256}."
        ),
        f"Board token used for reviewed closeout: {source_board_concurrency_token}.",
        *(
            [f"Runtime profile recorded by closeout receipt: {runtime_profile_id}."]
            if isinstance(runtime_profile_id, str) and runtime_profile_id
            else []
        ),
        *(
            [
                "Verification evidence referenced by closeout receipt: "
                f"{verification_evidence_ref}."
            ]
            if isinstance(verification_evidence_ref, str) and verification_evidence_ref
            else []
        ),
        *[f"Closeout artifact refreshed: {artifact_path}." for artifact_path in artifact_paths],
        *(
            [f"Stable closeout receipt recorded at {receipt_recorded_at}."]
            if isinstance(receipt_recorded_at, str) and receipt_recorded_at
            else [fallback_draft["evidence"][3]]
        ),
    ]

    return {
        "draft_source": COMPLETION_DRAFT_SOURCE_STABLE_CLOSEOUT_RECEIPT,
        "prepared_request": {
            "source_board_concurrency_token": source_board_concurrency_token,
            "expected_queue_sha256": expected_queue_sha256,
            "operator_intent": operator_intent,
            "completion": {
                "source_lane_id": source_lane_id,
                "queue_job_id": queue_job_id,
                "closure_summary": summary,
                "evidence": evidence,
                "closeout_receipt": closeout_receipt_payload,
            },
        },
    }


def build_developer_control_plane_completion_write_preparation_response_payload(
    *,
    source_lane_id: str,
    source_board_concurrency_token: str,
    expected_queue_sha256: str,
    queue_updated_at: str | None,
    queue_job_id: str,
    queue_status: Mapping[str, Any],
    closeout_receipt: Mapping[str, Any],
    operator_intent: str,
) -> dict[str, Any]:
    preparation = build_developer_control_plane_completion_write_preparation(
        source_lane_id=source_lane_id,
        source_board_concurrency_token=source_board_concurrency_token,
        expected_queue_sha256=expected_queue_sha256,
        queue_updated_at=queue_updated_at,
        queue_job_id=queue_job_id,
        closeout_receipt=closeout_receipt,
        operator_intent=operator_intent,
    )

    return {
        "source_lane_id": source_lane_id,
        "queue_job_id": queue_job_id,
        "draft_source": preparation["draft_source"],
        "queue_status": dict(queue_status),
        "closeout_receipt": dict(closeout_receipt),
        "prepared_request": preparation["prepared_request"],
    }


def build_developer_control_plane_first_actionable_completion_write_payload(
    next_actions: Iterable[Mapping[str, Any] | object],
) -> dict[str, Any] | None:
    for action_index, action in enumerate(next_actions):
        if _read_optional_text(action, "action") != "prepare-completion-write-back":
            continue

        detail = _read_mapping(action, "detail")
        if detail is None:
            continue

        preparation = detail.get("completionWritePreparation")
        if not isinstance(preparation, Mapping):
            continue

        source_lane_id = _read_optional_text(action, "source_lane_id", "sourceLaneId")
        if source_lane_id is None:
            source_lane_id = _read_optional_text(preparation, "source_lane_id")

        job_id = _read_optional_text(action, "job_id", "jobId")
        if job_id is None:
            job_id = _read_optional_text(preparation, "queue_job_id")

        if source_lane_id is None or job_id is None:
            continue

        return {
            "action": "prepare-completion-write-back",
            "action_index": action_index,
            "job_id": job_id,
            "source_lane_id": source_lane_id,
            "reason": _read_optional_text(action, "reason"),
            "mission_id": _read_optional_text(action, "mission_id", "missionId"),
            "receipt_path": _read_optional_text(action, "receipt_path", "receiptPath"),
            "preparation": dict(preparation),
        }

    return None