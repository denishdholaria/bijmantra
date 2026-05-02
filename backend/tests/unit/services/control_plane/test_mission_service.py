"""
Unit tests for Control Plane mission application service.

Tests mission state queries, snapshot loading, and response building in
``app.control_plane.application.mission_service.MissionService``.

**Validates: Requirements 9.3**
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.control_plane.application.mission_service import MissionService
from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneMissionDetailResponse,
    DeveloperControlPlaneMissionStateResponse,
    DeveloperControlPlaneMissionSummaryResponse,
    DeveloperControlPlaneMissionVerificationSummaryResponse,
)
from app.modules.ai.services.orchestrator_state import (
    AssignmentRecord,
    BlockerRecord,
    DecisionNoteRecord,
    EvidenceItemRecord,
    MissionRecord,
    MissionStateSnapshot,
    MissionStatus,
    SubtaskRecord,
    SubtaskStatus,
    VerificationResult,
    VerificationRunRecord,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight fakes for snapshot objects
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
_EARLIER = datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc)


def _make_mission(**overrides) -> MissionRecord:
    """Build a MissionRecord with sensible defaults."""
    defaults = dict(
        id="mission-001",
        objective="Deploy feature X",
        status=MissionStatus.ACTIVE,
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="Developer control-plane explicit completion write-back for lane lane-abc from queue job job-xyz. Context: source_board_concurrency_token=token-123.",
        producer_key="developer-control-plane",
        queue_job_id="job-xyz",
        source_lane_id="lane-abc",
        source_board_concurrency_token="token-123",
        final_summary=None,
        created_at=_EARLIER,
        updated_at=_NOW,
    )
    defaults.update(overrides)
    return MissionRecord(**defaults)


def _make_subtask(**overrides) -> SubtaskRecord:
    defaults = dict(
        id="subtask-001",
        mission_id="mission-001",
        title="Implement widget",
        status=SubtaskStatus.COMPLETED,
        owner_role="engineer",
        depends_on=(),
        created_at=_EARLIER,
        updated_at=_NOW,
    )
    defaults.update(overrides)
    return SubtaskRecord(**defaults)


def _make_assignment(**overrides) -> AssignmentRecord:
    defaults = dict(
        id="assignment-001",
        subtask_id="subtask-001",
        assigned_role="engineer",
        handoff_reason="Primary implementer",
        started_at=_EARLIER,
        completed_at=None,
    )
    defaults.update(overrides)
    return AssignmentRecord(**defaults)


def _make_evidence(**overrides) -> EvidenceItemRecord:
    defaults = dict(
        id="evidence-001",
        mission_id="mission-001",
        subtask_id=None,
        kind="test-result",
        source_path="/tmp/evidence/test.log",
        evidence_class="verification",
        summary="All tests passed",
        recorded_at=_NOW,
    )
    defaults.update(overrides)
    return EvidenceItemRecord(**defaults)


def _make_verification_run(**overrides) -> VerificationRunRecord:
    defaults = dict(
        id="vr-001",
        subject_id="mission-001",
        verification_type="unit-test",
        result=VerificationResult.PASSED,
        evidence_ref="evidence-001",
        executed_at=_NOW,
    )
    defaults.update(overrides)
    return VerificationRunRecord(**defaults)


def _make_decision_note(**overrides) -> DecisionNoteRecord:
    defaults = dict(
        id="decision-001",
        mission_id="mission-001",
        decision_class="approval",
        rationale="Meets criteria",
        authority_source="OmShriMaatreNamaha",
        recorded_at=_NOW,
    )
    defaults.update(overrides)
    return DecisionNoteRecord(**defaults)


def _make_blocker(**overrides) -> BlockerRecord:
    defaults = dict(
        id="blocker-001",
        mission_id="mission-001",
        subtask_id=None,
        blocker_type="dependency",
        impact="Blocks deployment",
        escalation_needed=False,
        recorded_at=_NOW,
    )
    defaults.update(overrides)
    return BlockerRecord(**defaults)


def _make_snapshot(**overrides) -> MissionStateSnapshot:
    """Build a MissionStateSnapshot with sensible defaults."""
    defaults = dict(
        mission=_make_mission(),
        subtasks=(_make_subtask(),),
        assignments=(_make_assignment(),),
        evidence_items=(_make_evidence(),),
        verification_runs=(_make_verification_run(),),
        decision_notes=(_make_decision_note(),),
        blockers=(_make_blocker(),),
    )
    defaults.update(overrides)
    return MissionStateSnapshot(**defaults)


# ---------------------------------------------------------------------------
# mission_summary_response (static, no DB)
# ---------------------------------------------------------------------------


class TestMissionSummaryResponse:
    """Tests for MissionService.mission_summary_response — pure mapping."""

    def test_maps_snapshot_to_summary_correctly(self):
        snapshot = _make_snapshot()
        resp = MissionService.mission_summary_response(snapshot)

        assert isinstance(resp, DeveloperControlPlaneMissionSummaryResponse)
        assert resp.mission_id == "mission-001"
        assert resp.objective == "Deploy feature X"
        assert resp.status == "active"
        assert resp.owner == "OmShriMaatreNamaha"
        assert resp.priority == "p1"
        assert resp.producer_key == "developer-control-plane"
        assert resp.created_at == _EARLIER.isoformat()
        assert resp.updated_at == _NOW.isoformat()
        assert resp.subtask_total == 1
        assert resp.subtask_completed == 1
        assert resp.assignment_total == 1
        assert resp.evidence_count == 1
        assert resp.blocker_count == 1
        assert resp.final_summary is None

    def test_handles_linkage_with_direct_columns(self):
        """When mission has direct queue_job_id/source_lane_id, linkage is populated."""
        snapshot = _make_snapshot(
            mission=_make_mission(
                queue_job_id="job-xyz",
                source_lane_id="lane-abc",
                source_board_concurrency_token="token-123",
            )
        )
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.queue_job_id == "job-xyz"
        assert resp.source_lane_id == "lane-abc"
        assert resp.source_board_concurrency_token == "token-123"

    def test_handles_no_linkage(self):
        """When mission has no linkage columns and no parseable source_request, linkage is None."""
        snapshot = _make_snapshot(
            mission=_make_mission(
                queue_job_id=None,
                source_lane_id=None,
                source_board_concurrency_token=None,
                source_request="some unstructured text",
            )
        )
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.queue_job_id is None
        assert resp.source_lane_id is None
        assert resp.source_board_concurrency_token is None

    def test_verification_counts_passed_warned_failed(self):
        """Verification summary counts are computed from verification_runs."""
        vr_passed = _make_verification_run(id="vr-p", result=VerificationResult.PASSED)
        vr_warn1 = _make_verification_run(id="vr-w1", result=VerificationResult.WARN)
        vr_warn2 = _make_verification_run(id="vr-w2", result=VerificationResult.WARN)
        vr_failed = _make_verification_run(id="vr-f", result=VerificationResult.FAILED)

        snapshot = _make_snapshot(
            verification_runs=(vr_passed, vr_warn1, vr_warn2, vr_failed),
        )
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.verification.passed == 1
        assert resp.verification.warned == 2
        assert resp.verification.failed == 1

    def test_verification_last_verified_at(self):
        """last_verified_at is the max executed_at across all verification runs."""
        early = datetime(2026, 4, 18, 8, 0, 0, tzinfo=timezone.utc)
        late = datetime(2026, 4, 20, 16, 0, 0, tzinfo=timezone.utc)
        vr1 = _make_verification_run(id="vr-1", executed_at=early)
        vr2 = _make_verification_run(id="vr-2", executed_at=late)

        snapshot = _make_snapshot(verification_runs=(vr1, vr2))
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.verification.last_verified_at == late.isoformat()

    def test_verification_empty_runs(self):
        """When there are no verification runs, counts are zero and last_verified_at is None."""
        snapshot = _make_snapshot(verification_runs=())
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.verification.passed == 0
        assert resp.verification.warned == 0
        assert resp.verification.failed == 0
        assert resp.verification.last_verified_at is None

    def test_escalation_needed_true_when_any_blocker_escalated(self):
        b1 = _make_blocker(id="b1", escalation_needed=False)
        b2 = _make_blocker(id="b2", escalation_needed=True)
        snapshot = _make_snapshot(blockers=(b1, b2))
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.escalation_needed is True

    def test_escalation_needed_false_when_no_blockers_escalated(self):
        b1 = _make_blocker(id="b1", escalation_needed=False)
        snapshot = _make_snapshot(blockers=(b1,))
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.escalation_needed is False

    def test_subtask_completed_count(self):
        """subtask_completed counts only subtasks with status 'completed'."""
        s1 = _make_subtask(id="s1", status=SubtaskStatus.COMPLETED)
        s2 = _make_subtask(id="s2", status=SubtaskStatus.IN_PROGRESS)
        s3 = _make_subtask(id="s3", status=SubtaskStatus.TODO)
        snapshot = _make_snapshot(subtasks=(s1, s2, s3))
        resp = MissionService.mission_summary_response(snapshot)

        assert resp.subtask_total == 3
        assert resp.subtask_completed == 1


# ---------------------------------------------------------------------------
# mission_detail_response (static, no DB)
# ---------------------------------------------------------------------------


class TestMissionDetailResponse:
    """Tests for MissionService.mission_detail_response — includes all detail fields."""

    @patch("app.control_plane.application.mission_service.normalize_runtime_reference")
    def test_includes_all_detail_fields(self, mock_normalize):
        mock_normalize.return_value = "/normalized/path"

        snapshot = _make_snapshot()
        resp = MissionService.mission_detail_response(snapshot)

        assert isinstance(resp, DeveloperControlPlaneMissionDetailResponse)

        # Summary fields are present (inherited)
        assert resp.mission_id == "mission-001"
        assert resp.objective == "Deploy feature X"

        # Detail collections
        assert len(resp.subtasks) == 1
        assert resp.subtasks[0].id == "subtask-001"
        assert resp.subtasks[0].title == "Implement widget"
        assert resp.subtasks[0].status == "completed"
        assert resp.subtasks[0].owner_role == "engineer"
        assert resp.subtasks[0].depends_on == []
        assert resp.subtasks[0].updated_at == _NOW.isoformat()

        assert len(resp.assignments) == 1
        assert resp.assignments[0].id == "assignment-001"
        assert resp.assignments[0].subtask_id == "subtask-001"
        assert resp.assignments[0].assigned_role == "engineer"
        assert resp.assignments[0].completed_at is None

        assert len(resp.evidence_items) == 1
        assert resp.evidence_items[0].id == "evidence-001"
        assert resp.evidence_items[0].source_path == "/normalized/path"

        assert len(resp.verification_runs) == 1
        assert resp.verification_runs[0].id == "vr-001"
        assert resp.verification_runs[0].result == "passed"

        assert len(resp.decision_notes) == 1
        assert resp.decision_notes[0].id == "decision-001"
        assert resp.decision_notes[0].decision_class == "approval"

        assert len(resp.blockers) == 1
        assert resp.blockers[0].id == "blocker-001"
        assert resp.blockers[0].blocker_type == "dependency"

    @patch("app.control_plane.application.mission_service.normalize_runtime_reference")
    def test_empty_collections(self, mock_normalize):
        """Detail response works with empty subtasks, assignments, etc."""
        snapshot = _make_snapshot(
            subtasks=(),
            assignments=(),
            evidence_items=(),
            verification_runs=(),
            decision_notes=(),
            blockers=(),
        )
        resp = MissionService.mission_detail_response(snapshot)

        assert resp.subtasks == []
        assert resp.assignments == []
        assert resp.evidence_items == []
        assert resp.verification_runs == []
        assert resp.decision_notes == []
        assert resp.blockers == []


# ---------------------------------------------------------------------------
# load_runtime_mission_snapshot
# ---------------------------------------------------------------------------


class TestLoadRuntimeMissionSnapshot:
    """Tests for MissionService.load_runtime_mission_snapshot — async DB query."""

    @pytest.mark.asyncio
    async def test_returns_snapshot_when_mission_exists_and_owned(self):
        mission = _make_mission(owner="OmShriMaatreNamaha")
        snapshot = _make_snapshot(mission=mission)

        mock_repo = AsyncMock()
        mock_repo.get_mission = AsyncMock(return_value=mission)

        mock_service = AsyncMock()
        mock_service.repository = mock_repo
        mock_service.get_mission_snapshot = AsyncMock(return_value=snapshot)

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            result = await svc.load_runtime_mission_snapshot(
                organization_id=10,
                mission_id="mission-001",
            )

        assert result is snapshot
        mock_repo.get_mission.assert_awaited_once_with("mission-001")
        mock_service.get_mission_snapshot.assert_awaited_once_with("mission-001")

    @pytest.mark.asyncio
    async def test_returns_none_when_mission_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_mission = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.repository = mock_repo

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            result = await svc.load_runtime_mission_snapshot(
                organization_id=10,
                mission_id="nonexistent",
            )

        assert result is None
        mock_service.get_mission_snapshot.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_mission_has_different_owner(self):
        mission = _make_mission(owner="SomeOtherAgent")

        mock_repo = AsyncMock()
        mock_repo.get_mission = AsyncMock(return_value=mission)

        mock_service = AsyncMock()
        mock_service.repository = mock_repo

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            result = await svc.load_runtime_mission_snapshot(
                organization_id=10,
                mission_id="mission-001",
            )

        assert result is None
        mock_service.get_mission_snapshot.assert_not_awaited()


# ---------------------------------------------------------------------------
# mission_state_response
# ---------------------------------------------------------------------------


class TestMissionStateResponse:
    """Tests for MissionService.mission_state_response — paginated response."""

    @pytest.mark.asyncio
    async def test_returns_paginated_response(self):
        m1 = _make_mission(id="m1", updated_at=_NOW)
        m2 = _make_mission(id="m2", updated_at=_EARLIER)
        snap1 = _make_snapshot(mission=m1)
        snap2 = _make_snapshot(mission=m2)

        mock_repo = AsyncMock()
        mock_repo.list_missions = AsyncMock(return_value=[m1, m2])

        mock_service = AsyncMock()
        mock_service.repository = mock_repo
        mock_service.get_mission_snapshot = AsyncMock(side_effect=[snap1, snap2])

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            resp = await svc.mission_state_response(
                organization_id=10,
                limit=10,
            )

        assert isinstance(resp, DeveloperControlPlaneMissionStateResponse)
        assert resp.count == 2
        assert len(resp.missions) == 2
        # Sorted by updated_at descending — m1 (_NOW) comes first
        assert resp.missions[0].mission_id == "m1"
        assert resp.missions[1].mission_id == "m2"

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        m1 = _make_mission(id="m1", updated_at=_NOW)
        m2 = _make_mission(id="m2", updated_at=_EARLIER)
        snap1 = _make_snapshot(mission=m1)

        mock_repo = AsyncMock()
        mock_repo.list_missions = AsyncMock(return_value=[m1, m2])

        mock_service = AsyncMock()
        mock_service.repository = mock_repo
        mock_service.get_mission_snapshot = AsyncMock(return_value=snap1)

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            resp = await svc.mission_state_response(
                organization_id=10,
                limit=1,
            )

        assert resp.count == 1
        assert len(resp.missions) == 1

    @pytest.mark.asyncio
    async def test_fallback_linkage_search_when_filters_yield_no_matches(self):
        """When queue_job_id filter yields no direct matches, fallback parses source_request."""
        # Direct filter returns empty
        # Fallback returns a mission whose source_request matches
        m_linked = _make_mission(
            id="m-linked",
            queue_job_id=None,
            source_lane_id=None,
            source_board_concurrency_token=None,
            source_request=(
                "Developer control-plane explicit completion write-back "
                "for lane lane-target from queue job job-target. "
                "Context: source_board_concurrency_token=tok-abc."
            ),
            updated_at=_NOW,
        )
        m_unrelated = _make_mission(
            id="m-unrelated",
            queue_job_id=None,
            source_lane_id=None,
            source_board_concurrency_token=None,
            source_request="some unrelated text",
            updated_at=_EARLIER,
        )
        snap_linked = _make_snapshot(mission=m_linked)

        mock_repo = AsyncMock()
        # First call with filter returns empty, second call (fallback) returns all
        mock_repo.list_missions = AsyncMock(
            side_effect=[[], [m_linked, m_unrelated]]
        )

        mock_service = AsyncMock()
        mock_service.repository = mock_repo
        mock_service.get_mission_snapshot = AsyncMock(return_value=snap_linked)

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            resp = await svc.mission_state_response(
                organization_id=10,
                limit=10,
                queue_job_id="job-target",
            )

        # Only the linked mission should be returned (m_unrelated has no matching linkage)
        assert resp.count == 1
        assert resp.missions[0].mission_id == "m-linked"

    @pytest.mark.asyncio
    async def test_no_fallback_when_direct_matches_exist(self):
        """When direct filter returns results, no fallback search is performed."""
        m1 = _make_mission(id="m1", queue_job_id="job-abc", updated_at=_NOW)
        snap1 = _make_snapshot(mission=m1)

        mock_repo = AsyncMock()
        mock_repo.list_missions = AsyncMock(return_value=[m1])

        mock_service = AsyncMock()
        mock_service.repository = mock_repo
        mock_service.get_mission_snapshot = AsyncMock(return_value=snap1)

        db = AsyncMock()
        svc = MissionService(db)

        with patch.object(svc, "_build_service", return_value=mock_service):
            resp = await svc.mission_state_response(
                organization_id=10,
                limit=10,
                queue_job_id="job-abc",
            )

        assert resp.count == 1
        # list_missions called only once (no fallback)
        assert mock_repo.list_missions.await_count == 1
