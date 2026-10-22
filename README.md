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
│   ├── audio.py                # Procedural NumPy audio synthesizer and sound manager.
│   ├── camera.py               # Sub-pixel damped camera with screen shake.
│   ├── config.py               # Constants, palettes, physics timesteps, jump metrics.
│   ├── cutscene.py             # CutsceneManager and timeline actions (MoveCameraTo, ShowDialogue, etc.).
│   ├── events.py               # Decoupled publisher-subscriber EventBus / EventManager.
│   ├── leaderboard.py          # High-score persistence.
│   ├── localization.py         # Singleton LocalizationManager with dynamic language switching.
│   └── save_system.py          # Unity-compatible DTO schemas & cross-platform SaveManager.
├── engine/                     # Game engine systems and mechanics
│   ├── asset_generator.py      # Procedural texture generator for spritesheets and icons.
│   ├── asset_manager.py        # Sprite loading, texture slicing, and mask caching.
│   ├── banana_pipeline.py      # Master image slicing, Chroma Key, and texture packing pipeline.
│   ├── dialogue.py             # DialogueBox with typewriter stream and EmoteBubble manager.
│   ├── entities.py             # Player, DriverCatEntity, SoldierCatEntity, FeralCatEntity, RockEntity.
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
    ├── test_afk_flashlight.py
    ├── test_audio_synthesis.py
    ├── test_cat_miner_sprites.py
    ├── test_character_remaster.py
    ├── test_cutscene_dialogue.py
    ├── test_driver_and_shale.py
    ├── test_events.py
    ├── test_feral_encounter.py
    ├── test_gameplay_improvements.py
    ├── test_issue1_motion_smoothing.py
    ├── test_issue2_pickaxe_isolation.py
    ├── test_issue3_performance_culling.py
    ├── test_issue4_save_system.py
    ├── test_issue5_cabin_checkpoint.py
    ├── test_issue6_map_passability.py
    ├── test_issue7_localization.py
    ├── test_issue8_hints_dispatcher.py
    ├── test_rope_physics.py
    ├── test_soldier_and_barricade.py
    └── test_visual_pipeline.py
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
- `test_rope_physics.py`: Grappling hook projectile physics, SlideJoint constraint attachment, ballistic aim arc, and rope climb/slide.
- `test_soldier_and_barricade.py`: Watermelon soldier patrol states, defense posture, dialogue triggers, and barricade post logic.
- `test_visual_pipeline.py`: Banana pipeline chroma keying, sprite normalization, texture atlas generation, and frame alignment.

---

## 11. NPC Encounters, Cutscenes & Dialogue Engine

- **CutsceneManager**: Data-driven sequencer executing timeline actions (`MoveCameraTo`, `MoveEntityTo`, `PlayAnimation`, `ShowEmote`, `ShowDialogue`, `Wait`, `TriggerEvent`). Supports graceful skipping via `Space` / `Esc`.
- **DialogueBox & Typewriter FX**: Localized dialogue presentation featuring animated text typewriter, procedural "meow-talk" voice chirps, speaker nameplate, and animated `EmoteBubble` indicators (`!`, `?`, `...`, `heart`, `rope`, `pickaxe`).
- **Train Driver Cat (Stage 2)**: Stops incoming subway train car at the Metro platform upon arrival, rewards the player with additional grappling rope coils (+3 ropes), and acts as a safe narrative anchor.
- **Watermelon Armor Soldier Cat (Stage 3)**: Guarding the fortified barricade clearing, equipped with watermelon rind helmet and cuirass, wielding a steel trench shovel with defensive bash and patrol states.
- **Feral Cat Ambush & Combat (Stage 4)**: Hostile white cat with heterochromia (red left eye, blue right eye) ambushing the soldier. Can be stunned with the directional headlamp beam or defeated with teamwork, dropping a victory gem (+100 score) and unlocking deep tunnel blast doors.

---

## QUALITY ASSURANCE FINDINGS

A systematic Tree of Thoughts quality assurance inspection was conducted across the codebase, runtime systems, spritesheets, UI/UX, and audio pipelines against the specifications defined in this document. Below is the categorized inventory of all identified defects and specification mismatches.

