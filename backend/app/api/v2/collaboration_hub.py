"""
Collaboration Hub API
Team collaboration, real-time presence, and shared workspaces
Database-backed implementation
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid

from app.core.database import get_db
from app.models.core import User
from app.api.deps import get_current_user
from app.models.collaboration import (
    CollaborationWorkspace, WorkspaceMember, UserPresence,
    CollaborationActivity, CollaborationTask, CollaborationComment,
    WorkspaceType, MemberRole, MemberStatus,
    CollabActivityType, TaskStatus, TaskPriority
)

router = APIRouter(prefix="/collaboration-hub", tags=["Collaboration Hub"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class CollaborationStats(BaseModel):
    total_members: int
    online_members: int
    active_workspaces: int
    pending_tasks: int
    comments_today: int
    activities_today: int


# ============================================
# ENDPOINTS
# ============================================

@router.get("/stats", response_model=CollaborationStats)
async def get_collaboration_stats(db: AsyncSession = Depends(get_db)):
    """Get collaboration statistics."""
    # Calculate today's start
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Execute all counts in a single query using scalar subqueries
    # This reduces DB round-trips from 6 to 1
    query = select(
        select(func.count(UserPresence.id)).scalar_subquery(),
        select(func.count(UserPresence.id)).where(
            UserPresence.status.in_([MemberStatus.ONLINE, MemberStatus.BUSY, MemberStatus.AWAY])
        ).scalar_subquery(),
        select(func.count(CollaborationWorkspace.id)).where(
            CollaborationWorkspace.is_active == True
        ).scalar_subquery(),
        select(func.count(CollaborationTask.id)).where(
            CollaborationTask.status != TaskStatus.DONE
        ).scalar_subquery(),
        select(func.count(CollaborationActivity.id)).where(
            CollaborationActivity.created_at >= today_start
        ).scalar_subquery(),
        select(func.count(CollaborationComment.id)).where(
            CollaborationComment.created_at >= today_start
        ).scalar_subquery()
    )

    result = await db.execute(query)
    row = result.one()

    total_members = row[0] or 0
    online_members = row[1] or 0
    active_workspaces = row[2] or 0
    pending_tasks = row[3] or 0
    activities_today = row[4] or 0
    comments_today = row[5] or 0
    
    return CollaborationStats(
        total_members=total_members,
        online_members=online_members,
        active_workspaces=active_workspaces,
        pending_tasks=pending_tasks,
        comments_today=comments_today,
        activities_today=activities_today
    )


# ============================================
# TEAM MEMBERS
# ============================================

@router.get("/members")
async def list_members(
    status: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List team members with presence."""
    query = select(UserPresence).options(selectinload(UserPresence.user))
    
    if status:
        try:
            member_status = MemberStatus(status)
            query = query.where(UserPresence.status == member_status)
        except ValueError:
            pass
    
    result = await db.execute(query)
    presences = result.scalars().all()
    
    members = []
    for p in presences:
        if p.user:
            members.append({
                "id": str(p.user.id),
                "name": p.user.full_name or p.user.email,
                "email": p.user.email,
                "status": p.status.value if p.status else "offline",
                "last_active": p.last_active.isoformat() if p.last_active else None,
                "current_workspace": str(p.current_workspace_id) if p.current_workspace_id else None
            })
    
    return {"members": members, "total": len(members)}


@router.get("/members/online")
async def get_online_members(db: AsyncSession = Depends(get_db)):
    """Get currently online members."""
    result = await db.execute(
        select(UserPresence)
        .options(selectinload(UserPresence.user))
        .where(UserPresence.status.in_([
            MemberStatus.ONLINE, MemberStatus.BUSY, MemberStatus.AWAY
        ]))
    )
    presences = result.scalars().all()
    
    members = []
    for p in presences:
        if p.user:
            members.append({
                "id": str(p.user.id),
                "name": p.user.full_name or p.user.email,
                "email": p.user.email,
                "status": p.status.value if p.status else "offline",
                "last_active": p.last_active.isoformat() if p.last_active else None
            })
    
    return {"members": members, "total": len(members)}


