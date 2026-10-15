import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pymunk
from engine.asset_generator import AssetGenerator
from engine.entities import CabinEntity, Player
from engine.level import Level
from states.play_state import PlayState
from states.state_machine import StateMachine

def test_cabin_proximity_and_activation() -> None:
    cabin = CabinEntity("cabin_test", 10, 30)
    assert cabin.is_near(cabin.x, cabin.y) is True
    assert cabin.is_near(cabin.x + 100.0, cabin.y) is False

    called = False
    def fake_emit(x, y, cols, count):
        nonlocal called
        called = True

    class DummyCam:
        def add_shake(self, s, d): pass

    cabin.activate(fake_emit, DummyCam())
    assert cabin.activated is True
    assert called is True

def test_level_has_cabin_locations() -> None:
    level = Level(seed=12345)
    assert len(level.cabin_locations) > 0
    depths = [ty for _, ty, _ in level.cabin_locations]
    for d in depths:
        assert d > 15

def test_checkpoint_save_and_respawn_cycle() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    assert len(ps.cabins) > 0
    cabin = ps.cabins[0]

    ps.player.body.position = (cabin.x, cabin.y)
    ps.player.health = 40.0
    ps.player.stamina = 50.0

    cabin.activate(ps.emit_particles, ps.camera)
    ps.save_checkpoint(cabin)
    assert ps.last_checkpoint_snapshot is not None
    assert ps.last_checkpoint_snapshot.progression.checkpoint_id == cabin.cabin_id

    ps.player.is_dead = True
    ps.player.health = 0.0
    ps.game_over = True
    ps.panel_over.visible = True

    ps.respawn_at_checkpoint()

    assert ps.player.is_dead is False
    assert ps.player.health == 100.0
    assert ps.player.stamina == 100.0
    assert ps.game_over is False
    assert ps.panel_over.visible is False
    assert abs(ps.player.body.position.x - cabin.x) < 2.0
