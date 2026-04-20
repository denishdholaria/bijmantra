from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.models.core import Organization, User
from app.models.user_management import Role, UserRole
from app.modules.ai.services.chaitanya.orchestrator import Chaitanya, PostureLevel, SystemPosture, chaitanya
from app.modules.ai.services.orchestrator_state import OrchestratorMissionStateService, VerificationResult
from app.modules.ai.services.orchestrator_state_postgres import PostgresMissionStateRepository


_VIEW_CHAITANYA_MISSIONS_PERMISSION = "view:chaitanya_missions"


def _grant_permission(db_session, *, user: User, permission_code: str) -> None:
    role = Role(
        organization_id=user.organization_id,
        role_id=f"permission-{permission_code.replace(':', '-')}-{user.id}",
        name=f"Permission {permission_code}",
        permissions=[permission_code],
        is_system=False,
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    db_session.add(UserRole(user_id=user.id, role_id=role.id, granted_at=datetime.now(UTC)))
    db_session.commit()


@pytest.fixture
def reset_global_chaitanya_state():
    snapshot = {
        "posture": chaitanya._current_posture,
        "history": list(chaitanya._posture_history),
        "actions": list(chaitanya._orchestrated_actions),
        "counter": chaitanya._action_counter,
        "last_assessment": chaitanya._last_assessment,
        "auto_response": chaitanya._auto_response_enabled,
    }
    chaitanya._current_posture = PostureLevel.NORMAL
    chaitanya._posture_history = []
    chaitanya._orchestrated_actions = []
    chaitanya._action_counter = 0
    chaitanya._last_assessment = None
    chaitanya._auto_response_enabled = True
    yield
    chaitanya._current_posture = snapshot["posture"]
    chaitanya._posture_history = snapshot["history"]
    chaitanya._orchestrated_actions = snapshot["actions"]
    chaitanya._action_counter = snapshot["counter"]
    chaitanya._last_assessment = snapshot["last_assessment"]
    chaitanya._auto_response_enabled = snapshot["auto_response"]


@pytest.mark.asyncio
async def test_chaitanya_manual_posture_api_persists_mission_state(
    authenticated_client,
    async_db_session,
    test_user,
    reset_global_chaitanya_state,
):
    response = await authenticated_client.put(
        "/api/v2/chaitanya/posture",
        json={"level": "elevated", "reason": "manual persistence verification"},
    )

    assert response.status_code == 200
    assert response.json()["current"] == "elevated"

    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    missions = await repository.list_missions()
    mission = next(
        item
        for item in missions
        if item.source_request == "Manual posture override: normal -> elevated. manual persistence verification"
    )
    snapshot = await OrchestratorMissionStateService(repository).get_mission_snapshot(mission.id)

    assert snapshot.mission.status.value == "completed"
    assert snapshot.mission.final_summary == "CHAITANYA posture transition recorded for normal -> elevated"
    assert snapshot.subtasks == ()
    assert len(snapshot.evidence_items) == 1
    assert snapshot.decision_notes[0].decision_class == "posture_transition"


@pytest.mark.asyncio
async def test_chaitanya_auto_response_persists_orchestrated_action(async_db_session, test_user, monkeypatch):
    runtime = Chaitanya()
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    mission_state = OrchestratorMissionStateService(repository)

    from app.modules.core.services.rakshaka import healer

    async def fake_heal(strategy, params=None):
        return SimpleNamespace(result="rate_limited")

    monkeypatch.setattr(healer, "heal", fake_heal)

    await runtime._handle_posture_change(
        PostureLevel.NORMAL,
        PostureLevel.SEVERE,
        mission_state=mission_state,
    )
    await async_db_session.commit()

    missions = await repository.list_missions()
    mission = next(
        item for item in missions if item.objective == "CHAITANYA posture transition: normal -> severe"
    )
    snapshot = await OrchestratorMissionStateService(repository).get_mission_snapshot(mission.id)

    assert snapshot.mission.final_summary == "CHAITANYA posture transition and 1 orchestrated action(s) recorded"
    assert len(snapshot.subtasks) == 1
    assert snapshot.subtasks[0].status.value == "completed"
    assert len(snapshot.assignments) == 1
    assert snapshot.assignments[0].assigned_role == "RAKSHAKA"
    assert len(snapshot.evidence_items) == 2
    assert len(snapshot.verification_runs) == 1
    assert snapshot.verification_runs[0].verification_type == "chaitanya_auto_response"


@pytest.mark.asyncio
async def test_chaitanya_persistence_isolated_by_organization(async_db_session, db_session):
    primary_org = Organization(name="Chaitanya Primary Org")
    secondary_org = Organization(name="Chaitanya Secondary Org")
    db_session.add(primary_org)
    db_session.add(secondary_org)
    db_session.commit()
    db_session.refresh(primary_org)
    db_session.refresh(secondary_org)

    primary_user = User(
        email="chaitanya-primary@example.com",
        hashed_password="password",
        organization_id=primary_org.id,
    )
    secondary_user = User(
        email="chaitanya-secondary@example.com",
        hashed_password="password",
        organization_id=secondary_org.id,
    )
    db_session.add(primary_user)
    db_session.add(secondary_user)
    db_session.commit()
    db_session.refresh(primary_user)
    db_session.refresh(secondary_user)

    primary_runtime = Chaitanya()
    secondary_runtime = Chaitanya()
    primary_repository = PostgresMissionStateRepository(async_db_session, organization_id=primary_user.organization_id)
    secondary_repository = PostgresMissionStateRepository(async_db_session, organization_id=secondary_user.organization_id)

    await primary_runtime.set_posture(
        PostureLevel.HIGH,
        "primary org posture",
        OrchestratorMissionStateService(primary_repository),
    )
    await secondary_runtime.set_posture(
        PostureLevel.LOCKDOWN,
        "secondary org posture",
        OrchestratorMissionStateService(secondary_repository),
    )
    await async_db_session.commit()

    primary_missions = await primary_repository.list_missions()
    secondary_missions = await secondary_repository.list_missions()

    assert [item.source_request for item in primary_missions] == [
        "Manual posture override: normal -> high. primary org posture"
    ]
    assert [item.source_request for item in secondary_missions] == [
        "Manual posture override: normal -> lockdown. secondary org posture"
    ]


@pytest.mark.asyncio
async def test_chaitanya_posture_history_reads_from_durable_state_after_reset(
    authenticated_client,
    reset_global_chaitanya_state,
):
    replay_reason = "durable history replay"
    response = await authenticated_client.put(
        "/api/v2/chaitanya/posture",
        json={"level": "elevated", "reason": replay_reason},
    )
    assert response.status_code == 200

    chaitanya._posture_history = []

    history_response = await authenticated_client.get("/api/v2/chaitanya/posture/history")

    assert history_response.status_code == 200
    payload = history_response.json()
    assert payload["count"] >= 1
    matching = next(item for item in payload["history"] if item.get("reason") == replay_reason)
    assert matching["from"] == "normal"
    assert matching["to"] == "elevated"
    assert matching["manual"] is True


@pytest.mark.asyncio
async def test_chaitanya_actions_reads_from_durable_state_after_reset(
    authenticated_client,
    async_db_session,
    test_user,
    monkeypatch,
    reset_global_chaitanya_state,
):
    runtime = Chaitanya()
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    mission_state = OrchestratorMissionStateService(repository)

    from app.modules.core.services.rakshaka import healer

    async def fake_heal(strategy, params=None):
        return SimpleNamespace(result="rate_limited_readback")

    monkeypatch.setattr(healer, "heal", fake_heal)

    await runtime._handle_posture_change(
        PostureLevel.NORMAL,
        PostureLevel.SEVERE,
        mission_state=mission_state,
    )
    await async_db_session.commit()

    chaitanya._orchestrated_actions = []

    actions_response = await authenticated_client.get("/api/v2/chaitanya/actions")

    assert actions_response.status_code == 200
    payload = actions_response.json()
    assert payload["count"] >= 1
    action = next(
        item
        for item in payload["actions"]
        if item["actions_taken"] == [
            {"system": "rakshaka", "action": "rate_limit", "result": "rate_limited_readback"}
        ]
    )
    assert action["trigger"] == "posture_change_normal_to_severe"
    assert action["systems_involved"] == ["rakshaka"]
    assert action["posture_before"] == "normal"
    assert action["posture_after"] == "severe"
    assert action["success"] is True


@pytest.mark.asyncio
async def test_chaitanya_dashboard_uses_durable_orchestration_projection(
    authenticated_client,
    async_db_session,
    test_user,
    monkeypatch,
    reset_global_chaitanya_state,
):
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    mission_state = OrchestratorMissionStateService(repository)
    await mission_state.register_mission(
        objective="CHAITANYA posture transition: normal -> high",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="Manual posture override: normal -> high. dashboard replay",
        mission_id="mission-dashboard",
    )
    await mission_state.record_evidence(
        mission_id="mission-dashboard",
        kind="security_posture",
        source_path="backend/app/modules/ai/services/chaitanya/orchestrator.py",
        evidence_class="runtime_posture_transition",
        summary="CHAITANYA posture changed from normal to high. Manual=True. Reason: dashboard replay",
        evidence_item_id="evidence-dashboard-posture",
    )
    subtask = await mission_state.add_subtask(
        mission_id="mission-dashboard",
        title="Execute CHAITANYA responses for high posture",
        owner_role="CHAITANYA",
        subtask_id="subtask-dashboard",
    )
    await mission_state.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="PRAHARI",
        handoff_reason="Dashboard projection verification",
        assignment_id="assignment-dashboard",
    )
    await mission_state.record_evidence(
        subtask_id=subtask.id,
        kind="orchestrated_action",
        source_path="backend/app/modules/ai/services/chaitanya/orchestrator.py",
        evidence_class="runtime_action",
        summary="System=prahari; action=contain; result=blocked",
        evidence_item_id="evidence-dashboard-action",
    )
    await mission_state.complete_mission("mission-dashboard", "Dashboard durable replay")
    await async_db_session.commit()

    chaitanya._posture_history = []
    chaitanya._orchestrated_actions = []

    async def fake_assess_posture(mission_state=None):
        return SystemPosture(
            level=PostureLevel.NORMAL,
            health_score=98.0,
            security_score=99.0,
            overall_score=98.6,
            active_threats=0,
            active_anomalies=0,
            blocked_ips=0,
            last_incident=None,
            recommendations=[],
        )

    monkeypatch.setattr(chaitanya, "assess_posture", fake_assess_posture)

    from app.modules.core.services.prahari import security_observer, threat_analyzer, threat_responder
    from app.modules.core.services.rakshaka import anomaly_detector, healer, health_monitor

    monkeypatch.setattr(health_monitor, "get_overall_health", lambda: {"status": "healthy"})
    monkeypatch.setattr(anomaly_detector, "get_active_anomalies", lambda: [])
    monkeypatch.setattr(healer, "get_stats", lambda: {"executions": 0})
    monkeypatch.setattr(security_observer, "get_recent_events", lambda limit=10: [])
    monkeypatch.setattr(threat_analyzer, "get_stats", lambda: {"assessments_24h": 0})
    monkeypatch.setattr(threat_responder, "get_stats", lambda: {"blocked_ips": 0})
    monkeypatch.setattr(threat_responder, "get_blocked_ips", lambda: [])

    dashboard_response = await authenticated_client.get("/api/v2/chaitanya/dashboard")

    assert dashboard_response.status_code == 200
    orchestration = dashboard_response.json()["orchestration"]
    history_item = next(item for item in orchestration["posture_history"] if item.get("reason") == "dashboard replay")
    action_item = next(
        item
        for item in orchestration["recent_actions"]
        if item["actions_taken"] == [
            {"system": "prahari", "action": "contain", "result": "blocked"}
        ]
    )
    assert history_item["from"] == "normal"
    assert history_item["to"] == "high"
    assert action_item["systems_involved"] == ["prahari"]
    assert action_item["actions_taken"] == [
        {"system": "prahari", "action": "contain", "result": "blocked"}
    ]


