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

def test_player_controller_selects_all_mandatory_animation_frames():
    import pymunk
    from engine.entities import Player
    space = pymunk.Space()
    player = Player(100.0, 100.0, "miner", space)

    player.on_ground = False
    player.body.velocity = (0.0, -200.0)
    assert player._get_current_frame_key() == "jump_0"
    player.body.velocity = (0.0, -50.0)
    assert player._get_current_frame_key() == "jump_1"
    player.body.velocity = (0.0, 50.0)
    assert player._get_current_frame_key() == "fall_0"
    player.body.velocity = (0.0, 200.0)
    assert player._get_current_frame_key() == "fall_1"

    player.hurt_timer = 0.35
    assert player._get_current_frame_key() == "hurt_0"
    player.hurt_timer = 0.1
    assert player._get_current_frame_key() == "hurt_1"
    player.hurt_timer = 0.0

    player.in_dialogue = True
    player.anim_time = 0.0
    assert player._get_current_frame_key() == "talk_0"
    player.anim_time = 0.25
    assert player._get_current_frame_key() == "talk_1"
    player.anim_time = 0.45
    assert player._get_current_frame_key() == "talk_2"
    player.anim_time = 0.65
    assert player._get_current_frame_key() == "talk_3"
    player.in_dialogue = False

    player.on_ground = True
    player.afk_phase = 2
    player.afk_timer = player._afk_knock_seconds + 0.0
    assert player._get_current_frame_key() == "afk_0"
    player.afk_timer = player._afk_knock_seconds + 0.4
    assert player._get_current_frame_key() == "afk_1"
    player.afk_timer = player._afk_knock_seconds + 0.8
    assert player._get_current_frame_key() == "afk_2"
    player.afk_timer = player._afk_knock_seconds + 1.2
    assert player._get_current_frame_key() == "afk_3"
    player.afk_phase = 4
    player.afk_timer = player._afk_blind_seconds + 0.0
    assert player._get_current_frame_key() == "afk_4"
    player.afk_timer = player._afk_blind_seconds + 0.5
    assert player._get_current_frame_key() == "afk_5"

def test_jump_fall_land_distinct_feline_poses():
    import json
    import numpy as np
    from PIL import Image

    with open("assets/data/cat_miner.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    sheet = Image.open("assets/spritesheets/cat_miner.png")

    def get_crop(key: str) -> np.ndarray:
        m = meta["frames"][key]
        return np.array(sheet.crop((m["x"], m["y"], m["x"] + m["w"], m["y"] + m["h"])))

    jump_0 = get_crop("jump_0")
    jump_1 = get_crop("jump_1")
    fall_0 = get_crop("fall_0")
    fall_1 = get_crop("fall_1")
    land_0 = get_crop("land_0")
    idle_0 = get_crop("idle_0")

    assert not np.array_equal(jump_0, idle_0)
    assert not np.array_equal(jump_1, idle_0)
    assert not np.array_equal(fall_0, idle_0)
    assert not np.array_equal(fall_1, idle_0)
    assert not np.array_equal(land_0, idle_0)

    assert not np.array_equal(jump_0, jump_1)
    assert not np.array_equal(fall_0, fall_1)
    assert not np.array_equal(jump_0, land_0)

