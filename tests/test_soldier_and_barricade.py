import os
import sys
import pytest
import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.asset_generator import AssetGenerator
from engine.asset_manager import AssetManager
from engine.entities import SoldierCatEntity
from states.state_machine import StateMachine
from states.play_state import PlayState
from core.leaderboard import LeaderboardManager


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """Initialise pygame and ensure assets are generated."""
    pygame.init()
    pygame.display.set_mode((320, 240))
    AssetGenerator.generate_all()
    yield


def test_cat_soldier_spritesheet_and_metadata():
    """Assert cat_soldier spritesheet exists and contains all required animations."""
    am = AssetManager.get()
    required_states = ["idle", "walk", "action_shovel", "hurt", "talk", "pinned"]
    for st in required_states:
        for idx in range(4):
            key = f"{st}_{idx}"
            surf = am.get_sprite("cat_soldier", key)
            assert surf.get_width() == 36
            assert surf.get_height() == 36
            assert surf.get_flags() & pygame.SRCALPHA


def test_soldier_cat_fsm_states():
    """Assert SoldierCatEntity transitions correctly across all required FSM states."""
    soldier = SoldierCatEntity(100.0, 500.0, 80.0, 120.0)
    assert soldier.state == SoldierCatEntity.STATE_GUARD_POST
    assert soldier.anim_state == "idle"

    soldier.set_state(SoldierCatEntity.STATE_PATROL)
    assert soldier.state == SoldierCatEntity.STATE_PATROL
    assert soldier.anim_state == "walk"

    init_x = soldier.x
    soldier.facing_right = True
    soldier.update(0.5)
    assert soldier.x > init_x

    soldier.set_state(SoldierCatEntity.STATE_DIALOGUE)
    assert soldier.state == SoldierCatEntity.STATE_DIALOGUE
    assert soldier.anim_state == "talk"

    soldier.set_state(SoldierCatEntity.STATE_COMBAT_DEFEND)
    assert soldier.state == SoldierCatEntity.STATE_COMBAT_DEFEND
    assert soldier.anim_state == "action_shovel"

    soldier.set_state(SoldierCatEntity.STATE_PINNED_DOWN)
    assert soldier.state == SoldierCatEntity.STATE_PINNED_DOWN
    assert soldier.anim_state == "pinned"


def test_soldier_encounter_cutscene_triggers_on_approach():
    """Assert approaching the soldier barricade initiates dialogue warning of feral cats."""
    sm = StateMachine()
    sm.leaderboard = LeaderboardManager()
    sm.selected_skin = "miner"

    ps = PlayState(sm)
    ps.enter()

    assert ps.soldier_cat is not None
    assert not ps.soldier_cutscene_triggered

    ps.player.body.position = (ps.soldier_cat.x, ps.soldier_cat.y)
    ps.update(1.0 / 60.0)

    assert ps.soldier_cutscene_triggered
    assert ps.cutscene_mgr.is_active

    for _ in range(40):
        ps.cutscene_mgr.update(0.05)
        ps.dialogue_box.update(0.05)
        if ps.dialogue_box.is_open:
            break

    assert ps.dialogue_box.is_open
    assert "feral" in ps.dialogue_box.full_text.lower() or "wild" in ps.dialogue_box.full_text.lower()
