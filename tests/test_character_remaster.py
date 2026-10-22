import json
import os
import sys
import numpy as np
import pytest
import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import CAT_MINER_ID
from engine.asset_generator import AssetGenerator
from engine.asset_manager import AssetManager


@pytest.fixture(scope="module", autouse=True)
def setup_module():
    """Ensure all remastered character assets are generated before testing."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    AssetGenerator.generate_all(force=True)


def test_character_spritesheets_dimensions_and_transparency() -> None:
    """Verify that all 4 character spritesheets have exact dimensions and alpha transparency."""
    configs = [
        (f"assets/spritesheets/cat_{CAT_MINER_ID}.png", 36 * 43, 36),
        ("assets/spritesheets/cat_driver.png", 32 * 16, 36),
        ("assets/spritesheets/cat_soldier.png", 36 * 24, 36),
        ("assets/spritesheets/cat_feral.png", 36 * 24, 36),
    ]
    for path, expected_w, expected_h in configs:
        assert os.path.exists(path), f"Missing spritesheet {path}"
        surf = pygame.image.load(path)
        assert surf.get_width() == expected_w, f"{path} width mismatch: {surf.get_width()} != {expected_w}"
        assert surf.get_height() == expected_h, f"{path} height mismatch: {surf.get_height()} != {expected_h}"
        assert bool(surf.get_flags() & pygame.SRCALPHA), f"{path} must preserve alpha transparency"


def test_character_metadata_consistency() -> None:
    """Verify JSON slice metadata, frame counts, and colliders for all 4 remastered characters."""
    specs = [
        (f"assets/data/cat_{CAT_MINER_ID}.json", 36, 36, 43, 12, 26),
        ("assets/data/cat_driver.json", 32, 36, 16, 12, 26),
        ("assets/data/cat_soldier.json", 36, 36, 24, 12, 26),
        ("assets/data/cat_feral.json", 36, 36, 24, 14, 24),
    ]
    for path, fw, fh, frame_count, col_w, col_h in specs:
        assert os.path.exists(path), f"Missing metadata {path}"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["frame_width"] == fw
        assert data["frame_height"] == fh
        assert len(data["frames"]) == frame_count
        assert data["collider"]["w"] == col_w
        assert data["collider"]["h"] == col_h
        for frame_key, fmeta in data["frames"].items():
            assert fmeta["w"] == fw
            assert fmeta["h"] == fh
            assert fmeta["pivot"] == [0.5, 0.75]


def test_miner_cat_remaster_features() -> None:
    """Verify Miner Cat features: yellow hardhat, olive utility vest, and glowing headlamp."""
    am = AssetManager.get()
    idle_0 = am.get_sprite(f"cat_{CAT_MINER_ID}", "idle_0")
    arr = pygame.surfarray.pixels3d(idle_0)

    hardhat_mask = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 160) & (arr[:, :, 2] < 60)
    assert np.any(hardhat_mask), "Miner Cat must feature yellow hardhat"

    olive_mask = (arr[:, :, 0] > 70) & (arr[:, :, 0] < 110) & (arr[:, :, 1] > 90) & (arr[:, :, 1] < 130) & (arr[:, :, 2] < 75)
    assert np.any(olive_mask), "Miner Cat must feature olive utility vest"

    lamp_mask = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 230) & (arr[:, :, 2] > 140)
    assert np.any(lamp_mask), "Miner Cat must feature glowing headlamp lens"


def test_driver_cat_remaster_features() -> None:
    """Verify Train Driver Cat features: ushanka fur, railway badge, and brass lantern."""
    am = AssetManager.get()
    idle_0 = am.get_sprite("cat_driver", "idle_0")
    arr = pygame.surfarray.pixels3d(idle_0)

    fleece_mask = (arr[:, :, 0] > 160) & (arr[:, :, 0] < 205) & (arr[:, :, 1] > 150) & (arr[:, :, 1] < 195) & (arr[:, :, 2] > 140) & (arr[:, :, 2] < 185)
    assert np.any(fleece_mask), "Train Driver Cat must feature ushanka fur earflaps"

    badge_mask = (arr[:, :, 0] > 230) & (arr[:, :, 1] > 195) & (arr[:, :, 2] < 90)
    assert np.any(badge_mask), "Train Driver Cat must feature golden railway badge"

    action_lantern = am.get_sprite("cat_driver", "action_lantern_2")
    act_arr = pygame.surfarray.pixels3d(action_lantern)
    lantern_mask = (act_arr[:, :, 0] > 230) & (act_arr[:, :, 1] > 210) & (act_arr[:, :, 2] > 110)
    assert np.any(lantern_mask), "Train Driver Cat must feature glowing brass lantern"


def test_soldier_cat_remaster_features() -> None:
    """Verify Watermelon Soldier Cat features: striped watermelon helmet, melon rind cuirass, and steel shovel."""
    am = AssetManager.get()
    idle_0 = am.get_sprite("cat_soldier", "idle_0")
    arr = pygame.surfarray.pixels3d(idle_0)

    rind_mask = (arr[:, :, 0] > 35) & (arr[:, :, 0] < 80) & (arr[:, :, 1] > 120) & (arr[:, :, 1] < 170) & (arr[:, :, 2] < 85)
    assert np.any(rind_mask), "Soldier Cat must feature watermelon green rind"

    flesh_mask = (arr[:, :, 0] > 210) & (arr[:, :, 1] < 80) & (arr[:, :, 2] < 95)
    assert np.any(flesh_mask), "Soldier Cat must feature watermelon pink flesh trim"

    action_shovel = am.get_sprite("cat_soldier", "action_shovel_1")
    sh_arr = pygame.surfarray.pixels3d(action_shovel)
    steel_mask = (sh_arr[:, :, 0] > 180) & (sh_arr[:, :, 1] > 190) & (sh_arr[:, :, 2] > 205)
    assert np.any(steel_mask), "Soldier Cat must feature steel trench shovel blade"


def test_feral_cat_remaster_features() -> None:
    """Verify Feral Cat features: white fur, red bandana scarf, and heterochromia eyes (left red, right blue)."""
    am = AssetManager.get()
    idle_0 = am.get_sprite("cat_feral", "idle_0")
    arr = pygame.surfarray.pixels3d(idle_0)

    white_mask = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 245)
    assert np.any(white_mask), "Feral Cat must feature fluffy white fur"

    scarf_mask = (arr[:, :, 0] > 190) & (arr[:, :, 1] < 60) & (arr[:, :, 2] < 70)
    assert np.any(scarf_mask), "Feral Cat must feature red bandana scarf"

    left_eye_mask = (arr[:, :, 0] > 230) & (arr[:, :, 1] < 70) & (arr[:, :, 2] < 70)
    assert np.any(left_eye_mask), "Feral Cat must feature red heterochromia left eye"

    right_eye_mask = (arr[:, :, 0] < 70) & (arr[:, :, 1] > 120) & (arr[:, :, 2] > 230)
    assert np.any(right_eye_mask), "Feral Cat must feature blue heterochromia right eye"


def test_idle_animation_palette_consistency_across_frames():
    am = AssetManager.get()
    for i in range(4):
        idle_miner = am.get_sprite(f"cat_{CAT_MINER_ID}", f"idle_{i}")
        arr_m = pygame.surfarray.pixels3d(idle_miner)
        assert np.any((arr_m[:, :, 0] > 200) & (arr_m[:, :, 1] > 160) & (arr_m[:, :, 2] < 60))
        assert np.any((arr_m[:, :, 0] > 70) & (arr_m[:, :, 0] < 110) & (arr_m[:, :, 1] > 90) & (arr_m[:, :, 1] < 130) & (arr_m[:, :, 2] < 75))

        idle_driver = am.get_sprite("cat_driver", f"idle_{i}")
        arr_d = pygame.surfarray.pixels3d(idle_driver)
        assert np.any((arr_d[:, :, 0] > 230) & (arr_d[:, :, 1] > 195) & (arr_d[:, :, 2] < 90))

        idle_soldier = am.get_sprite("cat_soldier", f"idle_{i}")
        arr_s = pygame.surfarray.pixels3d(idle_soldier)
        assert np.any((arr_s[:, :, 0] > 35) & (arr_s[:, :, 0] < 80) & (arr_s[:, :, 1] > 120) & (arr_s[:, :, 1] < 170) & (arr_s[:, :, 2] < 85))
        assert np.any((arr_s[:, :, 0] > 210) & (arr_s[:, :, 1] < 80) & (arr_s[:, :, 2] < 95))
