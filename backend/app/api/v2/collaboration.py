"""
Collaboration API - Real-time team collaboration endpoints

Provides:
- Team member management
- Real-time chat (WebSocket integration ready)
- Shared items (trials, studies, germplasm, reports)
- Activity feed
- Presence tracking
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.socketio import sio
from app.models.collaboration import (
    CollaborationActivity,
    Conversation,
    ConversationParticipant,
    Message,
    SharedItem,
    UserPresence,
)
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
    avatar: str | None = None
    status: str  # online, away, offline
    last_active: str | None = None


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
    participants: list[str]
    last_message: str | None = None
    unread_count: int = 0


class CreateMessageRequest(BaseModel):
    conversation_id: str
    content: str


class ShareItemRequest(BaseModel):
    item_type: str
    item_id: str
    user_ids: list[str]
    permission: str = "view"


class UpdatePresenceRequest(BaseModel):
    status: str  # online, away, offline


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/team-members", response_model=list[TeamMemberResponse])
async def get_team_members(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all team members in the user's organization.

    Returns a list of users belonging to the same organization as the current user,
    including their online status (online, away, offline) and last active timestamp.

    Returns:
        List[TeamMemberResponse]: A list of team members with their details and status.
    """

    # Query users in same organization
    result = await db.execute(
        select(User, UserProfile)
        .outerjoin(UserProfile, User.id == UserProfile.user_id)
        .where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active
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
            time_diff = datetime.now(UTC) - last_active
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
            name=user.full_name or getattr(user, "username", None) or user.email,
            email=user.email,
            role=getattr(user, "role", "Member") or "Member",
            avatar=profile.avatar_url if profile else None,
            status=status,
            last_active=last_active_str
        ))

    return team_members