### 1. Visual Inconsistencies (Gameplay vs. Spec Mismatch)

#### Issue 1.1: Equipment Skin Selection Bypassed at Runtime
- **Expected**: Selecting an equipment skin (`classic`, `ruby`, `emerald`, `obsidian`) in `SkinState` applies the chosen feline spritesheet to the player during active gameplay.
- **Observed**: In `PlayState.enter()` (`states/play_state.py`, lines 343–345), `skin` is unconditionally hardcoded via `if skin not in ("miner",): skin = CAT_MINER_ID`. Any skin selected in `SkinState` is ignored. Furthermore, `player_ruby.png`, `player_emerald.png`, and `player_obsidian.png` are legacy 28x24 human miner spritesheets (20 frames) that lack all cat animation states; if loaded, `Player.render()` falls back to static `idle_0` or `walk_0` for every action.
- **Severity**: High
- **Location**: `states/play_state.py` (lines 343–345), `states/skin_state.py`, `assets/spritesheets/player_{ruby,emerald,obsidian}.png`.

#### Issue 1.2: Cavern Background Brick Tile Deletion on Asset Regeneration
- **Expected**: Procedural tile generation (`AssetGenerator.generate_tiles()`) creates and preserves all environment tiles, including `bg_brick` used for cavern wall backdrops.
- **Observed**: `AssetGenerator.generate_tiles()` only creates 5 tiles (`wall_under`, `wall_surface`, `dirt`, `rock`, `stone`) on a `TILE_SIZE * 5` surface. It does not include `bg_brick`. If `AssetGenerator.generate_tiles(force=True)` is executed, `tiles.png` is truncated from 120px to 100px and `tiles.json` is overwritten, permanently stripping `bg_brick` and breaking cavern background rendering in `PlayState.render()`.
- **Severity**: High
- **Location**: `engine/asset_generator.py` (lines 43–125), `assets/spritesheets/tiles.png`, `assets/data/tiles.json`.

#### Issue 1.3: Shale Tile Visual Texture and Collision Representation Missing
- **Expected**: Biome 1 includes destructible shale mineral blocks requiring multi-hit mining (`SHALE = 6`, `SHALE_MAX_HITS = 3`).
- **Observed**: `SHALE` has no visual texture in `tiles.png`, no entry in `tiles.json`, no generation procedure in `AssetGenerator`, and no render block in `PlayState.render()` (lines 975–985 only handle `WALL`, `DIRT`, `STONE`, and `COIN`). In addition, `PlayState.enter()` does not register static physics bodies for `SHALE` tiles.
- **Severity**: Medium
- **Location**: `engine/asset_generator.py`, `assets/spritesheets/tiles.png`, `states/play_state.py` (lines 335–340, 975–985).

#### Issue 1.4: Deep Tunnel Blast Door Entity Completely Missing
- **Expected**: README Section 11 states defeating the Feral Cat unlocks "deep tunnel blast doors".
- **Observed**: `blast_door_opened` is merely a boolean flag in `PlayState` with no visual sprite, level geometry, tile representation, or physics collider in the cavern.
- **Severity**: Medium
- **Location**: `states/play_state.py` (lines 160, 424).

#### Issue 1.5: Player Hitbox Height Inconsistency with Specification
- **Expected**: README Section 3 states: "The player's physical Pymunk shape is locked to a constant bounding box (`PLAYER_BODY_W = 12.0`, `PLAYER_BODY_H = 18.0`)".
- **Observed**: `core/config.py` sets `CAT_BODY_H = 26.0`, and `engine/entities.py` assigns `PLAYER_BODY_H = CAT_BODY_H` (26.0). The physical collider height is 44% taller than specified, impacting narrow gap traversal.
- **Severity**: Low
- **Location**: `core/config.py` (line 30), `engine/entities.py` (line 11).

---

### 2. Spritesheet Artifacts (Visual Defects in Assets)

