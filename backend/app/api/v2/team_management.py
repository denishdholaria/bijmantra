"""
Team Management API
Endpoints for managing team members, teams, roles, and invitations

Production-ready: All data stored in database, no in-memory mock data.

RBAC: Write operations require manage:users permission
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
import uuid
import secrets

from app.core.database import get_db
from app.models.core import User
from app.models.user_management import (
    Team,
    Role,
    TeamMember,
    TeamInvitation
)
from app.api.deps import get_current_user
from app.core.permissions import Permission, PermissionChecker

router = APIRouter(prefix="/teams", tags=["Team Management"], dependencies=[Depends(get_current_user)])

# Permission dependencies
require_manage_users = PermissionChecker([Permission.MANAGE_USERS])


# ============ Response Models ============

class MemberResponse(BaseModel):
    id: int
    name: Optional[str]
    email: str
    role: str
    status: str
    joined_at: Optional[str]
    last_active: Optional[str]
    team_ids: List[int]
    avatar: Optional[str]


class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str
    lead_id: Optional[int]
    member_count: int = 0
    project_count: int = 0


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    color: Optional[str]
    member_count: int = 0


class InviteResponse(BaseModel):
    id: int
    email: str
    role: str
    sent_at: Optional[str]
    expires_at: Optional[str]
    status: str
    invited_by: Optional[int]


class TeamStatsResponse(BaseModel):
    total_members: int
    active_members: int
    pending_members: int
    inactive_members: int
    total_teams: int
    pending_invites: int
    admins: int
    by_role: dict


# ============ Request Models ============

class CreateMemberRequest(BaseModel):
    name: str
    email: str
    role: str = "viewer"
    team_ids: List[int] = []


class UpdateMemberRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    team_ids: Optional[List[int]] = None


class CreateTeamRequest(BaseModel):
    name: str
    description: Optional[str] = None
    lead_id: Optional[int] = None


class UpdateTeamRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lead_id: Optional[int] = None


class CreateInviteRequest(BaseModel):
    email: str
    role: str = "viewer"
    team_id: Optional[int] = None


# ============ Helper Functions ============

async def get_member_teams(db: AsyncSession, user_id: int) -> List[int]:
    """Get list of team IDs for a user"""
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return [row[0] for row in result.all()]


# ============ MEMBERS ============

@router.get("/members")
async def get_members(
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status: active, pending, inactive"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all team members with optional filters"""
    # Get users in organization
    query = select(User).where(User.organization_id == organization_id)
    
    if search:
        search_lower = f"%{search.lower()}%"
        query = query.where(
            (User.full_name.ilike(search_lower)) | (User.email.ilike(search_lower))
        )
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    members = []
    for user in users:
        # Get team memberships
        team_ids = await get_member_teams(db, user.id)
        
        # Get member status from team_members table
        member_result = await db.execute(
            select(TeamMember).where(TeamMember.user_id == user.id).limit(1)
        )
        member = member_result.scalar_one_or_none()
        
        member_role = member.role if member else "viewer"
        member_status = member.status if member else ("active" if user.is_active else "inactive")
        joined_at = member.joined_at if member else user.created_at
        last_active = member.last_active if member else None
        
        # Apply filters
        if role and member_role != role:
            continue
        if status and member_status != status:
            continue
        if team_id and team_id not in team_ids:
            continue
        
        members.append(MemberResponse(
            id=user.id,
            name=user.full_name,
            email=user.email,
            role=member_role,
            status=member_status,
            joined_at=joined_at.isoformat() if joined_at else None,
            last_active=last_active.isoformat() if last_active else None,
            team_ids=team_ids,
            avatar=None
        ))
    
    return {
        "status": "success",
        "data": [m.model_dump() for m in members],
        "count": len(members)
    }


@router.get("/members/{member_id}")
async def get_member(
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific member by ID"""
    result = await db.execute(
        select(User).where(User.id == member_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    team_ids = await get_member_teams(db, user.id)
    
    # Get teams
    teams_result = await db.execute(
        select(Team).where(Team.id.in_(team_ids)) if team_ids else select(Team).where(False)
    )
    teams = teams_result.scalars().all()
    
    # Get member info
    member_result = await db.execute(
        select(TeamMember).where(TeamMember.user_id == user.id).limit(1)
    )
    member = member_result.scalar_one_or_none()
    
    return {
        "status": "success",
        "data": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "role": member.role if member else "viewer",
            "status": member.status if member else "active",
            "joined_at": (member.joined_at.isoformat() if member and member.joined_at else None),
            "last_active": (member.last_active.isoformat() if member and member.last_active else None),
            "team_ids": team_ids,
            "teams": [{"id": t.id, "name": t.name} for t in teams]
        }
    }


@router.patch("/members/{member_id}")
async def update_member(
    member_id: int,
    data: UpdateMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Update a team member (requires manage:users permission)"""
    result = await db.execute(
        select(User).where(User.id == member_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Update user name if provided
    if data.name is not None:
        user.full_name = data.name
    
    # Update team memberships
    if data.role is not None or data.status is not None:
        member_result = await db.execute(
            select(TeamMember).where(TeamMember.user_id == member_id)
        )
        members = member_result.scalars().all()
        
        for member in members:
            if data.role is not None:
                member.role = data.role
            if data.status is not None:
                member.status = data.status
    
    # Update team assignments if provided
    if data.team_ids is not None:
        # Remove from teams not in new list
        await db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.user_id == member_id,
                    ~TeamMember.team_id.in_(data.team_ids)
                )
            )
        )
        
        # Add to new teams
        current_teams = await get_member_teams(db, member_id)
        for team_id in data.team_ids:
            if team_id not in current_teams:
                new_member = TeamMember(
                    organization_id=user.organization_id,
                    team_id=team_id,
                    user_id=member_id,
                    role=data.role or "viewer",
                    status="active",
                    joined_at=datetime.now(timezone.utc)
                )
                db.add(new_member)
    
    await db.commit()
    
    return {"status": "success", "message": "Member updated"}


