import os
import tempfile
import pygame
from core.localization import LocalizationManager
from core.save_system import SaveManager, SaveSlotDTO, PlayerStateDTO, WorldStateDTO, ProgressionDTO, Vector2DTO
from states.play_state import TutorialSystem

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()
pygame.font.init()

def test_tutorial_system_seen_hints_isolation():
    loc = LocalizationManager()
    font = pygame.font.Font(None, 16)
    
    fired_log = []
    def on_fired(key: str) -> None:
        fired_log.append(key)
        
    initial_seen = {"start", "first_wall"}
    tut = TutorialSystem(font, loc, on_hint_fired=on_fired, initial_seen=initial_seen)
    
    assert tut.fire("start") is False
    assert tut.fire("first_wall") is False
    assert len(fired_log) == 0
    assert len(tut.hints) == 0
    
    assert tut.fire("climb_stamina") is True
    assert "climb_stamina" in tut.seen_hints
    assert "climb_stamina" in fired_log
    assert len(tut.hints) == 1
    assert tut.fire("climb_stamina") is False

def test_tutorial_system_reset_hints():
    loc = LocalizationManager()
    font = pygame.font.Font(None, 16)
    
    tut = TutorialSystem(font, loc, initial_seen={"start", "mine_dirt"})
    assert "start" in tut.seen_hints
    
    tut.reset_hints()
    assert len(tut.seen_hints) == 0
    assert len(tut.hints) == 1
    assert tut.hints[0]["key"] == "reset_toast"
    
    assert tut.fire("start") is True
    assert "start" in tut.seen_hints

def test_tutorial_slot_dto_persistence():
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_mgr = SaveManager(base_path=tmp_dir)
        slot = SaveSlotDTO(
            player=PlayerStateDTO(
                position=Vector2DTO(50.0, 50.0),
                health=100.0,
                stamina=100.0,
                inventory=[],
                skin_id="miner_default"
            ),
            world=WorldStateDTO(
                seed=12345,
                mined_tiles=[],
                rocks=[]
            ),
            progression=ProgressionDTO(
                checkpoint_id="cabin_0",
                elapsed_playtime=12.5,
                seen_hints=["start", "first_wall"]
            )
        )
        save_mgr.save_slot(0, slot)
        
        loaded = save_mgr.load_slot(0)
        assert loaded is not None
        assert "start" in loaded.progression.seen_hints
        assert "first_wall" in loaded.progression.seen_hints
        
        loaded.progression.seen_hints.append("climb_stamina")
        save_mgr.save_slot(0, loaded)
        
        reloaded = save_mgr.load_slot(0)
        assert reloaded is not None
        assert set(reloaded.progression.seen_hints) == {"start", "first_wall", "climb_stamina"}