#### Issue 2.1: Feral Cat Eye Heterochromia Flashing / Missing Across Animation Frames
- **Expected**: README Section 2 specifies distinct iris colors for the Feral Cat with heterochromia (left amber/red, right blue) across all facial expressions and animation frames.
- **Observed**: In `engine/banana_pipeline.py` (lines 622–627), heterochromia pixels (`[245, 40, 50]` red left eye, `[45, 140, 245]` blue right eye) are manually patched exclusively into `idle_0`. Frames `idle_1..3`, `run_0..3`, `pounce_0..3`, `action_slash_0..3`, `talk_0..3`, and `hurt_0..3` lack heterochromia entirely. During idle playback, the eyes abruptly flicker from vivid colors to blank.
- **Severity**: High
- **Location**: `assets/spritesheets/cat_feral.png`, `engine/banana_pipeline.py` (lines 622–627).

#### Issue 2.2: Idle Animation Frame Palette Popping and Inconsistent Overlays
- **Expected**: Anthropomorphic cat characters feature consistent 3-tone ramp shading across all breathing frames (`idle_0..3`).
- **Observed**: `engine/banana_pipeline.py` injects artificial pixel blocks solely into `idle_0` for multiple character sheets:
  - `cat_miner.png`: Miner hard-hat (`[230, 185, 40]`), headlamp glow (`[255, 245, 170]`), and vest (`[85, 105, 55]`) are painted onto `idle_0` only (lines 222–227). Frames `idle_1..3` lack these colored regions, producing jarring 4 Hz color popping on the helmet and vest.
  - `cat_driver.png`: Yellow cap badge and coat accents are painted onto `idle_0` only (lines 356–360).
  - `cat_soldier.png`: Watermelon rind helmet green (`[60, 145, 55]`) and red rind stripe (`[230, 60, 75]`) are painted onto `idle_0` only (lines 489–493).
- **Severity**: High
- **Location**: `assets/spritesheets/cat_miner.png`, `cat_driver.png`, `cat_soldier.png`, `engine/banana_pipeline.py` (lines 222–227, 356–360, 489–493).

#### Issue 2.3: Artificial Semi-Transparent Alpha Contamination in Pixel Art
- **Expected**: All character spritesheets adhere to strict 1-bit alpha or clean outlines (`(22, 18, 24)`) without anti-aliasing blur.
- **Observed**: `cat_miner.png` (and `player_classic.png`) contains 85 semi-transparent pixels across `afk_3`, `afk_4`, and `afk_5` due to `arr[2:8, 14:22, 3] = np.maximum(..., glow_alpha)` in `banana_pipeline.py` (line 217). Additionally, `cat_soldier.png` exhibits a significant RGB color drift in `hurt_0..3` (green channel standard deviation of 12.1 across frames).
- **Severity**: Medium
- **Location**: `assets/spritesheets/cat_miner.png`, `cat_soldier.png`, `engine/banana_pipeline.py` (line 217).

#### Issue 2.4: Terrain Tileset Transparent Seams and Incomplete Borders
- **Expected**: Terrain tiles in `tiles.png` are solid 20x20 pixel blocks that seamlessly tile horizontally and vertically.
- **Observed**: In `tiles.png`, `wall_under`, `wall_surface`, `dirt`, and `stone` have a 100% transparent left border column (x=0 has 0 non-zero alpha across all 20 rows). `stone` also has a 100% transparent bottom row (y=19). This creates 1px transparent gaps/seams when tiles are placed next to each other.
- **Severity**: Medium
- **Location**: `assets/spritesheets/tiles.png`, `assets/data/tiles.json`, `engine/asset_generator.py` (lines 50–115).

#### Issue 2.5: Duplicate and Cloned Slices in Sliced Animation Sequences
- **Expected**: Each animation frame in character sheets represents a distinct hand-crafted or sliced keyframe.
- **Observed**:
  - `cat_miner.png`: Climb frame 1 and climb frame 3 are sliced from the identical box `(997, 382, 1131, 555)` in `cat_miner_raw.jpg`.
  - `cat_soldier.png`: `talk_0` and `talk_3` are cropped from the identical box `(26, 571, 166, 767)`.
  - `cat_soldier.png`: `pinned_1` and `pinned_3` are cropped from the identical box `(918, 571, 1120, 766)`.
  - `cat_miner.png`: `afk_0..2` reuse the exact bounding boxes of `talk_2..3`.
