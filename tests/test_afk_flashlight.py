import os
import sys
import math
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame
import pymunk

from core.config import AFK_KNOCK_SECONDS, AFK_BLIND_SECONDS, FLASHLIGHT_ANGLE


@pytest.fixture(autouse=True)
def pygame_display():
    """Initialise a headless pygame display for sprite tests."""
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


@pytest.fixture
def player_in_space():
    """Return a fully initialised Player in a pymunk space."""
    from engine.entities import Player
    space = pymunk.Space()
    space.gravity = (0, 600)
    player = Player(100.0, 100.0, "miner", space)
    return player, space


def test_afk_timer_increments_with_no_input(player_in_space):
    """afk_timer increases each update when any_input=False."""
    player, space = player_in_space
    dt = 1.0 / 60.0

    def noop(*a, **kw):
        pass

    class DummyCam:
        def add_shake(self, *a):
            pass

    cam = DummyCam()
    for _ in range(10):
        player.save_previous_state()
        player.update(False, False, False, False, False, False, dt, space, noop, cam, any_input=False)

    assert player.afk_timer > 0.0, "afk_timer should increment without input"


def test_afk_timer_resets_on_input(player_in_space):
    """afk_timer resets to zero when any_input=True."""
    player, space = player_in_space
    player.afk_timer = 5.0

    def noop(*a, **kw):
        pass

    class DummyCam:
        def add_shake(self, *a):
            pass

    cam = DummyCam()
    player.save_previous_state()
    player.update(False, False, False, False, False, False, 1.0 / 60.0, space, noop, cam, any_input=True)
    assert player.afk_timer == 0.0


def test_afk_phase_0_below_knock_threshold(player_in_space):
    """afk_phase is 0 when afk_timer is below AFK_KNOCK_SECONDS."""
    player, space = player_in_space
    player.afk_timer = AFK_KNOCK_SECONDS - 1.0

    def noop(*a, **kw):
        pass

    class DummyCam:
        def add_shake(self, *a):
            pass

    cam = DummyCam()
    player.save_previous_state()
    player.update(
        False, False, False, False, False, False,
        1.0 / 60.0, space, noop, cam, any_input=False,
        afk_knock_seconds=AFK_KNOCK_SECONDS,
        afk_blind_seconds=AFK_BLIND_SECONDS,
    )
    assert player.afk_phase == 0


def test_afk_phase_2_at_knock_threshold(player_in_space):
    """afk_phase is >= 2 when afk_timer >= AFK_KNOCK_SECONDS."""
    player, space = player_in_space
    player.afk_timer = AFK_KNOCK_SECONDS + 0.1

    def noop(*a, **kw):
        pass

    class DummyCam:
        def add_shake(self, *a):
            pass

    cam = DummyCam()
    player.save_previous_state()
    player.update(
        False, False, False, False, False, False,
        1.0 / 60.0, space, noop, cam, any_input=False,
        afk_knock_seconds=AFK_KNOCK_SECONDS,
        afk_blind_seconds=AFK_BLIND_SECONDS,
    )
    assert player.afk_phase >= 2, f"Expected afk_phase >= 2, got {player.afk_phase}"


def test_afk_phase_4_at_blind_threshold(player_in_space):
    """afk_phase is >= 4 when afk_timer >= AFK_BLIND_SECONDS."""
    player, space = player_in_space
    player.afk_timer = AFK_BLIND_SECONDS + 0.1

    def noop(*a, **kw):
        pass

    class DummyCam:
        def add_shake(self, *a):
            pass

    cam = DummyCam()
    player.save_previous_state()
    player.update(
        False, False, False, False, False, False,
        1.0 / 60.0, space, noop, cam, any_input=False,
        afk_knock_seconds=AFK_KNOCK_SECONDS,
        afk_blind_seconds=AFK_BLIND_SECONDS,
    )
    assert player.afk_phase >= 4, f"Expected afk_phase >= 4, got {player.afk_phase}"


def test_afk_frame_key_matches_phase(player_in_space):
    """_get_current_frame_key returns afk_N key when afk_phase >= 1."""
    player, space = player_in_space
    player.afk_phase = 2
    player.on_ground = True
    player.is_climbing = False
    player.is_digging = False
    key = player._get_current_frame_key()
    assert key.startswith("afk_"), f"Expected afk_* frame key, got '{key}'"


def test_flashlight_angle_facing_right(player_in_space):
    """Flashlight angle is 0.0 rad when facing right and no hook."""
    player, space = player_in_space
    player.facing_right = True
    player.hook = None
    angle = player.get_flashlight_angle_rad()
    assert abs(angle) < 1e-6


def test_flashlight_angle_facing_left(player_in_space):
    """Flashlight angle is math.pi when facing left and no hook."""
    player, space = player_in_space
    player.facing_right = False
    player.hook = None
    angle = player.get_flashlight_angle_rad()
    assert abs(angle - math.pi) < 1e-6


def test_flashlight_angle_config_is_positive():
    """FLASHLIGHT_ANGLE config constant is positive degrees."""
    assert FLASHLIGHT_ANGLE > 0


def test_player_body_collider_dimensions():
    """Player physics collider width and height match CAT_BODY_W and CAT_BODY_H."""
    from core.config import CAT_BODY_W, CAT_BODY_H
    from engine.entities import PLAYER_BODY_W, PLAYER_BODY_H
    assert PLAYER_BODY_W == CAT_BODY_W
    assert PLAYER_BODY_H == CAT_BODY_H


def test_afk_knock_blind_config_ordering():
    """AFK_KNOCK_SECONDS must be strictly less than AFK_BLIND_SECONDS."""
    assert AFK_KNOCK_SECONDS < AFK_BLIND_SECONDS
