import os
import sys
import math
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame

pygame.display.init()
pygame.display.set_mode((1, 1))


@pytest.fixture(scope="module", autouse=True)
def generate_assets():
    """Generate cat miner spritesheet before any sprite tests run."""
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    from engine.asset_generator import AssetGenerator
    AssetGenerator.generate_cat_miner()


def test_spritesheet_file_created():
    """Cat miner spritesheet PNG must exist after generation."""
    from core.config import CAT_MINER_ID
    path = f"assets/spritesheets/cat_{CAT_MINER_ID}.png"
    assert os.path.exists(path), f"Missing: {path}"


def test_metadata_file_created():
    """Cat miner JSON metadata must exist after generation."""
    from core.config import CAT_MINER_ID
    path = f"assets/data/cat_{CAT_MINER_ID}.json"
    assert os.path.exists(path), f"Missing: {path}"


def test_metadata_contains_all_required_frame_keys():
    """JSON must contain every mandatory animation state key."""
    import json
    from core.config import CAT_MINER_ID
    with open(f"assets/data/cat_{CAT_MINER_ID}.json", encoding="utf-8") as f:
        meta = json.load(f)
    frames = meta["frames"]
    required = (
        [f"idle_{i}" for i in range(4)] +
        [f"walk_{i}" for i in range(8)] +
        [f"run_{i}" for i in range(6)] +
        [f"jump_{i}" for i in range(2)] +
        [f"fall_{i}" for i in range(2)] +
        ["land_0"] +
        [f"action_{i}" for i in range(4)] +
        [f"climb_{i}" for i in range(4)] +
        [f"hurt_{i}" for i in range(2)] +
        [f"talk_{i}" for i in range(4)] +
        [f"afk_{i}" for i in range(6)]
    )
    missing = [k for k in required if k not in frames]
    assert missing == [], f"Missing frame keys: {missing}"


def test_total_frame_count():
    """Spritesheet must contain exactly 37 frames."""
    import json
    from core.config import CAT_MINER_ID
    with open(f"assets/data/cat_{CAT_MINER_ID}.json", encoding="utf-8") as f:
        meta = json.load(f)
    assert len(meta["frames"]) == 43, f"Expected 43 frames, got {len(meta["frames"])}"


def test_frame_dimensions_match_config():
    """Every frame must declare width and height matching CAT_FRAME_W/H."""
    import json
    from core.config import CAT_MINER_ID, CAT_FRAME_W, CAT_FRAME_H
    with open(f"assets/data/cat_{CAT_MINER_ID}.json", encoding="utf-8") as f:
        meta = json.load(f)
    for key, rect in meta["frames"].items():
        assert rect["w"] == CAT_FRAME_W, f"Frame {key}: width {rect['w']} != {CAT_FRAME_W}"
        assert rect["h"] == CAT_FRAME_H, f"Frame {key}: height {rect['h']} != {CAT_FRAME_H}"


def test_spritesheet_image_dimensions():
    """Spritesheet image width must equal frame_width * number_of_frames."""
    import json
    from core.config import CAT_MINER_ID, CAT_FRAME_W, CAT_FRAME_H
    with open(f"assets/data/cat_{CAT_MINER_ID}.json", encoding="utf-8") as f:
        meta = json.load(f)
    img = pygame.image.load(f"assets/spritesheets/cat_{CAT_MINER_ID}.png")
    n = len(meta["frames"])
    assert img.get_width() == CAT_FRAME_W * n
    assert img.get_height() == CAT_FRAME_H


def test_collider_metadata_present():
    """JSON must include a collider entry with w=12, h=26."""
    import json
    from core.config import CAT_MINER_ID
    with open(f"assets/data/cat_{CAT_MINER_ID}.json", encoding="utf-8") as f:
        meta = json.load(f)
    assert "collider" in meta
    assert meta["collider"]["w"] == 12
    assert meta["collider"]["h"] == 26


def test_afk_frames_exist_and_are_distinct():
    """Each afk_0..5 frame must load without error and have nonzero size."""
    import json
    from core.config import CAT_MINER_ID, CAT_FRAME_W, CAT_FRAME_H
    img = pygame.image.load(f"assets/spritesheets/cat_{CAT_MINER_ID}.png")
    with open(f"assets/data/cat_{CAT_MINER_ID}.json", encoding="utf-8") as f:
        meta = json.load(f)
    afk_surfs = []
    for i in range(6):
        rect_data = meta["frames"][f"afk_{i}"]
        sub = img.subsurface((rect_data["x"], rect_data["y"], rect_data["w"], rect_data["h"]))
        assert sub.get_width() == CAT_FRAME_W
        afk_surfs.append(sub)
    assert len(afk_surfs) == 6