- **Severity**: Low
- **Location**: `engine/banana_pipeline.py` (lines 108–130, 428–444).

---

### 3. Animation Issues (Frame Misalignment, Missing Frames)

#### Issue 3.1: NPC Spritesheets Fail Standard Mandatory Frame Matrix Specification
- **Expected**: README Section 3 specifies: "Every playable/interactive cat character spritesheet (`assets/spritesheets/cat_{id}.png` + `assets/data/cat_{id}.json`) MUST implement the standardized frame keys: idle_0..3 (4), walk_0..7 (8), run_0..5 (6), jump_0..1 (2), fall_0..1 (2), land_0 (1), action_0..3 (4), climb_0..3 (4), hurt_0..1 (2), talk_0..3 (4), afk_0..5 (6)". Total 37 standard keys.
- **Observed**: None of the interactive NPC sheets implement this standard matrix:
  - `cat_driver.json`: Contains only 16 frames. Completely lacks `run`, `jump`, `fall`, `land`, `climb`, `hurt`, and `afk`. Walk has only 4 frames instead of 8. Uses non-standard key `action_lantern_0..3` instead of `action_0..3`.
  - `cat_soldier.json`: Contains only 24 frames. Completely lacks `run`, `jump`, `fall`, `land`, `climb`, and `afk`. Walk has only 4 frames instead of 8. Uses non-standard key `action_shovel_0..3` instead of `action_0..3`. Has 4 hurt frames instead of 2.
  - `cat_feral.json`: Contains only 24 frames. Completely lacks `walk`, `jump`, `fall`, `land`, `climb`, and `afk`. Run has only 4 frames instead of 6. Uses non-standard key `action_slash_0..3` instead of `action_0..3`. Has 4 hurt frames instead of 2.
- **Severity**: Critical
- **Location**: `assets/data/cat_driver.json`, `cat_soldier.json`, `cat_feral.json`, `engine/banana_pipeline.py`.

#### Issue 3.2: Player Controller Ignores Multiple Mandatory Animation Frames
- **Expected**: Player state machine displays `jump_0..1`, `fall_0..1`, `hurt_0..1`, and `afk_0..5` during corresponding gameplay states.
- **Observed**: In `Player._get_current_frame_key()` (`engine/entities.py`, lines 510–535):
  - `jump_1` is never selected (returns `jump_0` for all negative vertical velocities).
  - `fall_1` is never selected (returns `fall_0` for all positive vertical velocities).
  - `hurt_0` and `hurt_1` are never returned under any circumstance (taking fall damage or getting hit plays no hurt animation).
  - `afk_phase` is only set to `0`, `2`, or `4` (`entities.py`, line 570). The calculation `idx = min(5, self.afk_phase - 1)` only ever yields indices 1 and 3. As a result, frames `afk_0`, `afk_2`, `afk_4`, and `afk_5` are never rendered.
  - Player `talk_0..3` frames are never triggered during dialogue sequences.
- **Severity**: High
- **Location**: `engine/entities.py` (lines 510–535, 570–575).

#### Issue 3.3: Inactive / Unreachable NPC Animation States
- **Expected**: Interactive NPCs animate according to their situational behaviors (patrol walk, dialogue talk, lantern swing, claw attack).
- **Observed**:
  - `DriverCatEntity`: `anim_state` is hardcoded to `"idle"` and never updated. Its `walk`, `talk`, and `action_lantern` frames are never displayed.
  - `SoldierCatEntity`: Never transitions to `STATE_DIALOGUE` during the stage 3 cutscene, omitting its `talk` animation.
  - `FeralCatEntity`: `anim_state` only toggles between `"idle"` and `"hurt"`. Its `run_0..3`, `pounce_0..3`, `action_slash_0..3`, and `talk_0..3` frames are never executed in runtime code.
- **Severity**: High
- **Location**: `engine/entities.py` (lines 750–880), `states/play_state.py` (lines 790–850).

