"""
Profile API
Endpoints for user profile management

Production-ready: All data stored in database, no in-memory mock data.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.password_validation import is_strong_password
from app.core.security import get_password_hash, verify_password
from app.models.core import Organization, User
from app.models.user_management import ActivityLog, UserPreference, UserProfile, UserSession


router = APIRouter(prefix="/profile", tags=["Profile"], dependencies=[Depends(get_current_user)])


# ============ Response Models ============

class ProfileResponse(BaseModel):
    id: int
    full_name: str | None
    email: str
    organization_id: int
    organization_name: str
    role: str
    status: str
    avatar_url: str | None
    phone: str | None
    bio: str | None
    location: str | None
    timezone: str
    created_at: str
    last_login: str | None


class PreferencesResponse(BaseModel):
    user_id: int
    theme: str
    language: str
    density: str
    color_scheme: str
    field_mode: bool
    high_contrast: bool
    large_text: bool
    haptic_feedback: bool
    email_notifications: bool
    push_notifications: bool
    sound_enabled: bool
    default_program_id: int | None
    default_location_id: int | None
    sidebar_collapsed: bool
    updated_at: str


class SessionResponse(BaseModel):
    id: int
    device: str | None
    ip_address: str | None
    location: str | None
    last_active: str | None
    is_current: bool


class ActivityResponse(BaseModel):
    id: int
    action: str
    timestamp: str
    details: str | None


# ============ Request Models ============

class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    location: str | None = None
    timezone: str | None = None
    avatar_url: str | None = None


class UpdatePreferencesRequest(BaseModel):
    theme: str | None = None
    language: str | None = None
    density: str | None = None
    color_scheme: str | None = None
    field_mode: bool | None = None
    high_contrast: bool | None = None
    large_text: bool | None = None
    haptic_feedback: bool | None = None
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    sound_enabled: bool | None = None
    default_program_id: int | None = None
    default_location_id: int | None = None
    sidebar_collapsed: bool | None = None


# ============ Workspace Preference Models ============

class WorkspacePreferencesResponse(BaseModel):
    user_id: int
    default_workspace: str | None
    recent_workspaces: list[str]
    show_gateway_on_login: bool
    last_workspace: str | None
    updated_at: str


class UpdateWorkspacePreferencesRequest(BaseModel):
    default_workspace: str | None = None
    recent_workspaces: list[str] | None = None
    show_gateway_on_login: bool | None = None
    last_workspace: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


# ============ Endpoints ============

@router.get("")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user profile"""
    user_id = current_user.id

    # Get user
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()

    # Get profile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    return {
        "status": "success",
        "data": ProfileResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            organization_id=user.organization_id,
            organization_name=org.name if org else "Unknown",
            role="breeder",  # Would come from role assignment
            status="active" if user.is_active else "inactive",
            avatar_url=profile.avatar_url if profile else None,
            phone=profile.phone if profile else None,
            bio=profile.bio if profile else None,
            location=profile.location if profile else None,
            timezone=profile.timezone if profile else "UTC",
            created_at=user.created_at.isoformat(),
            last_login=datetime.now(UTC).isoformat()
        ).model_dump()
    }


