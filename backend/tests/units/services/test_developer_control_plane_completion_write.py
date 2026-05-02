from types import SimpleNamespace

from app.modules.ai.services.developer_control_plane_completion_write import (
    build_developer_control_plane_first_actionable_completion_write_payload,
)


def test_resolve_first_actionable_completion_write_payload_skips_actions_without_packet():
    payload = build_developer_control_plane_first_actionable_completion_write_payload(
        [
            {
                "action": "dispatch-queue-job",
                "job_id": "queue-job-1",
                "source_lane_id": "control-plane",
            },
            {
                "action": "prepare-completion-write-back",
                "job_id": "queue-job-2",
                "source_lane_id": "platform-runtime",
                "detail": {
                    "queueStatus": "completed",
                },
            },
        ]
    )

    assert payload is None


def test_resolve_first_actionable_completion_write_payload_returns_first_embedded_packet():
    preparation = {
        "source_lane_id": "control-plane",
        "queue_job_id": "queue-job-2",
        "draft_source": "stable-closeout-receipt",
        "queue_status": {
            "queue_path": ".agent/jobs/overnight-queue.json",
            "queue_sha256": "queue-sha-77",
            "exists": True,
            "job_count": 1,
            "updated_at": "2026-03-19T12:00:00.000Z",
        },
        "closeout_receipt": {
            "exists": True,
            "queue_job_id": "queue-job-2",
            "mission_id": "mission-runtime-job",
            "producer_key": "openclaw-runtime",
            "source_lane_id": "control-plane",
            "source_board_concurrency_token": "shared-token-1",
            "runtime_profile_id": "bijmantra-bca-local-verify",
            "runtime_policy_sha256": "policy-sha-1234",
            "closeout_status": "passed",
            "state_refresh_required": True,
            "receipt_recorded_at": "2026-03-19T12:05:00.000Z",
            "started_at": "2026-03-19T12:03:00.000Z",
            "finished_at": "2026-03-19T12:04:00.000Z",
            "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
            "queue_sha256_at_closeout": "queue-sha-closeout-77",
            "closeout_commands": [],
            "artifacts": [],
        },
        "prepared_request": {
            "source_board_concurrency_token": "shared-token-1",
            "expected_queue_sha256": "queue-sha-77",
            "operator_intent": "write-reviewed-lane-completion",
            "completion": {
                "source_lane_id": "control-plane",
                "queue_job_id": "queue-job-2",
                "closure_summary": "Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.",
                "evidence": [
                    "Reviewed queue job queue-job-2 using watchdog closeout receipt before explicit board write-back.",
                ],
                "closeout_receipt": {
                    "queue_job_id": "queue-job-2",
                    "artifact_paths": [],
                    "mission_id": "mission-runtime-job",
                    "producer_key": "openclaw-runtime",
                    "source_lane_id": "control-plane",
                    "source_board_concurrency_token": "shared-token-1",
                    "runtime_profile_id": "bijmantra-bca-local-verify",
                    "runtime_policy_sha256": "policy-sha-1234",
                    "closeout_status": "passed",
                    "state_refresh_required": True,
                    "receipt_recorded_at": "2026-03-19T12:05:00.000Z",
                    "verification_evidence_ref": "runtime-artifacts/mission-evidence/job/verification_1.json",
                    "queue_sha256_at_closeout": "queue-sha-closeout-77",
                },
            },
        },
    }

    payload = build_developer_control_plane_first_actionable_completion_write_payload(
        [
            SimpleNamespace(
                action="review-closeout-receipt",
                job_id="queue-job-1",
                source_lane_id="control-plane",
                detail=None,
            ),
            {
                "action": "prepare-completion-write-back",
                "jobId": "queue-job-2",
                "sourceLaneId": "control-plane",
                "reason": "stable closeout ready for explicit board write-back",
                "missionId": "mission-runtime-job",
                "receiptPath": "runtime-artifacts/mission-evidence/job/closeout.json",
                "detail": {
                    "completionWritePreparation": preparation,
                },
            },
            {
                "action": "prepare-completion-write-back",
                "jobId": "queue-job-3",
                "sourceLaneId": "platform-runtime",
                "detail": {
                    "completionWritePreparation": {
                        **preparation,
                        "source_lane_id": "platform-runtime",
                        "queue_job_id": "queue-job-3",
                    },
                },
            },
        ]
    )

    assert payload == {
        "action": "prepare-completion-write-back",
        "action_index": 1,
        "job_id": "queue-job-2",
        "source_lane_id": "control-plane",
        "reason": "stable closeout ready for explicit board write-back",
        "mission_id": "mission-runtime-job",
        "receipt_path": "runtime-artifacts/mission-evidence/job/closeout.json",
        "preparation": preparation,
    }