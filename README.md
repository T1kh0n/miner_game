# 2D Miner Game (Pygame-CE / Pygame + Pymunk)

A 2D procedural mining platformer engineered with a clean, decoupled architecture ready for porting to Unity (C#).

---

## CHARACTER ART & ANIMATION PIPELINE (REAL CAT PHOTO TO PIXEL SPRITESHEET)

### 1. Visual Style & Proportions
- Canvas & Grid: Native character frame size is `32x36` pixels (or `36x36` for wide weapons/tails).
- Proportions: Bipedal Anthropomorphic Cat (1:2.5 head-to-body ratio). Stocky, grounded silhouette with expressive ears, whiskers, and animated tail counterweight.
- Outlines & Shading: 1px dark warm-charcoal outer outline `(22, 18, 24)`. Internal details (fur stripes, vest pockets, armor plates) use soft 3-tone ramp shading (Base, Shadow `-25%` luminance, Highlight `+20%` luminance) with selective outlining.

### 2. Translating a Real Cat Photo / Reference into Pixel Art
When given a photo of a real cat or a concept image:
1. Coat & Fur Extraction: Sample 3 primary fur colors from the photo (Primary Coat, Secondary Belly/Paws, Dark Markings/Tabby Stripes). Map facial markings (M-shaped forehead tabby lines, muzzle patches, ear tips).
2. Eye & Expression Mapping: Extract exact iris colors (including heterochromia, e.g., left red/amber, right blue). Express personality via eyelid height (half-closed tired eyes for the Miner; wide-open cheerful eyes for the Train Driver; stern furrowed brows for the Soldier; manic dilated pupils for the Feral Cat).
3. Silhouette & Gear Layering: Render the sprite in 4 modular procedural layers inside `AssetGenerator`:
   - Layer 0 (Back): Animated curved tail (`sin` wave phase offset) + backpack/cloak.
   - Layer 1 (Body & Limbs): Bipedal torso, fur coat, trousers/boots, and faction armor (e.g., khaki utility vest, railway coat, hollowed watermelon rind cuirass, or tattered rope harness).
   - Layer 2 (Head & headgear): Feline skull, ears (which flatten during attacks/falls), muzzle, whiskers, and headgear (miner hard-hat with headlamp, fur ushanka, watermelon helmet).
   - Layer 3 (Foreground Arms & Tool): Paws holding the character's signature tool (pickaxe, oil lantern, combat shovel, or bared claws).

### 3. Mandatory Animation States & Frame Matrix
Every playable/interactive cat character spritesheet (`assets/spritesheets/cat_{id}.png` + `assets/data/cat_{id}.json`) MUST implement the following standardized frame keys:
- `idle_0..3` (4 frames): Breathing cycle (1px chest/head bob, subtle tail sway, ear twitch on frame 3).
- `walk_0..7` (8 frames): Bipedal stride cycle with opposite arm/paw swing, 1px vertical bounce, and trailing tail sine wave.
- `run_0..5` (6 frames): Forward-leaning torso (`+2px` lean), rapid paw cycle, horizontal tail stabilizer.
- `jump_0..1` (2 frames): Upward stretch (`scale_y=1.12`), ears perked up, paws raised.
- `fall_0..1` (2 frames): Air-resistance pose, ears flattened back, tail swirling for balance.
- `land_0` (1 frame): Squash impact (`scale_x=1.18, scale_y=0.82`) with dust particle trigger.
- `action_0..3` (4 frames): Primary tool/weapon swing (Pickaxe dig for Miner, Lantern raise for Driver, Shovel strike/block for Soldier, Lunging claw swipe for Feral Cat).
- `climb_0..3` (4 frames): Wall/rope climbing cycle with alternating paw/pickaxe hooks.
- `hurt_0..1` (2 frames): Knockback flinch, white flash mask, squinted eyes (`><`).
- `talk_0..3` (4 frames): Dialogue gesture cycle (mouth open/close or expressive paw/ear movement + emote bubble anchor).
- `afk_0..5` (6 frames): 4th-wall break sequence (turns face-front toward camera, taps screen glass with paw/pickaxe, points headlamp directly into the player's monitor).

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
