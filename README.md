# 2D Miner Game (Pygame-CE / Pygame + Pymunk)

A 2D procedural mining platformer engineered with a clean, decoupled architecture ready for porting to Unity (C#).

---

## 1. Project Architecture & Directory Structure

```text
.
├── main.py                     # Entry point, adaptive window sizing, main loop.
├── generate_models.py          # Wavefront OBJ generation in assets/models/.
├── pyproject.toml              # Dependencies and pytest configuration.
├── core/                       # Core engine subsystems
│   ├── config.py               # Constants, palettes, physics timesteps, jump metrics.
│   ├── camera.py               # Sub-pixel damped camera with screen shake.
│   ├── leaderboard.py          # High-score persistence.
│   ├── localization.py         # Singleton LocalizationManager with dynamic language switching.
│   └── save_system.py          # Unity-compatible DTO schemas & cross-platform SaveManager.
├── engine/                     # Game engine systems and mechanics
│   ├── asset_generator.py      # Procedural texture generator for spritesheets and icons.
│   ├── asset_manager.py        # Sprite loading, texture slicing, and mask caching.
│   ├── entities.py             # Player (invariant torso collider), RockEntity, CabinEntity, ParticlePool.
│   ├── level.py                # Procedural cave generator with BFS solver guaranteed passability.
│   └── ui.py                   # Responsive UI framework with relative bounds and auto-font scaling.
├── states/                     # Finite State Machine states
│   ├── state_machine.py        # State base class and state stack manager.
│   ├── menu_state.py           # Main menu with dynamic language switching.
│   ├── play_state.py           # Core gameplay, fixed physics loop, checkpoints, and tutorial dispatcher.
│   ├── skin_state.py           # Character skin selection screen.
│   └── leaderboard_state.py    # High-score rankings view.
├── assets/                     # Game assets
│   ├── localization/           # Key-value translation dictionaries (en.json, ru.json).
│   ├── spritesheets/           # Procedurally generated texture atlas sheets.
│   ├── data/                   # Metadata mapping spritesheet frame slices.
│   ├── models/                 # Generated 3D OBJ models.
│   └── saves/                  # Fallback local directory for saves and leaderboards.
└── tests/                      # Automated headless unit and integration test suite
    ├── test_issue1_motion_smoothing.py
    ├── test_issue2_pickaxe_isolation.py
    ├── test_issue3_performance_culling.py
    ├── test_issue4_save_system.py
    ├── test_issue5_cabin_checkpoint.py
    ├── test_issue6_map_passability.py
    ├── test_issue7_localization.py
    └── test_issue8_hints_dispatcher.py
```

---

## 2. Physics & Motion Smoothing (Decoupled Loop)

- **Fixed Timestep Accumulator**: Physics steps run at a deterministic `FIXED_DT = 1/60` (`space.step(FIXED_DT)`) with a capped residual accumulator (`MAX_ACCUMULATOR = 0.2`) to eliminate physics slowdowns and tunneling.
- **Render Interpolation**: Physics positions of the player and dynamic rocks are recorded at each tick (`save_previous_state()`). The display rendering calculates `alpha = accumulator / FIXED_DT` and performs linear interpolation (`lerp`) between ticks for jitter-free unlocked display framerates.
- **Camera Damping**: `Camera` tracks target position with exponential decay smoothing (`1.0 - math.exp(-cam_speed * dt)`), sub-pixel float coordinates, and integrated screen shake.
- **Delta-Time Normalized Animations**: Sprite animation frames advance according to elapsed delta time (`anim_time += dt`), decoupled from display or physics framerates.

---

## 3. Player Collider & Collision Isolation

- **Torso/Legs Invariant Collider**: The player's physical Pymunk shape is locked to a constant bounding box (`PLAYER_BODY_W = 12.0`, `PLAYER_BODY_H = 18.0`) that never mutates or resets during swings or state changes.
- **Pickaxe Isolation**: The pickaxe is completely excluded from solid physical collisions, preventing walls or blocks from repelling the player.
- **Climbing Hook Raycast Query**: Climbing anchor attachment is computed via `space.segment_query()` filtering out self-hits, detecting walls within reach (`CLIMB_REACH_DIST = 16.0`) only while holding Shift.
- **Digging Spatial Trigger**: Digging uses a momentary rectangular query (`get_dig_sensor_bounds`) only during active swing frames, fully decoupled from physical collision bodies.

---

## 4. Performance Optimizations & Frustum Culling

- **Frustum Culling**: Off-screen static tiles, dynamic rocks, coins, and particles outside the active camera viewport (`cam_x, cam_y` + 1 tile margin) are discarded before rendering.
- **Low-LOD Lighting**: Tiles beyond the player's illumination radius under deep shadow skip multi-pass pixel blending and draw as single solid fills.
- **Zero-Allocation Hot Loop**: Particle systems utilize an allocation-free `ParticlePool` (180 pre-allocated instances) and surface alpha caches (`_PARTICLE_SURF_CACHE`), keeping game memory footprint well under 25 MB (target < 150 MB).

---

## 5. Save/Load Architecture & Unity Portability

Data models are structured as strongly-typed Data Transfer Objects (DTOs) conforming to Unity `JsonUtility` requirements:
- Primitives, arrays, and standard 2D vector structs (`Vector2DTO`: `{"x": 12.0, "y": 45.0}`).
- **Save Schemas**:
  - `SaveSlotDTO` (`save_slot_*.json`):
    - `player`: `position`, `health`, `stamina`, `inventory`, `skin_id`.
    - `world`: `seed`, `mined_tiles`, `rocks`.
    - `progression`: `checkpoint_id`, `elapsed_playtime`, `seen_hints`.
  - `EngineSettingsDTO` (`settings.json`):
    - `master_volume`, `music_volume`, `sfx_volume`, `locale`, `fullscreen`.
- **Cross-Platform Storage**:
  - Windows: `%APPDATA%/MinerGame/` or `%USERPROFILE%/AppData/LocalLow/MinerGame/`
  - Linux: `~/.config/miner_game/` or `~/.local/share/miner_game/`
  - macOS: `~/Library/Application Support/miner_game/`
  - Graceful fallback: `./saves/` if system directories are inaccessible.
- **Atomic Writes**: Writes first to temporary `.tmp` files before renaming to avoid corruption.

---

## 6. Cabin Checkpoint & Respawn System

- **Cabin Entities**: Wooden shelter cabins are placed at key depth intervals (`y ≈ 25, 55, 85`).
- **Interaction & Snapshot**: Pressing `E` or `Up` near an unlocked cabin triggers cabin entry particles, records an atomic save snapshot, and updates the active checkpoint ID.
- **Demise & Snapshot Rollback**: On player death, `respawn_at_checkpoint()` restores player health, stamina, position, and mined world blocks back to the snapshot of the last visited cabin.

---

## 7. Guaranteed Procedural Map Passability

- **Jump & Climb Metrics**:
  - Maximum vertical jump: 2 tiles (`MAX_JUMP_TILES_VERTICAL = 2`).
  - Maximum continuous climb: 12 tiles (`MAX_CLIMB_TILES_CONTINUOUS = 12`).
- **Protected Central Spine**: Indestructible `STONE` blocks are prohibited from spawning within the primary vertical corridor (`GRID_W // 2 ± 3`).
- **Automated BFS Passability Solver**: A flood-fill pathfinding algorithm evaluates reachability through air (`EMPTY`) and diggable (`DIRT`) tiles from spawn (`y=3`) to the cave bottom. If unreachable, it carves an evasive bypass corridor to guarantee map navigation.

---

## 8. Dual Localization (RU & EN)

- **Key-Value Translation Dictionaries**: `assets/localization/en.json` and `assets/localization/ru.json`.
- **LocalizationManager**: Singleton with observer callback pattern (`subscribe`), fallback lookups (`get_text`), and UTF-8 Cyrillic font rendering.
- **Dynamic Language Switching**: Toggle between English and Russian on the fly in the Main Menu and Pause Menu without restarting the engine.

---

## 9. One-Time Tutorial Hint Dispatcher

- **Contextual Dispatcher**: Tutorial hints trigger based on player actions (`hint_start`, `hint_first_wall`, `hint_climb_stamina`, `hint_mine_dirt`, `hint_checkpoint`, `hint_coin`).
- **Progression-Linked Persistence**: Seen hints are stored in `SaveSlotDTO.progression.seen_hints` and are never shown more than once per slot save.
- **Hint Reset**: Pause menu provides a "RESET HINTS" button that clears seen history, shows a temporary notification toast, and immediately updates the save file.

---

## 10. Automated Headless Testing

All systems are covered by automated unit and integration tests executing headlessly without audio or video displays:

```bash
# Run full headless test suite
uv run pytest

# Or with standard pytest
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest tests/
```

### Test Suite Coverage:
- `test_issue1_motion_smoothing.py`: Fixed timestep accumulation, position LERP, sub-pixel camera damping, delta-time animation progression.
- `test_issue2_pickaxe_isolation.py`: Torso collider invariance during swings, raycast climbing anchor isolation, momentary digging sensor bounds.
- `test_issue3_performance_culling.py`: Viewport frustum culling, particle pooling without dynamic allocations, low-LOD shadow optimization.
- `test_issue4_save_system.py`: Unity-compatible DTO serialization, cross-platform persistent directory resolution, atomic save/load/delete.
- `test_issue5_cabin_checkpoint.py`: Cabin placement, interaction radius, snapshot persistence, and respawn rollback.
- `test_issue6_map_passability.py`: Reachability solver, bypass corridor carving, and multi-seed traversal validation.
- `test_issue7_localization.py`: Key lookups, fallback behavior, Cyrillic font metrics, and dynamic subscriber switching.
- `test_issue8_hints_dispatcher.py`: One-time hint dispatching, seen hint isolation across saves, and UI reset functionality.
