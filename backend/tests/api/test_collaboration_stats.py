import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import User
from app.models.collaboration import Conversation, ConversationParticipant, Message, ConversationType
from datetime import datetime, timezone

@pytest.fixture
async def second_user(async_db_session: AsyncSession, test_user: User) -> User:
    """Creates a second user in the same organization."""
    from sqlalchemy import select
    result = await async_db_session.execute(select(User).filter_by(email="colleague@example.com"))
    user = result.scalars().first()
    if not user:
        user = User(
            email="colleague@example.com",
            hashed_password="password",
            organization_id=test_user.organization_id,
            full_name="Colleague User"
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
    return user

@pytest.mark.asyncio
async def test_stats_unread_messages(
    authenticated_client: AsyncClient,
    test_user: User,
    second_user: User,
    async_db_session: AsyncSession
):
    # Create conversation
    conversation = Conversation(
        organization_id=test_user.organization_id,
        name="Test Chat",
        type=ConversationType.DIRECT
    )
    async_db_session.add(conversation)
    await async_db_session.commit()
    await async_db_session.refresh(conversation)

    # Add participants
    # Ensure test_user has last_read_at set before the message
    part1 = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=test_user.id,
        last_read_at=datetime.now(timezone.utc)
    )
    part2 = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=second_user.id
    )
    async_db_session.add(part1)
    async_db_session.add(part2)
    await async_db_session.commit()

    # Get stats initially (should be 0)
    response = await authenticated_client.get("/api/v2/collaboration/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["unread_messages"] == 0

    # Add a message from second_user
    # Ensure message is created after last_read_at
    # In tests, sometimes execution is fast enough that timestamps are identical.
    # We can fake the message creation time if needed, but sleep is simple.
    import asyncio
    await asyncio.sleep(0.1)

    msg = Message(
        conversation_id=conversation.id,
        sender_id=second_user.id,
        content="Hello"
    )
    async_db_session.add(msg)
    await async_db_session.commit()

    # Get stats again (should be 1)
    response = await authenticated_client.get("/api/v2/collaboration/stats")
    assert response.status_code == 200
    stats = response.json()

    # This assertion is expected to FAIL until implementation is done
    assert stats["unread_messages"] == 1
