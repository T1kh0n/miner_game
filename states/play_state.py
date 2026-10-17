import random
import pygame
import pymunk
import math
from typing import Any, Callable
from core.config import (
    CANVAS_W, CANVAS_H, PANEL_HEIGHT, TILE_SIZE, GRID_W, GRID_H,
    COLOR_TEXT, COLOR_GOLD, COLOR_DANGER, COLOR_SUCCESS, PAL_OUTLINE,
    WALL, DIRT, ROCK, COIN, EMPTY, STONE, FIXED_DT, MAX_ACCUMULATOR,
    FLASHLIGHT_ANGLE, FLASHLIGHT_SELF_GLOW, AFK_KNOCK_SECONDS, AFK_BLIND_SECONDS,
    CAT_MINER_ID,
)
from core.events import (
    EventManager,
    EVT_PLAYER_JUMP, EVT_PLAYER_LAND, EVT_BLOCK_HIT, EVT_BLOCK_BREAK,
    EVT_ROPE_THROW, EVT_ROPE_ATTACH, EVT_ENTITY_HURT,
    EVT_CHECKPOINT_SAVE, EVT_AFK_KNOCK, EVT_AFK_BLIND,
)
from core.audio import AudioManager
from engine.level import Level
from engine.entities import Player, RockEntity, Particle, ParticlePool, CabinEntity, HookEntity
from engine.asset_manager import AssetManager
from engine.ui import UIButton, UILabel, UIPanel, UINode
from core.camera import Camera
from core.localization import LocalizationManager
from core.save_system import (
    SaveManager, SaveSlotDTO, PlayerStateDTO, WorldStateDTO,
    ProgressionDTO, Vector2DTO, InventoryItemDTO, MinedTileDTO, RockStateDTO
)
from states.state_machine import State


class TutorialSystem:
    """Context-sensitive one-time tutorial hint dispatcher."""

    def __init__(self, font: pygame.font.Font, loc: LocalizationManager, on_hint_fired: Callable[[str], None] | None = None, initial_seen: set[str] | None = None) -> None:
        """Initialise with font, localization manager, and optional callback."""
        self.font = font
        self.loc = loc
        self.hints: list[dict[str, Any]] = []
        self.seen_hints: set[str] = set(initial_seen) if initial_seen else set()
        self.on_hint_fired = on_hint_fired

    @property
    def fired(self) -> set[str]:
        """Return the set of hint keys that have already been shown."""
        return self.seen_hints

    def fire(self, key: str, default_text: str = "") -> bool:
        """Show a hint once; subsequent calls with the same key are no-ops."""
        if key in self.seen_hints:
            return False
        self.seen_hints.add(key)
        text = self.loc.get_text(f"hint_{key}", default_text if default_text else key)
        self.hints.append({"key": key, "text": text, "life": 240, "max_life": 240})
        if self.on_hint_fired:
            self.on_hint_fired(key)
        return True

    def reset_hints(self) -> None:
        """Clear seen hints and show a confirmation toast."""
        self.seen_hints.clear()
        self.hints.clear()
        toast = self.loc.get_text("hints_reset_done", "Tutorial hints have been reset.")
        self.hints.append({"key": "reset_toast", "text": toast, "life": 180, "max_life": 180})

    def refresh_strings(self) -> None:
        """Re-fetch localised text for all pending hints after a language switch."""
        for h in self.hints:
            if h["key"] == "reset_toast":
                h["text"] = self.loc.get_text("hints_reset_done", h["text"])
            else:
                h["text"] = self.loc.get_text(f"hint_{h['key']}", h["text"])

    def update(self) -> None:
        """Decrement lifetimes and remove expired hints."""
        for h in self.hints[:]:
            h["life"] -= 1
            if h["life"] <= 0:
                self.hints.remove(h)

    def render(self, surface: pygame.Surface) -> None:
        """Draw active hint toasts centred near the bottom of the canvas."""
        y_pos = CANVAS_H - 20
        for h in self.hints:
            alpha = min(255, int(255 * (h["life"] / 30.0))) if h["life"] < 30 else 255
            ts = self.font.render(h["text"], True, (255, 235, 150))
            max_w = CANVAS_W - 16
            if ts.get_width() > max_w and ts.get_width() > 0:
                scale = max_w / ts.get_width()
                ts = pygame.transform.smoothscale(ts, (int(ts.get_width() * scale), int(ts.get_height() * scale)))
            bg = pygame.Surface((ts.get_width() + 10, ts.get_height() + 6), pygame.SRCALPHA)
            bg.fill((16, 20, 30, int(210 * (alpha / 255.0))))
            pygame.draw.rect(bg, (255, 215, 60, int(180 * (alpha / 255.0))), bg.get_rect(), 1, border_radius=3)
            bx = (CANVAS_W - bg.get_width()) // 2
            surface.blit(bg, (bx, y_pos - 3))
            surf_a = ts.copy()
            surf_a.set_alpha(alpha)
            surface.blit(surf_a, (bx + 5, y_pos))
            y_pos -= ts.get_height() + 8


