import pytest

from app.modules.ai.services import OrchestratorMissionStateService, SubtaskStatus, VerificationResult
from app.modules.ai.services.orchestrator_state_postgres import PostgresMissionStateRepository


@pytest.mark.asyncio
async def test_postgres_repository_persists_full_mission_snapshot(async_db_session, test_user):
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    service = OrchestratorMissionStateService(repository)

    mission = await service.register_mission(
        objective="Persist orchestrator state",
        owner="OmShriMaatreNamaha",
        priority="p0",
        producer_key="chaitanya",
        queue_job_id="overnight-lane-control-plane-token1234",
        source_lane_id="control-plane",
        source_board_concurrency_token="token-1234",
        source_request="durable adapter",
        mission_id="mission-pg",
    )
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Persist accepted orchestration objects",
        owner_role="OmNamahShivaya",
        subtask_id="subtask-pg",
    )
    await service.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="OmVishnaveNamah",
        handoff_reason="Verify durable repository behavior",
        assignment_id="assignment-pg",
    )
    await service.record_evidence(
        subtask_id=subtask.id,
        kind="code",
        source_path="backend/app/modules/ai/services/orchestrator_state_postgres.py",
        evidence_class="implementation",
        summary="Durable PostgreSQL adapter added",
        evidence_item_id="evidence-pg",
    )
    await service.record_verification_run(
        subject_id=subtask.id,
        verification_type="pytest",
        result=VerificationResult.PASSED,
        evidence_ref="evidence-pg",
        verification_id="verification-pg",
    )
    await service.record_decision_note(
        mission_id=mission.id,
        decision_class="persistence",
        rationale="Use PostgreSQL first to prove access patterns before SurrealDB integration.",
        authority_source="ADR-010",
        decision_note_id="decision-pg",
    )
    await service.record_blocker(
        mission_id=mission.id,
        blocker_type="next_step",
        impact="API exposure still deferred.",
        escalation_needed=False,
        blocker_id="blocker-pg",
    )
    await service.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)
    await service.complete_mission(mission.id, "Durable repository path proved.")
    await async_db_session.commit()

    second_repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    snapshot = await OrchestratorMissionStateService(second_repository).get_mission_snapshot(mission.id)

    assert snapshot.mission.id == mission.id
    assert snapshot.mission.producer_key == "chaitanya"
    assert snapshot.mission.queue_job_id == "overnight-lane-control-plane-token1234"
    assert snapshot.mission.source_lane_id == "control-plane"
    assert snapshot.mission.source_board_concurrency_token == "token-1234"
    assert snapshot.mission.final_summary == "Durable repository path proved."
    assert [item.id for item in snapshot.subtasks] == ["subtask-pg"]
    assert [item.id for item in snapshot.assignments] == ["assignment-pg"]
    assert [item.id for item in snapshot.evidence_items] == ["evidence-pg"]
    assert [item.id for item in snapshot.verification_runs] == ["verification-pg"]
    assert [item.id for item in snapshot.decision_notes] == ["decision-pg"]
    assert [item.id for item in snapshot.blockers] == ["blocker-pg"]


@pytest.mark.asyncio
async def test_postgres_repository_isolates_by_organization(async_db_session, db_session):
    from app.models.core import Organization, User

    primary_org = Organization(name="Primary Mission Org")
    other_org = Organization(name="Other Mission Org")
    db_session.add(primary_org)
    db_session.add(other_org)
    db_session.commit()
    db_session.refresh(primary_org)
    db_session.refresh(other_org)

    primary_user = User(
        email="primary-mission@example.com",
        hashed_password="password",
        organization_id=primary_org.id,
    )

    other_user = User(
        email="other-mission@example.com",
        hashed_password="password",
        organization_id=other_org.id,
    )
    db_session.add(primary_user)
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(primary_user)
    db_session.refresh(other_user)

    primary_repository = PostgresMissionStateRepository(async_db_session, organization_id=primary_user.organization_id)
    primary_service = OrchestratorMissionStateService(primary_repository)
    await primary_service.register_mission(
        objective="Org one mission",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="org one",
        mission_id="mission-org-one",
    )

    secondary_repository = PostgresMissionStateRepository(async_db_session, organization_id=other_user.organization_id)
    secondary_service = OrchestratorMissionStateService(secondary_repository)
    await secondary_service.register_mission(
        objective="Org two mission",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="org two",
        mission_id="mission-org-two",
    )
    await async_db_session.commit()

    primary_missions = await primary_repository.list_missions()
    secondary_missions = await secondary_repository.list_missions()

    assert [item.id for item in primary_missions] == ["mission-org-one"]
    assert [item.id for item in secondary_missions] == ["mission-org-two"]


@pytest.mark.asyncio
async def test_postgres_repository_rejects_cross_mission_subject_mismatch(async_db_session, test_user):
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    service = OrchestratorMissionStateService(repository)

    mission_one = await service.register_mission(
        objective="Mission one",
        owner="OmShriMaatreNamaha",
        priority="p2",
        source_request="one",
        mission_id="mission-one",
    )
    mission_two = await service.register_mission(
        objective="Mission two",
        owner="OmShriMaatreNamaha",
        priority="p2",
        source_request="two",
        mission_id="mission-two",
    )
    subtask = await service.add_subtask(
        mission_id=mission_one.id,
        title="Subtask one",
        owner_role="OmShriGaneshayaNamah",
        subtask_id="subtask-one",
    )

    with pytest.raises(ValueError, match="does not belong to mission"):
        await service.record_evidence(
            mission_id=mission_two.id,
            subtask_id=subtask.id,
            kind="doc",
            source_path=".ai/decisions/ADR-012-orchestrator-authority-and-state-bootstrap.md",
            evidence_class="decision",
            summary="Mismatched subject",
        )


@pytest.mark.asyncio
async def test_postgres_repository_filters_missions_by_owner_queue_and_lane(async_db_session, test_user):
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    service = OrchestratorMissionStateService(repository)

    await service.register_mission(
        objective="Linked control-plane mission",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="structured linkage",
        queue_job_id="overnight-lane-control-plane-token1234",
        source_lane_id="control-plane",
        source_board_concurrency_token="token-1234",
        mission_id="mission-linked",
    )
    await service.register_mission(
        objective="Other control-plane mission",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="structured linkage",
        queue_job_id="overnight-lane-other-token9999",
        source_lane_id="other-lane",
        mission_id="mission-other",
    )
    await service.register_mission(
        objective="Different owner mission",
        owner="CHAITANYA",
        priority="p1",
        source_request="structured linkage",
        queue_job_id="overnight-lane-control-plane-token1234",
        source_lane_id="control-plane",
        mission_id="mission-chaitanya",
    )
    await async_db_session.commit()

    filtered = await repository.list_missions(
        owner="OmShriMaatreNamaha",
        queue_job_id="overnight-lane-control-plane-token1234",
        source_lane_id="control-plane",
    )

    assert [mission.id for mission in filtered] == ["mission-linked"]