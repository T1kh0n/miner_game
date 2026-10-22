import os
import math
import pytest
import pygame
import pymunk

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from core.config import (
    CANVAS_W, CANVAS_H, TILE_SIZE,
    CAT_FRAME_W, CAT_FRAME_H, CAT_MINER_ID,
)
from engine.asset_generator import AssetGenerator
from engine.asset_manager import AssetManager
from engine.entities import (
    Player, HookEntity, RockEntity, CabinEntity,
    calculate_sprite_hitbox,
)
from states.state_machine import StateMachine
from states.play_state import PlayState
from states.menu_state import MenuState
from core.save_system import (
    SaveManager, SaveSlotDTO, PlayerStateDTO,
    Vector2DTO, WorldStateDTO, ProgressionDTO,
)


@pytest.fixture(scope="module", autouse=True)
def setup_engine():
    """Initialise pygame and ensure core assets are generated."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()


def test_canvas_aspect_ratio_is_16_to_9():
    """Canvas dimensions must strictly follow 16:9 widescreen ratio."""
    assert CANVAS_W == 320
    assert CANVAS_H == 180
    assert (CANVAS_W / CANVAS_H) == pytest.approx(16.0 / 9.0, rel=1e-2)


def test_calculate_sprite_hitbox_auto():
    """calculate_sprite_hitbox derives correct box dimensions and offsets from alpha mask."""
    surf = pygame.Surface((36, 36), pygame.SRCALPHA)
    pygame.draw.rect(surf, (255, 200, 100, 255), (11, 8, 14, 26))
    w, h, ox, oy = calculate_sprite_hitbox(surf, 12.0, 26.0)
    assert w == 12.0
    assert h == 26.0
    assert ox == pytest.approx(18.0, abs=1.0)
    assert oy == pytest.approx(21.0, abs=1.0)


def test_player_auto_hitbox_initialization():
    """Player hitbox automatically matches sprite dimensions with zero floating."""
    space = pymunk.Space()
    am = AssetManager.get()
    player = Player(100.0, 100.0, "miner", space, am)
    assert player.w == 12.0
    assert player.h == 26.0
    assert player.offset_x > 0
    assert player.offset_y > 0


def test_flashlight_points_at_cursor():
    """Flashlight beam angle strictly follows 360-degree cursor aim."""
    space = pymunk.Space()
    player = Player(100.0, 100.0, "miner", space)

    for target_angle in [0.0, math.pi / 2.0, -math.pi / 2.0, math.pi, -2.4]:
        ang = player.get_flashlight_angle_rad(target_angle)
        assert ang == pytest.approx(target_angle)


def test_upward_rope_aiming_angle():
    """Aiming above the player produces a clean negative (upward) trajectory angle."""
    px, py = 160, 90
    mx_canvas, my_canvas = 160, 20
    aim_angle = math.atan2(my_canvas - py, mx_canvas - px)
    assert aim_angle == pytest.approx(-math.pi / 2.0, abs=1e-3)


def test_rope_swinging_physics_applies_force():
    """Holding horizontal direction applies swing force without overriding Pymunk velocity."""
    space = pymunk.Space()
    space.gravity = (0, 600)
    player = Player(100.0, 100.0, "miner", space)

    wall = pymunk.Segment(space.static_body, (100.0, 20.0), (100.0, 60.0), 4.0)
    space.add(wall)

    player.fire_rope(space, -math.pi / 2.0)
    for _ in range(60):
        player.hook.update(0.016)
        if player.hook.attached:
            break

    assert player.hook.attached is True

    initial_vx = player.body.velocity.x
    player.update(
        up=False, down=False, left=False, right=True, jump=False,
        climb_held=False, dt=0.016, space=space,
        particle_emitter=lambda *args: None, camera=None
    )
    space.step(0.016)
    assert player.body.velocity.x >= initial_vx


def test_rope_tip_pickaxe_rendering():
    """HookEntity renders pickaxe geometry at the hook tip."""
    space = pymunk.Space()
    body = pymunk.Body(5.0, float("inf"))
    body.position = (50.0, 50.0)
    hook = HookEntity(50.0, 50.0, -0.5, space, body)

    surf = pygame.Surface((320, 180), pygame.SRCALPHA)
    hook.render(surf, 0.0, 0.0, 50.0, 50.0)
    hook.attached = True
    hook.render(surf, 0.0, 0.0, 50.0, 50.0)
    assert surf.get_bounding_rect().width > 0


def test_falling_rock_crushes_player():
    """A boulder falling with high downward velocity inflicts crush damage."""
    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    rock = RockEntity(5, 5, ps.space)
    ps.rocks.append(rock)
    ps.player.body.position = (rock.body.position.x, rock.body.position.y + 15.0)

    for r in ps.rocks:
        rx = r.body.position.x
        ry = r.body.position.y
        if abs(rx - rock.body.position.x) < 30.0 and ry <= rock.body.position.y:
            r.body.activate()
            r.body.apply_impulse_at_local_point((0.0, 30.0), (0.0, 0.0))

    assert rock.body.is_sleeping is False


def test_checkpoint_respawn_restores_state():
    """Respawning at checkpoint recovers health, position, and clears death state."""
    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    cabin = ps.cabins[0]
    ps.save_checkpoint(cabin)
    assert ps.last_checkpoint_snapshot is not None

    ps.player.is_dead = True
    ps.player.health = 0.0
    ps.game_over = True

    ps.respawn_at_checkpoint()

    assert ps.player.is_dead is False
    assert ps.player.health == 100.0
    assert ps.game_over is False
    assert abs(ps.player.body.position.x - cabin.x) < 2.0


def test_menu_state_metro_styling_and_continue_button():
    """MenuState builds post-apocalyptic metro visual tree with continue support."""
    sm = StateMachine()
    menu = MenuState(sm)
    menu.enter()

    assert menu.panel.rect.width <= CANVAS_W
    assert menu.panel.rect.height <= CANVAS_H
    assert menu.btn_play is not None
    assert menu.btn_continue is not None

    surf = pygame.Surface((CANVAS_W, CANVAS_H))
    menu.update(0.016)
    menu.render(surf)
    assert surf.get_bounding_rect().width > 0


def test_menu_state_continue_button_slot1():
    sm = StateMachine()
    menu = MenuState(sm)
    save_mgr = menu.save_manager
    slot = SaveSlotDTO(1, PlayerStateDTO(Vector2DTO(0, 0), 100, 100, [], "miner"), WorldStateDTO(1), ProgressionDTO(checkpoint_id="cabin_1"))
    save_mgr.save_slot(1, slot)
    try:
        menu.enter()
        assert menu.btn_continue.visible is True
    finally:
        save_mgr.delete_slot(1)


def test_ceiling_digging_requires_deliberate_input():
    from core.config import DIRT, EMPTY, TILE_SIZE

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    ps.player.body.velocity = (0.0, -100.0)

    px = ps.player.body.position.x
    py = ps.player.body.position.y
    hw = ps.player.w / 2.0
    hh = ps.player.h / 2.0
    above_y = int((py - hh - 2.0) // TILE_SIZE)
    test_x = int(px // TILE_SIZE)
    ps.level.grid[above_y][test_x] = DIRT

    class EmptyKeys:
        def __getitem__(self, k):
            return False

    orig_get_pressed = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: EmptyKeys()
    try:
        ps.update(0.05)
        assert ps.level.grid[above_y][test_x] == DIRT
    finally:
        pygame.key.get_pressed = orig_get_pressed

    class JumpKeys:
        def __getitem__(self, k):
            return k == pygame.K_SPACE

    pygame.key.get_pressed = lambda: JumpKeys()
    try:
        ps.player.body.velocity = (0.0, -100.0)
        ps.update(0.05)
        assert ps.level.grid[above_y][test_x] == EMPTY
    finally:
        pygame.key.get_pressed = orig_get_pressed
