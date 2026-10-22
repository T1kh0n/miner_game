import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import json
import pygame
from core.config import TILE_SIZE, SHALE, EMPTY, SHALE_MAX_HITS
from engine.asset_generator import AssetGenerator
from states.play_state import PlayState
from states.state_machine import StateMachine

def test_cat_driver_spritesheet_and_metadata() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    png_path = "assets/spritesheets/cat_driver.png"
    json_path = "assets/data/cat_driver.json"

    assert os.path.exists(png_path)
    assert os.path.exists(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["frame_width"] == 32
    assert meta["frame_height"] == 36
    frames = meta["frames"]

    for i in range(4):
        assert f"idle_{i}" in frames
        assert f"walk_{i}" in frames
        assert f"action_lantern_{i}" in frames
        assert f"talk_{i}" in frames

def test_driver_arrival_cutscene_and_rope_reward() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    assert ps.player.ropes == 3
    assert ps.metro_cutscene_triggered is False
    assert ps.driver_cat.visible is False

    ps.player.body.position = (ps.player.body.position.x, 8.0 * TILE_SIZE)
    ps.update(0.016)

    assert ps.metro_cutscene_triggered is True
    assert ps.cutscene_mgr.is_active is True

    ps.cutscene_mgr.skip()

    assert ps.cutscene_mgr.is_active is False
    assert ps.train_x == float(2 * TILE_SIZE)
    assert ps.driver_cat.visible is True
    assert ps.driver_cat.has_spoken is True
    assert ps.player.ropes == 6

def test_shale_multi_hit_and_cracks() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all()

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    sx, sy = 10, 15
    ps.level.grid[sy][sx] = SHALE
    ps.add_static_tile(sx, sy)

    assert (sx, sy) in ps.tile_shapes

    hit1 = ps._dig_tile(sx, sy)
    assert hit1 is True
    assert ps.level.grid[sy][sx] == SHALE
    assert ps.block_hits.get((sx, sy)) == 1
    assert (sx, sy) in ps.tile_shapes

    hit2 = ps._dig_tile(sx, sy)
    assert hit2 is True
    assert ps.level.grid[sy][sx] == SHALE
    assert ps.block_hits.get((sx, sy)) == 2
    assert (sx, sy) in ps.tile_shapes

    hit3 = ps._dig_tile(sx, sy)
    assert hit3 is True
    assert ps.level.grid[sy][sx] == EMPTY
    assert (sx, sy) not in ps.block_hits
    assert (sx, sy) in ps.mined_tile_coords
    assert (sx, sy) not in ps.tile_shapes


def test_level_generates_shale_and_playstate_creates_collision():
    from engine.level import Level

    lvl = Level(seed=42)
    shale_count = sum(row.count(SHALE) for row in lvl.grid)
    assert shale_count > 0

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    shale_tiles_in_level = [
        (x, y) for y in range(ps.level.h) for x in range(ps.level.w)
        if ps.level.grid[y][x] == SHALE
    ]
    assert len(shale_tiles_in_level) > 0

    for sx, sy in shale_tiles_in_level[:5]:
        assert (sx, sy) in ps.tile_shapes


def test_shale_tile_visual_texture_and_rendering():
    from engine.asset_manager import AssetManager

    with open("assets/data/tiles.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert "shale" in meta["frames"]
    assert meta["frames"]["shale"]["w"] == TILE_SIZE
    assert meta["frames"]["shale"]["h"] == TILE_SIZE

    am = AssetManager.get()
    shale_sprite = am.get_sprite("tiles", "shale")
    assert isinstance(shale_sprite, pygame.Surface)
    assert shale_sprite.get_width() == TILE_SIZE
    assert shale_sprite.get_height() == TILE_SIZE

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()
    ps.level.grid[1][1] = SHALE
    render_surf = pygame.Surface((320, 240))
    ps.render(render_surf)
