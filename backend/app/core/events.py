"""
Parashakti Framework - Event Bus

Decoupled communication between divisions and services.
Events are published and subscribed to asynchronously.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(str, Enum):
    """Event processing priority."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Event:
    """Represents an event in the system."""
    name: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None


@dataclass
class EventResult:
    """Result of event handler execution."""
    handler_name: str
    success: bool
    error: Optional[str] = None
    duration_ms: float = 0


class EventBus:
    """
    Central event bus for inter-division communication.
    
    Usage:
        # Subscribe to events
        @event_bus.on("germplasm.created")
        async def handle_germplasm_created(event: Event):
            print(f"New germplasm: {event.payload}")
        
        # Publish events
        await event_bus.publish("germplasm.created", {
            "germplasm_id": "G001",
            "name": "Sample Germplasm"
        })
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def on(self, event_name: str) -> Callable:
        """
        Decorator to subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to (e.g., "germplasm.created")
        
        Returns:
            Decorator function
        """
        def decorator(handler: Callable) -> Callable:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(handler)
            logger.debug(f"Registered handler {handler.__name__} for event {event_name}")
            return handler
        return decorator

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """
        Subscribe a handler to an event.
        
        Args:
            event_name: Name of the event
            handler: Async function to handle the event
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable) -> bool:
        """
        Unsubscribe a handler from an event.
        
        Args:
            event_name: Name of the event
            handler: Handler to remove
        
        Returns:
            True if handler was removed, False if not found
        """
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(handler)
                return True
            except ValueError:
                pass
        return False

    async def publish(
        self,
        event_name: str,
        payload: Dict[str, Any],
        source: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_name: Name of the event (e.g., "germplasm.created")
            payload: Event data
            source: Source division/module
            priority: Processing priority
            correlation_id: ID to correlate related events
        """
        event = Event(
            name=event_name,
            payload=payload,
            source=source,
            priority=priority,
            correlation_id=correlation_id,
        )

        await self._queue.put(event)
        logger.debug(f"Published event: {event_name}")

    async def publish_sync(
        self,
        event_name: str,
        payload: Dict[str, Any],
        source: Optional[str] = None,
    ) -> List[EventResult]:
        """
        Publish an event and wait for all handlers to complete.
        
        Args:
            event_name: Name of the event
            payload: Event data
            source: Source division/module
        
        Returns:
            List of results from all handlers
        """
        event = Event(name=event_name, payload=payload, source=source)
        return await self._process_event(event)

    async def _process_event(self, event: Event) -> List[EventResult]:
        """Process a single event through all subscribers."""
        results = []
        handlers = self._subscribers.get(event.name, [])

        # Also check for wildcard subscribers
        wildcard_handlers = self._subscribers.get("*", [])
        all_handlers = handlers + wildcard_handlers

        for handler in all_handlers:
            start_time = asyncio.get_event_loop().time()
            try:
                await handler(event)
                duration = (asyncio.get_event_loop().time() - start_time) * 1000
                results.append(EventResult(
                    handler_name=handler.__name__,
                    success=True,
                    duration_ms=duration,
                ))
            except Exception as e:
                duration = (asyncio.get_event_loop().time() - start_time) * 1000
                logger.error(f"Event handler {handler.__name__} failed: {e}")
                results.append(EventResult(
                    handler_name=handler.__name__,
                    success=False,
                    error=str(e),
                    duration_ms=duration,
                ))

        return results

    async def start(self) -> None:
        """Start the event processing loop."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus stopped")

    async def _process_loop(self) -> None:
        """Background loop to process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def get_subscribers(self, event_name: str) -> List[str]:
        """Get list of subscriber names for an event."""
        handlers = self._subscribers.get(event_name, [])
        return [h.__name__ for h in handlers]

    def get_all_events(self) -> List[str]:
        """Get list of all registered event names."""
        return list(self._subscribers.keys())


# Global event bus instance
event_bus = EventBus()


# Standard event names
class Events:
    """Standard event names used across the platform."""

    # Germplasm events
    GERMPLASM_CREATED = "germplasm.created"
    GERMPLASM_UPDATED = "germplasm.updated"
    GERMPLASM_DELETED = "germplasm.deleted"

    # Trial events
    TRIAL_CREATED = "trial.created"
    TRIAL_UPDATED = "trial.updated"
    TRIAL_COMPLETED = "trial.completed"

    # Observation events
    OBSERVATION_RECORDED = "observation.recorded"
    OBSERVATION_VALIDATED = "observation.validated"

    # Sync events
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    INTEGRATION_SYNC_COMPLETED = "integration.sync.completed"

    # User events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