@pytest.mark.asyncio
async def test_chaitanya_mission_inspection_requires_permission(authenticated_client):
    response = await authenticated_client.get("/api/v2/chaitanya/missions")

    assert response.status_code == 403
    assert response.json()["detail"] == f"Missing permission: {_VIEW_CHAITANYA_MISSIONS_PERMISSION}"


@pytest.mark.asyncio
async def test_chaitanya_permissioned_user_can_list_missions(
    authenticated_client,
    async_db_session,
    db_session,
    test_user,
):
    _grant_permission(db_session, user=test_user, permission_code=_VIEW_CHAITANYA_MISSIONS_PERMISSION)

    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    mission_state = OrchestratorMissionStateService(repository)
    await mission_state.register_mission(
        objective="CHAITANYA posture transition: normal -> elevated",
        owner="OmShriMaatreNamaha",
        priority="p2",
        producer_key="chaitanya",
        source_request="Manual posture override: normal -> elevated. permissioned list",
        mission_id="mission-permissioned-list",
    )
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v2/chaitanya/missions")

    assert response.status_code == 200
    mission_ids = {item["mission_id"] for item in response.json()}
    assert "mission-permissioned-list" in mission_ids


@pytest.mark.asyncio
async def test_chaitanya_permissioned_user_can_get_mission_detail(
    authenticated_client,
    async_db_session,
    db_session,
    test_user,
):
    _grant_permission(db_session, user=test_user, permission_code=_VIEW_CHAITANYA_MISSIONS_PERMISSION)

    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_user.organization_id)
    mission_state = OrchestratorMissionStateService(repository)
    mission = await mission_state.register_mission(
        objective="CHAITANYA posture transition: elevated -> severe",
        owner="OmShriMaatreNamaha",
        priority="p0",
        producer_key="chaitanya",
        source_request="Automatic posture transition: elevated -> severe. permissioned detail",
        mission_id="mission-permissioned-detail",
    )
    await mission_state.complete_mission(mission.id, "Permissioned detail replay")
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v2/chaitanya/missions/mission-permissioned-detail")

    assert response.status_code == 200
    assert response.json()["mission_id"] == "mission-permissioned-detail"


