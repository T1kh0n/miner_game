from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

EVT_PLAYER_JUMP = "PLAYER_JUMP"
EVT_PLAYER_LAND = "PLAYER_LAND"
EVT_BLOCK_HIT = "BLOCK_HIT"
EVT_BLOCK_BREAK = "BLOCK_BREAK"
EVT_ROPE_THROW = "ROPE_THROW"
EVT_ROPE_ATTACH = "ROPE_ATTACH"
EVT_ENTITY_HURT = "ENTITY_HURT"
EVT_DIALOGUE_START = "DIALOGUE_START"
EVT_CHECKPOINT_SAVE = "CHECKPOINT_SAVE"
EVT_AFK_KNOCK = "AFK_KNOCK"
EVT_AFK_BLIND = "AFK_BLIND"


class EventManager:
    """Singleton pub/sub event bus for decoupled game-wide communication.

    Subscribers register callbacks keyed by event name strings. Any code
    may emit an event with arbitrary keyword arguments; all registered
    callbacks for that event are invoked synchronously in subscription order.
    """

    _instance: EventManager | None = None

    def __init__(self) -> None:
        """Initialise an empty subscriber registry."""
        self._subscribers: dict[str, list[Callable[..., None]]] = defaultdict(list)

    @classmethod
    def get(cls) -> "EventManager":
        """Return the singleton EventManager, creating it on first call."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Register callback to be called whenever event_name is emitted.

        Args:
            event_name: The string identifier of the event to listen for.
            callback: A callable that accepts the keyword arguments passed to
                emit.
        """
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Remove a previously registered callback for event_name.

        If callback is not currently subscribed the call is a no-op.

        Args:
            event_name: The string identifier of the event.
            callback: The callable to remove.
        """
        try:
            self._subscribers[event_name].remove(callback)
        except ValueError:
            pass

    def emit(self, event_name: str, **kwargs: Any) -> None:
        """Invoke all callbacks subscribed to event_name with kwargs.

        Callbacks are called in the order they were subscribed. Exceptions
        raised by individual callbacks propagate immediately.

        Args:
            event_name: The string identifier of the event to fire.
            **kwargs: Arbitrary keyword arguments forwarded to every callback.
        """
        for callback in list(self._subscribers[event_name]):
            callback(**kwargs)

    def clear(self) -> None:
        """Remove all subscriptions from every event channel.

        Primarily intended for use in unit tests to reset shared state between
        test cases.
        """
        self._subscribers.clear()


EventBus = EventManager
