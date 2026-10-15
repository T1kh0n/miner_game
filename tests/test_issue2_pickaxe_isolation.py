import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pymunk
from core.camera import Camera
from core.config import FIXED_DT
from engine.entities import Player, PLAYER_BODY_W, PLAYER_BODY_H
from engine.asset_generator import AssetGenerator

def test_player_body_invariant_size() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    space = pymunk.Space()
    player = Player(100.0, 100.0, "classic", space)
    orig_shape = player.shape
    orig_w = player.w
    orig_h = player.h

    assert orig_w == PLAYER_BODY_W
    assert orig_h == PLAYER_BODY_H

    player.is_digging = True
    player.dig_time = 0.2
    player.update(False, False, True, False, False, False, FIXED_DT, space, lambda *_: None, Camera(500, 500))

    assert player.shape == orig_shape
    assert player.w == orig_w
    assert player.h == orig_h

    player.is_climbing = True
    player.climb_time = 0.3
    player.update(True, False, False, False, False, True, FIXED_DT, space, lambda *_: None, Camera(500, 500))

    assert player.shape == orig_shape
    assert player.w == orig_w
    assert player.h == orig_h

def test_climbing_hook_raycast_anchor() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    space = pymunk.Space()
    player = Player(100.0, 100.0, "classic", space)

    wall_shape = pymunk.Segment(space.static_body, (110.0, 80.0), (110.0, 120.0), 2)
    wall_shape.collision_type = 1
    space.add(wall_shape)

    player.facing_right = True
    assert player.check_climb_anchor(space) is True
    assert player.climb_anchor_point is not None

    player.facing_right = False
    assert player.check_climb_anchor(space) is False
    assert player.climb_anchor_point is None

def test_dig_sensor_bounds_decoupled_from_body() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    space = pymunk.Space()
    player = Player(50.0, 50.0, "classic", space)

    b_right = player.get_dig_sensor_bounds(1, 0)
    assert b_right[0] >= player.body.position.x
    assert player.w == PLAYER_BODY_W
    assert player.h == PLAYER_BODY_H

    b_down = player.get_dig_sensor_bounds(0, 1)
    assert b_down[1] >= player.body.position.y
    assert player.w == PLAYER_BODY_W
    assert player.h == PLAYER_BODY_H