@pytest.mark.asyncio
async def test_chaitanya_permissioned_user_detail_is_tenant_scoped_404(
    authenticated_client,
    async_db_session,
    db_session,
    test_user,
):
    _grant_permission(db_session, user=test_user, permission_code=_VIEW_CHAITANYA_MISSIONS_PERMISSION)

    foreign_org = Organization(name="Foreign Chaitanya Permission Org")
    db_session.add(foreign_org)
    db_session.commit()
    db_session.refresh(foreign_org)

    foreign_repository = PostgresMissionStateRepository(async_db_session, organization_id=foreign_org.id)
    foreign_state = OrchestratorMissionStateService(foreign_repository)
    await foreign_state.register_mission(
        objective="CHAITANYA posture transition: normal -> lockdown",
        owner="OmShriMaatreNamaha",
        priority="p0",
        producer_key="chaitanya",
        source_request="Manual posture override: normal -> lockdown. foreign detail",
        mission_id="mission-foreign-detail",
    )
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v2/chaitanya/missions/mission-foreign-detail")

    assert response.status_code == 404
    assert response.json()["detail"] == "CHAITANYA mission not found"


@pytest.mark.asyncio
async def test_chaitanya_superuser_mission_inspection_returns_sanitized_projection(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_superuser.organization_id)
    mission_state = OrchestratorMissionStateService(repository)
    mission = await mission_state.register_mission(
        objective="CHAITANYA posture transition: elevated -> severe",
        owner="OmShriMaatreNamaha",
        priority="p0",
        producer_key="chaitanya",
        source_request="Automatic posture transition: elevated -> severe. inspection replay",
        mission_id="mission-inspection",
    )
    subtask = await mission_state.add_subtask(
        mission_id=mission.id,
        title="Execute CHAITANYA responses for severe posture",
        owner_role="CHAITANYA",
        subtask_id="subtask-inspection",
    )
    await mission_state.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="RAKSHAKA",
        handoff_reason="internal-only reason should remain hidden",
        assignment_id="assignment-inspection",
    )
    await mission_state.record_evidence(
        mission_id=mission.id,
        kind="security_posture",
        source_path="sensitive/path.py",
        evidence_class="runtime_posture_transition",
        summary="internal posture summary",
        evidence_item_id="evidence-inspection-posture",
    )
    await mission_state.record_evidence(
        subtask_id=subtask.id,
        kind="orchestrated_action",
        source_path="sensitive/action.py",
        evidence_class="runtime_action",
        summary="System=rakshaka; action=rate_limit; result=applied",
        evidence_item_id="evidence-inspection-action",
    )
    await mission_state.record_decision_note(
        mission_id=mission.id,
        decision_class="posture_transition",
        rationale="internal rationale should remain hidden",
        authority_source="CHAITANYA",
        decision_note_id="decision-inspection",
    )
    await mission_state.record_verification_run(
        subject_id=subtask.id,
        verification_type="chaitanya_auto_response",
        result=VerificationResult.PASSED,
        evidence_ref="sensitive-evidence-ref",
        verification_id="verification-inspection",
    )
    await mission_state.complete_mission(mission.id, "Sanitized inspection summary")
    await async_db_session.commit()

    list_response = await superuser_client.get("/api/v2/chaitanya/missions")

    assert list_response.status_code == 200
    summary = next(item for item in list_response.json() if item["mission_id"] == "mission-inspection")
    assert summary["display_title"] == "Posture elevated -> severe"
    assert summary["systems_involved"] == ["rakshaka"]
    assert summary["verification"]["passed"] == 1
    assert "source_request" not in summary
    assert "decision_notes" not in summary

    detail_response = await superuser_client.get("/api/v2/chaitanya/missions/mission-inspection")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["decision_classes"] == ["posture_transition"]
    assert detail["verification_types"] == ["chaitanya_auto_response"]
    assert detail["actions"] == [
        {"system": "rakshaka", "action": "rate_limit", "result": "applied"}
    ]
    assert detail["assignments"][0]["assigned_role"] == "RAKSHAKA"
    assert "source_request" not in detail
    assert "rationale" not in detail
    assert "evidence_ref" not in detail
    assert "impact" not in detail


