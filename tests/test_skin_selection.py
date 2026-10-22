import os
import json
import pygame
import pymunk
import pytest

from engine.asset_manager import AssetManager
from engine.entities import Player
from states.state_machine import StateMachine
from states.skin_state import SkinState


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((320, 240))


def test_skin_spritesheets_and_meta():
    skins = ["classic", "ruby", "emerald", "obsidian"]
    for skin in skins:
        sheet_path = f"assets/spritesheets/player_{skin}.png"
        meta_path = f"assets/data/player_{skin}.json"
        assert os.path.exists(sheet_path)
        assert os.path.exists(meta_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["frame_width"] == 36
        assert data["frame_height"] == 36
        assert len(data["frames"]) == 43
        surf = pygame.image.load(sheet_path)
        assert surf.get_width() == 36 * 43
        assert surf.get_height() == 36


def test_skin_state_selection_and_play_state_integration():
    sm = StateMachine()
    skin_state = SkinState(sm)
    skin_state.enter()
    assert sm.selected_skin == "classic"

    skin_state._next()
    assert sm.selected_skin == "ruby"

    space = pymunk.Space()
    asset_mgr = AssetManager.get()
    player = Player(100.0, 100.0, sm.selected_skin, space, asset_mgr)
    assert player.skin_id == "ruby"

    test_surf = pygame.Surface((320, 240), pygame.SRCALPHA)
    player.render(test_surf, 0.0, 0.0, asset_mgr)

    player.is_digging = True
    player.dig_time = 0.1
    player.render(test_surf, 0.0, 0.0, asset_mgr)

    player.is_digging = False
    player.is_climbing = True
    player.climb_time = 0.2
    player.render(test_surf, 0.0, 0.0, asset_mgr)

    skin_state._next()
    assert sm.selected_skin == "emerald"
    player_emerald = Player(100.0, 100.0, sm.selected_skin, space, asset_mgr)
    assert player_emerald.skin_id == "emerald"
    player_emerald.render(test_surf, 0.0, 0.0, asset_mgr)

    skin_state._next()
    assert sm.selected_skin == "obsidian"
    player_obsidian = Player(100.0, 100.0, sm.selected_skin, space, asset_mgr)
    assert player_obsidian.skin_id == "obsidian"
    player_obsidian.render(test_surf, 0.0, 0.0, asset_mgr)