#### Issue 3.4: Algorithmic Scaling Substituted for Jump and Land Sprite Poses
- **Expected**: Player jump stretch and landing squash feature distinct feline poses with ear and paw positioning.
- **Observed**: In `banana_pipeline.py` (lines 152–178), `jump_0..1`, `fall_0..1`, and `land_0` are generated by programmatically stretching and squashing `idle_boxes` crops (`scale_x=0.96..1.08`, `scale_y=0.92..1.06`) instead of slicing distinct feline jump/fall/land poses.
- **Severity**: Medium
- **Location**: `engine/banana_pipeline.py` (lines 152–178).

---

### 4. UI/UX Problems (Text Overflow, Layout Issues, Localization Gaps)

#### Issue 4.1: Severe Dialogue Box Text Overflow Outside Canvas Frame
- **Expected**: Dialogue text comfortably fits within the designated pixel-art dialogue window (`dw = CANVAS_W - 24`, `dh = 52`).
- **Observed**: The inner text area of `DialogueBox` provides ~32px of vertical clearance below the speaker title. `PlayState.render()` passes font size 15 (line height ~18px) to `dialogue_box.render()`:
  - English `driver_greeting`: Wraps to 5 lines (105px height), spilling 53px below the bottom edge of the dialogue frame.
  - English `soldier_warning`: Wraps to 4 lines (87px height), spilling 35px below the frame.
  - Russian `driver_greeting`: Wraps to 5 lines (105px height), overflowing the box.
  - Russian `soldier_warning`: Wraps to 4 lines (87px height), overflowing the box.
- **Severity**: Critical
- **Location**: `engine/dialogue.py` (lines 235–265, 305–330), `states/play_state.py` (line 1038).
- **Status**: Resolved

#### Issue 4.2: Main Menu Continue Button Permanently Hidden (Save Slot Index Conflict)
- **Expected**: Upon launching the game, players who have previously saved at a cabin checkpoint see and can click the "CONTINUE" button on the main menu.
- **Observed**: `MenuState.enter()` checks `save_manager.slot_exists(0)` to determine continue button visibility (`states/menu_state.py`, line 125). However, `PlayState` exclusively saves to and loads from slot 1 (`active_slot_index = 1`). `save_slot_0.json` is never written. Consequently, the "CONTINUE" button is permanently hidden, preventing players from resuming saved expeditions.
- **Severity**: Critical
- **Location**: `states/menu_state.py` (line 125), `states/play_state.py` (lines 131, 560–600).
- **Status**: Resolved

#### Issue 4.3: Hardcoded Untranslated Strings and Broken Localization Lookups
- **Expected**: Full Russian and English bilingual support across all gameplay messages, menus, and HUD readouts.
- **Observed**:
  - `Player.death_reason = "РАЗБИЛСЯ НАСМЕРТЬ"` is hardcoded in Russian inside `engine/entities.py` (line 617), causing Russian death text to display when the user has selected English.
  - In `assets/localization/ru.json`, `soldier_warning` contains raw untranslated English text: `(feral cats)`.
  - Tool HUD indicators in `PlayState._draw_tool_slot()` (`[Q]`, `HOOK`, `x1`, `[Rope]`, `[Pickaxe]`) are hardcoded English strings.
  - Equipment skin titles in `SkinState` (`CLASSIC`, `RUBY`, `EMERALD`, `OBSIDIAN`) are hardcoded English strings.
  - `PlayState.handle_event()` fires hints `tool_rope` and `tool_pickaxe`, but `hint_tool_rope` and `hint_tool_pickaxe` are missing from both `en.json` and `ru.json`, resulting in untranslated English fallback text.
- **Severity**: High
- **Location**: `engine/entities.py` (line 617), `assets/localization/ru.json`, `states/play_state.py` (lines 685, 1310–1325), `states/skin_state.py` (line 55).

#### Issue 4.4: Missing Settings Menu and Volume Configuration UI
- **Expected**: README Section 5 and `assets/localization/en.json` (`menu_settings`) specify engine settings management for master volume, music volume, SFX volume, locale, and fullscreen.
- **Observed**: There is no Settings button in `MenuState` and no `SettingsState` exists in the finite state machine. Sound volumes and display mode cannot be configured by the user via the UI.
- **Severity**: Medium
- **Location**: `states/menu_state.py`, `states/state_machine.py`, `core/save_system.py`.

---

### 5. Performance (Stutters, FPS Drops, Memory Issues)

