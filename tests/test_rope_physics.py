import os
import sys
import math
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pymunk


@pytest.fixture
def fresh_space():
    """Return a new pymunk Space with gravity for rope physics tests."""
    space = pymunk.Space()
    space.gravity = (0, 600)
    space.iterations = 20
    return space


@pytest.fixture
def player_body(fresh_space):
    """Return a simple dynamic body simulating the player."""
    body = pymunk.Body(5.0, float("inf"))
    body.position = (100.0, 100.0)
    shape = pymunk.Poly.create_box(body, (12.0, 26.0))
    shape.friction = 0.0
    shape.elasticity = 0.0
    shape.collision_type = 3
    fresh_space.add(body, shape)
    return body, shape, fresh_space


def test_hook_entity_imports():
    """HookEntity must be importable from engine.entities."""
    from engine.entities import HookEntity
    assert HookEntity is not None


def test_hook_launches_and_travels(player_body):
    """A launched hook moves away from the origin each tick."""
    from engine.entities import HookEntity
    body, shape, space = player_body
    hook = HookEntity(body.position.x, body.position.y, 0.0, space, body)
    start_x = hook.x
    hook.update(0.05)
    assert hook.x > start_x, "Hook should travel in the launch direction"


def test_hook_dies_when_exceeding_max_length(player_body):
    """Hook marks itself dead once it exceeds ROPE_MAX_LENGTH travel."""
    from engine.entities import HookEntity
    from core.config import ROPE_MAX_LENGTH
    body, shape, space = player_body
    hook = HookEntity(body.position.x, body.position.y, 0.0, space, body)
    for _ in range(200):
        hook.update(0.05)
        if hook.dead:
            break
    assert hook.dead, "Hook should die after exceeding ROPE_MAX_LENGTH"


def test_hook_attaches_to_static_surface(player_body):
    """Hook attaches when hitting a static segment."""
    from engine.entities import HookEntity
    body, shape, space = player_body

    wall = pymunk.Segment(space.static_body, (200.0, 80.0), (200.0, 200.0), 4.0)
    wall.collision_type = 1
    wall.friction = 0.5
    space.add(wall)

    hook = HookEntity(body.position.x, body.position.y, 0.0, space, body)
    for _ in range(60):
        hook.update(0.016)
        if hook.attached:
            break

    assert hook.attached, "Hook should attach to the static wall segment"
    assert hook.joint is not None, "SlideJoint must be created on attach"


def test_retract_removes_joint(player_body):
    """Retracting the hook removes its joint from the space."""
    from engine.entities import HookEntity
    body, shape, space = player_body

    wall = pymunk.Segment(space.static_body, (200.0, 80.0), (200.0, 200.0), 4.0)
    wall.collision_type = 1
    space.add(wall)

    hook = HookEntity(body.position.x, body.position.y, 0.0, space, body)
    for _ in range(60):
        hook.update(0.016)
        if hook.attached:
            break

    hook.retract()
    assert hook.dead
    assert hook.joint is None or hook.joint not in space.constraints


def test_shorten_reduces_joint_max(player_body):
    """shorten() reduces the slide joint max distance."""
    from engine.entities import HookEntity
    body, shape, space = player_body

    wall = pymunk.Segment(space.static_body, (200.0, 80.0), (200.0, 200.0), 4.0)
    wall.collision_type = 1
    space.add(wall)

    hook = HookEntity(body.position.x, body.position.y, 0.0, space, body)
    for _ in range(60):
        hook.update(0.016)
        if hook.attached:
            break

    if not hook.attached:
        pytest.skip("Hook did not attach in this run")

    before = hook.joint.max
    hook.shorten(10.0)
    assert hook.joint.max < before


def test_lengthen_increases_joint_max(player_body):
    """lengthen() increases the slide joint max distance."""
    from engine.entities import HookEntity
    body, shape, space = player_body

    wall = pymunk.Segment(space.static_body, (200.0, 80.0), (200.0, 200.0), 4.0)
    wall.collision_type = 1
    space.add(wall)

    hook = HookEntity(body.position.x, body.position.y, 0.0, space, body)
    for _ in range(60):
        hook.update(0.016)
        if hook.attached:
            break

    if not hook.attached:
        pytest.skip("Hook did not attach in this run")

    before = hook.joint.max
    hook.shorten(20.0)
    after_shorten = hook.joint.max
    hook.lengthen(10.0)
    assert hook.joint.max > after_shorten


def test_player_toggle_tool():
    """Player.toggle_tool() switches between pickaxe and rope."""
    import pygame
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    import pymunk as pm
    from engine.entities import Player
    space = pm.Space()
    space.gravity = (0, 600)
    player = Player(100.0, 100.0, "miner", space)
    assert not player.using_rope
    player.toggle_tool()
    assert player.using_rope
    player.toggle_tool()
    assert not player.using_rope


def test_player_fire_rope_creates_hook():
    """Player.fire_rope() instantiates a HookEntity on the player."""
    import pygame
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    import pymunk as pm
    from engine.entities import Player
    space = pm.Space()
    space.gravity = (0, 600)
    player = Player(100.0, 100.0, "miner", space)
    assert player.hook is None
    player.fire_rope(space, 0.0)
    assert player.hook is not None


def test_player_retract_rope_removes_hook():
    """Player.retract_rope() sets hook to None."""
    import pygame
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    import pymunk as pm
    from engine.entities import Player
    space = pm.Space()
    space.gravity = (0, 600)
    player = Player(100.0, 100.0, "miner", space)
    player.fire_rope(space, 0.0)
    player.retract_rope()
    assert player.hook is None


def test_rope_mode_disables_dirt_digging():
    import pygame
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))
    from states.state_machine import StateMachine
    from states.play_state import PlayState
    from core.config import DIRT, EMPTY, TILE_SIZE

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    px = ps.player.body.position.x
    py = ps.player.body.position.y
    tx = int((px + 10) // TILE_SIZE)
    ty = int(py // TILE_SIZE)
    ps.level.grid[ty][tx] = DIRT

    ps.player.using_rope = True
    assert ps._dig_tile(tx, ty) is False
    assert ps.level.grid[ty][tx] == DIRT

    class KeyMock:
        def __getitem__(self, k):
            return k in (pygame.K_RIGHT, pygame.K_d)

    orig_get_pressed = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: KeyMock()
    try:
        ps.update(0.05)
        assert ps.level.grid[ty][tx] == DIRT
        ps.player.using_rope = False
        ps.update(0.05)
        assert ps.level.grid[ty][tx] == EMPTY
    finally:
        pygame.key.get_pressed = orig_get_pressed
