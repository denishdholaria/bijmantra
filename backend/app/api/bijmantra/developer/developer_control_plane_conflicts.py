"""
Conflict detail builders for the developer control-plane API.

Extracted from developer_control_plane.py — pure functions, no imports needed.
These are used by the thin routers under app.api.bijmantra.control_plane.
"""

from __future__ import annotations

from typing import Any


def _queue_write_conflict_detail(
    reason: str, detail: str, **extra: Any
) -> dict[str, Any]:
    """Build a structured conflict response for queue-write rejections."""
    remediation_message = {
        "lane-review-missing": (
            "Update the canonical lane with explicit spec_review and risk_review evidence, "
            "save the shared board, then retry queue export from the current board token."
        ),
        "missing-active-board": (
            "Restore or resave the shared active board first. Queue writes stay blocked "
            "until shared board provenance exists."
        ),
        "stale-board-token": (
            "Refresh the shared board state, confirm the selected lane still "
            "materializes to the intended queue entry, then retry with the current "
            "board token."
        ),
        "queue-sha-mismatch": (
            "Refresh queue status, compare the latest queue hash shown here, then retry "
            "only if the reviewed queue entry is still valid."
        ),
        "duplicate-job-id": (
            "Do not overwrite. Inspect whether the existing queued job already "
            "represents this lane and token pair, or regenerate from a newer board token "
            "if the board changed."
        ),
    }[reason]
    refresh_targets = {
        "lane-review-missing": ["active-board"],
        "missing-active-board": ["active-board"],
        "stale-board-token": ["active-board"],
        "queue-sha-mismatch": ["overnight-queue"],
        "duplicate-job-id": ["overnight-queue", "active-board"],
    }[reason]
    retry_permitted_after_refresh = {
        "lane-review-missing": False,
        "missing-active-board": True,
        "stale-board-token": True,
        "queue-sha-mismatch": True,
        "duplicate-job-id": False,
    }[reason]

    return {
        "detail": detail,
        "conflict_reason": reason,
        "remediation_message": remediation_message,
        "refresh_targets": refresh_targets,
        "retry_permitted_after_refresh": retry_permitted_after_refresh,
        **extra,
    }


def _completion_write_conflict_detail(
    reason: str, detail: str, **extra: Any
) -> dict[str, Any]:
    """Build a structured conflict response for completion-write rejections."""
    remediation_message = {
        "lane-verification-missing": (
            "Attach canonical verification_evidence to the lane, save the shared board, "
            "and retry completion write-back only after the reviewed verification gate "
            "is visible."
        ),
        "missing-active-board": (
            "Restore or resave the shared active board first. Completion write-back "
            "stays blocked until shared board provenance exists."
        ),
        "queue-sha-mismatch": (
            "Refresh queue status, confirm the current queue hash and the reviewed "
            "completion target, then retry only if the same job still applies."
        ),
        "queue-job-missing": (
            "The reviewed queue job is no longer present in the current queue snapshot. "
            "Refresh queue status and verify the job id before retrying."
        ),
        "queue-job-not-completed": (
            "Wait until the reviewed queue job reaches completed status before writing "
            "closure evidence back into the board."
        ),
        "closeout-receipt-required": (
            "Refresh the reviewed closeout receipt and retry only after the normalized "
            "receipt is visible in the control plane. Runtime-backed lanes should not be "
            "closed from freeform evidence alone."
        ),
        "closeout-receipt-mismatch": (
            "Refresh the reviewed closeout receipt, compare the latest normalized runtime "
            "evidence, and retry only if the receipt still matches the queue job being "
            "closed."
        ),
        "lane-job-mismatch": (
            "Refresh the shared board state and use the deterministic lane job id for the "
            "selected lane and board token. Do not apply completion evidence to a "
            "mismatched job."
        ),
        "stale-board-token": (
            "Refresh the shared board state, confirm the lane is still the intended "
            "completion target, then retry with the current board token."
        ),
        "lane-status-conflict": (
            "Only active lanes can move to completed in this slice. Review the current "
            "lane status and avoid forcing completion onto a non-active lane."
        ),
        "completion-overwrite-conflict": (
            "This lane already has different closure evidence. Review the current board "
            "record instead of overwriting closure data implicitly."
        ),
    }[reason]
    refresh_targets = {
        "lane-verification-missing": ["active-board"],
        "missing-active-board": ["active-board"],
        "queue-sha-mismatch": ["overnight-queue"],
        "queue-job-missing": ["overnight-queue"],
        "queue-job-not-completed": ["overnight-queue", "closeout-receipt"],
        "closeout-receipt-required": ["closeout-receipt", "overnight-queue"],
        "closeout-receipt-mismatch": ["closeout-receipt", "overnight-queue"],
        "lane-job-mismatch": ["active-board", "overnight-queue"],
        "stale-board-token": ["active-board"],
        "lane-status-conflict": ["active-board"],
        "completion-overwrite-conflict": ["active-board"],
    }[reason]
    retry_permitted_after_refresh = {
        "lane-verification-missing": False,
        "missing-active-board": True,
        "queue-sha-mismatch": True,
        "queue-job-missing": False,
        "queue-job-not-completed": True,
        "closeout-receipt-required": True,
        "closeout-receipt-mismatch": True,
        "lane-job-mismatch": True,
        "stale-board-token": True,
        "lane-status-conflict": False,
        "completion-overwrite-conflict": False,
    }[reason]

    return {
        "detail": detail,
        "conflict_reason": reason,
        "remediation_message": remediation_message,
        "refresh_targets": refresh_targets,
        "retry_permitted_after_refresh": retry_permitted_after_refresh,
        **extra,
    }