@router.delete("/members/{member_id}")
async def delete_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Remove a team member (requires manage:users permission)"""
    # Remove from all teams
    result = await db.execute(
        select(TeamMember).where(TeamMember.user_id == member_id)
    )
    members = result.scalars().all()
    
    for member in members:
        await db.delete(member)
    
    await db.commit()
    
    return {"status": "success", "message": "Member removed from all teams"}


# ============ TEAMS ============

@router.get("")
async def get_teams(
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all teams"""
    result = await db.execute(
        select(Team).where(Team.organization_id == organization_id)
    )
    teams = result.scalars().all()
    
    teams_with_stats = []
    for team in teams:
        # Count members
        member_count_result = await db.execute(
            select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team.id)
        )
        member_count = member_count_result.scalar() or 0
        
        teams_with_stats.append(TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_at=team.created_at.isoformat(),
            lead_id=team.lead_id,
            member_count=member_count,
            project_count=0
        ))
    
    return {
        "status": "success",
        "data": [t.model_dump() for t in teams_with_stats],
        "count": len(teams_with_stats)
    }


@router.get("/{team_id}")
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific team with members"""
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get members
    members_result = await db.execute(
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    )
    member_rows = members_result.all()
    
    members = []
    for tm, user in member_rows:
        members.append({
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "role": tm.role,
            "status": tm.status,
            "joined_at": tm.joined_at.isoformat() if tm.joined_at else None
        })
    
    return {
        "status": "success",
        "data": {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "created_at": team.created_at.isoformat(),
            "lead_id": team.lead_id,
            "members": members
        }
    }


@router.post("")
async def create_team(
    data: CreateTeamRequest,
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Create a new team (requires manage:users permission)"""
    team = Team(
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        lead_id=data.lead_id
    )
    
    db.add(team)
    await db.commit()
    await db.refresh(team)
    
    return {
        "status": "success",
        "data": TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_at=team.created_at.isoformat(),
            lead_id=team.lead_id,
            member_count=0,
            project_count=0
        ).model_dump(),
        "message": "Team created"
    }


@router.patch("/{team_id}")
async def update_team(
    team_id: int,
    data: UpdateTeamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Update a team (requires manage:users permission)"""
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if data.name is not None:
        team.name = data.name
    if data.description is not None:
        team.description = data.description
    if data.lead_id is not None:
        team.lead_id = data.lead_id
    
    await db.commit()
    
    return {"status": "success", "message": "Team updated"}


@router.delete("/{team_id}")
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Delete a team (requires manage:users permission)"""
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Delete team members first
    members_result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id)
    )
    members = members_result.scalars().all()
    for member in members:
        await db.delete(member)
    
    await db.delete(team)
    await db.commit()
    
    return {"status": "success", "message": "Team deleted"}


# ============ ROLES ============

