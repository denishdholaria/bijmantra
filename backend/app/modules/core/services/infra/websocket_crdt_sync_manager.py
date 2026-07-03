from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, TypedDict


logger = logging.getLogger(__name__)


class PresenceMetadata(TypedDict, total=False):
    """
    Metadata associated with a user's presence.
    Extensible for future needs (cursor position, current page, etc.).
    """
    username: str
    avatar_url: str | None
    session_id: str
    current_page: str | None
    last_active: str | None
    # Add other fields as needed


@dataclass
class CRDTEntry:
    """
    Represents a single entry in the CRDT state.
    Uses Last-Writer-Wins (LWW) semantics based on timestamp.
    """
    value: PresenceMetadata
    timestamp: float
    is_deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "is_deleted": self.is_deleted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CRDTEntry:
        """Deserialize from dictionary."""
        return cls(
            value=data.get("value", {}),
            timestamp=data.get("timestamp", 0.0),
            is_deleted=data.get("is_deleted", False),
        )


class WebsocketCRDTSyncManager:
    """
    Manages live presence state using a CRDT (Conflict-free Replicated Data Type) approach.
    Specifically implements an Observed-Remove Set (OR-Set) via Last-Writer-Wins (LWW).

    Ensures that multiple WebSocket nodes can converge to the same state
    even with out-of-order updates.
    """

    def __init__(self):
        # State is a map of user_id -> CRDTEntry
        self._state: dict[str, CRDTEntry] = {}
        # Simple lock is not strictly needed if running in single async event loop,
        # but useful if we add threading later. For now, we assume async usage.

    def get_state_snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a full snapshot of the current state (including tombstones)."""
        return {k: v.to_dict() for k, v in self._state.items()}

    def get_active_peers(self) -> dict[str, PresenceMetadata]:
        """Return only active (non-deleted) peers."""
        return {
            k: v.value
            for k, v in self._state.items()
            if not v.is_deleted
        }

    def update_peer(self, user_id: str, metadata: PresenceMetadata, timestamp: float) -> bool:
        """
        Update a peer's status. Returns True if state changed.
        LWW Rule: Update if new timestamp > current timestamp.
        """
        current_entry = self._state.get(user_id)

        if current_entry:
            if timestamp > current_entry.timestamp:
                self._state[user_id] = CRDTEntry(value=metadata, timestamp=timestamp, is_deleted=False)
                return True
            # If timestamps are equal, we could use a tie-breaker (e.g., value hash),
            # but for presence, usually "latest wins" is enough, and re-applying same update is idempotent.
            return False
        else:
            self._state[user_id] = CRDTEntry(value=metadata, timestamp=timestamp, is_deleted=False)
            return True

    def remove_peer(self, user_id: str, timestamp: float) -> bool:
        """
        Mark a peer as removed (tombstone). Returns True if state changed.
        LWW Rule: Remove if new timestamp > current timestamp.
        """
        current_entry = self._state.get(user_id)

        if current_entry:
            if timestamp > current_entry.timestamp:
                # Keep the last known value but mark deleted, or clear value?
                # Keeping value helps with "undo" or debugging, but clearing saves space.
                # Standard LWW-Element-Set keeps the value in the "remove set".
                # Here we just mark is_deleted.
                self._state[user_id] = CRDTEntry(
                    value=current_entry.value,
                    timestamp=timestamp,
                    is_deleted=True
                )
                return True
            return False
        else:
            # We received a delete for a user we didn't know about.
            # We must store the tombstone to ensure convergence if we later receive an older "add".
            self._state[user_id] = CRDTEntry(
                value={}, # type: ignore
                timestamp=timestamp,
                is_deleted=True
            )
            return True

    def merge(self, remote_state: dict[str, dict[str, Any]]) -> None:
        """
        Merge a full state dump from another node.
        """
        for user_id, entry_dict in remote_state.items():
            remote_entry = CRDTEntry.from_dict(entry_dict)
            local_entry = self._state.get(user_id)

            if not local_entry:
                self._state[user_id] = remote_entry
            else:
                if remote_entry.timestamp > local_entry.timestamp:
                    self._state[user_id] = remote_entry
                # If equal, we can define a deterministic tie breaker if needed.
                # For now, we do nothing (local wins tie, or effectively same).

    def prune(self, ttl_seconds: int, current_time: float) -> int:
        """
        Remove tombstones older than TTL.
        Returns number of pruned entries.
        CAUTION: If a node is disconnected for longer than TTL, it might re-introduce
        deleted items if it rejoins with old state.
        """
        to_remove = []
        for user_id, entry in self._state.items():
            if entry.is_deleted:
                age = current_time - entry.timestamp
                if age > ttl_seconds:
                    to_remove.append(user_id)

        for user_id in to_remove:
            del self._state[user_id]

        return len(to_remove)
