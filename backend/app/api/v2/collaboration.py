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
from app.models.collaboration import (
    Conversation,
    ConversationParticipant,
    Message,
    ConversationType
)

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
    from app.models.collaboration import SharedItem, CollaborationActivity, CollabActivityType
    
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
        # Create activity log
        activity = CollaborationActivity(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            activity_type=CollabActivityType.SHARED,
            entity_type=request.item_type,
            entity_id=request.item_id,
            entity_name=f"{request.item_type} #{request.item_id}",
            description=f"Shared {request.item_type} with {count} users"
        )
        db.add(activity)
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
    from app.models.collaboration import CollaborationActivity
    
    stmt = (
        select(CollaborationActivity)
        .where(CollaborationActivity.organization_id == current_user.organization_id)
        .order_by(desc(CollaborationActivity.created_at))
        .limit(limit)
        .offset(offset)
        .options(selectinload(CollaborationActivity.user))
    )
    
    result = await db.execute(stmt)
    activities = result.scalars().all()

    response = []
    for activity in activities:
        user_name = "Unknown"
        if activity.user:
            user_name = activity.user.full_name or getattr(activity.user, "username", activity.user.email)

        response.append(ActivityResponse(
            id=str(activity.id),
            user=user_name,
            action=activity.description or f"{activity.activity_type} {activity.entity_type}",
            target=activity.entity_name or f"#{activity.entity_id}",
            timestamp=activity.created_at.strftime("%Y-%m-%d %H:%M"),
            type=activity.activity_type
        ))
    
    return response


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all conversations for the current user"""
    
    # Subquery for unread count
    # Count messages where created_at > last_read_at OR last_read_at is NULL
    unread_subq = (
        select(func.count(Message.id))
        .where(
            and_(
                Message.conversation_id == Conversation.id,
                or_(
                    ConversationParticipant.last_read_at.is_(None),
                    Message.created_at > ConversationParticipant.last_read_at
                )
            )
        )
        .correlate(Conversation, ConversationParticipant)
        .scalar_subquery()
    )

    # Query conversations where user is a participant
    stmt = (
        select(Conversation, ConversationParticipant, unread_subq.label("unread_count"))
        .join(ConversationParticipant, Conversation.id == ConversationParticipant.conversation_id)
        .where(ConversationParticipant.user_id == current_user.id)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user)
        )
        .order_by(desc(Conversation.last_message_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    conversations = []
    for conv, participation, unread_count in rows:
        # Get participant names
        participant_names = []
        for p in conv.participants:
            if p.user:
                participant_names.append(p.user.full_name or getattr(p.user, "username", p.user.email))

        # Get last message content - fetch latest message efficiently
        last_msg_content = None
        msg_stmt = (
            select(Message.content)
            .where(Message.conversation_id == conv.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        msg_res = await db.execute(msg_stmt)
        last_msg_content = msg_res.scalar_one_or_none()

        conversations.append(ConversationResponse(
            id=str(conv.id),
            name=conv.name or "Direct Message", # Fallback for DMs
            type=conv.type,
            participants=participant_names,
            last_message=last_msg_content,
            unread_count=unread_count or 0
        ))
    
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
    
    # Check if user is participant
    stmt = select(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == int(conversation_id),
            ConversationParticipant.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    participation = result.scalar_one_or_none()
    
    if not participation:
        raise HTTPException(status_code=403, detail="Not a participant of this conversation")

    # Query messages
    stmt = (
        select(Message)
        .where(Message.conversation_id == int(conversation_id))
        .options(selectinload(Message.sender))
        .order_by(desc(Message.created_at))
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Update last_read_at for the user
    participation.last_read_at = datetime.now(timezone.utc)
    await db.commit()

    response_messages = []
    # Reverse to show oldest first if that's what UI expects,
    # but usually chat APIs return latest first for pagination or oldest first for display.
    # The Mock returned empty list.
    # Usually frontend wants chronological order for display.
    # But we queried DESC for latest. Let's reverse for display.
    for msg in reversed(messages):
        sender_name = (msg.sender.full_name or getattr(msg.sender, "username", msg.sender.email)) if msg.sender else "Unknown"

        response_messages.append(MessageResponse(
            id=str(msg.id),
            sender=sender_name,
            content=msg.content,
            timestamp=msg.created_at.strftime("%I:%M %p"), # Match mock format
            is_own=msg.sender_id == current_user.id,
            conversation_id=str(msg.conversation_id)
        ))

    return response_messages


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    request: CreateMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to a conversation"""
    
    # Check conversation exists and user is participant
    stmt = select(Conversation).where(Conversation.id == int(request.conversation_id))
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check participation
    stmt = select(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == int(request.conversation_id),
            ConversationParticipant.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    participation = result.scalar_one_or_none()

    if not participation:
         raise HTTPException(status_code=403, detail="Not a participant of this conversation")

    # Create message
    new_message = Message(
        conversation_id=int(request.conversation_id),
        sender_id=current_user.id,
        content=request.content
    )
    db.add(new_message)

    # Update conversation last message timestamp
    conversation.last_message_at = datetime.now(timezone.utc)

    # Update sender's last_read_at so it doesn't appear as unread
    participation.last_read_at = conversation.last_message_at

    await db.commit()
    await db.refresh(new_message)
    
    # TODO: Broadcast via WebSocket to conversation participants
    
    return MessageResponse(
        id=str(new_message.id),
        sender=current_user.full_name or getattr(current_user, "username", current_user.email),
        content=new_message.content,
        timestamp=new_message.created_at.strftime("%I:%M %p"),
        is_own=True,
        conversation_id=str(new_message.conversation_id)
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
