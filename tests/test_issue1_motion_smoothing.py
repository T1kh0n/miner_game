import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pymunk
from core.camera import Camera
from core.config import FIXED_DT
from engine.entities import Player, RockEntity
from engine.asset_generator import AssetGenerator
from states.play_state import PlayState
from states.state_machine import StateMachine

def test_camera_subpixel_smoothing() -> None:
    cam = Camera(1000.0, 1000.0)
    pos1_x, pos1_y = cam.update(200.0, 200.0, True, False, FIXED_DT)
    pos2_x, pos2_y = cam.update(200.0, 200.0, True, False, FIXED_DT)
    assert pos2_x > pos1_x
    assert pos2_y > pos1_y

def test_rock_lerp_interpolation() -> None:
    space = pymunk.Space()
    rock = RockEntity(5, 5, space)
    rock.save_previous_state()
    rock.body.position = (rock.body.position.x + 10.0, rock.body.position.y + 20.0)
    rock.body.angle = 1.0

    x_mid, y_mid, a_mid = rock.get_interpolated_pose(0.5)
    assert abs(x_mid - (rock.prev_x + 5.0)) < 1e-4
    assert abs(y_mid - (rock.prev_y + 10.0)) < 1e-4
    assert abs(a_mid - 0.5) < 1e-4

def test_player_lerp_and_animation_dt() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    space = pymunk.Space()
    player = Player(100.0, 100.0, "classic", space)
    player.save_previous_state()
    player.body.position = (120.0, 140.0)

    px, py = player.get_interpolated_pos(0.25)
    assert abs(px - 105.0) < 1e-4
    assert abs(py - 110.0) < 1e-4

    initial_anim_time = player.anim_time
    player.update(False, False, False, False, False, False, 0.05, space, lambda *_: None, Camera(500, 500))
    assert player.anim_time > initial_anim_time
    assert abs(player.anim_time - 0.05) < 1e-4

def test_play_state_fixed_accumulator() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    ps.update(FIXED_DT * 2.5)
    assert ps.physics_accumulator < FIXED_DT
    assert 0.0 <= ps.render_alpha <= 1.0