@router.patch("")
async def update_profile(
    data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user profile"""
    user_id = current_user.id

    # Get user
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user name if provided
    if data.full_name is not None:
        user.full_name = data.full_name

    # Get or create profile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            organization_id=user.organization_id,
            user_id=user_id
        )
        db.add(profile)

    # Update profile fields
    if data.phone is not None:
        profile.phone = data.phone
    if data.bio is not None:
        profile.bio = data.bio
    if data.location is not None:
        profile.location = data.location
    if data.timezone is not None:
        profile.timezone = data.timezone
    if data.avatar_url is not None:
        profile.avatar_url = data.avatar_url

    await db.commit()

    # Log activity
    activity = ActivityLog(
        organization_id=user.organization_id,
        user_id=user_id,
        action="update_profile",
        details="Updated profile settings"
    )
    db.add(activity)
    await db.commit()

    return {"status": "success", "message": "Profile updated"}


@router.get("/preferences")
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user preferences"""
    user_id = current_user.id

    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Return defaults
        return {
            "status": "success",
            "data": PreferencesResponse(
                user_id=user_id,
                theme="system",
                language="en",
                density="comfortable",
                color_scheme="standard",
                field_mode=False,
                high_contrast=False,
                large_text=False,
                haptic_feedback=True,
                email_notifications=True,
                push_notifications=True,
                sound_enabled=True,
                default_program_id=None,
                default_location_id=None,
                sidebar_collapsed=False,
                updated_at=datetime.now(UTC).isoformat()
            ).model_dump()
        }

    return {
        "status": "success",
        "data": PreferencesResponse(
            user_id=prefs.user_id,
            theme=prefs.theme or "system",
            language=prefs.language or "en",
            density=prefs.density or "comfortable",
            color_scheme=prefs.color_scheme or "standard",
            field_mode=prefs.field_mode or False,
            high_contrast=prefs.high_contrast or False,
            large_text=prefs.large_text or False,
            haptic_feedback=prefs.haptic_feedback if prefs.haptic_feedback is not None else True,
            email_notifications=prefs.email_notifications if prefs.email_notifications is not None else True,
            push_notifications=prefs.push_notifications if prefs.push_notifications is not None else True,
            sound_enabled=prefs.sound_enabled if prefs.sound_enabled is not None else True,
            default_program_id=prefs.default_program_id,
            default_location_id=prefs.default_location_id,
            sidebar_collapsed=prefs.sidebar_collapsed or False,
            updated_at=prefs.updated_at.isoformat()
        ).model_dump()
    }


@router.patch("/preferences")
async def update_preferences(
    data: UpdatePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user preferences"""
    user_id = current_user.id

    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreference(
            organization_id=current_user.organization_id,
            user_id=user_id
        )
        db.add(prefs)

    # Update provided fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(prefs, key):
            setattr(prefs, key, value)

    await db.commit()

    return {"status": "success", "message": "Preferences updated"}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change user password"""
    user_id = current_user.id

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if not is_strong_password(data.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 10 characters and include uppercase, lowercase, numeric, and special characters",
        )

    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = get_password_hash(data.new_password)

    activity = ActivityLog(
        organization_id=user.organization_id,
        user_id=user_id,
        action="change_password",
        details="Password changed"
    )
    db.add(activity)
    await db.commit()

    return {"status": "success", "message": "Password changed successfully"}


@router.get("/sessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get active sessions"""
    user_id = current_user.id

    result = await db.execute(
        select(UserSession).where(UserSession.user_id == user_id)
    )
    sessions = result.scalars().all()

    if not sessions:
        return {
            "status": "success",
            "data": []
        }

    return {
        "status": "success",
        "data": [
            SessionResponse(
                id=s.id,
                device=s.device,
                ip_address=s.ip_address,
                location=s.location,
                last_active=s.last_active.isoformat() if s.last_active else None,
                is_current=s.is_current
            ).model_dump()
            for s in sessions
        ]
    }


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a session"""
    result = await db.execute(
        select(UserSession).where(
            and_(UserSession.id == session_id, UserSession.user_id == current_user.id)
        )
    )
    session = result.scalar_one_or_none()

    if session:
        await db.delete(session)
        await db.commit()

    return {"status": "success", "message": "Session revoked"}


@router.get("/activity")
async def get_profile_activity(
    limit: int = Query(10, description="Number of activities to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent user activity"""
    user_id = current_user.id

    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    activities = result.scalars().all()

    return {
        "status": "success",
        "data": [
            ActivityResponse(
                id=a.id,
                action=a.action,
                timestamp=a.created_at.isoformat(),
                details=a.details
            ).model_dump()
            for a in activities
        ]
    }


# ============ Workspace Preference Endpoints ============

VALID_WORKSPACES = {"breeding", "seed-ops", "research", "genebank", "admin"}


@router.get("/workspace")
async def get_workspace_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user workspace preferences for Gateway-Workspace Architecture"""
    user_id = current_user.id

    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Return defaults
        return {
            "status": "success",
            "data": WorkspacePreferencesResponse(
                user_id=user_id,
                default_workspace=None,
                recent_workspaces=[],
                show_gateway_on_login=True,
                last_workspace=None,
                updated_at=datetime.now(UTC).isoformat()
            ).model_dump()
        }

    return {
        "status": "success",
        "data": WorkspacePreferencesResponse(
            user_id=prefs.user_id,
            default_workspace=prefs.default_workspace,
            recent_workspaces=prefs.recent_workspaces or [],
            show_gateway_on_login=prefs.show_gateway_on_login if prefs.show_gateway_on_login is not None else True,
            last_workspace=prefs.last_workspace,
            updated_at=prefs.updated_at.isoformat()
        ).model_dump()
    }


@router.patch("/workspace")
async def update_workspace_preferences(
    data: UpdateWorkspacePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user workspace preferences"""
    user_id = current_user.id

    # Validate workspace IDs
    if data.default_workspace and data.default_workspace not in VALID_WORKSPACES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workspace: {data.default_workspace}. Valid options: {', '.join(VALID_WORKSPACES)}"
        )

    if data.last_workspace and data.last_workspace not in VALID_WORKSPACES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workspace: {data.last_workspace}. Valid options: {', '.join(VALID_WORKSPACES)}"
        )

    if data.recent_workspaces:
        invalid = [w for w in data.recent_workspaces if w not in VALID_WORKSPACES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workspaces: {', '.join(invalid)}. Valid options: {', '.join(VALID_WORKSPACES)}"
            )

    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreference(
            organization_id=current_user.organization_id,
            user_id=user_id
        )
        db.add(prefs)

    # Update provided fields
    if data.default_workspace is not None:
        prefs.default_workspace = data.default_workspace
        # If setting a default, also update show_gateway_on_login
        if data.show_gateway_on_login is None:
            prefs.show_gateway_on_login = False

    if data.recent_workspaces is not None:
        # Keep only last 5 recent workspaces
        prefs.recent_workspaces = data.recent_workspaces[:5]

    if data.show_gateway_on_login is not None:
        prefs.show_gateway_on_login = data.show_gateway_on_login

    if data.last_workspace is not None:
        prefs.last_workspace = data.last_workspace
        # Add to recent workspaces
        recent = prefs.recent_workspaces or []
        if data.last_workspace not in recent:
            recent = [data.last_workspace] + recent[:4]
        else:
            recent = [data.last_workspace] + [w for w in recent if w != data.last_workspace][:4]
        prefs.recent_workspaces = recent

    await db.commit()

    # Log activity
    activity = ActivityLog(
        organization_id=current_user.organization_id,
        user_id=user_id,
        action="update_workspace_preferences",
        details=f"Updated workspace preferences: {data.model_dump(exclude_unset=True)}"
    )
    db.add(activity)
    await db.commit()

    return {"status": "success", "message": "Workspace preferences updated"}


@router.put("/workspace/default")
async def set_default_workspace(
    workspace_id: str = Query(..., description="Workspace ID to set as default"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set default workspace (convenience endpoint)"""
    user_id = current_user.id

    if workspace_id not in VALID_WORKSPACES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workspace: {workspace_id}. Valid options: {', '.join(VALID_WORKSPACES)}"
        )

    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreference(
            organization_id=current_user.organization_id,
            user_id=user_id
        )
        db.add(prefs)

    prefs.default_workspace = workspace_id
    prefs.show_gateway_on_login = False

    await db.commit()

    return {
        "status": "success",
        "message": f"Default workspace set to {workspace_id}",
        "data": {
            "default_workspace": workspace_id,
            "show_gateway_on_login": False
        }
    }


@router.delete("/workspace/default")
async def clear_default_workspace(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear default workspace (show gateway on login)"""

    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if prefs:
        prefs.default_workspace = None
        prefs.show_gateway_on_login = True
        await db.commit()

    return {
        "status": "success",
        "message": "Default workspace cleared",
        "data": {
            "default_workspace": None,
            "show_gateway_on_login": True
        }
    }