@router.get("/members/{member_id}")
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific team member."""
    result = await db.execute(
        select(UserPresence)
        .options(selectinload(UserPresence.user))
        .where(UserPresence.user_id == member_id)
    )
    presence = result.scalar_one_or_none()
    
    if not presence or not presence.user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {
        "id": str(presence.user.id),
        "name": presence.user.full_name or presence.user.email,
        "email": presence.user.email,
        "status": presence.status.value if presence.status else "offline",
        "last_active": presence.last_active.isoformat() if presence.last_active else None,
        "current_workspace": str(presence.current_workspace_id) if presence.current_workspace_id else None
    }


@router.patch("/members/{member_id}/status")
async def update_member_status(
    member_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Update member's online status."""
    result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == member_id)
    )
    presence = result.scalar_one_or_none()
    
    if not presence:
        # Create presence record if doesn't exist
        presence = UserPresence(
            user_id=member_id,
            status=MemberStatus.ONLINE,
            last_active=datetime.now(timezone.utc)
        )
        db.add(presence)
    
    try:
        presence.status = MemberStatus(status)
    except ValueError:
        presence.status = MemberStatus.ONLINE
    
    presence.last_active = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": "Status updated", "status": presence.status.value}


# ============================================
# WORKSPACES
# ============================================

@router.get("/workspaces")
async def list_workspaces(
    type: Optional[str] = Query(None),
    member_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List shared workspaces."""
    query = select(CollaborationWorkspace).where(
        CollaborationWorkspace.is_active == True
    )
    
    if type:
        try:
            ws_type = WorkspaceType(type)
            query = query.where(CollaborationWorkspace.type == ws_type)
        except ValueError:
            pass
    
    # Filter by member if specified
    if member_id:
        query = query.join(WorkspaceMember).where(
            WorkspaceMember.user_id == member_id
        )

    result = await db.execute(query.order_by(CollaborationWorkspace.updated_at.desc()))
    workspaces = result.scalars().all()
    
    return {
        "workspaces": [
            {
                "id": str(w.id),
                "name": w.name,
                "type": w.type.value if w.type else None,
                "description": w.description,
                "owner_id": str(w.owner_id),
                "entity_id": w.entity_id,
                "is_active": w.is_active,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
            for w in workspaces
        ],
        "total": len(workspaces)
    }


@router.post("/workspaces")
async def create_workspace(
    name: str,
    type: str,
    description: Optional[str] = None,
    members: list[int] = [],
    db: AsyncSession = Depends(get_db)
):
    """Create a new shared workspace."""
    # Get first user as owner (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    owner = user_result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=400, detail="No users found")
    
    try:
        ws_type = WorkspaceType(type)
    except ValueError:
        ws_type = WorkspaceType.TRIAL
    
    workspace = CollaborationWorkspace(
        organization_id=owner.organization_id,
        name=name,
        type=ws_type,
        description=description,
        owner_id=owner.id,
        is_active=True
    )
    
    db.add(workspace)
    await db.flush()
    
    # Add owner as member
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner.id,
        role=MemberRole.OWNER,
        joined_at=datetime.now(timezone.utc)
    )
    db.add(owner_member)
    
    # Add other members
    for member_id in members:
        if member_id != owner.id:
            member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=member_id,
                role=MemberRole.EDITOR,
                joined_at=datetime.now(timezone.utc)
            )
            db.add(member)
    
    await db.commit()
    await db.refresh(workspace)
    
    return {
        "workspace": {
            "id": str(workspace.id),
            "name": workspace.name,
            "type": workspace.type.value
        },
        "message": "Workspace created"
    }


@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: int, db: AsyncSession = Depends(get_db)):
    """Get workspace details."""
    result = await db.execute(
        select(CollaborationWorkspace).where(
            CollaborationWorkspace.id == workspace_id
        )
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get members
    members_result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.user))
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    members = members_result.scalars().all()
    
    return {
        "id": str(workspace.id),
        "name": workspace.name,
        "type": workspace.type.value if workspace.type else None,
        "description": workspace.description,
        "owner_id": str(workspace.owner_id),
        "is_active": workspace.is_active,
        "members": [
            {
                "id": str(m.user_id),
                "name": m.user.full_name if m.user else None,
                "role": m.role.value if m.role else None,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None
            }
            for m in members
        ]
    }


@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Add a member to a workspace."""
    # Verify workspace exists
    ws_result = await db.execute(
        select(CollaborationWorkspace).where(
            CollaborationWorkspace.id == workspace_id
        )
    )
    workspace = ws_result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if already a member
    existing = await db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == member_id
            )
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "Already a member"}
    
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_id,
        role=MemberRole.EDITOR,
        joined_at=datetime.now(timezone.utc)
    )
    db.add(member)
    
    workspace.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": "Member added to workspace"}


