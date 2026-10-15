import random
import pygame
import pymunk
import math
from core.config import (
    CANVAS_W, CANVAS_H, PANEL_HEIGHT, TILE_SIZE, GRID_W, GRID_H,
    COLOR_TEXT, COLOR_GOLD, COLOR_DANGER, COLOR_SUCCESS, PAL_OUTLINE,
    WALL, DIRT, ROCK, COIN, EMPTY, STONE, FIXED_DT, MAX_ACCUMULATOR
)
from engine.level import Level
from engine.entities import Player, RockEntity, Particle
from engine.asset_manager import AssetManager
from engine.ui import UIButton, UILabel, UIPanel, UINode
from core.camera import Camera
from states.state_machine import State

class TutorialSystem:
    def __init__(self, font: pygame.font.Font) -> None:
        self.font = font
        self.hints = []
        self.fired = set()

    def fire(self, key: str, text: str) -> None:
        if key not in self.fired:
            self.fired.add(key)
            self.hints.append({"text": text, "life": 240, "max_life": 240})

    def update(self) -> None:
        for h in self.hints[:]:
            h["life"] -= 1
            if h["life"] <= 0:
                self.hints.remove(h)

    def render(self, surface: pygame.Surface) -> None:
        y_pos = CANVAS_H - PANEL_HEIGHT - 16
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
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.font = pygame.font.Font(None, 16)
        self.font_big = pygame.font.Font(None, 22)
        self.world_w = GRID_W * TILE_SIZE
        self.world_h = GRID_H * TILE_SIZE

        self.play_view = pygame.Surface((CANVAS_W, CANVAS_H - PANEL_HEIGHT))
        self.darkness_layer = pygame.Surface((CANVAS_W, CANVAS_H - PANEL_HEIGHT), pygame.SRCALPHA)
        self.panel_surface = pygame.Surface((CANVAS_W, PANEL_HEIGHT))

        self.light_player = self._make_light_mask(70)
        self.light_coin = self._make_light_mask(24)

        self.camera = Camera(self.world_w, self.world_h)
        self._coin_ticks = 0
        self.physics_accumulator = 0.0
        self.render_alpha = 1.0
        self._setup_end_panels()

    def _setup_end_panels(self) -> None:
        canvas_rect = pygame.Rect(0, 0, CANVAS_W, CANVAS_H)
        self.root = UINode(0.5, 0.5, 1.0, 1.0)

        self.panel_over = UIPanel(0.5, 0.5, 190, 84, border_color=COLOR_DANGER)
        self.death_label = UILabel(0.5, 0.28, "ОБВАЛ В ШАХТЕ", self.font_big, COLOR_DANGER)
        self.panel_over.add_child(self.death_label)
        self.panel_over.add_child(UIButton(0.25, 0.75, 68, 20, "ЗАНОВО", self.font, self.enter))
        self.panel_over.add_child(UIButton(0.75, 0.75, 68, 20, "МЕНЮ", self.font, lambda: self.manager.change("menu")))
        self.panel_over.visible = False
        self.root.add_child(self.panel_over)

        self.panel_won = UIPanel(0.5, 0.5, 190, 84, border_color=COLOR_SUCCESS)
        self.panel_won.add_child(UILabel(0.5, 0.28, "ПОБЕДА!", self.font_big, COLOR_SUCCESS))
        self.panel_won.add_child(UIButton(0.25, 0.75, 68, 20, "ЗАНОВО", self.font, self.enter))
        self.panel_won.add_child(UIButton(0.75, 0.75, 68, 20, "МЕНЮ", self.font, lambda: self.manager.change("menu")))
        self.panel_won.visible = False
        self.root.add_child(self.panel_won)

        self.panel_pause = UIPanel(0.5, 0.5, 190, 100, border_color=(100, 150, 255))
        self.panel_pause.add_child(UILabel(0.5, 0.2, "ПАУЗА", self.font_big, (100, 150, 255)))
        self.panel_pause.add_child(UIButton(0.5, 0.5, 140, 20, "ПРОДОЛЖИТЬ", self.font, self._unpause))
        self.panel_pause.add_child(UIButton(0.25, 0.8, 68, 20, "ЗАНОВО", self.font, self.enter))
        self.panel_pause.add_child(UIButton(0.75, 0.8, 68, 20, "МЕНЮ", self.font, lambda: self.manager.change("menu")))
        self.panel_pause.visible = False
        self.root.add_child(self.panel_pause)

        self.root.layout(canvas_rect)

    def _unpause(self) -> None:
        self.paused = False
        self.panel_pause.visible = False

    def _make_light_mask(self, radius: int) -> pygame.Surface:
        diam = radius * 2
        surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            alpha = int(220 * ((radius - r) / radius) ** 1.6)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (radius, radius), r)
        return surf

    def enter(self) -> None:
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

        self.panel_over.visible = False
        self.panel_won.visible = False
        self.panel_pause.visible = False

        self.particles = []
        self.rocks = []
        self.tile_shapes = {}

        self.tutorial = TutorialSystem(self.font)
        self.tutorial.fire("start", "WASD / Arrows: Move  |  Space: Jump  |  Shift: Climb")

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

        skin = getattr(self.manager, "selected_skin", "classic")
        spawn_x, spawn_y = self.level.spawn_x, self.level.spawn_y
        self.player = Player(spawn_x, spawn_y, skin, self.space)

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
                        p.death_reason = "РАЗМАЗАЛО О СТЕНУ"
                    else:
                        p.death_reason = "РАЗДАВИЛО КАМНЕМ"
                    data["camera"].add_shake(8.0, 20)
                    data["emit"](p.body.position.x, p.body.position.y, [(255, 60, 60), (255, 180, 40)], 25)

        def post_solve_wall(arbiter, space, data):
            if arbiter.total_impulse.length > 2500:
                p = data["player"]
                if not p.is_dead:
                    p.is_dead = True
                    n = arbiter.contact_point_set.normal
                    if abs(n.x) > abs(n.y):
                        p.death_reason = "РАЗМАЗАЛО О СТЕНУ"
                    else:
                        p.death_reason = "РАЗДАВИЛО КАМНЕМ"
                    data["camera"].add_shake(8.0, 20)
                    data["emit"](p.body.position.x, p.body.position.y, [(255, 60, 60), (255, 180, 40)], 25)

        player_rock_data = {
            "player": self.player,
            "camera": self.camera,
            "emit": self.emit_particles,
            "rock_map": rock_map
        }
        wall_data = {
            "player": self.player,
            "camera": self.camera,
            "emit": self.emit_particles
        }
        self.space.on_collision(3, 2, pre_solve=pre_solve_player_rock, post_solve=post_solve_player_rock, data=player_rock_data)
        self.space.on_collision(3, 1, post_solve=post_solve_wall, data=wall_data)

    def add_static_tile(self, tx: int, ty: int) -> None:
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
        for _ in range(count):
            ang = random.uniform(0, 6.28)
            spd = random.uniform(0.6, 2.2)
            self.particles.append(Particle(
                x, y,
                math.cos(ang) * spd,
                math.sin(ang) * spd,
                random.choice(colors),
                random.randint(14, 24)
            ))

    def _is_key(self, keys, code_en: int, char_ru_code: int) -> bool:
        try:
            return bool(keys[code_en] or keys[char_ru_code])
        except Exception:
            return bool(keys[code_en])

    def _dig_tile(self, dig_x: int, dig_y: int) -> bool:
        if 0 <= dig_x < GRID_W and 0 <= dig_y < GRID_H:
            if self.level.grid[dig_y][dig_x] == DIRT:
                self.level.grid[dig_y][dig_x] = EMPTY
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
                self.tutorial.fire("dig", "Dirt cleared! Watch for falling rocks above.")
                return True
        return False

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        clicked = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        self.root.update(mouse_pos, clicked)

        if event.type == pygame.KEYDOWN and not self.game_over and not self.game_won:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
                self.panel_pause.visible = self.paused

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, 1082, 1050):
                self.enter()

    def update(self, dt: float) -> None:
        if self.game_over or self.game_won or self.paused:
            return

        self._coin_ticks += int(dt * 1000)
        self.physics_accumulator = min(self.physics_accumulator + dt, MAX_ACCUMULATOR)

        keys = pygame.key.get_pressed()
        up = self._is_key(keys, pygame.K_UP, 1094) or self._is_key(keys, pygame.K_w, 1094)
        down = self._is_key(keys, pygame.K_DOWN, 1099) or self._is_key(keys, pygame.K_s, 1099)
        left = self._is_key(keys, pygame.K_LEFT, 1092) or self._is_key(keys, pygame.K_a, 1092)
        right = self._is_key(keys, pygame.K_RIGHT, 1074) or self._is_key(keys, pygame.K_d, 1074)
        jump = keys[pygame.K_SPACE]
        climb_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        while self.physics_accumulator >= FIXED_DT:
            self.player.save_previous_state()
            for rock in self.rocks:
                rock.save_previous_state()

            self.player.update(up, down, left, right, jump, climb_held, FIXED_DT, self.space, self.emit_particles, self.camera)

            if (self.player.on_wall_l or self.player.on_wall_r) and not self.player.on_ground:
                self.tutorial.fire("wall_contact", "Press Shift to climb or grab the wall!")

            if self.player.is_climbing:
                self.tutorial.fire("climb", "Climbing uses stamina. Rest on ground to recover!")

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

        if self.player.is_dead:
            self.game_over = True
            self.panel_over.visible = True
            if hasattr(self.player, 'death_reason'):
                self.death_label.set_text(self.player.death_reason)
            if not self.recorded_score:
                depth = int(self.player.body.position.y // TILE_SIZE)
                self.manager.leaderboard.add_score(self.score, depth, self.player.skin_id)
                self.recorded_score = True

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

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

        depth_ratio = min(1.0, max(0.0, ((interp_py - 60.0) / self.world_h) * 2.5))
        for y in range(CANVAS_H - PANEL_HEIGHT):
            t = y / (CANVAS_H - PANEL_HEIGHT)
            cr = int((45 * (1.0 - depth_ratio) + 8 * depth_ratio) * (1.0 - t * 0.5))
            cg = int((120 * (1.0 - depth_ratio) + 12 * depth_ratio) * (1.0 - t * 0.5))
            cb = int((130 * (1.0 - depth_ratio) + 18 * depth_ratio) * (1.0 - t * 0.5))
            pygame.draw.line(self.play_view, (cr, cg, cb), (0, y), (CANVAS_W, y))

        start_col = max(0, int(cam_x // TILE_SIZE))
        end_col = min(GRID_W, int((cam_x + CANVAS_W) // TILE_SIZE) + 2)
        start_row = max(0, int(cam_y // TILE_SIZE))
        end_row = min(GRID_H, int((cam_y + CANVAS_H - PANEL_HEIGHT) // TILE_SIZE) + 2)

        coin_sprites = AssetManager.get().get_sprite("coin")
        coin_frame = coin_sprites[(self._coin_ticks // 80) % len(coin_sprites)]

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                rx, ry = int(x * TILE_SIZE - cam_x), int(y * TILE_SIZE - cam_y)
                if 0 <= x < GRID_W and 0 <= y < GRID_H:
                    cell = self.level.grid[y][x]
                    if cell == WALL:
                        t_name = "wall_surface" if (y == 0 or self.level.grid[y - 1][x] == EMPTY) else "wall_under"
                        self.play_view.blit(AssetManager.get().get_sprite("tiles", t_name), (rx, ry))
                    elif cell == DIRT:
                        self.play_view.blit(AssetManager.get().get_sprite("tiles", "dirt"), (rx, ry))
                    elif cell == STONE:
                        self.play_view.blit(AssetManager.get().get_sprite("tiles", "stone"), (rx, ry))
                    elif cell == COIN:
                        self.play_view.blit(coin_frame, (rx, ry))

        asset_mgr = AssetManager.get()
        for rock in self.rocks:
            rock.render(self.play_view, cam_x, cam_y, asset_mgr, self.render_alpha)
        for p in self.particles:
            p.render(self.play_view, cam_x, cam_y)
        self.player.render(self.play_view, cam_x, cam_y, asset_mgr, self.render_alpha)

        self.darkness_layer.fill((6, 8, 12, min(255, int(30 + depth_ratio * 225))))
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if 0 <= x < GRID_W and 0 <= y < GRID_H and self.level.grid[y][x] == COIN:
                    self.darkness_layer.blit(
                        self.light_coin,
                        (int(x * TILE_SIZE - cam_x) - 2, int(y * TILE_SIZE - cam_y) - 2),
                        special_flags=pygame.BLEND_RGBA_SUB
                    )

        if not self.player.is_dead:
            px = int(interp_px - cam_x) - self.light_player.get_width() // 2
            py = int(interp_py - cam_y) - self.light_player.get_height() // 2
            self.darkness_layer.blit(self.light_player, (px, py), special_flags=pygame.BLEND_RGBA_SUB)

        self.play_view.blit(self.darkness_layer, (0, 0))
        surface.blit(self.play_view, (0, PANEL_HEIGHT))
        self._render_panel(surface)
        self.tutorial.render(surface)
        self.root.render(surface)

    def _render_panel(self, surface: pygame.Surface) -> None:
        for py in range(PANEL_HEIGHT):
            pt = py / PANEL_HEIGHT
            pygame.draw.line(
                self.panel_surface,
                (int(32 - 16 * pt), int(38 - 18 * pt), int(50 - 22 * pt)),
                (0, py), (CANVAS_W, py)
            )
        pygame.draw.line(self.panel_surface, (255, 200, 60), (0, PANEL_HEIGHT - 2), (CANVAS_W, PANEL_HEIGHT - 2), 2)
        pygame.draw.line(self.panel_surface, PAL_OUTLINE, (0, PANEL_HEIGHT - 1), (CANVAS_W, PANEL_HEIGHT - 1), 1)

        score_surf = self.font.render(f"SCORE:{self.score}", True, COLOR_GOLD)
        self.panel_surface.blit(score_surf, (6, 5))

        depth_val = max(0, int((self.player.body.position.y - 60.0) // TILE_SIZE))
        depth_surf = self.font.render(f"DEPTH:{depth_val}m", True, COLOR_TEXT)
        self.panel_surface.blit(depth_surf, (6, 17))

        coins_surf = self.font.render(f"COINS:{self.coins_left}", True, COLOR_TEXT)
        cx_pos = CANVAS_W // 2 - coins_surf.get_width() // 2
        self.panel_surface.blit(coins_surf, (cx_pos, 5))

        bar_x = CANVAS_W - 68
        bar_w = 60

        hp_label = self.font.render("HP", True, COLOR_TEXT)
        self.panel_surface.blit(hp_label, (bar_x - hp_label.get_width() - 3, 5))
        pygame.draw.rect(self.panel_surface, (100, 20, 20), (bar_x, 5, bar_w, 8))
        pygame.draw.rect(self.panel_surface, (250, 40, 40), (bar_x, 5, int(bar_w * max(0.0, self.player.health / 100.0)), 8))
        pygame.draw.rect(self.panel_surface, PAL_OUTLINE, (bar_x, 5, bar_w, 8), 1)

        st_label = self.font.render("ST", True, COLOR_TEXT)
        self.panel_surface.blit(st_label, (bar_x - st_label.get_width() - 3, 17))
        pygame.draw.rect(self.panel_surface, (20, 80, 20), (bar_x, 17, bar_w, 8))
        pygame.draw.rect(self.panel_surface, (40, 200, 40), (bar_x, 17, int(bar_w * max(0.0, self.player.stamina / 100.0)), 8))
        pygame.draw.rect(self.panel_surface, PAL_OUTLINE, (bar_x, 17, bar_w, 8), 1)

        surface.blit(self.panel_surface, (0, 0))