#### Issue 5.1: Dynamic Full-Screen Surface Allocations in Darkness Lighting Loop
- **Expected**: Zero-allocation hot rendering loop with pre-allocated surfaces maintaining memory footprint well under 25 MB.
- **Observed**: In `PlayState._render_darkness_layer()`, `self._build_smooth_cone_mask()` and `self._build_cone_mask()` allocate new `pygame.Surface((view_w, view_h), pygame.SRCALPHA)` instances on every single frame. At 60 FPS, this generates 60 full-screen RGBA surface allocations per second, triggering repetitive garbage collection and potential frame time stutters.
- **Severity**: Medium
- **Location**: `states/play_state.py` (lines 1160–1250).

#### Issue 5.2: Per-Frame Font Surface Regeneration and Smoothscaling
- **Expected**: Responsive UI with cached text surfaces.
- **Observed**: In `engine/ui.py` (`UILabel.render` and `UIButton.render`), `font.render()` and `pygame.transform.smoothscale()` are called unconditionally on every render tick for every active label and button, instead of caching the rendered text surface until content or locale changes.
- **Severity**: Low
- **Location**: `engine/ui.py` (lines 45–60, 85–105).

---

### 6. Gameplay Mechanics (Unintended Behavior, Broken Features)

#### Issue 6.1: Feral Cat Combat and Victory Sequence Completely Inoperative
- **Expected**: README Section 11 specifies: "Feral Cat Ambush & Combat (Stage 4)... Can be stunned with the directional headlamp beam or defeated with teamwork, dropping a victory gem (+100 score) and unlocking deep tunnel blast doors."
- **Observed**:
  - In `PlayState.update()`, `self.feral_cat.update(dt, ...)` is called without passing `is_illuminated=True`, so the headlamp beam can never stun the feral cat.
  - `self.feral_cat.take_damage()` is never called anywhere in `PlayState` (by digging, melee, or tool interaction).
  - `self._on_feral_defeated()` is never invoked in runtime gameplay (only called in headless unit tests).
  - As a result, the feral cat is permanently invincible, the victory gem never spawns, and the combat encounter cannot be completed.
- **Severity**: Critical
- **Location**: `states/play_state.py` (lines 421, 795, 830–850), `engine/entities.py` (lines 820–860).
- **Status**: Resolved

#### Issue 6.2: Automatic Unintended Dirt Digging While Holding Grappling Rope
- **Expected**: Switching to the rope tool (`Q`) selects rope aiming and grappling mechanics; digging is restricted to pickaxe mode.
- **Observed**: In `PlayState.update()` (lines 760–775), directional digging triggers whenever directional keys are held against dirt (`if up or down or left or right: ... self._dig_tile(tx, ty)`). It does not check `if not self.player.using_rope`. The player automatically mines and destroys terrain simply by moving or climbing, even while the grappling rope is equipped.
- **Severity**: High
- **Location**: `states/play_state.py` (lines 760–775).
- **Status**: Resolved

#### Issue 6.3: Shale Mineral Blocks Absent from Procedural Level Generation
- **Expected**: Biome 1 cavern generates shale mineral blocks requiring multi-hit mining (`SHALE_MAX_HITS = 3`).
- **Observed**: `Level.generate()` in `engine/level.py` never places `SHALE` tiles into the world grid. `SHALE` blocks only exist in isolated unit test mocks. Furthermore, `PlayState.enter()` does not add physics collision shapes for `SHALE` tiles.
- **Severity**: High
- **Location**: `engine/level.py` (lines 25–180), `states/play_state.py` (lines 335–340).

#### Issue 6.4: Unintended Ceiling Destruction on Upward Velocity
- **Expected**: Ceiling digging occurs only upon deliberate upward action.
- **Observed**: In `PlayState.update()` (line 755), `if (jump and self.player.on_ground) or (self.player.body.velocity.y < -30.0):` automatically calls `_dig_tile()` on blocks above the player. Any vertical launch, explosion recoil, or rope swing velocity exceeding -30 px/s unintentionally destroys ceiling blocks above the player.
- **Severity**: Medium
- **Location**: `states/play_state.py` (lines 755–760).
- **Status**: Resolved