@router.delete("/workspaces/{workspace_id}/members/{member_id}")
async def remove_workspace_member(
    workspace_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove a member from a workspace."""
    result = await db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == member_id
            )
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Don't allow removing owner
    if member.role == MemberRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")
    
    await db.delete(member)
    await db.commit()
    
    return {"message": "Member removed from workspace"}


# ============================================
# ACTIVITY FEED
# ============================================

@router.get("/activities")
async def get_activities(
    workspace_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    activity_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get activity feed."""
    query = select(CollaborationActivity).options(
        selectinload(CollaborationActivity.user)
    )
    
    if workspace_id:
        query = query.where(CollaborationActivity.workspace_id == workspace_id)
    if user_id:
        query = query.where(CollaborationActivity.user_id == user_id)
    if activity_type:
        try:
            act_type = CollabActivityType(activity_type)
            query = query.where(CollaborationActivity.activity_type == act_type)
        except ValueError:
            pass
    
    query = query.order_by(CollaborationActivity.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return {
        "activities": [
            {
                "id": str(a.id),
                "user_id": str(a.user_id),
                "user_name": a.user.full_name if a.user else None,
                "activity_type": a.activity_type.value if a.activity_type else None,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "entity_name": a.entity_name,
                "description": a.description,
                "timestamp": a.created_at.isoformat() if a.created_at else None,
                "workspace_id": str(a.workspace_id) if a.workspace_id else None
            }
            for a in activities
        ],
        "total": len(activities)
    }


@router.post("/activities")
async def log_activity(
    activity_type: str,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    description: str,
    workspace_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Log a new activity."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    
    try:
        act_type = CollabActivityType(activity_type)
    except ValueError:
        act_type = CollabActivityType.UPDATED
    
    activity = CollaborationActivity(
        organization_id=user.organization_id,
        workspace_id=workspace_id,
        user_id=user.id,
        activity_type=act_type,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        description=description
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    return {
        "activity": {
            "id": str(activity.id),
            "activity_type": activity.activity_type.value
        }
    }


# ============================================
# TASKS
# ============================================

@router.get("/tasks")
async def list_tasks(
    workspace_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List tasks."""
    query = select(CollaborationTask).options(
        selectinload(CollaborationTask.assignee)
    )
    
    if workspace_id:
        query = query.where(CollaborationTask.workspace_id == workspace_id)
    if assignee_id:
        query = query.where(CollaborationTask.assignee_id == assignee_id)
    if status:
        try:
            task_status = TaskStatus(status)
            query = query.where(CollaborationTask.status == task_status)
        except ValueError:
            pass
    if priority:
        try:
            task_priority = TaskPriority(priority)
            query = query.where(CollaborationTask.priority == task_priority)
        except ValueError:
            pass
    
    query = query.order_by(CollaborationTask.due_date.asc().nullslast())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return {
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "assignee_id": str(t.assignee_id) if t.assignee_id else None,
                "assignee_name": t.assignee.full_name if t.assignee else None,
                "workspace_id": str(t.workspace_id) if t.workspace_id else None,
                "status": t.status.value if t.status else None,
                "priority": t.priority.value if t.priority else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in tasks
        ],
        "total": len(tasks)
    }


@router.post("/tasks")
async def create_task(
    title: str,
    description: Optional[str] = None,
    assignee_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    priority: str = "medium",
    due_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task."""
    # Get first user as creator (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    
    try:
        task_priority = TaskPriority(priority)
    except ValueError:
        task_priority = TaskPriority.MEDIUM
    
    task = CollaborationTask(
        organization_id=user.organization_id,
        workspace_id=workspace_id,
        title=title,
        description=description,
        assignee_id=assignee_id,
        created_by_id=user.id,
        status=TaskStatus.TODO,
        priority=task_priority,
        due_date=due_date
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return {
        "task": {
            "id": str(task.id),
            "title": task.title,
            "status": task.status.value
        },
        "message": "Task created"
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    result = await db.execute(
        select(CollaborationTask).where(CollaborationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status:
        try:
            task.status = TaskStatus(status)
            if task.status == TaskStatus.DONE:
                task.completed_at = datetime.now(timezone.utc)
        except ValueError:
            pass
    if assignee_id is not None:
        task.assignee_id = assignee_id if assignee_id > 0 else None
    if priority:
        try:
            task.priority = TaskPriority(priority)
        except ValueError:
            pass
    
    await db.commit()
    
    return {
        "task": {
            "id": str(task.id),
            "title": task.title,
            "status": task.status.value if task.status else None
        },
        "message": "Task updated"
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a task."""
    result = await db.execute(
        select(CollaborationTask).where(CollaborationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "Task deleted"}


# ============================================
# COMMENTS
# ============================================

@router.get("/comments")
async def get_comments(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get comments for an entity."""
    result = await db.execute(
        select(CollaborationComment)
        .options(selectinload(CollaborationComment.user))
        .where(
            and_(
                CollaborationComment.entity_type == entity_type,
                CollaborationComment.entity_id == entity_id
            )
        )
        .order_by(CollaborationComment.created_at.asc())
    )
    comments = result.scalars().all()
    
    return {
        "comments": [
            {
                "id": str(c.id),
                "user_id": str(c.user_id),
                "user_name": c.user.full_name if c.user else None,
                "content": c.content,
                "entity_type": c.entity_type,
                "entity_id": c.entity_id,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in comments
        ],
        "total": len(comments)
    }


@router.post("/comments")
async def add_comment(
    entity_type: str,
    entity_id: str,
    content: str,
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to an entity."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    
    comment = CollaborationComment(
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        content=content
    )
    
    db.add(comment)
    
    # Log activity
    activity = CollaborationActivity(
        organization_id=user.organization_id,
        user_id=user.id,
        activity_type=CollabActivityType.COMMENTED,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_id,
        description=f"Added comment: {content[:50]}..."
    )
    db.add(activity)
    
    await db.commit()
    await db.refresh(comment)
    
    return {
        "comment": {
            "id": str(comment.id),
            "content": comment.content
        },
        "message": "Comment added"
    }


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a comment."""
    result = await db.execute(
        select(CollaborationComment).where(CollaborationComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    await db.delete(comment)
    await db.commit()
    
    return {"message": "Comment deleted"}


# ============================================
# PRESENCE
# ============================================

@router.post("/presence/join")
async def join_workspace(workspace_id: int, db: AsyncSession = Depends(get_db)):
    """Join a workspace (update presence)."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    
    # Get or create presence
    presence_result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user.id)
    )
    presence = presence_result.scalar_one_or_none()
    
    if not presence:
        presence = UserPresence(
            user_id=user.id,
            status=MemberStatus.ONLINE,
            current_workspace_id=workspace_id,
            last_active=datetime.now(timezone.utc),
            last_heartbeat=datetime.now(timezone.utc)
        )
        db.add(presence)
    else:
        presence.current_workspace_id = workspace_id
        presence.status = MemberStatus.ONLINE
        presence.last_active = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {"message": f"Joined workspace {workspace_id}"}


@router.post("/presence/leave")
async def leave_workspace(db: AsyncSession = Depends(get_db)):
    """Leave current workspace."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        return {"message": "Left workspace"}
    
    presence_result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user.id)
    )
    presence = presence_result.scalar_one_or_none()
    
    if presence:
        presence.current_workspace_id = None
        await db.commit()
    
    return {"message": "Left workspace"}


@router.post("/presence/heartbeat")
async def heartbeat(db: AsyncSession = Depends(get_db)):
    """Update presence heartbeat."""
    # Get first user (in real app, use current user)
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    
    if not user:
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    presence_result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user.id)
    )
    presence = presence_result.scalar_one_or_none()
    
    if presence:
        presence.last_heartbeat = datetime.now(timezone.utc)
        presence.last_active = datetime.now(timezone.utc)
        if presence.status == MemberStatus.OFFLINE:
            presence.status = MemberStatus.ONLINE
        await db.commit()
    
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
