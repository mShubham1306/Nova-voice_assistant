"""
NOVA Core — Event Bus
Decoupled publish-subscribe event system for NOVA 3.0 architecture.

Tools and execution engines publish events (e.g. 'app_opened', 'file_opened', 'danger_requested').
Subscribers (Memory, History, WebSocket, Audit Logger) react asynchronously without coupling.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger("nova.event_bus")


@dataclass
class Event:
    """Standardized Event object."""
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    sender: str = "nova_system"


class EventBus:
    """
    In-memory async publish-subscribe event bus.
    Supports both sync and async subscriber callbacks.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], Any]]] = defaultdict(list)
        self._wildcard_subscribers: list[Callable[[Event], Any]] = []
        self._event_history: list[Event] = []

    def subscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe to a specific event name (or '*' for all events)."""
        if event_name == "*":
            self._wildcard_subscribers.append(handler)
        else:
            self._subscribers[event_name].append(handler)
        logger.debug("Subscribed to event '%s'", event_name)

    def unsubscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Remove a subscriber handler."""
        if event_name == "*" and handler in self._wildcard_subscribers:
            self._wildcard_subscribers.remove(handler)
        elif handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    def publish(self, event_name: str, payload: dict[str, Any] | None = None, sender: str = "system") -> Event:
        """
        Publish an event to all subscribers.
        Executes callbacks safely without stopping on subscriber errors.
        """
        event = Event(name=event_name, payload=payload or {}, sender=sender)
        self._event_history.append(event)
        if len(self._event_history) > 200:
            self._event_history.pop(0)

        logger.info("[EventBus] 📢 %s (from %s): %s", event_name, sender, list((payload or {}).keys()))

        # Dispatch to specific subscribers
        handlers = list(self._subscribers.get(event_name, [])) + list(self._wildcard_subscribers)
        for handler in handlers:
            try:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(res)
                    except RuntimeError:
                        pass
            except Exception as e:
                logger.error("[EventBus] Handler error for '%s': %s", event_name, e)

        return event

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Return history of published events."""
        return [
            {
                "name": e.name,
                "payload": e.payload,
                "timestamp": e.timestamp,
                "sender": e.sender,
            }
            for e in self._event_history[-limit:][::-1]
        ]


# Singleton instance
event_bus = EventBus()
