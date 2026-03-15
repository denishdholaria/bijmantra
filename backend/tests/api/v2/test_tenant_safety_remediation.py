from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.api.v2 import proposals as proposals_api
from app.api.v2 import team_management
from app.models.core import User
from app.models.proposal import ActionType, ProposalStatus
from app.modules.breeding.services.cross_service import CrossService
from app.modules.breeding.services.trial_planning_service import TrialPlanningService
from app.schemas.germplasm import CrossCreate


def _proposal_payload(
    *,
    proposal_id: int,
    organization_id: int,
    user_id: int,
    status: ProposalStatus,
) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "id": proposal_id,
        "organization_id": organization_id,
        "user_id": user_id,
        "title": "Scoped proposal",
        "description": "Tenant-safe proposal response",
        "action_type": ActionType.CREATE_TRIAL.value,
        "target_data": {"trialName": "Scoped Trial"},
        "ai_rationale": "Tenant-safe router binding",
        "confidence_score": 88,
        "status": status.value,
        "reviewer_notes": "ok",
        "execution_result": {},
        "created_at": now,
        "updated_at": now,
        "executed_at": None,
        "created_by_ai": True,
    }


class RecordingProposalService:
    def __init__(self, organization_id: int, user_id: int):
        self.organization_id = organization_id
        self.user_id = user_id
        self.list_calls: list[dict] = []
        self.get_calls: list[dict] = []
        self.review_calls: list[dict] = []
        self.execute_calls: list[dict] = []

    async def list_proposals(self, db, organization_id: int, status=None, limit: int = 50):
        self.list_calls.append({"organization_id": organization_id, "status": status, "limit": limit})
        return [
            _proposal_payload(
                proposal_id=1,
                organization_id=organization_id,
                user_id=self.user_id,
                status=ProposalStatus.DRAFT,
            )
        ]

    async def get_proposal(self, db, proposal_id: int, organization_id: int):
        self.get_calls.append({"proposal_id": proposal_id, "organization_id": organization_id})
        return _proposal_payload(
            proposal_id=proposal_id,
            organization_id=organization_id,
            user_id=self.user_id,
            status=ProposalStatus.DRAFT,
        )

    async def review_proposal(
        self,
        db,
        proposal_id: int,
        organization_id: int,
        approved: bool,
        reviewer_id: int,
        notes: str = "",
    ):
        self.review_calls.append(
            {
                "proposal_id": proposal_id,
                "organization_id": organization_id,
                "approved": approved,
                "reviewer_id": reviewer_id,
                "notes": notes,
            }
        )
        return _proposal_payload(
            proposal_id=proposal_id,
            organization_id=organization_id,
            user_id=self.user_id,
            status=ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED,
        )

    async def execute_proposal(self, db, proposal_id: int, organization_id: int, user_id: int):
        self.execute_calls.append(
            {
                "proposal_id": proposal_id,
                "organization_id": organization_id,
                "user_id": user_id,
            }
        )
        return _proposal_payload(
            proposal_id=proposal_id,
            organization_id=organization_id,
            user_id=user_id,
            status=ProposalStatus.EXECUTED,
        )


class FakeDBSession:
    def __init__(self):
        self.added = None

    def add(self, obj):
        self.added = obj

    async def commit(self):
        return None

    async def refresh(self, obj):
        obj.id = 12
        obj.created_at = datetime.now(UTC)


class ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class ServiceDBSession(FakeDBSession):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    async def execute(self, stmt):
        if not self._values:
            raise AssertionError("Unexpected execute call")
        return ScalarResult(self._values.pop(0))


