from unittest.mock import AsyncMock, patch

import pytest
import socketio

from app.core.security import create_access_token
from app.core import socketio as socket_module


@pytest.fixture(autouse=True)
def clear_socket_state():
    socket_module.connected_users.clear()
    socket_module.rooms.clear()
    yield
    socket_module.connected_users.clear()
    socket_module.rooms.clear()


@pytest.mark.asyncio
async def test_socket_connect_rejects_missing_token():
    with pytest.raises(socketio.exceptions.ConnectionRefusedError):
        await socket_module.connect("sid-1", {}, auth={})


@pytest.mark.asyncio
async def test_socket_connect_derives_identity_and_org_from_jwt():
    token = create_access_token(
        {"sub": "42", "organization_id": 7, "is_superuser": False}
    )

    with (
        patch.object(socket_module.sio, "emit", new_callable=AsyncMock) as emit,
        patch.object(socket_module.sio, "enter_room", new_callable=AsyncMock) as enter_room,
    ):
        await socket_module.connect(
            "sid-1",
            {},
            auth={
                "token": token,
                "userId": "999",
                "userName": "Client Supplied Name",
                "color": "#123456",
            },
        )

    assert socket_module.connected_users["sid-1"]["id"] == "42"
    assert socket_module.connected_users["sid-1"]["organization_id"] == 7
    enter_room.assert_awaited_once_with("sid-1", "org:7:presence")
    assert emit.await_args_list[0].kwargs["room"] == "org:7:presence"


@pytest.mark.asyncio
async def test_socket_room_join_scopes_room_by_organization():
    token = create_access_token(
        {"sub": "42", "organization_id": 7, "is_superuser": False}
    )

    with (
        patch.object(socket_module.sio, "emit", new_callable=AsyncMock),
        patch.object(socket_module.sio, "enter_room", new_callable=AsyncMock),
    ):
        await socket_module.connect("sid-1", {}, auth={"token": token})
        await socket_module.room_join("sid-1", {"roomId": "trial-123"})

    assert "trial-123" not in socket_module.rooms
    assert "org:7:room:trial-123" in socket_module.rooms
    assert "sid-1" in socket_module.rooms["org:7:room:trial-123"]