class PlayState(State):
    """Core gameplay state: physics loop, multi-layer rendering, Biome 1 metro cavern, and diegetic HUD."""

    def __init__(self, manager) -> None:
        """Construct the play state and initialise persistent subsystems."""
        super().__init__(manager)
        self.loc = LocalizationManager.get()
        self.font = self.loc.get_font(15)
        self.font_big = self.loc.get_font(20)
        self.world_w = GRID_W * TILE_SIZE
        self.world_h = GRID_H * TILE_SIZE

        self.play_view = pygame.Surface((CANVAS_W, CANVAS_H))
        self.darkness_layer = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)

        self.camera = Camera(self.world_w, self.world_h)
        self.save_manager = SaveManager()
        self.active_slot_index = 1
        self.last_checkpoint_snapshot: SaveSlotDTO | None = None
        self.mined_tile_coords: list[tuple[int, int]] = []
        self.elapsed_playtime = 0.0

        self._coin_ticks = 0
        self.physics_accumulator = 0.0
        self.render_alpha = 1.0
        self.particle_pool = ParticlePool(180)
        self.particles = self.particle_pool.particles
        self.cabins: list[CabinEntity] = []

        self._afk_knock_emitted = False
        self._afk_blind_emitted = False
        self._afk_blind_alpha = 0.0
        self._afk_ripples: list[dict] = []

        self._events = EventManager.get()
        self._audio = AudioManager.get()

        self._setup_end_panels()
        self.loc.subscribe(self._refresh_strings)

    def _setup_end_panels(self) -> None:
        """Build all overlay UI panels (death, win, pause)."""
        canvas_rect = pygame.Rect(0, 0, CANVAS_W, CANVAS_H)
        self.root = UINode(0.5, 0.5, 1.0, 1.0)

        self.panel_over = UIPanel(0.5, 0.5, 190, 84, border_color=COLOR_DANGER)
        self.death_label = UILabel(0.5, 0.28, self.loc.get_text("death_cave_in", "CAVE-IN COLLAPSE"), self.font_big, COLOR_DANGER)
        self.panel_over.add_child(self.death_label)
        self.btn_over_restart = UIButton(0.25, 0.75, 68, 20, self.loc.get_text("btn_restart", "RESTART"), self.font, self.respawn_at_checkpoint)
        self.panel_over.add_child(self.btn_over_restart)
        self.btn_over_menu = UIButton(0.75, 0.75, 68, 20, self.loc.get_text("btn_menu", "MENU"), self.font, lambda: self.manager.change("menu"))
        self.panel_over.add_child(self.btn_over_menu)
        self.panel_over.visible = False
        self.root.add_child(self.panel_over)

        self.panel_won = UIPanel(0.5, 0.5, 190, 84, border_color=COLOR_SUCCESS)
        self.lbl_won = UILabel(0.5, 0.28, self.loc.get_text("win_title", "VICTORY!"), self.font_big, COLOR_SUCCESS)
        self.panel_won.add_child(self.lbl_won)
        self.btn_won_restart = UIButton(0.25, 0.75, 68, 20, self.loc.get_text("btn_restart", "RESTART"), self.font, self.enter)
        self.panel_won.add_child(self.btn_won_restart)
        self.btn_won_menu = UIButton(0.75, 0.75, 68, 20, self.loc.get_text("btn_menu", "MENU"), self.font, lambda: self.manager.change("menu"))
        self.panel_won.add_child(self.btn_won_menu)
        self.panel_won.visible = False
        self.root.add_child(self.panel_won)

        self.panel_pause = UIPanel(0.5, 0.5, 190, 134, border_color=(100, 150, 255))
        self.lbl_pause = UILabel(0.5, 0.12, self.loc.get_text("pause_title", "PAUSED"), self.font_big, (100, 150, 255))
        self.panel_pause.add_child(self.lbl_pause)
        self.btn_pause_resume = UIButton(0.5, 0.32, 140, 20, self.loc.get_text("btn_resume", "RESUME"), self.font, self._unpause)
        self.panel_pause.add_child(self.btn_pause_resume)
        self.btn_pause_lang = UIButton(0.5, 0.51, 140, 20, self.loc.get_text("ui_lang", "LANG: EN"), self.font, self._toggle_lang)
        self.panel_pause.add_child(self.btn_pause_lang)
        self.btn_pause_hints = UIButton(0.5, 0.70, 140, 20, self.loc.get_text("btn_reset_hints", "RESET HINTS"), self.font, self._reset_hints)
        self.panel_pause.add_child(self.btn_pause_hints)
        self.btn_pause_restart = UIButton(0.25, 0.88, 68, 20, self.loc.get_text("btn_restart", "RESTART"), self.font, self.enter)
        self.panel_pause.add_child(self.btn_pause_restart)
        self.btn_pause_menu = UIButton(0.75, 0.88, 68, 20, self.loc.get_text("btn_menu", "MENU"), self.font, lambda: self.manager.change("menu"))
        self.panel_pause.add_child(self.btn_pause_menu)
        self.panel_pause.visible = False
        self.root.add_child(self.panel_pause)

        self.root.layout(canvas_rect)

    def _toggle_lang(self) -> None:
        """Cycle the active locale."""
        self.loc.toggle_locale()
        self._refresh_strings()

    def _reset_hints(self) -> None:
        """Clear the tutorial hint history and update the save file."""
        if hasattr(self, "tutorial"):
            self.tutorial.reset_hints()
        existing_slot = self.save_manager.load_slot(self.active_slot_index)
        if existing_slot is not None:
            existing_slot.progression.seen_hints = []
            self.save_manager.save_slot(self.active_slot_index, existing_slot)
        if self.last_checkpoint_snapshot is not None:
            self.last_checkpoint_snapshot.progression.seen_hints = []

    def _refresh_strings(self) -> None:
        """Re-apply localised strings to all UI labels after a locale change."""
        self.btn_over_restart.set_text(self.loc.get_text("btn_restart", "RESTART"))
        self.btn_over_menu.set_text(self.loc.get_text("btn_menu", "MENU"))
        self.lbl_won.set_text(self.loc.get_text("win_title", "VICTORY!"))
        self.btn_won_restart.set_text(self.loc.get_text("btn_restart", "RESTART"))
        self.btn_won_menu.set_text(self.loc.get_text("btn_menu", "MENU"))
        self.lbl_pause.set_text(self.loc.get_text("pause_title", "PAUSED"))
        self.btn_pause_resume.set_text(self.loc.get_text("btn_resume", "RESUME"))
        self.btn_pause_lang.set_text(self.loc.get_text("ui_lang", "LANG: EN"))
        self.btn_pause_hints.set_text(self.loc.get_text("btn_reset_hints", "RESET HINTS"))
        self.btn_pause_restart.set_text(self.loc.get_text("btn_restart", "RESTART"))
        self.btn_pause_menu.set_text(self.loc.get_text("btn_menu", "MENU"))
        if hasattr(self, "player") and hasattr(self.player, "death_key") and self.player.death_key:
            self.death_label.set_text(self.loc.get_text(self.player.death_key, "CAVE-IN COLLAPSE"))
        if hasattr(self, "tutorial"):
            self.tutorial.refresh_strings()

    def _unpause(self) -> None:
        """Resume gameplay and hide the pause panel."""
        self.paused = False
        self.panel_pause.visible = False

    def enter(self) -> None:
        """(Re-)initialise the full gameplay session."""
        self.space = pymunk.Space()
        self.space.gravity = (0, 600)
        self.space.iterations = 20

        self.level = Level(GRID_W, GRID_H)
        self.score = 0
        self.coins_left = self.level.total_coins
        self.game_over = False
        self.game_won = False
        self.paused = False
        self.recorded_score = False
        self._coin_ticks = 0
        self.physics_accumulator = 0.0
        self.render_alpha = 1.0
        self.mined_tile_coords = []
        self.elapsed_playtime = 0.0
        self.last_checkpoint_snapshot = None

        self._afk_knock_emitted = False
        self._afk_blind_emitted = False
        self._afk_blind_alpha = 0.0
        self._afk_ripples = []

        self.panel_over.visible = False
        self.panel_won.visible = False
        self.panel_pause.visible = False

        self.particle_pool = ParticlePool(180)
        self.particles = self.particle_pool.particles
        self.rocks = []
        self.tile_shapes = {}

        existing_slot = self.save_manager.load_slot(self.active_slot_index)
        initial_seen = set(existing_slot.progression.seen_hints) if existing_slot else set()

        def _on_hint_fired(key: str) -> None:
            if self.last_checkpoint_snapshot is not None:
                self.last_checkpoint_snapshot.progression.seen_hints = list(self.tutorial.seen_hints)
                self.save_manager.save_slot(self.active_slot_index, self.last_checkpoint_snapshot)

        self.tutorial = TutorialSystem(self.font, self.loc, on_hint_fired=_on_hint_fired, initial_seen=initial_seen)
        self.tutorial.fire("start", "WASD/Arrows:Move | Space:Jump | Shift:Climb | Q:Rope | E:Cabin")

        self.cabins = [CabinEntity(cid, cx, cy) for cx, cy, cid in self.level.cabin_locations]

        top_boundary = pymunk.Segment(self.space.static_body, (0, 0), (self.world_w, 0), 2)
        top_boundary.friction = 0.5
        top_boundary.collision_type = 1
        self.space.add(top_boundary)

        left_boundary = pymunk.Segment(self.space.static_body, (0, 0), (0, self.world_h), 2)
        left_boundary.friction = 0.5
        left_boundary.collision_type = 1
        self.space.add(left_boundary)

        right_boundary = pymunk.Segment(self.space.static_body, (self.world_w, 0), (self.world_w, self.world_h), 2)
        right_boundary.friction = 0.5
        right_boundary.collision_type = 1
        self.space.add(right_boundary)

        for y in range(GRID_H):
            for x in range(GRID_W):
                tile = self.level.grid[y][x]
                if tile in (WALL, DIRT, STONE):
                    self.add_static_tile(x, y)
                elif tile == ROCK:
                    self.level.grid[y][x] = EMPTY
                    self.rocks.append(RockEntity(x, y, self.space))

        skin = getattr(self.manager, "selected_skin", CAT_MINER_ID)
        if skin not in ("miner",):
            skin = CAT_MINER_ID
        spawn_x, spawn_y = self.level.spawn_x, self.level.spawn_y
        self.player = Player(spawn_x, spawn_y, skin, self.space)
        self.player.death_key = "death_cave_in"

        rock_map = {r.shape: r for r in self.rocks}

        def pre_solve_player_rock(arbiter, space, data):
            rock_shape = arbiter.shapes[1] if arbiter.shapes[0] == data["player"].shape else arbiter.shapes[0]
            rock = data["rock_map"].get(rock_shape)
            if rock:
                rock.lock_velocity()
            return True

        def post_solve_player_rock(arbiter, space, data):
            rock_shape = arbiter.shapes[1] if arbiter.shapes[0] == data["player"].shape else arbiter.shapes[0]
            rock = data["rock_map"].get(rock_shape)
            if rock:
                rock.restore_velocity()
            if arbiter.total_impulse.length > 2500:
                p = data["player"]
                if not p.is_dead:
                    p.is_dead = True
                    n = arbiter.contact_point_set.normal
                    if abs(n.x) > abs(n.y):
                        p.death_key = "death_wall"
                    else:
                        p.death_key = "death_rock"
                    p.death_reason = data["loc"].get_text(p.death_key, "CRUSHED")
                    data["camera"].add_shake(8.0, 20)
                    data["emit"](p.body.position.x, p.body.position.y, [(255, 60, 60), (255, 180, 40)], 25)
                    data["events"].emit(EVT_ENTITY_HURT, x=p.body.position.x, y=p.body.position.y)

        def post_solve_wall(arbiter, space, data):
            if arbiter.total_impulse.length > 2500:
                p = data["player"]
                if not p.is_dead:
                    p.is_dead = True
                    n = arbiter.contact_point_set.normal
                    if abs(n.x) > abs(n.y):
                        p.death_key = "death_wall"
                    else:
                        p.death_key = "death_rock"
                    p.death_reason = data["loc"].get_text(p.death_key, "CRUSHED")
                    data["camera"].add_shake(8.0, 20)
                    data["emit"](p.body.position.x, p.body.position.y, [(255, 60, 60), (255, 180, 40)], 25)
                    data["events"].emit(EVT_ENTITY_HURT, x=p.body.position.x, y=p.body.position.y)

        shared_data = {
            "player": self.player,
            "camera": self.camera,
            "emit": self.emit_particles,
            "rock_map": rock_map,
            "loc": self.loc,
            "events": self._events,
        }
        self.space.on_collision(3, 2, pre_solve=pre_solve_player_rock, post_solve=post_solve_player_rock, data=shared_data)
        self.space.on_collision(3, 1, post_solve=post_solve_wall, data=shared_data)

    def add_static_tile(self, tx: int, ty: int) -> None:
        """Register a static physics tile shape for the tile at (tx, ty)."""
        shape = pymunk.Poly(self.space.static_body, [
            (tx * TILE_SIZE, ty * TILE_SIZE),
            ((tx + 1) * TILE_SIZE, ty * TILE_SIZE),
            ((tx + 1) * TILE_SIZE, (ty + 1) * TILE_SIZE),
            (tx * TILE_SIZE, (ty + 1) * TILE_SIZE)
        ])
        shape.friction = 0.5
        shape.collision_type = 1
        self.space.add(shape)
        self.tile_shapes[(tx, ty)] = shape

    def emit_particles(self, x: float, y: float, colors: list[tuple[int, int, int]], count: int) -> None:
        """Spawn burst particles at world position (x, y)."""
        for _ in range(count):
            ang = random.uniform(0, 6.28)
            spd = random.uniform(0.6, 2.2)
            self.particle_pool.spawn(
                x, y,
                math.cos(ang) * spd,
                math.sin(ang) * spd,
                random.choice(colors),
                random.randint(14, 24)
            )

    def _is_key(self, keys, code_en: int, char_ru_code: int) -> bool:
        """Check either the English or Cyrillic scancode for a logical key."""
        try:
            return bool(keys[code_en] or keys[char_ru_code])
        except Exception:
            return bool(keys[code_en])

    def _dig_tile(self, dig_x: int, dig_y: int) -> bool:
        """Attempt to dig the tile at grid coordinates (dig_x, dig_y)."""
        if 0 <= dig_x < GRID_W and 0 <= dig_y < GRID_H:
            if self.level.grid[dig_y][dig_x] == DIRT:
                self.level.grid[dig_y][dig_x] = EMPTY
                self.mined_tile_coords.append((dig_x, dig_y))
                self.player.dig_time = self.player.dig_duration
                self.player.dig_timer = int(self.player.dig_duration * 60)
                self.camera.add_shake(0.6, 3)
                self.emit_particles(
                    dig_x * TILE_SIZE + TILE_SIZE // 2,
                    dig_y * TILE_SIZE + TILE_SIZE // 2,
                    [(155, 92, 54), (195, 132, 84)], 10
                )
                if (dig_x, dig_y) in self.tile_shapes:
                    self.space.remove(self.tile_shapes[(dig_x, dig_y)])
                    del self.tile_shapes[(dig_x, dig_y)]
                self._events.emit(EVT_BLOCK_BREAK, x=dig_x, y=dig_y)
                self._audio.play("pickaxe_clink")
                self.tutorial.fire("mine_dirt", "Dirt cleared! Watch for falling rocks above.")
                return True
        return False

    def save_checkpoint(self, cabin: CabinEntity) -> None:
        """Snapshot the current game state to the active save slot."""
        slot = SaveSlotDTO(
            version=1,
            player=PlayerStateDTO(
                position=Vector2DTO(cabin.x, cabin.y - 2.0),
                health=100.0,
                stamina=100.0,
                inventory=[InventoryItemDTO("coin", self.score)],
                skin_id=self.player.skin_id
            ),
            world=WorldStateDTO(
                seed=self.level.seed,
                mined_tiles=[MinedTileDTO(x, y) for x, y in self.mined_tile_coords],
                rocks=[
                    RockStateDTO(
                        id=i,
                        position=Vector2DTO(r.body.position.x, r.body.position.y),
                        velocity=Vector2DTO(r.body.velocity.x, r.body.velocity.y),
                        angle=r.body.angle
                    )
                    for i, r in enumerate(self.rocks)
                ]
            ),
            progression=ProgressionDTO(
                checkpoint_id=cabin.cabin_id,
                elapsed_playtime=self.elapsed_playtime,
                seen_hints=list(self.tutorial.seen_hints)
            )
        )
        self.last_checkpoint_snapshot = slot
        self.save_manager.save_slot(self.active_slot_index, slot)
        self._events.emit(EVT_CHECKPOINT_SAVE, cabin_id=cabin.cabin_id)
        self._audio.play("ui_click")

    def respawn_at_checkpoint(self) -> None:
        """Restore player state from the last checkpoint snapshot."""
        if self.last_checkpoint_snapshot is None:
            self.enter()
            return

        snap = self.last_checkpoint_snapshot
        self.player.is_dead = False
        self.player.death_key = ""
        self.player.death_reason = ""
        self.player.health = snap.player.health
        self.player.stamina = snap.player.stamina
        self.player.body.position = (snap.player.position.x, snap.player.position.y)
        self.player.body.velocity = (0.0, 0.0)
        self.player.prev_x = snap.player.position.x
        self.player.prev_y = snap.player.position.y
        self.player.prev_vy = 0.0
        self.player.anim_time = 0.0
        self.player.climb_time = 0.0
        self.player.dig_time = 0.0
        self.player.is_climbing = False
        self.player.is_digging = False
        self.player.retract_rope()
        self._afk_knock_emitted = False
        self._afk_blind_emitted = False
        self._afk_blind_alpha = 0.0
        self._afk_ripples = []

        self.game_over = False
        self.panel_over.visible = False
        self.camera.x = self.player.body.position.x - CANVAS_W / 2.0
        self.camera.y = self.player.body.position.y - CANVAS_H / 2.0

        for r_dto, rock in zip(snap.world.rocks, self.rocks):
            rock.body.position = (r_dto.position.x, r_dto.position.y)
            rock.body.velocity = (r_dto.velocity.x, r_dto.velocity.y)
            rock.body.angle = r_dto.angle
            rock.prev_x = r_dto.position.x
            rock.prev_y = r_dto.position.y
            rock.prev_angle = r_dto.angle

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        """Process a single pygame event for UI and input."""
        clicked = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        self.root.update(mouse_pos, clicked)

        if event.type == pygame.KEYDOWN and not self.game_over and not self.game_won:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
                self.panel_pause.visible = self.paused

            if event.key == pygame.K_q and not self.paused:
                self.player.toggle_tool()
                self._audio.play("ui_click")
                mode = "Rope" if self.player.using_rope else "Pickaxe"
                self.tutorial.fire(f"tool_{mode.lower()}", f"Tool: {mode}")

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, 1082, 1050):
                self.enter()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.player.using_rope and not self.paused and not self.game_over and not self.game_won:
                cam_x = int(self.camera.x)
                cam_y = int(self.camera.y)
                mx, my = mouse_pos
                px = int(self.player.body.position.x)
                py = int(self.player.body.position.y)
                angle = math.atan2((my + cam_y) - py, (mx + cam_x) - px)
                if self.player.hook is not None and not self.player.hook.dead:
                    self.player.retract_rope()
                else:
                    self.player.fire_rope(self.space, angle)
                    self._events.emit(EVT_ROPE_THROW, x=px, y=py, angle=angle)
                    self._audio.play("rope_whoosh")

        if event.type == pygame.MOUSEWHEEL:
            if not self.paused and not self.game_over and not self.game_won:
                self.player.toggle_tool()

    def update(self, dt: float) -> None:
        """Advance physics, animation, AFK timers, and game logic by dt seconds."""
        if self.game_over or self.game_won or self.paused:
            return

        self.elapsed_playtime += dt
        self._coin_ticks += int(dt * 1000)
        self.physics_accumulator = min(self.physics_accumulator + dt, MAX_ACCUMULATOR)

        keys = pygame.key.get_pressed()
        up = self._is_key(keys, pygame.K_UP, 1094) or self._is_key(keys, pygame.K_w, 1094)
        down = self._is_key(keys, pygame.K_DOWN, 1099) or self._is_key(keys, pygame.K_s, 1099)
        left = self._is_key(keys, pygame.K_LEFT, 1092) or self._is_key(keys, pygame.K_a, 1092)
        right = self._is_key(keys, pygame.K_RIGHT, 1074) or self._is_key(keys, pygame.K_d, 1074)
        jump = keys[pygame.K_SPACE]
        climb_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        interact = keys[pygame.K_e] or self._is_key(keys, pygame.K_e, 1091) or up

        any_input = up or down or left or right or jump or climb_held or keys[pygame.K_q]

        was_on_ground_before = getattr(self.player, "on_ground", False)
        prev_afk_phase = self.player.afk_phase if hasattr(self.player, "afk_phase") else 0

        while self.physics_accumulator >= FIXED_DT:
            self.player.save_previous_state()
            for rock in self.rocks:
                rock.save_previous_state()

            self.player.update(
                up, down, left, right, jump, climb_held, FIXED_DT,
                self.space, self.emit_particles, self.camera,
                any_input=any_input,
                afk_knock_seconds=AFK_KNOCK_SECONDS,
                afk_blind_seconds=AFK_BLIND_SECONDS,
            )

            if self.player.on_ground and not was_on_ground_before:
                self._events.emit(EVT_PLAYER_LAND, x=self.player.body.position.x, y=self.player.body.position.y)
                self._audio.play("dirt_crumble")
            was_on_ground_before = self.player.on_ground

            if jump and self.player.on_ground:
                self._events.emit(EVT_PLAYER_JUMP, x=self.player.body.position.x, y=self.player.body.position.y)
                self._audio.play("cat_meow")

            new_afk = self.player.afk_phase
            if new_afk >= 2 and prev_afk_phase < 2 and not self._afk_knock_emitted:
                self._afk_knock_emitted = True
                self._events.emit(EVT_AFK_KNOCK)
                self._audio.play("screen_knock")
                for _ in range(3):
                    self._afk_ripples.append({"r": 0.0, "max_r": 30.0, "alpha": 200})
            if new_afk >= 4 and prev_afk_phase < 4 and not self._afk_blind_emitted:
                self._afk_blind_emitted = True
                self._events.emit(EVT_AFK_BLIND)
                self._audio.play("screen_knock")
            prev_afk_phase = new_afk

            if interact and not self.player.is_dead and not self.player.is_climbing:
                px = self.player.body.position.x
                py = self.player.body.position.y
                for cabin in self.cabins:
                    if cabin.is_near(px, py):
                        if not cabin.activated:
                            cabin.activate(self.emit_particles, self.camera)
                            self.player.health = 100.0
                            self.player.stamina = 100.0
                            self.save_checkpoint(cabin)
                            self.tutorial.fire("checkpoint", "Checkpoint saved! Progress secured.")

            if (self.player.on_wall_l or self.player.on_wall_r) and not self.player.on_ground:
                self.tutorial.fire("first_wall", "Press Shift to climb or grab the wall!")

            if self.player.is_climbing:
                self.tutorial.fire("climb_stamina", "Climbing uses stamina. Rest on ground to recover!")

            if not self.player.is_dead and not self.player.is_climbing:
                px = self.player.body.position.x
                py = self.player.body.position.y
                hw = self.player.w / 2.0
                hh = self.player.h / 2.0

                if (jump and self.player.on_ground) or (self.player.body.velocity.y < -30.0):
                    above_y = int((py - hh - 2.0) // TILE_SIZE)
                    for test_x in [int((px - hw + 2.0) // TILE_SIZE), int((px + hw - 2.0) // TILE_SIZE)]:
                        self._dig_tile(test_x, above_y)

                if up or down or left or right:
                    dir_x, dir_y = 0, 0
                    if down and self.player.on_ground:
                        dir_y = 1
                    elif up and not self.player.on_ground:
                        dir_y = -1
                    else:
                        dir_x = 1 if self.player.facing_right else -1

                    bx1, by1, bx2, by2 = self.player.get_dig_sensor_bounds(dir_x, dir_y)
                    t_x1 = max(0, int(bx1 // TILE_SIZE))
                    t_x2 = min(GRID_W - 1, int(bx2 // TILE_SIZE))
                    t_y1 = max(0, int(by1 // TILE_SIZE))
                    t_y2 = min(GRID_H - 1, int(by2 // TILE_SIZE))
                    for ty in range(t_y1, t_y2 + 1):
                        for tx in range(t_x1, t_x2 + 1):
                            self._dig_tile(tx, ty)

            self.space.step(FIXED_DT)
            self.physics_accumulator -= FIXED_DT

        self.render_alpha = self.physics_accumulator / FIXED_DT
        self.tutorial.update()
        self.particle_pool.update()

        for rip in self._afk_ripples[:]:
            rip["r"] += 1.2
            rip["alpha"] = max(0, rip["alpha"] - 8)
            if rip["r"] >= rip["max_r"] or rip["alpha"] <= 0:
                self._afk_ripples.remove(rip)

        if self.player.afk_phase >= 4:
            target_alpha = 160.0 + math.sin(self.elapsed_playtime * 3.0) * 60.0
            self._afk_blind_alpha = min(220.0, self._afk_blind_alpha + 4.0)
            self._afk_blind_alpha = min(self._afk_blind_alpha, target_alpha)
        else:
            self._afk_blind_alpha = max(0.0, self._afk_blind_alpha - 10.0)

        if self.player.is_dead:
            self.game_over = True
            self.panel_over.visible = True
            if hasattr(self.player, 'death_key') and self.player.death_key:
                self.death_label.set_text(self.loc.get_text(self.player.death_key, "CAVE-IN COLLAPSE"))
            elif hasattr(self.player, 'death_reason'):
                self.death_label.set_text(self.player.death_reason)
            if not self.recorded_score:
                depth = int(self.player.body.position.y // TILE_SIZE)
                self.manager.leaderboard.add_score(self.score, depth, self.player.skin_id)
                self.recorded_score = True

        p_tx = int(self.player.body.position.x // TILE_SIZE)
        p_ty = int(self.player.body.position.y // TILE_SIZE)
        if 0 <= p_tx < GRID_W and 0 <= p_ty < GRID_H:
            if self.level.grid[p_ty][p_tx] == COIN:
                self.level.grid[p_ty][p_tx] = EMPTY
                self.score += 10
                self.coins_left -= 1
                self.emit_particles(
                    p_tx * TILE_SIZE + TILE_SIZE // 2,
                    p_ty * TILE_SIZE + TILE_SIZE // 2,
                    [(255, 230, 80), (255, 180, 30)], 14
                )
                self.tutorial.fire("coin", "Collect all coins to win!")
                if self.coins_left <= 0:
                    self.game_won = True
                    self.panel_won.visible = True
                    if not self.recorded_score:
                        depth = int(self.player.body.position.y // TILE_SIZE)
                        self.manager.leaderboard.add_score(self.score, depth, self.player.skin_id)
                        self.recorded_score = True

    def render(self, surface: pygame.Surface) -> None:
        """Render the full frame: multi-layer world, Biome 1 metro cavern, lighting, diegetic HUD, and overlays."""
        interp_px, interp_py = self.player.get_interpolated_pos(self.render_alpha)
        if not self.paused:
            moving_down = (not self.player.on_ground and self.player.body.velocity.y > 60.0)
            cam_x, cam_y = self.camera.update(
                interp_px, interp_py,
                self.player.facing_right, moving_down, FIXED_DT
            )
        else:
            cam_x, cam_y = self.camera.x, self.camera.y
        cam_x, cam_y = int(cam_x), int(cam_y)

        view_w = CANVAS_W
        view_h = CANVAS_H

        depth_ratio = min(1.0, max(0.0, ((interp_py - 60.0) / self.world_h) * 2.5))
        self.play_view.fill((20, 24, 32))

        start_col = max(0, int((cam_x - TILE_SIZE) // TILE_SIZE))
        end_col = min(GRID_W, int((cam_x + CANVAS_W + TILE_SIZE) // TILE_SIZE) + 1)
        start_row = max(0, int((cam_y - TILE_SIZE) // TILE_SIZE))
        end_row = min(GRID_H, int((cam_y + view_h + TILE_SIZE) // TILE_SIZE) + 1)

        am = AssetManager.get()

        if cam_y < 80:
            sky_rect = pygame.Rect(0, 0, CANVAS_W, max(0, int(3 * TILE_SIZE - cam_y)))
            if sky_rect.height > 0:
                for sy in range(sky_rect.height):
                    ratio = sy / max(1, sky_rect.height)
                    r = int(22 * (1.0 - ratio) + 42 * ratio)
                    g = int(26 * (1.0 - ratio) + 48 * ratio)
                    b = int(36 * (1.0 - ratio) + 62 * ratio)
                    pygame.draw.line(self.play_view, (r, g, b), (0, sy), (CANVAS_W, sy))
                try:
                    panelki = am.get_sprite("metro_props", "panelki")
                    px_pan = int((-cam_x * 0.25) % panelki.get_width()) - panelki.get_width()
                    py_pan = int(3 * TILE_SIZE - cam_y - panelki.get_height())
                    while px_pan < CANVAS_W:
                        self.play_view.blit(panelki, (px_pan, py_pan))
                        px_pan += panelki.get_width()
                except Exception:
                    pass

        try:
            bg_brick = am.get_sprite("tiles", "bg_brick")
        except Exception:
            bg_brick = None

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if 0 <= x < GRID_W and 0 <= y < GRID_H:
                    if self.level.grid[y][x] == EMPTY and y >= 4 and bg_brick is not None:
                        rx = int(x * TILE_SIZE - cam_x)
                        ry = int(y * TILE_SIZE - cam_y)
                        self.play_view.blit(bg_brick, (rx, ry))

        self._render_metro_props(cam_x, cam_y, am)

        coin_sprites = am.get_sprite("coin")
        coin_frame = coin_sprites[(self._coin_ticks // 80) % len(coin_sprites)]

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if 0 <= x < GRID_W and 0 <= y < GRID_H:
                    cell = self.level.grid[y][x]
                    if cell == EMPTY:
                        continue
                    rx = int(x * TILE_SIZE - cam_x)
                    ry = int(y * TILE_SIZE - cam_y)

                    if cell == WALL:
                        t_name = "wall_surface" if (y == 0 or self.level.grid[y - 1][x] == EMPTY) else "wall_under"
                        self.play_view.blit(am.get_sprite("tiles", t_name), (rx, ry))
                    elif cell == DIRT:
                        self.play_view.blit(am.get_sprite("tiles", "dirt"), (rx, ry))
                    elif cell == STONE:
                        self.play_view.blit(am.get_sprite("tiles", "stone"), (rx, ry))
                    elif cell == COIN:
                        self.play_view.blit(coin_frame, (rx, ry))

                    border_col = (18, 14, 20)
                    if y > 0 and self.level.grid[y - 1][x] == EMPTY:
                        pygame.draw.rect(self.play_view, border_col, (rx, ry, TILE_SIZE, 2))
                    if y < GRID_H - 1 and self.level.grid[y + 1][x] == EMPTY:
                        pygame.draw.rect(self.play_view, border_col, (rx, ry + TILE_SIZE - 2, TILE_SIZE, 2))
                    if x > 0 and self.level.grid[y][x - 1] == EMPTY:
                        pygame.draw.rect(self.play_view, border_col, (rx, ry, 2, TILE_SIZE))
                    if x < GRID_W - 1 and self.level.grid[y][x + 1] == EMPTY:
                        pygame.draw.rect(self.play_view, border_col, (rx + TILE_SIZE - 2, ry, 2, TILE_SIZE))

        for cabin in self.cabins:
            cabin.render(self.play_view, cam_x, cam_y)

        for rock in self.rocks:
            rock.render(self.play_view, cam_x, cam_y, am, self.render_alpha, view_w, view_h)

        self.particle_pool.render(self.play_view, cam_x, cam_y, view_w, view_h)

        if self.player.using_rope and self.player.hook is None:
            mx, my = pygame.mouse.get_pos()
            scale = surface.get_width() / CANVAS_W
            mx_canvas = int(mx / scale)
            my_canvas = int(my / scale)
            px_screen = int(interp_px - cam_x)
            py_screen = int(interp_py - cam_y)
            aim_angle = math.atan2(my_canvas - py_screen, mx_canvas - px_screen)
            dummy = HookEntity(interp_px, interp_py, aim_angle, self.space, self.player.body)
            dummy.render_preview(self.play_view, cam_x, cam_y, interp_px, interp_py, aim_angle)

        self.player.render(self.play_view, cam_x, cam_y, am, self.render_alpha)

        self._render_darkness_layer(cam_x, cam_y, interp_px, interp_py, depth_ratio, start_row, end_row, start_col, end_col)

        surface.blit(self.play_view, (0, 0))
        self._render_diegetic_hud(surface)

        if self._afk_ripples:
            px_s = int(interp_px - cam_x)
            py_s = int(interp_py - cam_y)
            for rip in self._afk_ripples:
                if rip["alpha"] > 0:
                    pygame.draw.circle(surface, (200, 200, 255), (px_s, py_s), int(rip["r"]), 1)

        if self._afk_blind_alpha > 0:
            blind = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)
            blind.fill((255, 255, 220, int(self._afk_blind_alpha)))
            surface.blit(blind, (0, 0))

        self.tutorial.render(surface)
        self.root.render(surface)

    def _render_metro_props(self, cam_x: int, cam_y: int, am: AssetManager) -> None:
        """Render Metro Station Cavern props: train car, pipes, tracks, scaffolding, and bulbs."""
        try:
            pipes_img = am.get_sprite("metro_props", "pipes")
            pipes_y = int(5 * TILE_SIZE - 2 - cam_y)
            for px in range(2 * TILE_SIZE, (GRID_W - 2) * TILE_SIZE, pipes_img.get_width()):
                rx = int(px - cam_x)
                if -pipes_img.get_width() <= rx <= CANVAS_W:
                    self.play_view.blit(pipes_img, (rx, pipes_y))
        except Exception:
            pass

        try:
            tracks_img = am.get_sprite("metro_props", "tracks")
            tracks_y = int(10 * TILE_SIZE - 8 - cam_y)
            for tx in range(2 * TILE_SIZE, (GRID_W - 2) * TILE_SIZE, tracks_img.get_width()):
                rx = int(tx - cam_x)
                if -tracks_img.get_width() <= rx <= CANVAS_W:
                    self.play_view.blit(tracks_img, (rx, tracks_y))
        except Exception:
            pass

        try:
            scaff_img = am.get_sprite("metro_props", "scaffolding")
            scaff_x = int((GRID_W - 6) * TILE_SIZE - cam_x)
            scaff_y = int(10 * TILE_SIZE - scaff_img.get_height() - cam_y)
            if -scaff_img.get_width() <= scaff_x <= CANVAS_W:
                self.play_view.blit(scaff_img, (scaff_x, scaff_y))
        except Exception:
            pass

        try:
            bulb_img = am.get_sprite("metro_props", "hanging_bulb")
            bulb_xs = [8, 14, 20, 26, 32, 38]
            bulb_y = int(5 * TILE_SIZE - 2 - cam_y)
            for bx_tile in bulb_xs:
                rx = int(bx_tile * TILE_SIZE + 4 - cam_x)
                if -bulb_img.get_width() <= rx <= CANVAS_W:
                    self.play_view.blit(bulb_img, (rx, bulb_y))
        except Exception:
            pass

        try:
            train_img = am.get_sprite("metro_props", "train_car")
            train_x = int(2 * TILE_SIZE - cam_x)
            train_y = int(10 * TILE_SIZE - train_img.get_height() - cam_y)
            if -train_img.get_width() <= train_x <= CANVAS_W:
                self.play_view.blit(train_img, (train_x, train_y))
        except Exception:
            pass

    def _render_darkness_layer(
        self,
        cam_x: int,
        cam_y: int,
        interp_px: float,
        interp_py: float,
        depth_ratio: float,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
    ) -> None:
        """Compose darkness, metro station lighting, and smooth directional headlamp cone."""
        base_alpha = min(255, int(30 + depth_ratio * 225))
        self.darkness_layer.fill((6, 8, 12, base_alpha))

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if 0 <= x < GRID_W and 0 <= y < GRID_H and self.level.grid[y][x] == COIN:
                    coin_light = self._get_or_make_coin_light()
                    self.darkness_layer.blit(
                        coin_light,
                        (int(x * TILE_SIZE - cam_x) - 2, int(y * TILE_SIZE - cam_y) - 2),
                        special_flags=pygame.BLEND_RGBA_SUB
                    )

        bulb_xs = [8, 14, 20, 26, 32, 38]
        bulb_y_screen = int(5 * TILE_SIZE + 10 - cam_y)
        if -50 <= bulb_y_screen <= CANVAS_H + 50:
            bulb_glow = self._get_or_make_bulb_glow(38)
            for bx_tile in bulb_xs:
                bx_s = int(bx_tile * TILE_SIZE + 10 - cam_x)
                if -40 <= bx_s <= CANVAS_W + 40:
                    self.darkness_layer.blit(
                        bulb_glow,
                        (bx_s - 38, bulb_y_screen - 38),
                        special_flags=pygame.BLEND_RGBA_SUB,
                    )

        train_front_x = int(2 * TILE_SIZE + 140 - cam_x)
        train_front_y = int(10 * TILE_SIZE - 28 - cam_y)
        if -100 <= train_front_x <= CANVAS_W + 100 and -100 <= train_front_y <= CANVAS_H + 100:
            headlight_cone = self._build_cone_mask(CANVAS_W, CANVAS_H, train_front_x, train_front_y, 0.0, 0.0, beam_length=150, beam_angle=40.0)
            self.darkness_layer.blit(headlight_cone, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        if not self.player.is_dead:
            px_s = int(interp_px - cam_x)
            py_s = int(interp_py - cam_y)
            angle_rad = self.player.get_flashlight_angle_rad()

            glow_r = FLASHLIGHT_SELF_GLOW
            self_glow_surf = self._get_or_make_self_glow(glow_r)
            self.darkness_layer.blit(
                self_glow_surf,
                (px_s - glow_r, py_s - glow_r),
                special_flags=pygame.BLEND_RGBA_SUB,
            )

            cone_surf = self._build_smooth_cone_mask(CANVAS_W, CANVAS_H, px_s, py_s, angle_rad)
            self.darkness_layer.blit(cone_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        self.play_view.blit(self.darkness_layer, (0, 0))

    def _get_or_make_coin_light(self) -> pygame.Surface:
        """Return cached coin light mask."""
        if not hasattr(self, "_coin_light_surf"):
            radius = 24
            diam = radius * 2
            surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                alpha = int(220 * ((radius - r) / radius) ** 1.6)
                pygame.draw.circle(surf, (0, 0, 0, alpha), (radius, radius), r)
            self._coin_light_surf = surf
        return self._coin_light_surf

    def _get_or_make_self_glow(self, radius: int) -> pygame.Surface:
        """Return cached player self-glow circle mask."""
        key = radius
        if not hasattr(self, "_self_glow_cache"):
            self._self_glow_cache: dict[int, pygame.Surface] = {}
        if key not in self._self_glow_cache:
            diam = radius * 2
            surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                alpha = int(200 * ((radius - r) / radius) ** 1.4)
                pygame.draw.circle(surf, (0, 0, 0, alpha), (radius, radius), r)
            self._self_glow_cache[key] = surf
        return self._self_glow_cache[key]

    def _get_or_make_bulb_glow(self, radius: int) -> pygame.Surface:
        """Return cached hanging bulb warm radial glow mask."""
        if not hasattr(self, "_bulb_glow_surf"):
            diam = radius * 2
            surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                alpha = int(190 * ((radius - r) / radius) ** 1.3)
                pygame.draw.circle(surf, (0, 0, 0, alpha), (radius, radius), r)
            self._bulb_glow_surf = surf
        return self._bulb_glow_surf

    def _build_smooth_cone_mask(
        self,
        view_w: int,
        view_h: int,
        px: int,
        py: int,
        angle_rad: float,
    ) -> pygame.Surface:
        """Build smooth multi-layer warm flashlight cone with soft falloff."""
        cone_surf = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        cone_surf.fill((0, 0, 0, 0))

        layers = [
            (135, FLASHLIGHT_ANGLE * 0.55, 230),
            (120, FLASHLIGHT_ANGLE * 0.80, 180),
            (105, FLASHLIGHT_ANGLE * 1.05, 120),
            (85, FLASHLIGHT_ANGLE * 1.25, 60),
        ]

        steps = 16
        for length, angle_deg, alpha in layers:
            half_a = math.radians(angle_deg / 2.0)
            l_rad = angle_rad - half_a
            r_rad = angle_rad + half_a
            pts = [(px, py)]
            for i in range(steps + 1):
                a = l_rad + (r_rad - l_rad) * (i / steps)
                pts.append((px + int(math.cos(a) * length), py + int(math.sin(a) * length)))
            if len(pts) >= 3:
                pygame.draw.polygon(cone_surf, (0, 0, 0, alpha), pts)

        return cone_surf

    def _build_cone_mask(
        self,
        view_w: int,
        view_h: int,
        px: int,
        py: int,
        angle_rad: float,
        depth_ratio: float,
        beam_length: int = 140,
        beam_angle: float = FLASHLIGHT_ANGLE,
    ) -> pygame.Surface:
        """Build simple directional cone mask for train headlights or distant spotters."""
        half_angle = math.radians(beam_angle / 2.0)
        left_rad = angle_rad - half_angle
        right_rad = angle_rad + half_angle

        steps = 14
        cone_pts = [(px, py)]
        for i in range(steps + 1):
            a = left_rad + (right_rad - left_rad) * (i / steps)
            cone_pts.append((
                px + int(math.cos(a) * beam_length),
                py + int(math.sin(a) * beam_length),
            ))

        cone_surf = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        cone_surf.fill((0, 0, 0, 0))
        if len(cone_pts) >= 3:
            pygame.draw.polygon(cone_surf, (0, 0, 0, 180), cone_pts)
        return cone_surf

    def _render_diegetic_hud(self, surface: pygame.Surface) -> None:
        """Draw diegetic HUD elements: canned food rations, coin counter, tool icon slot, and stamina arc."""
        self._draw_health_icons(surface)
        self._draw_ore_counter(surface)
        self._draw_tool_slot(surface)
        if self.player.stamina < 100.0:
            self._draw_stamina_arc(surface)

    def _draw_health_icons(self, surface: pygame.Surface) -> None:
        """Render canned-food health icons in the top-left corner."""
        icon_size = 8
        spacing = 10
        health_ratio = max(0.0, self.player.health / 100.0)
        total_icons = 5
        filled_icons = round(health_ratio * total_icons)
        for i in range(total_icons):
            x = 4 + i * spacing
            y = 4
            filled = i < filled_icons
            body_col = (180, 60, 60) if filled else (70, 60, 60)
            pygame.draw.rect(surface, PAL_OUTLINE, (x, y, icon_size, icon_size), border_radius=2)
            pygame.draw.rect(surface, body_col, (x + 1, y + 1, icon_size - 2, icon_size - 2), border_radius=1)
            if filled:
                pygame.draw.rect(surface, (220, 90, 80), (x + 2, y + 2, 2, 2))
            pygame.draw.rect(surface, PAL_OUTLINE, (x + 2, y - 1, 4, 2))
            pygame.draw.rect(surface, (140, 140, 140), (x + 3, y - 1, 2, 1))

    def _draw_ore_counter(self, surface: pygame.Surface) -> None:
        """Render the score/coin counter in the top-right corner."""
        score_text = f"x{self.score}"
        ts = self.font.render(score_text, True, COLOR_GOLD)
        coin_x = CANVAS_W - ts.get_width() - 14
        coin_y = 4
        pygame.draw.circle(surface, PAL_OUTLINE, (CANVAS_W - 8, coin_y + 4), 5)
        pygame.draw.circle(surface, COLOR_GOLD, (CANVAS_W - 8, coin_y + 4), 4)
        pygame.draw.circle(surface, (255, 240, 100), (CANVAS_W - 8, coin_y + 3), 2)
        surface.blit(ts, (coin_x, coin_y))

    def _draw_tool_slot(self, surface: pygame.Surface) -> None:
        """Render 24x24 pixel-art tool icon in bottom-left corner with status indicator."""
        am = AssetManager.get()
        try:
            icon_key = "rope" if self.player.using_rope else "pickaxe"
            tool_icon = am.get_sprite("ui_icons", icon_key)
            slot_x = 4
            slot_y = CANVAS_H - 28
            surface.blit(tool_icon, (slot_x, slot_y))

            if self.player.using_rope:
                status_txt = "HOOK" if (self.player.hook and self.player.hook.attached) else "x1"
                ts = self.font.render(status_txt, True, (220, 240, 255))
                surface.blit(ts, (slot_x + 28, slot_y + 6))
            else:
                ts = self.font.render("[Q]", True, (180, 190, 205))
                surface.blit(ts, (slot_x + 28, slot_y + 6))
        except Exception:
            tool_name = "[Rope]" if self.player.using_rope else "[Pickaxe]"
            ts = self.font.render(tool_name, True, (220, 200, 160))
            surface.blit(ts, (4, CANVAS_H - 18))

    def _draw_stamina_arc(self, surface: pygame.Surface) -> None:
        """Render a contextual arc stamina indicator beside the cat when stamina < 100%."""
        interp_px, interp_py = self.player.get_interpolated_pos(self.render_alpha)
        cam_x = int(self.camera.x)
        cam_y = int(self.camera.y)
        sx = int(interp_px - cam_x) + 14
        sy = int(interp_py - cam_y)
        radius = 7
        ratio = max(0.0, min(1.0, self.player.stamina / 100.0))
        start_angle = -math.pi / 2
        steps = 16
        bg_pts = []
        fg_pts = []
        for i in range(steps + 1):
            a_bg = start_angle + (i / steps) * math.pi * 2
            bg_pts.append((sx + int(math.cos(a_bg) * radius), sy + int(math.sin(a_bg) * radius)))
        filled_steps = max(1, int(ratio * steps))
        for i in range(filled_steps + 1):
            a_fg = start_angle + (i / steps) * math.pi * 2
            fg_pts.append((sx + int(math.cos(a_fg) * radius), sy + int(math.sin(a_fg) * radius)))
        if len(bg_pts) >= 2:
            pygame.draw.lines(surface, (40, 80, 40), False, bg_pts, 2)
        if len(fg_pts) >= 2:
            st_col = (80, 220, 80) if ratio > 0.3 else (220, 180, 40)
            pygame.draw.lines(surface, st_col, False, fg_pts, 2)
