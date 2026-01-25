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
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, ConfigDict

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.models.user_management import UserProfile

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
        select(User, UserProfile)
        .outerjoin(UserProfile, User.id == UserProfile.user_id)
        .where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active == True
            )
        )
    )
    users = result.all()
    
    # Convert to response format
    team_members = []
    for user, profile in users:
        # Calculate status based on last_active
        status = "offline"
        last_active_str = None
        
        # Safely access last_active as it might not be in the User model
        last_active = getattr(user, "last_active", None)

        if last_active:
            time_diff = datetime.now(timezone.utc) - last_active
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
            name=user.full_name or getattr(user, "username", user.email),
            email=user.email,
            role=getattr(user, "role", "Member") or "Member",
            avatar=profile.avatar_url if profile else None,
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
    from app.models.collaboration import SharedItem
    
    stmt = select(SharedItem).where(
        and_(
            SharedItem.organization_id == current_user.organization_id,
            SharedItem.shared_with_id == current_user.id
        )
    )
    
    if item_type:
        stmt = stmt.where(SharedItem.item_type == item_type)
        
    stmt = stmt.options(selectinload(SharedItem.shared_by))
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # Transform to response
    response_items = []
    for item in items:
        # Fetch item name? Ideally we join or the client fetches details.
        # For listing, we might return a generic name or the item_id.
        # For now, we return item_id as name placeholder if we don't do a complex polymorphic join.
        sender_name = item.shared_by.full_name if item.shared_by else "Unknown"
        
        response_items.append(SharedItemResponse(
            id=str(item.id),
            type=item.item_type,
            name=f"{item.item_type} #{item.item_id}", # Placeholder name
            shared_by=sender_name,
            shared_at=item.shared_at.strftime("%Y-%m-%d"),
            permission=item.permission
        ))
        
    return response_items


@router.post("/share-item")
async def share_item(
    request: ShareItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Share an item with other users"""
    from app.models.collaboration import SharedItem
    
    count = 0
    for user_id in request.user_ids:
        # Check if already shared
        stmt = select(SharedItem).where(
            and_(
                SharedItem.organization_id == current_user.organization_id,
                SharedItem.item_type == request.item_type,
                SharedItem.item_id == request.item_id,
                SharedItem.shared_with_id == int(user_id)
            )
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            continue
            
        share = SharedItem(
            organization_id=current_user.organization_id,
            item_type=request.item_type,
            item_id=request.item_id,
            shared_by_id=current_user.id,
            shared_with_id=int(user_id),
            permission=request.permission
        )
        db.add(share)
        count += 1
        
    if count > 0:
        await db.commit()
    
    return {
        "success": True,
        "message": f"Shared {request.item_type} with {count} users"
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
