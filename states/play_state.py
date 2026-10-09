import random
import pygame
import pymunk
import math
from core.config import (
    CANVAS_W, CANVAS_H, PANEL_HEIGHT, TILE_SIZE, GRID_W, GRID_H,
    COLOR_TEXT, COLOR_GOLD, COLOR_DANGER, COLOR_SUCCESS, PAL_OUTLINE,
    WALL, DIRT, ROCK, COIN, EMPTY
)
from engine.level import Level
from engine.entities import Player, RockEntity, Particle
from engine.asset_manager import AssetManager
from engine.ui import UIButton, UILabel, UIPanel, UINode
from core.camera import Camera
from states.state_machine import State

class PlayState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 18)
        self.font_big = pygame.font.Font(None, 28)
        self.world_w = GRID_W * TILE_SIZE
        self.world_h = GRID_H * TILE_SIZE

        self.play_view = pygame.Surface((CANVAS_W, CANVAS_H - PANEL_HEIGHT))
        self.darkness_layer = pygame.Surface((CANVAS_W, CANVAS_H - PANEL_HEIGHT), pygame.SRCALPHA)
        self.panel_surface = pygame.Surface((CANVAS_W, PANEL_HEIGHT))

        self.light_player = self._make_light_mask(70)
        self.light_coin = self._make_light_mask(24)

        self.camera = Camera(self.world_w, self.world_h)
        self._setup_end_panels()

    def _setup_end_panels(self):
        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        
        self.panel_over = UIPanel(0.5, 0.5, 180, 80, border_color=COLOR_DANGER)
        self.death_label = UILabel(0.5, 0.25, "ОБВАЛ В ШАХТЕ", self.font_big, COLOR_DANGER)
        self.panel_over.add_child(self.death_label)
        self.panel_over.add_child(UIButton(0.25, 0.75, 65, 20, "ЗАНОВО", self.font, self.enter))
        self.panel_over.add_child(UIButton(0.75, 0.75, 65, 20, "МЕНЮ", self.font, lambda: self.manager.change("menu")))
        self.panel_over.visible = False
        self.root.add_child(self.panel_over)

        self.panel_won = UIPanel(0.5, 0.5, 180, 80, border_color=COLOR_SUCCESS)
        self.panel_won.add_child(UILabel(0.5, 0.25, "ПОБЕДА!", self.font_big, COLOR_SUCCESS))
        self.panel_won.add_child(UIButton(0.25, 0.75, 65, 20, "ЗАНОВО", self.font, self.enter))
        self.panel_won.add_child(UIButton(0.75, 0.75, 65, 20, "МЕНЮ", self.font, lambda: self.manager.change("menu")))
        self.panel_won.visible = False
        self.root.add_child(self.panel_won)

        self.panel_pause = UIPanel(0.5, 0.5, 180, 100, border_color=(100, 150, 255))
        self.panel_pause.add_child(UILabel(0.5, 0.2, "ПАУЗА", self.font_big, (100, 150, 255)))
        self.panel_pause.add_child(UIButton(0.5, 0.5, 140, 20, "ПРОДОЛЖИТЬ", self.font, lambda: setattr(self, 'paused', False)))
        self.panel_pause.add_child(UIButton(0.25, 0.8, 65, 20, "ЗАНОВО", self.font, self.enter))
        self.panel_pause.add_child(UIButton(0.75, 0.8, 65, 20, "МЕНЮ", self.font, lambda: self.manager.change("menu")))
        self.panel_pause.visible = False
        self.root.add_child(self.panel_pause)
        
        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))

    def _make_light_mask(self, radius):
        diam = radius * 2
        surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            alpha = int(220 * ((radius - r) / radius) ** 1.6)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (radius, radius), r)
        return surf

    def enter(self):
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

        self.panel_over.visible = False
        self.panel_won.visible = False
        self.panel_pause.visible = False

        self.particles = []
        self.rocks = []
        self.tile_shapes = {}

        for y in range(GRID_H):
            for x in range(GRID_W):
                tile = self.level.grid[y][x]
                if tile in (WALL, DIRT):
                    self.add_static_tile(x, y)
                elif tile == ROCK:
                    self.level.grid[y][x] = EMPTY
                    self.rocks.append(RockEntity(x, y, self.space))

        skin = getattr(self.manager, "selected_skin", "classic")
        self.player = Player(self.level.spawn_x, self.level.spawn_y, skin, self.space)

        def post_solve_crush(arbiter, space, data):
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

        if hasattr(self.space, "on_collision"):
            self.space.on_collision(3, 2, post_solve=post_solve_crush)
            self.space.on_collision(3, 1, post_solve=post_solve_crush)
        else:
            h1 = self.space.add_collision_handler(3, 2)
            h1.post_solve = post_solve_crush
            h2 = self.space.add_collision_handler(3, 1)
            h2.post_solve = post_solve_crush

    def add_static_tile(self, tx, ty):
        shape = pymunk.Poly(self.space.static_body, [
            (tx*TILE_SIZE, ty*TILE_SIZE),
            ((tx+1)*TILE_SIZE, ty*TILE_SIZE),
            ((tx+1)*TILE_SIZE, (ty+1)*TILE_SIZE),
            (tx*TILE_SIZE, (ty+1)*TILE_SIZE)
        ])
        shape.friction = 0.5
        shape.collision_type = 1
        self.space.add(shape)
        self.tile_shapes[(tx, ty)] = shape

    def emit_particles(self, x, y, colors, count):
        for _ in range(count):
            ang = random.uniform(0, 6.28)
            spd = random.uniform(0.6, 2.2)
            self.particles.append(Particle(x, y, math.cos(ang)*spd, math.sin(ang)*spd, random.choice(colors), random.randint(14, 24)))

    def _is_key(self, keys, code_en, char_ru_code):
        try:
            return keys[code_en] or keys[char_ru_code]
        except:
            return keys[code_en]

    def handle_event(self, event, mouse_pos):
        clicked = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        self.root.update(mouse_pos, clicked)
        
        if event.type == pygame.KEYDOWN and not self.game_over and not self.game_won:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
                self.panel_pause.visible = self.paused

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, 1082, 1050):
                self.enter()

    def update(self, dt):
        if self.game_over or self.game_won or self.paused: return

        keys = pygame.key.get_pressed()
        up = self._is_key(keys, pygame.K_UP, 1094) or self._is_key(keys, pygame.K_w, 1094)
        down = self._is_key(keys, pygame.K_DOWN, 1099) or self._is_key(keys, pygame.K_s, 1099)
        left = self._is_key(keys, pygame.K_LEFT, 1092) or self._is_key(keys, pygame.K_a, 1092)
        right = self._is_key(keys, pygame.K_RIGHT, 1074) or self._is_key(keys, pygame.K_d, 1074)
        jump = keys[pygame.K_SPACE]
        
        self.player.update(up, down, left, right, jump, dt, self.space, self.emit_particles, self.camera)
        
        if (up or down or left or right) and not self.player.is_dead:
            px, py = self.player.body.position.x, self.player.body.position.y
            dig_x, dig_y = -1, -1
            if down and self.player.on_ground:
                dig_x = int(px // TILE_SIZE)
                dig_y = int((py + self.player.h/2 + 2) // TILE_SIZE)
            elif up and not self.player.on_ground:
                dig_x = int(px // TILE_SIZE)
                dig_y = int((py - self.player.h/2 - 2) // TILE_SIZE)
            else:
                offset = self.player.w/2 + 2 if self.player.facing_right else -self.player.w/2 - 2
                dig_x = int((px + offset) // TILE_SIZE)
                dig_y = int(py // TILE_SIZE)

            if 0 <= dig_x < GRID_W and 0 <= dig_y < GRID_H:
                if self.level.grid[dig_y][dig_x] == DIRT:
                    self.level.grid[dig_y][dig_x] = EMPTY
                    self.player.dig_timer = 12
                    self.camera.add_shake(1.0, 4)
                    self.emit_particles(dig_x*TILE_SIZE + 10, dig_y*TILE_SIZE + 10, [(155, 92, 54), (195, 132, 84)], 10)
                    if (dig_x, dig_y) in self.tile_shapes:
                        self.space.remove(self.tile_shapes[(dig_x, dig_y)])
                        del self.tile_shapes[(dig_x, dig_y)]

        self.space.step(dt)

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
            if p.life <= 0: self.particles.remove(p)

        p_tx = int(self.player.body.position.x // TILE_SIZE)
        p_ty = int(self.player.body.position.y // TILE_SIZE)
        if 0 <= p_tx < GRID_W and 0 <= p_ty < GRID_H:
            if self.level.grid[p_ty][p_tx] == COIN:
                self.level.grid[p_ty][p_tx] = EMPTY
                self.score += 10
                self.coins_left -= 1
                self.emit_particles(p_tx*TILE_SIZE + 10, p_ty*TILE_SIZE + 10, [(255, 230, 80), (255, 180, 30)], 14)
                if self.coins_left <= 0:
                    self.game_won = True
                    self.panel_won.visible = True
                    if not self.recorded_score:
                        depth = int(self.player.body.position.y // TILE_SIZE)
                        self.manager.leaderboard.add_score(self.score, depth, self.player.skin_id)
                        self.recorded_score = True

    def render(self, surface):
        cam_x, cam_y = self.camera.update(
            self.player.body.position.x, self.player.body.position.y,
            self.player.facing_right, self.player.body.velocity.y > 0
        )
        cam_x, cam_y = int(cam_x), int(cam_y)

        depth_ratio = min(1.0, (self.player.body.position.y / self.world_h) * 2.5)
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
        coin_frame = coin_sprites[(pygame.time.get_ticks() // 80) % len(coin_sprites)]

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                rx, ry = int(x * TILE_SIZE - cam_x), int(y * TILE_SIZE - cam_y)
                if 0 <= x < GRID_W and 0 <= y < GRID_H:
                    cell = self.level.grid[y][x]
                    if cell == WALL:
                        t_name = "wall_surface" if y <= 1 and (y == 0 or self.level.grid[y-1][x] != WALL) else "wall_under"
                        self.play_view.blit(AssetManager.get().get_sprite("tiles", t_name), (rx, ry))
                    elif cell == DIRT:
                        self.play_view.blit(AssetManager.get().get_sprite("tiles", "dirt"), (rx, ry))
                    elif cell == COIN:
                        self.play_view.blit(coin_frame, (rx, ry))

        asset_mgr = AssetManager.get()
        for rock in self.rocks:
            rock.render(self.play_view, cam_x, cam_y, asset_mgr)
        for p in self.particles:
            p.render(self.play_view, cam_x, cam_y)
        self.player.render(self.play_view, cam_x, cam_y, asset_mgr)

        self.darkness_layer.fill((6, 8, 12, min(255, int(40 + depth_ratio * 215))))
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if 0 <= x < GRID_W and 0 <= y < GRID_H and self.level.grid[y][x] == COIN:
                    self.darkness_layer.blit(self.light_coin, (int(x*TILE_SIZE - cam_x) - 2, int(y*TILE_SIZE - cam_y) - 2), special_flags=pygame.BLEND_RGBA_SUB)

        if not self.player.is_dead:
            px = int(self.player.body.position.x - cam_x) - self.light_player.get_width() // 2
            py = int(self.player.body.position.y - cam_y) - self.light_player.get_height() // 2
            self.darkness_layer.blit(self.light_player, (px, py), special_flags=pygame.BLEND_RGBA_SUB)

        self.play_view.blit(self.darkness_layer, (0, 0))
        surface.blit(self.play_view, (0, PANEL_HEIGHT))
        self._render_panel(surface)

        self.root.render(surface)

    def _render_panel(self, surface):
        for py in range(PANEL_HEIGHT):
            pt = py / PANEL_HEIGHT
            pygame.draw.line(self.panel_surface, (int(32 - 16*pt), int(38 - 18*pt), int(50 - 22*pt)), (0, py), (CANVAS_W, py))
        pygame.draw.line(self.panel_surface, (255, 200, 60), (0, PANEL_HEIGHT - 2), (CANVAS_W, PANEL_HEIGHT - 2), 2)
        pygame.draw.line(self.panel_surface, PAL_OUTLINE, (0, PANEL_HEIGHT - 1), (CANVAS_W, PANEL_HEIGHT - 1), 1)
        
        self.panel_surface.blit(self.font.render(f"СЧЁТ: {self.score}", True, COLOR_GOLD), (8, 6))
        self.panel_surface.blit(self.font.render(f"ГЛУБИНА: {int(self.player.body.position.y // TILE_SIZE)}м", True, COLOR_TEXT), (80, 6))
        
        pygame.draw.rect(self.panel_surface, (100, 20, 20), (170, 5, 50, 8))
        pygame.draw.rect(self.panel_surface, (250, 40, 40), (170, 5, 50 * (self.player.health / 100.0), 8))
        pygame.draw.rect(self.panel_surface, PAL_OUTLINE, (170, 5, 50, 8), 1)
        self.panel_surface.blit(self.font.render("HP", True, COLOR_TEXT), (150, 4))
        
        pygame.draw.rect(self.panel_surface, (20, 80, 20), (170, 16, 50, 8))
        pygame.draw.rect(self.panel_surface, (40, 200, 40), (170, 16, 50 * (self.player.stamina / 100.0), 8))
        pygame.draw.rect(self.panel_surface, PAL_OUTLINE, (170, 16, 50, 8), 1)
        self.panel_surface.blit(self.font.render("ST", True, COLOR_TEXT), (150, 15))

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.circle(self.panel_surface, (255, 60, 60), (285, 15), 3)
        self.panel_surface.blit(self.font.render("REC", True, (255, 100, 100)), (292, 10))
        surface.blit(self.panel_surface, (0, 0))
