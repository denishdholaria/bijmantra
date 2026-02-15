import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import User
from app.models.collaboration import Conversation, ConversationParticipant, ConversationType

@pytest.fixture
async def other_user(async_db_session: AsyncSession, test_user: User) -> User:
    """Creates another user in the same organization."""
    user = User(
        email="other@example.com",
        hashed_password="password",
        organization_id=test_user.organization_id,
        full_name="Other User"
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user

@pytest.fixture
async def conversation(
    async_db_session: AsyncSession,
    test_user: User,
    other_user: User
) -> Conversation:
    """Creates a conversation between test_user and other_user."""
    conv = Conversation(
        organization_id=test_user.organization_id,
        type=ConversationType.DIRECT,
        name="Test Chat"
    )
    async_db_session.add(conv)
    await async_db_session.commit()
    await async_db_session.refresh(conv)

    p1 = ConversationParticipant(
        conversation_id=conv.id,
        user_id=test_user.id
    )
    p2 = ConversationParticipant(
        conversation_id=conv.id,
        user_id=other_user.id
    )
    async_db_session.add_all([p1, p2])
    await async_db_session.commit()

    return conv

@pytest.mark.asyncio
async def test_send_message_broadcasts_websocket(
    authenticated_client: AsyncClient,
    conversation: Conversation,
    test_user: User
):
    # Mock socketio
    with patch("app.api.v2.collaboration.sio", new_callable=AsyncMock) as mock_sio:
        payload = {
            "conversation_id": str(conversation.id),
            "content": "Hello World"
        }

        response = await authenticated_client.post("/api/v2/collaboration/messages", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello World"

        # Verify socket broadcast
        assert mock_sio.emit.called

        # Get arguments of the first call
        args, kwargs = mock_sio.emit.call_args

        event = args[0]
        msg_payload = args[1]

        assert event == "room:message"
        assert msg_payload["content"] == "Hello World"
        assert msg_payload["sender_id"] == str(test_user.id)
        assert msg_payload["conversation_id"] == str(conversation.id)

        # Check room argument
        assert kwargs["room"] == str(conversation.id)

@pytest.mark.asyncio
async def test_update_presence_broadcasts_websocket(
    authenticated_client: AsyncClient,
    test_user: User
):
    with patch("app.api.v2.collaboration.sio", new_callable=AsyncMock) as mock_sio:
        payload = {
            "status": "online"
        }

        response = await authenticated_client.post("/api/v2/collaboration/presence", json=payload)

        assert response.status_code == 200

        # Verify socket broadcast
        assert mock_sio.emit.called

        args, kwargs = mock_sio.emit.call_args
        event = args[0]
        status_payload = args[1]

        assert event == "user:status"
        assert status_payload["userId"] == str(test_user.id)
        assert status_payload["status"] == "online"
        assert "last_active" in status_payload