@pytest.mark.asyncio
async def test_team_management_get_member_rejects_foreign_user(monkeypatch: pytest.MonkeyPatch):
    async def fake_get_user_in_org(db, user_id: int, organization_id: int):
        assert user_id == 77
        assert organization_id == 5
        return None

    monkeypatch.setattr(team_management, "get_user_in_org", fake_get_user_in_org)

    with pytest.raises(team_management.HTTPException) as exc_info:
        await team_management.get_member(
            member_id=77,
            db=FakeDBSession(),
            current_user=SimpleNamespace(id=10, organization_id=5),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Member not found"


@pytest.mark.asyncio
async def test_team_management_create_team_binds_current_user_org(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, int | None] = {}

    async def fake_ensure_lead_in_org(db, lead_id: int | None, organization_id: int):
        captured["lead_id"] = lead_id
        captured["organization_id"] = organization_id

    monkeypatch.setattr(team_management, "ensure_lead_in_org", fake_ensure_lead_in_org)

    db = FakeDBSession()
    response = await team_management.create_team(
        data=team_management.CreateTeamRequest(
            name="Scoped Team",
            description="Tenant-scoped creation",
            lead_id=33,
        ),
        db=db,
        current_user=SimpleNamespace(id=10, organization_id=7),
        _=None,
    )

    assert captured == {"lead_id": 33, "organization_id": 7}
    assert db.added.organization_id == 7
    assert response["data"]["id"] == 12


@pytest.mark.asyncio
async def test_team_management_create_invite_rejects_foreign_team(monkeypatch: pytest.MonkeyPatch):
    async def fake_get_team_in_org(db, team_id: int, organization_id: int):
        assert team_id == 44
        assert organization_id == 9
        return None

    monkeypatch.setattr(team_management, "get_team_in_org", fake_get_team_in_org)

    with pytest.raises(team_management.HTTPException) as exc_info:
        await team_management.create_invite(
            data=team_management.CreateInviteRequest(
                email="scoped@example.com",
                role="viewer",
                team_id=44,
            ),
            db=FakeDBSession(),
            current_user=SimpleNamespace(id=20, organization_id=9),
            _=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Team not found"


@pytest.mark.asyncio
async def test_team_management_resend_invite_rejects_foreign_invite(monkeypatch: pytest.MonkeyPatch):
    async def fake_get_invite_in_org(db, invite_id: int, organization_id: int):
        assert invite_id == 55
        assert organization_id == 11
        return None

    monkeypatch.setattr(team_management, "get_invite_in_org", fake_get_invite_in_org)

    with pytest.raises(team_management.HTTPException) as exc_info:
        await team_management.resend_invite(
            invite_id=55,
            db=FakeDBSession(),
            current_user=SimpleNamespace(id=30, organization_id=11),
            _=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Invitation not found"


@pytest.mark.asyncio
async def test_proposals_router_binds_org_and_user_from_current_user(
    authenticated_client: AsyncClient,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    service = RecordingProposalService(test_user.organization_id, test_user.id)
    monkeypatch.setattr(proposals_api, "get_proposal_service", lambda: service)

    list_response = await authenticated_client.get(
        "/api/v2/proposals/?organization_id=999&limit=5"
    )
    assert list_response.status_code == 200
    assert service.list_calls[0]["organization_id"] == test_user.organization_id

    get_response = await authenticated_client.get("/api/v2/proposals/7?organization_id=999")
    assert get_response.status_code == 200
    assert service.get_calls[0]["organization_id"] == test_user.organization_id

    review_response = await authenticated_client.post(
        "/api/v2/proposals/7/review?organization_id=999&user_id=999",
        json={"approved": True, "notes": "Looks good"},
    )
    assert review_response.status_code == 200
    assert service.review_calls[0]["organization_id"] == test_user.organization_id
    assert service.review_calls[0]["reviewer_id"] == test_user.id

    execute_response = await authenticated_client.post(
        "/api/v2/proposals/7/execute?organization_id=999&user_id=999"
    )
    assert execute_response.status_code == 200
    assert service.execute_calls[0]["organization_id"] == test_user.organization_id
    assert service.execute_calls[0]["user_id"] == test_user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"crossingProjectDbId": "foreign-project"}, "Crossing project not found"),
        ({"parent1DbId": "foreign-parent-1"}, "Parent 1 germplasm not found"),
        ({"parent2DbId": "foreign-parent-2"}, "Parent 2 germplasm not found"),
    ],
)
async def test_cross_service_rejects_foreign_org_references(payload: dict, message: str):
    db = ServiceDBSession([None])

    with pytest.raises(ValueError, match=message):
        await CrossService.create_cross(
            db,
            CrossCreate(crossName="Scoped Cross", **payload),
            organization_id=3,
        )

    assert db.added is None


@pytest.mark.asyncio
async def test_trial_planning_service_rejects_foreign_org_program_reference():
    db = ServiceDBSession([None])
    service = TrialPlanningService()

    with pytest.raises(ValueError, match="Program not found"):
        await service.create_trial(
            db,
            organization_id=4,
            data={"name": "Scoped Trial", "programId": "99"},
        )

    assert db.added is None