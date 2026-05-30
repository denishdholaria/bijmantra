"""
Socket.io Integration for Real-time Collaboration
FastAPI + python-socketio for WebSocket support
"""

import logging
from datetime import UTC, datetime
from typing import Any

import socketio

from app.core.config import settings
from app.core.security import decode_access_token


logger = logging.getLogger(__name__)


# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.BACKEND_CORS_ORIGINS,
    logger=True,
    engineio_logger=True,
)

# Create ASGI app
socket_app = socketio.ASGIApp(sio)

# Store connected users and their info
connected_users: dict[str, dict] = {}
# Store room memberships
rooms: dict[str, set[str]] = {}


def _extract_token(auth: dict[str, Any] | None) -> str | None:
    if not auth:
        return None

    token = auth.get('token') or auth.get('accessToken') or auth.get('access_token')
    if not isinstance(token, str) or not token.strip():
        return None

    token = token.strip()
    if token.lower().startswith('bearer '):
        return token[7:].strip()
    return token


def _org_presence_room(organization_id: int | str) -> str:
    return f'org:{organization_id}:presence'


def _scoped_room_id(organization_id: int | str, room_id: str) -> str:
    return f'org:{organization_id}:room:{room_id}'


def _room_for_sid(sid: str, room_id: str | None) -> str | None:
    user = connected_users.get(sid)
    if not user or not room_id:
        return None
    return _scoped_room_id(user['organization_id'], room_id)


def _users_for_org(organization_id: int | str) -> list[dict]:
    return [
        user
        for user in connected_users.values()
        if str(user.get('organization_id')) == str(organization_id)
    ]


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None):
    """Handle new connection"""
    token = _extract_token(auth)
    payload = decode_access_token(token) if token else None
    if not payload or not payload.get('sub') or payload.get('organization_id') is None:
        logger.warning("[Socket.IO] Rejected unauthenticated connection: %s", sid)
        raise socketio.exceptions.ConnectionRefusedError('authentication required')

    user_id = str(payload['sub'])
    organization_id = payload['organization_id']
    user_name = auth.get('userName') if auth else None
    if not isinstance(user_name, str) or not user_name.strip():
        user_name = f'User {user_id}'
    user_color = auth.get('color') if auth else '#3b82f6'

    connected_users[sid] = {
        'id': user_id,
        'organization_id': organization_id,
        'name': user_name,
        'color': user_color,
        'connected_at': datetime.now(UTC).isoformat(),
        'cursor': None,
    }

    org_room = _org_presence_room(organization_id)
    rooms.setdefault(org_room, set()).add(sid)
    await sio.enter_room(sid, org_room)

    # Broadcast user joined only within the authenticated organization.
    await sio.emit('user:joined', connected_users[sid], room=org_room, skip_sid=sid)

    # Send current online users for this organization to the new connection.
    await sio.emit('users:online', _users_for_org(organization_id), to=sid)

    logger.info("[Socket.IO] User connected: %s (%s)", user_id, sid)


@sio.event
async def disconnect(sid: str):
    """Handle disconnection"""
    user = connected_users.pop(sid, None)
    if user:
        # Remove from all rooms
        for _room_id, members in rooms.items():
            members.discard(sid)

        # Broadcast user left within the authenticated organization.
        await sio.emit(
            'user:left',
            {'userId': user['id']},
            room=_org_presence_room(user['organization_id']),
        )
        logger.info("[Socket.IO] User disconnected: %s (%s)", user['id'], sid)


@sio.event
async def cursor_move(sid: str, data: dict):
    """Handle cursor movement for presence"""
    if sid in connected_users:
        user = connected_users[sid]
        connected_users[sid]['cursor'] = {
            'x': data.get('x'),
            'y': data.get('y'),
            'page': data.get('page'),
        }
        await sio.emit('cursor:move', {
            'userId': user['id'],
            **connected_users[sid]['cursor'],
        }, room=_org_presence_room(user['organization_id']), skip_sid=sid)


@sio.event
async def room_join(sid: str, data: dict):
    """Join a collaboration room"""
    room_id = data.get('roomId')
    if not room_id:
        return
    user = connected_users.get(sid)
    if not user:
        return

    scoped_room_id = _scoped_room_id(user['organization_id'], str(room_id))

    if scoped_room_id not in rooms:
        rooms[scoped_room_id] = set()

    rooms[scoped_room_id].add(sid)
    await sio.enter_room(sid, scoped_room_id)

    # Notify room members
    await sio.emit('user:joined', user, room=scoped_room_id, skip_sid=sid)

    logger.info("[Socket.IO] %s joined room: %s", user.get('id'), scoped_room_id)


