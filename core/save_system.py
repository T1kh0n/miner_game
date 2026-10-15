from dataclasses import dataclass, field, asdict
import json
import os
import platform
import sys
from typing import Any

@dataclass
class Vector2DTO:
    x: float
    y: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Vector2DTO":
        return cls(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))

@dataclass
class InventoryItemDTO:
    id: str
    count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InventoryItemDTO":
        return cls(id=str(data.get("id", "")), count=int(data.get("count", 0)))

@dataclass
class PlayerStateDTO:
    position: Vector2DTO
    health: float
    stamina: float
    inventory: list[InventoryItemDTO]
    skin_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerStateDTO":
        pos_data = data.get("position", {"x": 0.0, "y": 0.0})
        pos = Vector2DTO.from_dict(pos_data) if isinstance(pos_data, dict) else Vector2DTO(0.0, 0.0)
        raw_inv = data.get("inventory", [])
        inv = [InventoryItemDTO.from_dict(item) for item in raw_inv] if isinstance(raw_inv, list) else []
        return cls(
            position=pos,
            health=float(data.get("health", 100.0)),
            stamina=float(data.get("stamina", 100.0)),
            inventory=inv,
            skin_id=str(data.get("skin_id", "classic"))
        )

@dataclass
class MinedTileDTO:
    x: int
    y: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MinedTileDTO":
        return cls(x=int(data.get("x", 0)), y=int(data.get("y", 0)))

@dataclass
class RockStateDTO:
    id: int
    position: Vector2DTO
    velocity: Vector2DTO
    angle: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RockStateDTO":
        pos_data = data.get("position", {"x": 0.0, "y": 0.0})
        vel_data = data.get("velocity", {"x": 0.0, "y": 0.0})
        pos = Vector2DTO.from_dict(pos_data) if isinstance(pos_data, dict) else Vector2DTO(0.0, 0.0)
        vel = Vector2DTO.from_dict(vel_data) if isinstance(vel_data, dict) else Vector2DTO(0.0, 0.0)
        return cls(
            id=int(data.get("id", 0)),
            position=pos,
            velocity=vel,
            angle=float(data.get("angle", 0.0))
        )

@dataclass
class WorldStateDTO:
    seed: int
    mined_tiles: list[MinedTileDTO] = field(default_factory=list)
    rocks: list[RockStateDTO] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldStateDTO":
        raw_mined = data.get("mined_tiles", [])
        mined = [MinedTileDTO.from_dict(t) for t in raw_mined] if isinstance(raw_mined, list) else []
        raw_rocks = data.get("rocks", [])
        rocks = [RockStateDTO.from_dict(r) for r in raw_rocks] if isinstance(raw_rocks, list) else []
        return cls(
            seed=int(data.get("seed", 0)),
            mined_tiles=mined,
            rocks=rocks
        )

@dataclass
class ProgressionDTO:
    checkpoint_id: str = ""
    elapsed_playtime: float = 0.0
    seen_hints: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgressionDTO":
        raw_hints = data.get("seen_hints", [])
        hints = [str(h) for h in raw_hints] if isinstance(raw_hints, list) else []
        return cls(
            checkpoint_id=str(data.get("checkpoint_id", "")),
            elapsed_playtime=float(data.get("elapsed_playtime", 0.0)),
            seen_hints=hints
        )

@dataclass
class SaveSlotDTO:
    version: int = 1
    player: PlayerStateDTO = field(default_factory=lambda: PlayerStateDTO(Vector2DTO(0.0, 0.0), 100.0, 100.0, [], "classic"))
    world: WorldStateDTO = field(default_factory=lambda: WorldStateDTO(0))
    progression: ProgressionDTO = field(default_factory=ProgressionDTO)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SaveSlotDTO":
        raw_player = data.get("player", {})
        player = PlayerStateDTO.from_dict(raw_player) if isinstance(raw_player, dict) else PlayerStateDTO(Vector2DTO(0.0, 0.0), 100.0, 100.0, [], "classic")
        raw_world = data.get("world", {})
        world = WorldStateDTO.from_dict(raw_world) if isinstance(raw_world, dict) else WorldStateDTO(0)
        raw_prog = data.get("progression", {})
        prog = ProgressionDTO.from_dict(raw_prog) if isinstance(raw_prog, dict) else ProgressionDTO()
        return cls(
            version=int(data.get("version", 1)),
            player=player,
            world=world,
            progression=prog
        )

@dataclass
class EngineSettingsDTO:
    master_volume: float = 1.0
    music_volume: float = 0.8
    sfx_volume: float = 0.8
    locale: str = "en"
    fullscreen: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EngineSettingsDTO":
        return cls(
            master_volume=float(data.get("master_volume", 1.0)),
            music_volume=float(data.get("music_volume", 0.8)),
            sfx_volume=float(data.get("sfx_volume", 0.8)),
            locale=str(data.get("locale", "en")),
            fullscreen=bool(data.get("fullscreen", False))
        )

def get_persistent_data_path() -> str:
    system = platform.system()
    candidates = []

    if system == "Windows":
        app_data = os.environ.get("APPDATA")
        if app_data:
            candidates.append(os.path.join(app_data, "MinerGame"))
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            candidates.append(os.path.join(user_profile, "AppData", "LocalLow", "MinerGame"))
    elif system == "Darwin":
        home = os.path.expanduser("~")
        candidates.append(os.path.join(home, "Library", "Application Support", "miner_game"))
    else:
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            candidates.append(os.path.join(config_home, "miner_game"))
        home = os.path.expanduser("~")
        candidates.append(os.path.join(home, ".config", "miner_game"))
        candidates.append(os.path.join(home, ".local", "share", "miner_game"))

    candidates.append(os.path.abspath("./saves"))

    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, ".probe")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("probe")
            os.remove(test_file)
            return path
        except (OSError, PermissionError):
            continue

    fallback = os.path.abspath("./saves")
    os.makedirs(fallback, exist_ok=True)
    return fallback

class SaveManager:
    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = base_path if base_path is not None else get_persistent_data_path()
        os.makedirs(self.base_path, exist_ok=True)

    def get_slot_path(self, slot_index: int) -> str:
        return os.path.join(self.base_path, f"save_slot_{slot_index}.json")

    def get_settings_path(self) -> str:
        return os.path.join(self.base_path, "settings.json")

    def slot_exists(self, slot_index: int) -> bool:
        return os.path.isfile(self.get_slot_path(slot_index))

    def save_slot(self, slot_index: int, slot_data: SaveSlotDTO) -> bool:
        path = self.get_slot_path(slot_index)
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(slot_data.to_dict(), f, indent=2, ensure_ascii=False)
            os.replace(temp_path, path)
            return True
        except (OSError, PermissionError):
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            return False

    def load_slot(self, slot_index: int) -> SaveSlotDTO | None:
        path = self.get_slot_path(slot_index)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            return SaveSlotDTO.from_dict(raw_data)
        except (json.JSONDecodeError, OSError):
            return None

    def delete_slot(self, slot_index: int) -> bool:
        path = self.get_slot_path(slot_index)
        if os.path.isfile(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False

    def save_settings(self, settings: EngineSettingsDTO) -> bool:
        path = self.get_settings_path()
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
            os.replace(temp_path, path)
            return True
        except (OSError, PermissionError):
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            return False

    def load_settings(self) -> EngineSettingsDTO:
        path = self.get_settings_path()
        if not os.path.isfile(path):
            return EngineSettingsDTO()
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            return EngineSettingsDTO.from_dict(raw_data)
        except (json.JSONDecodeError, OSError):
            return EngineSettingsDTO()