@router.get("/shared-items", response_model=list[SharedItemResponse])
async def get_shared_items(
    item_type: str | None = Query(None, description="Filter by type: trial, study, germplasm, report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get items shared with the current user.

    Retrieves a list of items (trials, studies, germplasm, reports) that have been shared
    with the current user. Results can be filtered by item type.

    Args:
        item_type (Optional[str]): Filter by item type (e.g., "trial", "study").

    Returns:
        List[SharedItemResponse]: A list of shared items with details about who shared them and permissions.
    """
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
    """
    Share an item with other users.

    Grant access permissions to one or more users for a specific item.
    Also creates an activity log entry for the sharing action.

    Args:
        request (ShareItemRequest): The sharing details including item type, ID, target user IDs, and permission level.

    Returns:
        dict: A success message indicating how many users the item was shared with.
    """
    from app.models.collaboration import CollabActivityType, CollaborationActivity, SharedItem

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


@router.get("/activity", response_model=list[ActivityResponse])
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent activity feed for the team.

    Retrieves a paginated list of recent collaboration activities within the user's organization,
    such as sharing items, creating entries, or updating records.

    Args:
        limit (int): Maximum number of activities to return (default: 20, max: 100).
        offset (int): Number of activities to skip (default: 0).

    Returns:
        List[ActivityResponse]: A list of activity records sorted by creation time (descending).
    """
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
            user_name = activity.user.full_name or getattr(activity.user, "username", None) or activity.user.email

        response.append(ActivityResponse(
            id=str(activity.id),
            user=user_name,
            action=activity.description or f"{activity.activity_type} {activity.entity_type}",
            target=activity.entity_name or f"#{activity.entity_id}",
            timestamp=activity.created_at.strftime("%Y-%m-%d %H:%M"),
            type=activity.activity_type
        ))

    return response


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all conversations for the current user.

    Retrieves a list of conversations where the current user is a participant.
    Each conversation includes details like the last message content and unread message count.

    Returns:
        List[ConversationResponse]: A list of conversations sorted by the last message timestamp.
    """

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

    # Subquery for last message content
    last_msg_subq = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id)
        .order_by(desc(Message.created_at))
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )

    # Query conversations where user is a participant
    stmt = (
        select(
            Conversation,
            ConversationParticipant,
            unread_subq.label("unread_count"),
            last_msg_subq.label("last_message_content")
        )
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
    for conv, _participation, unread_count, last_message_content in rows:
        # Get participant names
        participant_names = []
        for p in conv.participants:
            if p.user:
                participant_names.append(p.user.full_name or getattr(p.user, "username", None) or p.user.email)

        conversations.append(ConversationResponse(
            id=str(conv.id),
            name=conv.name or "Direct Message", # Fallback for DMs
            type=conv.type,
            participants=participant_names,
            last_message=last_message_content,
            unread_count=unread_count or 0
        ))

    return conversations


@router.get("/messages/{conversation_id}", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get messages for a conversation.

    Retrieves a paginated list of messages for a specific conversation.
    Mark the conversation as read for the current user.

    Args:
        conversation_id (str): The ID of the conversation to retrieve messages from.
        limit (int): Maximum number of messages to return (default: 50, max: 100).
        offset (int): Number of messages to skip (default: 0).

    Returns:
        List[MessageResponse]: A list of messages in chronological order (oldest first).

    Raises:
        HTTPException(403): If the user is not a participant of the conversation.
    """

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
    participation.last_read_at = datetime.now(UTC)
    await db.commit()

    response_messages = []
    # Reverse to show oldest first if that's what UI expects,
    # but usually chat APIs return latest first for pagination or oldest first for display.
    # The Mock returned empty list.
    # Usually frontend wants chronological order for display.
    # But we queried DESC for latest. Let's reverse for display.
    for msg in reversed(messages):
        sender_name = (msg.sender.full_name or getattr(msg.sender, "username", None) or msg.sender.email) if msg.sender else "Unknown"

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
    """
    Send a message to a conversation.

    Creates a new message in the specified conversation and broadcasts it to all participants
    via WebSocket. Updates the conversation's last message timestamp.

    Args:
        request (CreateMessageRequest): The message content and conversation ID.

    Returns:
        MessageResponse: The created message details.

    Raises:
        HTTPException(404): If the conversation does not exist.
        HTTPException(403): If the user is not a participant of the conversation.
    """

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
    conversation.last_message_at = datetime.now(UTC)

    # Update sender's last_read_at so it doesn't appear as unread
    participation.last_read_at = conversation.last_message_at

    await db.commit()
    await db.refresh(new_message)

    # Broadcast via WebSocket to conversation participants
    sender_name = current_user.full_name or getattr(current_user, "username", None) or current_user.email
    ws_message = {
        "id": str(new_message.id),
        "sender": sender_name,
        "sender_id": str(current_user.id),
        "content": new_message.content,
        "timestamp": new_message.created_at.strftime("%I:%M %p"),
        "conversation_id": str(new_message.conversation_id),
        # Compatibility fields with socketio.py
        "roomId": str(new_message.conversation_id),
        "userId": str(current_user.id),
        "userName": sender_name
    }

    # Broadcast to room (clients must join room 'conversation_id')
    await sio.emit("room:message", ws_message, room=str(new_message.conversation_id))

    return MessageResponse(
        id=str(new_message.id),
        sender=current_user.full_name or getattr(current_user, "username", None) or current_user.email,
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
    """
    Update user's online presence status.

    Updates the user's last active timestamp and status (e.g., online, away, offline).
    This status is broadcast to other users via WebSocket.

    Args:
        request (UpdatePresenceRequest): The new status to set.

    Returns:
        dict: A confirmation of the status update including the timestamp.
    """

    # Update last_active timestamp
    stmt = select(UserPresence).where(UserPresence.user_id == current_user.id)
    result = await db.execute(stmt)
    presence = result.scalar_one_or_none()

    if not presence:
        presence = UserPresence(user_id=current_user.id, status=request.status, last_active=datetime.now(UTC))
        db.add(presence)
    else:
        presence.status = request.status
        presence.last_active = datetime.now(UTC)
    await db.commit()

    # Broadcast presence update via WebSocket
    status_payload = {
        "userId": str(current_user.id),
        "status": request.status,
        "last_active": datetime.now(UTC).isoformat()
    }
    await sio.emit("user:status", status_payload)

    return {
        "success": True,
        "status": request.status,
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.get("/stats")
async def get_collaboration_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get collaboration statistics.

    Retrieves aggregated statistics for the user's organization, including the total number
    of team members and the count of members currently online (active within the last 5 minutes).

    Returns:
        dict: A dictionary containing 'team_members', 'online_now', and placeholders for other stats.
    """

    # Count team members
    result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active
            )
        )
    )
    total_members = result.scalar() or 0

    # Count online members (active in last 5 minutes)
    five_min_ago = datetime.now(UTC) - timedelta(minutes=5)
    result = await db.execute(
        select(func.count(UserPresence.user_id))
        .join(User, UserPresence.user_id == User.id)
        .where(
            and_(
                User.organization_id == current_user.organization_id,
                User.is_active == True,
                UserPresence.last_active >= five_min_ago
            )
        )
    )
    online_members = result.scalar() or 0

    # Count unread messages
    unread_result = await db.execute(
        select(func.count(Message.id))
        .join(ConversationParticipant, ConversationParticipant.conversation_id == Message.conversation_id)
        .where(
            and_(
                ConversationParticipant.user_id == current_user.id,
                Message.sender_id != current_user.id,
                or_(
                    ConversationParticipant.last_read_at.is_(None),
                    Message.created_at > ConversationParticipant.last_read_at
                )
            )
        )
    )
    unread_messages = unread_result.scalar() or 0

    # Count shared items for the organization
    try:
        shared_result = await db.execute(
            select(func.count(SharedItem.id)).where(
                SharedItem.organization_id == current_user.organization_id
            )
        )
        shared_items = shared_result.scalar() or 0
    except Exception:
        shared_items = 0

    # Count today's activity
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        activity_result = await db.execute(
            select(func.count(CollaborationActivity.id)).where(
                and_(
                    CollaborationActivity.organization_id == current_user.organization_id,
                    CollaborationActivity.created_at >= today_start
                )
            )
        )
        today_activity = activity_result.scalar() or 0
    except Exception:
        today_activity = 0

    return {
        "team_members": total_members,
        "online_now": online_members,
        "shared_items": shared_items,
        "today_activity": today_activity,
        "unread_messages": unread_messages
    }
