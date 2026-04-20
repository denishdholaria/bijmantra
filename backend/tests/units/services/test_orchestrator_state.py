import pytest

from app.modules.ai.services import (
    MissionStatus,
    OrchestratorMissionStateService,
    SubtaskStatus,
    VerificationResult,
    VolatileMissionStateRepository,
)


@pytest.mark.asyncio
async def test_orchestrator_state_tracks_core_bootstrap_objects():
    service = OrchestratorMissionStateService(VolatileMissionStateRepository())

    mission = await service.register_mission(
        objective="Stabilize mission-state bootstrap",
        owner="OmShriMaatreNamaha",
        priority="p0",
        producer_key="chaitanya",
        queue_job_id="overnight-lane-control-plane-token1234",
        source_lane_id="control-plane",
        source_board_concurrency_token="token-1234",
        source_request="proceed autonomously",
        mission_id="mission-bootstrap",
    )
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Implement storage-neutral interface",
        owner_role="OmNamahShivaya",
        subtask_id="subtask-interface",
    )
    assignment = await service.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="OmVishnaveNamah",
        handoff_reason="Validate the contract after implementation",
        assignment_id="assignment-verify",
    )
    completed_assignment = await service.complete_assignment(assignment.id)
    evidence = await service.record_evidence(
        subtask_id=subtask.id,
        kind="code",
        source_path="backend/app/modules/ai/services/orchestrator_state.py",
        evidence_class="implementation",
        summary="Mission-state interface and volatile adapter added",
        evidence_item_id="evidence-implementation",
    )
    verification = await service.record_verification_run(
        subject_id=subtask.id,
        verification_type="pytest",
        result=VerificationResult.PASSED,
        evidence_ref=evidence.id,
        verification_id="verification-pytest",
    )
    decision = await service.record_decision_note(
        mission_id=mission.id,
        decision_class="bootstrap_scope",
        rationale="Prove the contract before committing to SurrealDB runtime integration.",
        authority_source="ADR-012",
        decision_note_id="decision-bootstrap",
    )
    blocker = await service.record_blocker(
        mission_id=mission.id,
        blocker_type="durability_gap",
        impact="Cross-process persistence still deferred to later adapters.",
        escalation_needed=False,
        blocker_id="blocker-durability",
    )
    subtask = await service.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)
    mission = await service.complete_mission(
        mission.id,
        "Bootstrap mission-state contract proved with repository abstraction and tests.",
    )

    snapshot = await service.get_mission_snapshot(mission.id)

    assert mission.status is MissionStatus.COMPLETED
    assert subtask.status is SubtaskStatus.COMPLETED
    assert completed_assignment.completed_at is not None
    assert verification.evidence_ref == evidence.id
    assert decision.authority_source == "ADR-012"
    assert blocker.escalation_needed is False
    assert snapshot.mission.producer_key == "chaitanya"
    assert snapshot.mission.queue_job_id == "overnight-lane-control-plane-token1234"
    assert snapshot.mission.source_lane_id == "control-plane"
    assert snapshot.mission.source_board_concurrency_token == "token-1234"
    assert snapshot.mission.final_summary is not None
    assert [item.id for item in snapshot.subtasks] == [subtask.id]
    assert [item.id for item in snapshot.assignments] == [assignment.id]
    assert [item.id for item in snapshot.evidence_items] == [evidence.id]
    assert [item.id for item in snapshot.verification_runs] == [verification.id]
    assert [item.id for item in snapshot.decision_notes] == [decision.id]
    assert [item.id for item in snapshot.blockers] == [blocker.id]
    assert snapshot.to_dict()["mission"]["status"] == "completed"


@pytest.mark.asyncio
async def test_add_subtask_rejects_unknown_dependency():
    service = OrchestratorMissionStateService(VolatileMissionStateRepository())
    mission = await service.register_mission(
        objective="Validate dependency wiring",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="dependency validation",
    )

    with pytest.raises(ValueError, match="Unknown subtask dependencies"):
        await service.add_subtask(
            mission_id=mission.id,
            title="Blocked task",
            owner_role="OmNamahShivaya",
            depends_on=("subtask-missing",),
        )


@pytest.mark.asyncio
async def test_record_evidence_for_subtask_inherits_parent_mission():
    service = OrchestratorMissionStateService(VolatileMissionStateRepository())
    mission = await service.register_mission(
        objective="Link evidence correctly",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="evidence linking",
    )
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Gather evidence",
        owner_role="OmShriGaneshayaNamah",
    )

    evidence = await service.record_evidence(
        subtask_id=subtask.id,
        kind="doc",
        source_path=".ai/decisions/ADR-012-orchestrator-authority-and-state-bootstrap.md",
        evidence_class="decision",
        summary="Accepted bootstrap state model",
    )

    assert evidence.mission_id == mission.id
    assert evidence.subtask_id == subtask.id


@pytest.mark.asyncio
async def test_record_verification_run_rejects_unknown_subject():
    service = OrchestratorMissionStateService(VolatileMissionStateRepository())

    with pytest.raises(ValueError, match="Unknown mission or subtask subject"):
        await service.record_verification_run(
            subject_id="subtask-missing",
            verification_type="pytest",
            result=VerificationResult.PASSED,
        )


@pytest.mark.asyncio
async def test_record_blocker_requires_subject_reference():
    service = OrchestratorMissionStateService(VolatileMissionStateRepository())

    with pytest.raises(ValueError, match="mission_id or subtask_id"):
        await service.record_blocker(
            blocker_type="scope_gap",
            impact="No mission context",
            escalation_needed=True,
        )