@router.get("/roles")
async def get_roles(
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all available roles"""
    result = await db.execute(
        select(Role).where(Role.organization_id == organization_id)
    )
    roles = result.scalars().all()
    
    # If no roles exist, return defaults
    if not roles:
        default_roles = [
            RoleResponse(id="admin", name="Admin", description="Full system access", 
                        permissions=["full_access", "manage_users", "system_settings"], color="red", member_count=0),
            RoleResponse(id="breeder", name="Breeder", description="Breeding program management",
                        permissions=["create_trials", "edit_germplasm", "run_analyses"], color="blue", member_count=0),
            RoleResponse(id="technician", name="Technician", description="Field and lab operations",
                        permissions=["collect_data", "view_trials", "upload_images"], color="green", member_count=0),
            RoleResponse(id="viewer", name="Viewer", description="Read-only access",
                        permissions=["view_data", "generate_reports"], color="gray", member_count=0),
        ]
        return {"status": "success", "data": [r.model_dump() for r in default_roles]}
    
    roles_with_counts = []
    for role in roles:
        # Count members with this role
        count_result = await db.execute(
            select(func.count()).select_from(TeamMember).where(TeamMember.role == role.role_id)
        )
        member_count = count_result.scalar() or 0
        
        roles_with_counts.append(RoleResponse(
            id=role.role_id,
            name=role.name,
            description=role.description,
            permissions=role.permissions or [],
            color=role.color,
            member_count=member_count
        ))
    
    return {"status": "success", "data": [r.model_dump() for r in roles_with_counts]}


# ============ INVITES ============

@router.get("/invites")
async def get_invites(
    status: Optional[str] = Query(None, description="Filter: pending, expired"),
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get pending invitations"""
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.organization_id == organization_id)
    )
    invites = result.scalars().all()
    
    now = datetime.now(timezone.utc)
    invite_responses = []
    
    for invite in invites:
        invite_status = invite.status
        if invite.expires_at and invite.expires_at < now and invite_status == "pending":
            invite_status = "expired"
        
        if status is None or invite_status == status:
            invite_responses.append(InviteResponse(
                id=invite.id,
                email=invite.email,
                role=invite.role,
                sent_at=invite.sent_at.isoformat() if invite.sent_at else None,
                expires_at=invite.expires_at.isoformat() if invite.expires_at else None,
                status=invite_status,
                invited_by=invite.invited_by_id
            ))
    
    return {
        "status": "success",
        "data": [i.model_dump() for i in invite_responses],
        "count": len(invite_responses)
    }


@router.post("/invites")
async def create_invite(
    data: CreateInviteRequest,
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Send a new invitation (requires manage:users permission)"""
    invite = TeamInvitation(
        organization_id=organization_id,
        email=data.email,
        role=data.role,
        team_id=data.team_id,
        invited_by_id=current_user.id,
        sent_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        status="pending",
        token=secrets.token_urlsafe(32)
    )
    
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    
    return {
        "status": "success",
        "data": InviteResponse(
            id=invite.id,
            email=invite.email,
            role=invite.role,
            sent_at=invite.sent_at.isoformat(),
            expires_at=invite.expires_at.isoformat(),
            status=invite.status,
            invited_by=invite.invited_by_id
        ).model_dump(),
        "message": f"Invitation sent to {invite.email}"
    }


@router.post("/invites/{invite_id}/resend")
async def resend_invite(
    invite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Resend an invitation (requires manage:users permission)"""
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invite_id)
    )
    invite = result.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    invite.sent_at = datetime.now(timezone.utc)
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    invite.status = "pending"
    
    await db.commit()
    
    return {"status": "success", "message": "Invitation resent"}


@router.delete("/invites/{invite_id}")
async def delete_invite(
    invite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_manage_users),
):
    """Cancel an invitation (requires manage:users permission)"""
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invite_id)
    )
    invite = result.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    await db.delete(invite)
    await db.commit()
    
    return {"status": "success", "message": "Invitation cancelled"}


# ============ STATS ============

@router.get("/stats")
async def get_team_stats(
    organization_id: int = Query(1, description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get team management statistics"""
    # Count users
    users_result = await db.execute(
        select(User).where(User.organization_id == organization_id)
    )
    users = users_result.scalars().all()
    
    total_members = len(users)
    active_members = len([u for u in users if u.is_active])
    
    # Count by status from team_members
    pending_result = await db.execute(
        select(func.count()).select_from(TeamMember).where(
            and_(TeamMember.organization_id == organization_id, TeamMember.status == "pending")
        )
    )
    pending_members = pending_result.scalar() or 0
    
    inactive_result = await db.execute(
        select(func.count()).select_from(TeamMember).where(
            and_(TeamMember.organization_id == organization_id, TeamMember.status == "inactive")
        )
    )
    inactive_members = inactive_result.scalar() or 0
    
    # Count teams
    teams_result = await db.execute(
        select(func.count()).select_from(Team).where(Team.organization_id == organization_id)
    )
    total_teams = teams_result.scalar() or 0
    
    # Count pending invites
    invites_result = await db.execute(
        select(func.count()).select_from(TeamInvitation).where(
            and_(TeamInvitation.organization_id == organization_id, TeamInvitation.status == "pending")
        )
    )
    pending_invites = invites_result.scalar() or 0
    
    # Count admins
    admins_result = await db.execute(
        select(func.count()).select_from(TeamMember).where(
            and_(TeamMember.organization_id == organization_id, TeamMember.role == "admin")
        )
    )
    admins = admins_result.scalar() or 0
    
    # Count by role
    by_role = {}
    for role_id in ["admin", "breeder", "technician", "viewer"]:
        role_result = await db.execute(
            select(func.count()).select_from(TeamMember).where(
                and_(TeamMember.organization_id == organization_id, TeamMember.role == role_id)
            )
        )
        by_role[role_id] = role_result.scalar() or 0
    
    return {
        "status": "success",
        "data": TeamStatsResponse(
            total_members=total_members,
            active_members=active_members,
            pending_members=pending_members,
            inactive_members=inactive_members,
            total_teams=total_teams,
            pending_invites=pending_invites,
            admins=admins,
            by_role=by_role
        ).model_dump()
    }
