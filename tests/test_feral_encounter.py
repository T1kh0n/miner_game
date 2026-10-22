import os
import sys
import pytest
import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.asset_generator import AssetGenerator
from engine.asset_manager import AssetManager
from engine.entities import FeralCatEntity, SoldierCatEntity
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


def test_cat_feral_spritesheet_and_metadata():
    """Assert cat_feral spritesheet exists and contains all required animations."""
    am = AssetManager.get()
    required_states = ["idle", "run", "pounce", "action_slash", "talk", "hurt"]
    for st in required_states:
        for idx in range(4):
            key = f"{st}_{idx}"
            surf = am.get_sprite("cat_feral", key)
            assert surf.get_width() == 36
            assert surf.get_height() == 36
            assert surf.get_flags() & pygame.SRCALPHA


def test_feral_cat_entity_fsm_and_flashlight_stun():
    """Assert FeralCatEntity is stunned by flashlight glare and takes damage."""
    feral = FeralCatEntity(200.0, 300.0)
    assert feral.state == FeralCatEntity.STATE_STALK
    assert feral.hp == 3

    for _ in range(15):
        feral.update(0.02, 100.0, 300.0, is_illuminated=True)

    assert feral.state == FeralCatEntity.STATE_STUNNED
    assert feral.stun_timer > 0.0

    feral.update(1.6, 100.0, 300.0, is_illuminated=False)
    assert feral.state == FeralCatEntity.STATE_STALK

    defeated = feral.take_damage(1, 1.0)
    assert not defeated
    assert feral.hp == 2
    assert feral.state == FeralCatEntity.STATE_HURT

    feral.invulnerable_timer = 0.0
    defeated = feral.take_damage(2, -1.0)
    assert defeated
    assert feral.hp == 0
    assert feral.is_defeated
    assert feral.state == FeralCatEntity.STATE_DEFEATED


def test_feral_ambush_cutscene_and_defeat_victory():
    """Assert encounter cutscene triggers, pins soldier, drops gem, and unlocks blast door on defeat."""
    sm = StateMachine()
    sm.leaderboard = LeaderboardManager()
    sm.selected_skin = "miner"

    ps = PlayState(sm)
    ps.enter()

    assert ps.feral_cat is not None
    assert not ps.feral_cutscene_triggered
    assert not ps.blast_door_opened

    ps.player.body.position = (ps.feral_cat.x - 30.0, ps.feral_cat.y)
    ps.update(1.0 / 60.0)

    assert ps.feral_cutscene_triggered
    assert ps.cutscene_mgr.is_active

    for _ in range(60):
        ps.cutscene_mgr.update(0.05)
        if not ps.cutscene_mgr.is_active:
            break

    initial_score = ps.score
    ps._on_feral_defeated()

    assert ps.feral_defeated
    assert ps.blast_door_opened
    assert ps.victory_gem_pos is not None

    for _ in range(40):
        if ps.dialogue_box.is_open:
            ps.dialogue_box.close()
        ps.cutscene_mgr.update(0.1)
        if not ps.cutscene_mgr.is_active:
            break

    gem_x, gem_y = ps.victory_gem_pos
    ps.player.body.position = (gem_x, gem_y)
    ps.update(1.0 / 60.0)

    assert ps.victory_gem_collected
    assert ps.score >= initial_score + 100


def test_feral_combat_damage_and_defeat_runtime():
    sm = StateMachine()
    sm.leaderboard = LeaderboardManager()
    sm.selected_skin = "miner"
    ps = PlayState(sm)
    ps.enter()
    ps.player.body.position = (ps.feral_cat.x - 20.0, ps.feral_cat.y)
    ps.feral_cutscene_triggered = True
    ps.cutscene_mgr.is_active = False
    ps.player.is_digging = True
    ps.feral_cat.invulnerable_timer = 0.0
    ps.update(0.016)
    assert ps.feral_cat.hp < 3


def test_blast_door_entity_and_interaction():
    import pymunk
    from engine.entities import BlastDoorEntity
    space = pymunk.Space()
    door = BlastDoorEntity(500.0, 560.0, space)
    assert not door.is_open
    assert door.shape in space.shapes

    test_surf = pygame.Surface((320, 240))
    door.render(test_surf, 400.0, 500.0)

    door.open()
    assert door.is_open
    assert door.shape not in space.shapes

    door.update(0.5)
    assert door.open_progress > 0.0
    door.render(test_surf, 400.0, 500.0)

    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()
    assert ps.blast_door is not None
    assert not ps.blast_door.is_open
    assert not ps.blast_door_opened

    ps._on_feral_defeated()
    assert ps.blast_door.is_open
    assert ps.blast_door_opened
