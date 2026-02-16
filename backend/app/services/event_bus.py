"""
Event Bus Service
Inter-module pub/sub communication for Bijmantra

Features:
- Async event publishing
- Multiple subscribers per event
- Event history/replay
- Dead letter queue for failed handlers
"""

from typing import Dict, List, Callable, Any, Optional
from datetime import datetime, UTC
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import asyncio
import traceback
import uuid

from pydantic import BaseModel


class EventType(str, Enum):
    """Standard event types across modules"""
    # Germplasm events
    GERMPLASM_CREATED = "germplasm.created"
    GERMPLASM_UPDATED = "germplasm.updated"
    GERMPLASM_DELETED = "germplasm.deleted"

    # Cross/Breeding events
    CROSS_CREATED = "cross.created"
    CROSS_COMPLETED = "cross.completed"
    CROSS_PREDICTION_READY = "cross.prediction_ready"

    # Trial events
    TRIAL_CREATED = "trial.created"
    TRIAL_STARTED = "trial.started"
    TRIAL_COMPLETED = "trial.completed"

    # Observation events
    OBSERVATION_RECORDED = "observation.recorded"
    OBSERVATION_BATCH_UPLOADED = "observation.batch_uploaded"

    # Seed Bank events
    ACCESSION_ADDED = "seedbank.accession_added"
    ACCESSION_DISTRIBUTED = "seedbank.accession_distributed"
    VIABILITY_TEST_COMPLETED = "seedbank.viability_test"

    # Compute events
    COMPUTE_JOB_STARTED = "compute.job_started"
    COMPUTE_JOB_COMPLETED = "compute.job_completed"
    COMPUTE_JOB_FAILED = "compute.job_failed"

    # AI/ML events
    EMBEDDING_GENERATED = "ai.embedding_generated"
    PREDICTION_COMPLETED = "ai.prediction_completed"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_SYNC_COMPLETED = "integration.sync_completed"
    INTEGRATION_ERROR = "integration.error"

    # User events
    USER_LOGGED_IN = "user.logged_in"
    USER_ACTION = "user.action"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"

    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """Event payload"""
    id: str
    type: EventType
    source: str  # Module that emitted the event
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    correlation_id: Optional[str] = None  # For tracking related events


@dataclass
class Subscription:
    """Event subscription"""
    id: str
    event_type: EventType
    handler: Callable
    module: str
    filter_fn: Optional[Callable] = None  # Optional filter function


@dataclass
class DeadLetter:
    """Failed event for retry"""
    event: Event
    error: str
    handler_module: str
    failed_at: datetime
    retry_count: int = 0


class EventBus:
    """
    Central event bus for inter-module communication
    
    Usage:
        # Subscribe to events
        event_bus.subscribe(EventType.GERMPLASM_CREATED, handle_germplasm, "seed_bank")
        
        # Publish events
        await event_bus.publish(EventType.GERMPLASM_CREATED, {"id": "123"}, "plant_sciences")
    """

    def __init__(self, history_size: int = 1000):
        self._subscriptions: Dict[EventType, List[Subscription]] = {}
        self._history: deque = deque(maxlen=history_size)
        self._dead_letters: List[DeadLetter] = []
        self._running = True

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        module: str,
        filter_fn: Optional[Callable] = None
    ) -> str:
        """Subscribe to an event type"""
        subscription_id = str(uuid.uuid4())[:8]

        subscription = Subscription(
            id=subscription_id,
            event_type=event_type,
            handler=handler,
            module=module,
            filter_fn=filter_fn
        )

        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []

        self._subscriptions[event_type].append(subscription)
        print(f"[EventBus] {module} subscribed to {event_type.value}")

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event"""
        for event_type, subs in self._subscriptions.items():
            for sub in subs:
                if sub.id == subscription_id:
                    subs.remove(sub)
                    print(f"[EventBus] Unsubscribed {subscription_id}")
                    return True
        return False

    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Event:
        """Publish an event to all subscribers"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            data=data,
            timestamp=datetime.now(UTC),
            user_id=user_id,
            organization_id=organization_id,
            correlation_id=correlation_id or str(uuid.uuid4())[:8]
        )

        # Store in history
        self._history.append(event)

        # Get subscribers
        subscribers = self._subscriptions.get(event_type, [])

        if not subscribers:
            return event

        # Notify all subscribers
        for sub in subscribers:
            # Apply filter if present
            if sub.filter_fn and not sub.filter_fn(event):
                continue

            try:
                # Call handler (async or sync)
                if asyncio.iscoroutinefunction(sub.handler):
                    await sub.handler(event)
                else:
                    sub.handler(event)
            except Exception as e:
                # Add to dead letter queue
                self._dead_letters.append(DeadLetter(
                    event=event,
                    error=f"{type(e).__name__}: {str(e)}",
                    handler_module=sub.module,
                    failed_at=datetime.now(UTC)
                ))
                print(f"[EventBus] Handler error in {sub.module}: {e}")

        return event

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history with optional filters"""
        events = list(self._history)

        if event_type:
            events = [e for e in events if e.type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]

    def get_dead_letters(self, limit: int = 50) -> List[DeadLetter]:
        """Get failed events"""
        return self._dead_letters[-limit:]

    async def retry_dead_letter(self, index: int) -> bool:
        """Retry a failed event"""
        if index >= len(self._dead_letters):
            return False

        dead_letter = self._dead_letters[index]
        dead_letter.retry_count += 1

        # Re-publish the event
        await self.publish(
            event_type=dead_letter.event.type,
            data=dead_letter.event.data,
            source=dead_letter.event.source,
            user_id=dead_letter.event.user_id,
            organization_id=dead_letter.event.organization_id,
            correlation_id=dead_letter.event.correlation_id
        )

        # Remove from dead letters if successful
        self._dead_letters.pop(index)
        return True

    def get_subscriptions(self) -> Dict[str, List[str]]:
        """Get all active subscriptions"""
        return {
            event_type.value: [sub.module for sub in subs]
            for event_type, subs in self._subscriptions.items()
        }

    def clear_history(self):
        """Clear event history"""
        self._history.clear()

    def clear_dead_letters(self):
        """Clear dead letter queue"""
        self._dead_letters.clear()


# Global event bus instance
event_bus = EventBus()
