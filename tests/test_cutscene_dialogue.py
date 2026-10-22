import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from core.cutscene import (
    CutsceneManager, MoveCameraTo, MoveEntityTo, Wait,
    ShowDialogue, TriggerEvent, ShowEmote, PlayAnimation
)
from engine.dialogue import DialogueBox, EmoteBubble, EmoteManager
from core.events import EventBus

def test_typewriter_and_dialogue_box() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    dbox = DialogueBox()
    assert dbox.is_open is False
    assert dbox.is_typing is False

    called_close = False
    def on_close():
        nonlocal called_close
        called_close = True

    dbox.show_message("driver", "Train Driver", "driver_dialogue_1", "Hello miner!", on_close=on_close)
    assert dbox.is_open is True
    assert dbox.is_typing is True
    assert dbox.char_index == 0

    dbox.update(0.1)
    assert dbox.char_index > 0
    assert dbox.char_index < len(dbox.full_text)

    dbox.fast_forward()
    assert dbox.char_index == len(dbox.full_text)
    assert dbox.is_typing is False

    closed = dbox.advance()
    assert closed is True
    assert dbox.is_open is False
    assert called_close is True

def test_emote_bubble_and_manager() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    class DummyEntity:
        def __init__(self):
            self.x = 100.0
            self.y = 80.0

    entity = DummyEntity()
    mgr = EmoteManager()
    bubble = mgr.spawn_bubble("hero", entity, "exclamation", duration=0.5)

    assert len(mgr.bubbles) == 1
    assert bubble.is_alive is True

    mgr.update(0.2)
    assert bubble.is_alive is True

    surf = pygame.Surface((320, 240))
    mgr.render(surf, 0.0, 0.0)

    mgr.update(0.4)
    assert len(mgr.bubbles) == 0

def test_cutscene_manager_timeline_and_skip() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    class DummyCam:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0

    class DummyEntity:
        def __init__(self):
            self.x = 10.0
            self.y = 10.0

    cam = DummyCam()
    ent = DummyEntity()
    dbox = DialogueBox()
    event_bus = EventBus()
    events_received = []

    event_bus.subscribe("test_event", lambda **kw: events_received.append(kw))

    ctx = {
        "camera": cam,
        "entities": {"player": ent},
        "dialogue_box": dbox,
        "event_bus": event_bus,
    }

    actions = [
        MoveCameraTo(100.0, 50.0, duration=0.5),
        MoveEntityTo("player", 50.0, 10.0, speed=100.0),
        Wait(duration=0.2),
        ShowDialogue("driver", "Train Driver", "test_key", default_text="Greetings"),
        TriggerEvent("test_event", {"arg": 42}),
    ]

    cm = CutsceneManager()
    cm.start_cutscene(actions, ctx)
    assert cm.is_active is True
    assert cm.current_index == 0

    cm.update(0.25)
    assert 0.0 < cam.x < 100.0
    assert cm.current_index == 0

    cm.update(0.3)
    assert cam.x == 100.0
    assert cm.current_index >= 1

    cm.skip()
    assert cm.is_active is False
    assert cam.x == 100.0
    assert cam.y == 50.0
    assert ent.x == 50.0
    assert ent.y == 10.0
    assert len(events_received) == 1
    assert events_received[0]["arg"] == 42


def test_dialogue_box_text_does_not_overflow():
    pygame.init()
    pygame.display.set_mode((1, 1))
    dbox = DialogueBox()
    surf = pygame.Surface((320, 180))
    long_text = "Greetings, weary miner! The upper bunker gates are sealed, but you can find deeper tunnels ahead. Take these ropes!"
    dbox.show_message("driver", "Train Driver", "test_overflow", long_text)
    dbox.fast_forward()
    dbox.render(surf)
    assert dbox.is_open is True
