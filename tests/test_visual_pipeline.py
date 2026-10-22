import os
import sys
import numpy as np
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame


@pytest.fixture(scope="module", autouse=True)
def setup_display_and_assets():
    """Initialise headless display and ensure assets are generated."""
    pygame.init()
    pygame.display.set_mode((320, 240))
    from engine.banana_pipeline import run_pipeline
    run_pipeline()
    yield
    pygame.quit()


def test_player_sprite_alpha_silhouette_and_dimensions():
    """Assert the player sprite has non-rectangular alpha silhouette and matches 36x36 dimensions."""
    from engine.asset_manager import AssetManager
    am = AssetManager.get()
    sprite = am.get_sprite("cat_miner", "idle_0")
    assert sprite.get_width() == 36
    assert sprite.get_height() == 36

    arr = pygame.surfarray.pixels_alpha(sprite)
    transparent_count = int(np.sum(arr == 0))
    solid_count = int(np.sum(arr > 0))
    assert transparent_count > 0, "Player sprite must have transparent background pixels"
    assert solid_count > 0, "Player sprite must have non-empty character pixels"
    assert transparent_count + solid_count == 36 * 36


def test_metro_props_and_panel_buildings_loaded():
    """Assert metro train, pipes, scaffolding, panel buildings, and UI icons are loaded."""
    from engine.asset_manager import AssetManager
    am = AssetManager.get()

    train = am.get_sprite("metro_props", "train_car")
    assert train.get_width() == 140
    assert train.get_height() == 56

    pipes = am.get_sprite("metro_props", "pipes")
    assert pipes.get_width() == 60
    assert pipes.get_height() == 16

    scaff = am.get_sprite("metro_props", "scaffolding")
    assert scaff.get_width() == 40
    assert scaff.get_height() == 60

    panelki = am.get_sprite("metro_props", "panelki")
    assert panelki.get_width() == 320
    assert panelki.get_height() == 60

    pickaxe = am.get_sprite("ui_icons", "pickaxe")
    assert pickaxe.get_width() == 24
    assert pickaxe.get_height() == 24

    rope = am.get_sprite("ui_icons", "rope")
    assert rope.get_width() == 24
    assert rope.get_height() == 24


def test_background_empty_tiles_contain_textured_brick_pixels():
    """Assert background empty cavern tiles contain textured brick pixels rather than solid flat color."""
    from engine.asset_manager import AssetManager
    am = AssetManager.get()
    bg_brick = am.get_sprite("tiles", "bg_brick")
    assert bg_brick.get_width() == 20
    assert bg_brick.get_height() == 20

    rgb_arr = pygame.surfarray.pixels3d(bg_brick)
    unique_pixel_colors = len(np.unique(rgb_arr.reshape(-1, 3), axis=0))
    assert unique_pixel_colors > 4, "Background brick tile must be textured, not flat solid color"


def test_render_metro_cavern_frame_and_save_debug_screenshot():
    """Render 1 frame of PlayState at the Metro Cavern and save assets/debug_biome1_preview.png."""
    from states.state_machine import StateMachine
    from states.play_state import PlayState
    from core.leaderboard import LeaderboardManager

    sm = StateMachine()
    sm.leaderboard = LeaderboardManager()
    sm.selected_skin = "miner"

    ps = PlayState(sm)
    ps.enter()
    ps.player.body.position = (100.0, 160.0)
    ps.camera.x = 0.0
    ps.camera.y = 40.0

    canvas = pygame.Surface((320, 240))
    ps.render(canvas)

    out_path = "assets/debug_biome1_preview.png"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pygame.image.save(canvas, out_path)
    assert os.path.exists(out_path)

    arr = pygame.surfarray.pixels3d(canvas)
    unique_colors = len(np.unique(arr.reshape(-1, 3), axis=0))
    assert unique_colors > 100, f"Rendered frame must contain rich multi-layer visuals, got {unique_colors} colors"


def test_generate_tiles_force_preserves_bg_brick():
    import json
    from engine.asset_generator import AssetGenerator
    AssetGenerator.generate_tiles(force=True)
    with open("assets/data/tiles.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert "bg_brick" in meta["frames"]
    surf = pygame.image.load("assets/spritesheets/tiles.png")
    assert surf.get_width() >= 120
    assert surf.get_height() == 20

def test_terrain_tiles_have_no_transparent_seams_or_borders():
    import json
    from PIL import Image
    from engine.banana_pipeline import process_metro_props
    process_metro_props()
    with open("assets/data/tiles.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    img = Image.open("assets/spritesheets/tiles.png")
    arr = np.array(img)
    solid_tiles = ["wall_under", "wall_surface", "dirt", "stone", "bg_brick", "shale"]
    for name in solid_tiles:
        assert name in meta["frames"]
        fx = meta["frames"][name]["x"]
        w = meta["frames"][name]["w"]
        h = meta["frames"][name]["h"]
        tile = arr[0:h, fx:fx+w]
        assert np.all(tile[:, 0, 3] == 255)
        assert np.all(tile[:, -1, 3] == 255)
        assert np.all(tile[0, :, 3] == 255)
        assert np.all(tile[-1, :, 3] == 255)