@pytest.mark.asyncio
async def test_chaitanya_mission_inspection_legacy_rows_fallback_without_producer_key(
    superuser_client,
    async_db_session,
    test_superuser,
):
    repository = PostgresMissionStateRepository(async_db_session, organization_id=test_superuser.organization_id)
    mission_state = OrchestratorMissionStateService(repository)
    await mission_state.register_mission(
        objective="CHAITANYA posture transition: high -> lockdown",
        owner="OmShriMaatreNamaha",
        priority="p0",
        source_request="Manual posture override: high -> lockdown. legacy row",
        mission_id="mission-legacy-fallback",
    )
    await async_db_session.commit()

    response = await superuser_client.get("/api/v2/chaitanya/missions/mission-legacy-fallback")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mission_id"] == "mission-legacy-fallback"
    assert payload["posture_before"] == "high"
    assert payload["posture_after"] == "lockdown"


@pytest.mark.asyncio
async def test_chaitanya_superuser_mission_inspection_is_tenant_scoped(
    superuser_client,
    async_db_session,
    db_session,
    test_superuser,
):
    foreign_org = Organization(name="Foreign Chaitanya Inspection Org")
    db_session.add(foreign_org)
    db_session.commit()
    db_session.refresh(foreign_org)

    foreign_repository = PostgresMissionStateRepository(async_db_session, organization_id=foreign_org.id)
    foreign_state = OrchestratorMissionStateService(foreign_repository)
    await foreign_state.register_mission(
        objective="CHAITANYA posture transition: normal -> lockdown",
        owner="OmShriMaatreNamaha",
        priority="p0",
        source_request="Manual posture override: normal -> lockdown. foreign org",
        mission_id="mission-foreign-org",
    )

    local_repository = PostgresMissionStateRepository(async_db_session, organization_id=test_superuser.organization_id)
    local_state = OrchestratorMissionStateService(local_repository)
    await local_state.register_mission(
        objective="CHAITANYA posture transition: normal -> high",
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request="Manual posture override: normal -> high. local org",
        mission_id="mission-local-org",
    )
    await async_db_session.commit()

    response = await superuser_client.get("/api/v2/chaitanya/missions")

    assert response.status_code == 200
    mission_ids = {item["mission_id"] for item in response.json()}
    assert "mission-local-org" in mission_ids
    assert "mission-foreign-org" not in mission_ids