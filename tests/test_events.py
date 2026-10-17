import os
import sys
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.events import (
    EventManager,
    EVT_PLAYER_JUMP,
    EVT_PLAYER_LAND,
    EVT_BLOCK_HIT,
    EVT_BLOCK_BREAK,
    EVT_ROPE_THROW,
    EVT_ROPE_ATTACH,
    EVT_ENTITY_HURT,
    EVT_DIALOGUE_START,
    EVT_CHECKPOINT_SAVE,
    EVT_AFK_KNOCK,
    EVT_AFK_BLIND,
)


@pytest.fixture(autouse=True)
def fresh_event_manager():
    """Reset singleton state between tests."""
    EventManager.get().clear()
    yield
    EventManager.get().clear()


def test_event_constants_are_strings():
    """All event name constants must be non-empty strings."""
    constants = [
        EVT_PLAYER_JUMP, EVT_PLAYER_LAND, EVT_BLOCK_HIT, EVT_BLOCK_BREAK,
        EVT_ROPE_THROW, EVT_ROPE_ATTACH, EVT_ENTITY_HURT, EVT_DIALOGUE_START,
        EVT_CHECKPOINT_SAVE, EVT_AFK_KNOCK, EVT_AFK_BLIND,
    ]
    for c in constants:
        assert isinstance(c, str) and len(c) > 0


def test_subscribe_and_emit_single_listener():
    """A subscribed callback receives emitted kwargs."""
    em = EventManager.get()
    received = []
    em.subscribe(EVT_PLAYER_JUMP, lambda **kw: received.append(kw))
    em.emit(EVT_PLAYER_JUMP, x=1.0, y=2.0)
    assert received == [{"x": 1.0, "y": 2.0}]


def test_emit_multiple_listeners():
    """All subscribers for an event are called in subscription order."""
    em = EventManager.get()
    log = []
    em.subscribe(EVT_BLOCK_BREAK, lambda **kw: log.append(("a", kw)))
    em.subscribe(EVT_BLOCK_BREAK, lambda **kw: log.append(("b", kw)))
    em.emit(EVT_BLOCK_BREAK, x=3, y=5)
    assert log == [("a", {"x": 3, "y": 5}), ("b", {"x": 3, "y": 5})]


def test_unsubscribe_removes_listener():
    """Unsubscribed callback is not called on subsequent emits."""
    em = EventManager.get()
    log = []

    def cb(**kw):
        log.append(kw)

    em.subscribe(EVT_ENTITY_HURT, cb)
    em.unsubscribe(EVT_ENTITY_HURT, cb)
    em.emit(EVT_ENTITY_HURT, x=0.0)
    assert log == []


def test_emit_no_listeners_is_silent():
    """Emitting to an event with no subscribers does not raise."""
    em = EventManager.get()
    em.emit(EVT_DIALOGUE_START, speaker="ghost")


def test_emit_no_kwargs():
    """Emitting with no kwargs delivers an empty dict to the callback."""
    em = EventManager.get()
    received = []
    em.subscribe(EVT_AFK_KNOCK, lambda **kw: received.append(kw))
    em.emit(EVT_AFK_KNOCK)
    assert received == [{}]


def test_clear_removes_all_subscriptions():
    """After clear(), emit calls no callbacks."""
    em = EventManager.get()
    log = []
    em.subscribe(EVT_CHECKPOINT_SAVE, lambda **kw: log.append(kw))
    em.clear()
    em.emit(EVT_CHECKPOINT_SAVE, cabin_id="c1")
    assert log == []


def test_same_callback_subscribed_twice_is_called_twice():
    """If the same callable is subscribed twice it is invoked twice."""
    em = EventManager.get()
    log = []

    def cb(**kw):
        log.append(kw)

    em.subscribe(EVT_ROPE_ATTACH, cb)
    em.subscribe(EVT_ROPE_ATTACH, cb)
    em.emit(EVT_ROPE_ATTACH)
    assert len(log) == 2


def test_independent_events_do_not_cross_fire():
    """Listeners on EVT_PLAYER_JUMP are not triggered by EVT_PLAYER_LAND."""
    em = EventManager.get()
    jump_log = []
    land_log = []
    em.subscribe(EVT_PLAYER_JUMP, lambda **kw: jump_log.append(kw))
    em.subscribe(EVT_PLAYER_LAND, lambda **kw: land_log.append(kw))
    em.emit(EVT_PLAYER_LAND, x=0.0, y=0.0)
    assert jump_log == []
    assert len(land_log) == 1


def test_afk_blind_event_constant_unique():
    """EVT_AFK_BLIND and EVT_AFK_KNOCK are distinct strings."""
    assert EVT_AFK_BLIND != EVT_AFK_KNOCK
