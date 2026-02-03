import pytest
from httpx import AsyncClient
from app.models.core import User, Organization
from app.models.collaboration import CollaborationActivity, CollabActivityType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def second_user(async_db_session: AsyncSession, test_user: User) -> User:
    """Creates a second user in the same organization."""
    # We use async_db_session here because this test file is async
    # test_user is passed from conftest (which created it using sync session), but it's a model instance so it's fine.
    # However, if we need to access its lazy loaded attributes, we might have issues if it's detached.
    # But id and organization_id should be available.

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
async def test_get_activity_feed_empty(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v2/collaboration/activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_share_item_creates_activity(
    authenticated_client: AsyncClient,
    second_user: User,
    async_db_session: AsyncSession
):
    # Share an item
    payload = {
        "item_type": "trial",
        "item_id": "123",
        "user_ids": [str(second_user.id)],
        "permission": "view"
    }

    response = await authenticated_client.post("/api/v2/collaboration/share-item", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Check activity feed
    response = await authenticated_client.get("/api/v2/collaboration/activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Verify the latest activity is the one we just created
    assert len(data) > 0
    activity = data[0]
    # action field maps to description or constructed string
    assert "Shared trial with 1 users" in activity["action"]
    assert activity["type"] == "shared"
    assert activity["target"] == "trial #123"

@pytest.mark.asyncio
async def test_get_conversations(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession,
    test_user: User,
    second_user: User
):
    from app.models.collaboration import Conversation, ConversationParticipant, Message, ConversationType

    # Create conversation
    conv = Conversation(
        organization_id=test_user.organization_id,
        name="Test Conversation",
        type=ConversationType.DIRECT
    )
    async_db_session.add(conv)
    await async_db_session.flush()

    # Participants
    p1 = ConversationParticipant(conversation_id=conv.id, user_id=test_user.id)
    p2 = ConversationParticipant(conversation_id=conv.id, user_id=second_user.id)
    async_db_session.add(p1)
    async_db_session.add(p2)

    # Add messages
    msg1 = Message(conversation_id=conv.id, sender_id=second_user.id, content="Hello")
    async_db_session.add(msg1)
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v2/collaboration/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["last_message"] == "Hello"
    assert len(data[0]["participants"]) > 0
