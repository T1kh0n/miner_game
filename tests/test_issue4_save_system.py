import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import tempfile
from core.save_system import (
    Vector2DTO, InventoryItemDTO, PlayerStateDTO,
    MinedTileDTO, RockStateDTO, WorldStateDTO,
    ProgressionDTO, SaveSlotDTO, EngineSettingsDTO,
    SaveManager, get_persistent_data_path
)

def test_vector2_and_slot_serialization() -> None:
    slot = SaveSlotDTO(
        version=1,
        player=PlayerStateDTO(
            position=Vector2DTO(12.5, 45.0),
            health=85.0,
            stamina=90.0,
            inventory=[InventoryItemDTO("gem_ruby", 3)],
            skin_id="emerald"
        ),
        world=WorldStateDTO(
            seed=4242,
            mined_tiles=[MinedTileDTO(5, 10)],
            rocks=[RockStateDTO(1, Vector2DTO(100.0, 150.0), Vector2DTO(0.0, 50.0), 0.5)]
        ),
        progression=ProgressionDTO(
            checkpoint_id="cabin_depth_20",
            elapsed_playtime=125.4,
            seen_hints=["hint_start", "hint_dig"]
        )
    )

    data = slot.to_dict()
    assert data["player"]["position"]["x"] == 12.5
    assert data["player"]["position"]["y"] == 45.0
    assert data["player"]["skin_id"] == "emerald"
    assert data["world"]["seed"] == 4242
    assert len(data["world"]["mined_tiles"]) == 1
    assert data["progression"]["checkpoint_id"] == "cabin_depth_20"

    deserialized = SaveSlotDTO.from_dict(data)
    assert deserialized.player.position.x == 12.5
    assert deserialized.player.position.y == 45.0
    assert deserialized.player.health == 85.0
    assert deserialized.progression.seen_hints == ["hint_start", "hint_dig"]

def test_save_manager_file_operations() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = SaveManager(base_path=tmp_dir)
        assert not manager.slot_exists(1)

        slot = SaveSlotDTO(
            version=1,
            player=PlayerStateDTO(Vector2DTO(10.0, 20.0), 100.0, 100.0, [], "classic"),
            world=WorldStateDTO(1001),
            progression=ProgressionDTO()
        )

        success = manager.save_slot(1, slot)
        assert success is True
        assert manager.slot_exists(1) is True

        loaded = manager.load_slot(1)
        assert loaded is not None
        assert loaded.world.seed == 1001

        assert manager.delete_slot(1) is True
        assert manager.slot_exists(1) is False

def test_settings_persistence() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = SaveManager(base_path=tmp_dir)
        settings = EngineSettingsDTO(
            master_volume=0.9,
            music_volume=0.5,
            sfx_volume=0.7,
            locale="ru",
            fullscreen=True
        )

        assert manager.save_settings(settings) is True
        loaded = manager.load_settings()
        assert loaded.locale == "ru"
        assert loaded.fullscreen is True
        assert abs(loaded.master_volume - 0.9) < 1e-4

def test_persistent_data_path_writable() -> None:
    path = get_persistent_data_path()
    assert os.path.isdir(path)
    test_file = os.path.join(path, ".test_write")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("ok")
    assert os.path.exists(test_file)
    os.remove(test_file)