@sio.event
async def room_leave(sid: str, data: dict):
    """Leave a collaboration room"""
    room_id = data.get('roomId')
    scoped_room_id = _room_for_sid(sid, str(room_id) if room_id else None)
    if not scoped_room_id or scoped_room_id not in rooms:
        return

    rooms[scoped_room_id].discard(sid)
    await sio.leave_room(sid, scoped_room_id)

    user = connected_users.get(sid, {})
    await sio.emit('user:left', {'userId': user.get('id')}, room=scoped_room_id)

    logger.info("[Socket.IO] %s left room: %s", user.get('id'), scoped_room_id)


@sio.event
async def room_message(sid: str, data: dict):
    """Send message to a room"""
    room_id = data.get('roomId')
    content = data.get('content')

    if not room_id or not content:
        return

    user = connected_users.get(sid, {})
    scoped_room_id = _room_for_sid(sid, str(room_id))
    if not scoped_room_id or sid not in rooms.get(scoped_room_id, set()):
        return

    message = {
        'id': f"{sid}-{datetime.now(UTC).timestamp()}",
        'roomId': room_id,
        'userId': user.get('id'),
        'userName': user.get('name'),
        'content': content,
        'timestamp': datetime.now(UTC).isoformat(),
    }

    await sio.emit('room:message', message, room=scoped_room_id)


@sio.event
async def data_updated(sid: str, data: dict):
    """Broadcast data changes to all connected clients"""
    user = connected_users.get(sid, {})
    if not user:
        return

    event_data = {
        **data,
        'userId': user.get('id'),
        'timestamp': datetime.now(UTC).isoformat(),
    }

    # Broadcast to the sender's organization only.
    await sio.emit(
        'data:updated',
        event_data,
        room=_org_presence_room(user['organization_id']),
        skip_sid=sid,
    )


@sio.event
async def typing_start(sid: str, data: dict):
    """Notify room that user started typing"""
    room_id = data.get('roomId')
    scoped_room_id = _room_for_sid(sid, str(room_id) if room_id else None)
    if scoped_room_id and sid in rooms.get(scoped_room_id, set()):
        user = connected_users.get(sid, {})
        await sio.emit('typing:start', {
            'userId': user.get('id'),
            'userName': user.get('name'),
        }, room=scoped_room_id, skip_sid=sid)


@sio.event
async def typing_stop(sid: str, data: dict):
    """Notify room that user stopped typing"""
    room_id = data.get('roomId')
    scoped_room_id = _room_for_sid(sid, str(room_id) if room_id else None)
    if scoped_room_id and sid in rooms.get(scoped_room_id, set()):
        user = connected_users.get(sid, {})
        await sio.emit('typing:stop', {
            'userId': user.get('id'),
        }, room=scoped_room_id, skip_sid=sid)


# Helper functions for server-side events
async def broadcast_notification(
    title: str,
    message: str,
    type: str = 'info',
    organization_id: int | str | None = None,
):
    """Send notification to connected users in one organization."""
    if organization_id is None:
        logger.warning("[Socket.IO] Skipped global notification without organization_id")
        return

    await sio.emit('notification', {
        'title': title,
        'message': message,
        'type': type,
        'timestamp': datetime.now(UTC).isoformat(),
    }, room=_org_presence_room(organization_id))


async def broadcast_data_change(
    entity_type: str,
    action: str,
    entity_id: str,
    data: dict = None,
    organization_id: int | str | None = None,
):
    """Broadcast data change to connected users in one organization."""
    if organization_id is None:
        logger.warning("[Socket.IO] Skipped global data change without organization_id")
        return

    await sio.emit('data:updated', {
        'type': entity_type,
        'action': action,
        'id': entity_id,
        'data': data,
        'timestamp': datetime.now(UTC).isoformat(),
    }, room=_org_presence_room(organization_id))


async def send_to_user(user_id: str, event: str, data: dict):
    """Send event to specific user"""
    for sid, user in connected_users.items():
        if user.get('id') == user_id:
            await sio.emit(event, data, to=sid)
            break


def get_online_users(organization_id: int | str | None = None) -> list:
    """Get currently online users, optionally scoped to one organization."""
    if organization_id is None:
        return list(connected_users.values())
    return _users_for_org(organization_id)


def get_room_members(room_id: str, organization_id: int | str | None = None) -> list:
    """Get members of a specific room"""
    lookup_room_id = _scoped_room_id(organization_id, room_id) if organization_id is not None else room_id
    if lookup_room_id not in rooms:
        return []
    return [connected_users[sid] for sid in rooms[lookup_room_id] if sid in connected_users]
