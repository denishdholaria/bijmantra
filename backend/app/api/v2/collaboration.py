"""
Collaboration API - Real-time team collaboration endpoints

Provides:
- Team member management
- Real-time chat (WebSocket integration ready)
- Shared items (trials, studies, germplasm, reports)
- Activity feed
- Presence tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, ConfigDict

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    status: str  # online, away, offline
    last_active: Optional[str] = None


class SharedItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str  # trial, study, germplasm, report
    name: str
    shared_by: str
    shared_at: str
    permission: str  # view, edit, admin


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user: str
    action: str
    target: str
    timestamp: str
    type: str  # create, update, share, comment


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender: str
    content: str
    timestamp: str
    is_own: bool
    conversation_id: str


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str  # team, direct
    participants: List[str]
    last_message: Optional[str] = None
    unread_count: int = 0


class CreateMessageRequest(BaseModel):
    conversation_id: str
    content: str


class ShareItemRequest(BaseModel):
    item_type: str
    item_id: str
    user_ids: List[str]
    permission: str = "view"


class UpdatePresenceRequest(BaseModel):
    status: str  # online, away, offline


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/team-members", response_model=List[TeamMemberResponse])
async def get_team_members(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all team members in the user's organization"""
    
    # Query users in same organization
    result = await db.execute(
        select(User).where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active == True
            )
        )
    )
    users = result.scalars().all()
    
    # Convert to response format
    team_members = []
    for user in users:
        # Calculate status based on last_active
        status = "offline"
        last_active_str = None
        
        if user.last_active:
            time_diff = datetime.now(timezone.utc) - user.last_active
            if time_diff < timedelta(minutes=5):
                status = "online"
            elif time_diff < timedelta(minutes=30):
                status = "away"
                last_active_str = f"{int(time_diff.total_seconds() / 60)} min ago"
            else:
                hours = int(time_diff.total_seconds() / 3600)
                if hours < 24:
                    last_active_str = f"{hours} hours ago"
                else:
                    last_active_str = f"{int(hours / 24)} days ago"
        
        team_members.append(TeamMemberResponse(
            id=str(user.id),
            name=user.full_name or user.username,
            email=user.email,
            role=user.role or "Member",
            avatar=None,  # TODO: Add avatar support
            status=status,
            last_active=last_active_str
        ))
    
    return team_members


@router.get("/shared-items", response_model=List[SharedItemResponse])
async def get_shared_items(
    item_type: Optional[str] = Query(None, description="Filter by type: trial, study, germplasm, report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get items shared with the current user"""
    
    # TODO: Implement proper sharing table
    # For now, return demo data structure
    shared_items = []
    
    # This would query a sharing table in production:
    # SELECT * FROM shared_items WHERE user_id = current_user.id
    
    return shared_items


@router.post("/share-item")
async def share_item(
    request: ShareItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Share an item with other users"""
    
    # TODO: Implement sharing table
    # INSERT INTO shared_items (item_type, item_id, shared_by, shared_with, permission)
    
    return {
        "success": True,
        "message": f"Shared {request.item_type} with {len(request.user_ids)} users"
    }


@router.get("/activity", response_model=List[ActivityResponse])
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent activity feed for the team"""
    
    # TODO: Implement activity log table
    # For now, return empty list
    activities = []
    
    # This would query an activity_log table in production:
    # SELECT * FROM activity_log 
    # WHERE organization_id = current_user.organization_id
    # ORDER BY timestamp DESC
    # LIMIT limit OFFSET offset
    
    return activities


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all conversations for the current user"""
    
    # TODO: Implement conversations table
    # For now, return team chat only
    conversations = [
        ConversationResponse(
            id="team",
            name="Team Chat",
            type="team",
            participants=[],
            last_message=None,
            unread_count=0
        )
    ]
    
    return conversations


@router.get("/messages/{conversation_id}", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages for a conversation"""
    
    # TODO: Implement messages table
    # For now, return empty list
    messages = []
    
    # This would query a messages table in production:
    # SELECT * FROM messages 
    # WHERE conversation_id = conversation_id
    # ORDER BY timestamp DESC
    # LIMIT limit OFFSET offset
    
    return messages


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    request: CreateMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to a conversation"""
    
    # TODO: Implement message creation
    # INSERT INTO messages (conversation_id, sender_id, content, timestamp)
    
    # TODO: Broadcast via WebSocket to conversation participants
    
    return MessageResponse(
        id="new-msg-id",
        sender=current_user.full_name or current_user.username,
        content=request.content,
        timestamp=datetime.now(timezone.utc).strftime("%I:%M %p"),
        is_own=True,
        conversation_id=request.conversation_id
    )


@router.post("/presence")
async def update_presence(
    request: UpdatePresenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user's online presence status"""
    
    # Update last_active timestamp
    current_user.last_active = datetime.now(timezone.utc)
    await db.commit()
    
    # TODO: Broadcast presence update via WebSocket
    
    return {
        "success": True,
        "status": request.status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stats")
async def get_collaboration_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get collaboration statistics"""
    
    # Count team members
    result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active == True
            )
        )
    )
    total_members = result.scalar() or 0
    
    # Count online members (active in last 5 minutes)
    five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active == True,
                User.last_active >= five_min_ago
            )
        )
    )
    online_members = result.scalar() or 0
    
    return {
        "team_members": total_members,
        "online_now": online_members,
        "shared_items": 0,  # TODO: Count from sharing table
        "today_activity": 0,  # TODO: Count from activity_log
        "unread_messages": 0  # TODO: Count from messages table
    }
