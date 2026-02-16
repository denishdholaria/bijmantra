"""
Socket.io Integration for Real-time Collaboration
FastAPI + python-socketio for WebSocket support
"""

import socketio
from typing import Dict, Set, Optional
from datetime import datetime, timezone
import json

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure for production
    logger=True,
    engineio_logger=True,
)

# Create ASGI app
socket_app = socketio.ASGIApp(sio)

# Store connected users and their info
connected_users: Dict[str, dict] = {}
# Store room memberships
rooms: Dict[str, Set[str]] = {}


@sio.event
async def connect(sid: str, environ: dict, auth: Optional[dict] = None):
    """Handle new connection"""
    user_id = auth.get('userId') if auth else None
    user_name = auth.get('userName') if auth else 'Anonymous'
    user_color = auth.get('color') if auth else '#3b82f6'

    connected_users[sid] = {
        'id': user_id or sid,
        'name': user_name,
        'color': user_color,
        'connected_at': datetime.now(timezone.utc).isoformat(),
        'cursor': None,
    }

    # Broadcast user joined
    await sio.emit('user:joined', connected_users[sid], skip_sid=sid)

    # Send current online users to new connection
    await sio.emit('users:online', list(connected_users.values()), to=sid)

    print(f"[Socket.IO] User connected: {user_name} ({sid})")


@sio.event
async def disconnect(sid: str):
    """Handle disconnection"""
    user = connected_users.pop(sid, None)
    if user:
        # Remove from all rooms
        for room_id, members in rooms.items():
            members.discard(sid)

        # Broadcast user left
        await sio.emit('user:left', {'userId': user['id']})
        print(f"[Socket.IO] User disconnected: {user['name']} ({sid})")


@sio.event
async def cursor_move(sid: str, data: dict):
    """Handle cursor movement for presence"""
    if sid in connected_users:
        connected_users[sid]['cursor'] = {
            'x': data.get('x'),
            'y': data.get('y'),
            'page': data.get('page'),
        }
        await sio.emit('cursor:move', {
            'userId': connected_users[sid]['id'],
            **connected_users[sid]['cursor'],
        }, skip_sid=sid)


@sio.event
async def room_join(sid: str, data: dict):
    """Join a collaboration room"""
    room_id = data.get('roomId')
    if not room_id:
        return

    if room_id not in rooms:
        rooms[room_id] = set()

    rooms[room_id].add(sid)
    await sio.enter_room(sid, room_id)

    # Notify room members
    user = connected_users.get(sid, {})
    await sio.emit('user:joined', user, room=room_id, skip_sid=sid)

    print(f"[Socket.IO] {user.get('name')} joined room: {room_id}")


@sio.event
async def room_leave(sid: str, data: dict):
    """Leave a collaboration room"""
    room_id = data.get('roomId')
    if not room_id or room_id not in rooms:
        return

    rooms[room_id].discard(sid)
    await sio.leave_room(sid, room_id)

    user = connected_users.get(sid, {})
    await sio.emit('user:left', {'userId': user.get('id')}, room=room_id)

    print(f"[Socket.IO] {user.get('name')} left room: {room_id}")


@sio.event
async def room_message(sid: str, data: dict):
    """Send message to a room"""
    room_id = data.get('roomId')
    content = data.get('content')

    if not room_id or not content:
        return

    user = connected_users.get(sid, {})
    message = {
        'id': f"{sid}-{datetime.now(timezone.utc).timestamp()}",
        'roomId': room_id,
        'userId': user.get('id'),
        'userName': user.get('name'),
        'content': content,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    await sio.emit('room:message', message, room=room_id)


@sio.event
async def data_updated(sid: str, data: dict):
    """Broadcast data changes to all connected clients"""
    user = connected_users.get(sid, {})

    event_data = {
        **data,
        'userId': user.get('id'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    # Broadcast to all except sender
    await sio.emit('data:updated', event_data, skip_sid=sid)


@sio.event
async def typing_start(sid: str, data: dict):
    """Notify room that user started typing"""
    room_id = data.get('roomId')
    if room_id:
        user = connected_users.get(sid, {})
        await sio.emit('typing:start', {
            'userId': user.get('id'),
            'userName': user.get('name'),
        }, room=room_id, skip_sid=sid)


@sio.event
async def typing_stop(sid: str, data: dict):
    """Notify room that user stopped typing"""
    room_id = data.get('roomId')
    if room_id:
        user = connected_users.get(sid, {})
        await sio.emit('typing:stop', {
            'userId': user.get('id'),
        }, room=room_id, skip_sid=sid)


# Helper functions for server-side events
async def broadcast_notification(title: str, message: str, type: str = 'info'):
    """Send notification to all connected users"""
    await sio.emit('notification', {
        'title': title,
        'message': message,
        'type': type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_data_change(entity_type: str, action: str, entity_id: str, data: dict = None):
    """Broadcast data change to all connected users"""
    await sio.emit('data:updated', {
        'type': entity_type,
        'action': action,
        'id': entity_id,
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


async def send_to_user(user_id: str, event: str, data: dict):
    """Send event to specific user"""
    for sid, user in connected_users.items():
        if user.get('id') == user_id:
            await sio.emit(event, data, to=sid)
            break


def get_online_users() -> list:
    """Get list of currently online users"""
    return list(connected_users.values())


def get_room_members(room_id: str) -> list:
    """Get members of a specific room"""
    if room_id not in rooms:
        return []
    return [connected_users[sid] for sid in rooms[room_id] if sid in connected_users]
