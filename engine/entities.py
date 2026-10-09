import pygame
import pymunk
import math
from core.config import TILE_SIZE
from engine.asset_manager import AssetManager

class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def render(self, surf, cam_x, cam_y):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            ps = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*self.color, alpha), (self.size, self.size), self.size)
            surf.blit(ps, (int(self.x - cam_x) - self.size, int(self.y - cam_y) - self.size))

class RockEntity:
    def __init__(self, tx, ty, space):
        self.radius = 9.0
        mass = 10.0
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (tx * TILE_SIZE + TILE_SIZE / 2.0, ty * TILE_SIZE + TILE_SIZE / 2.0)
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.friction = 0.6
        self.shape.elasticity = 0.1
        self.shape.collision_type = 2
        space.add(self.body, self.shape)

    def render(self, surface, cam_x, cam_y, asset_mgr):
        sprite = asset_mgr.get_sprite("tiles", "rock")
        angle_deg = math.degrees(self.body.angle)
        rotated = pygame.transform.rotate(sprite, -angle_deg)
        rx = int(self.body.position.x - cam_x)
        ry = int(self.body.position.y - cam_y)
        rect = rotated.get_rect(center=(rx, ry))
        surface.blit(rotated, rect)

PLAYER_W = 12
PLAYER_H = 17
_PLAYER_SPRITE_CY = 13

class Player:
    def __init__(self, x, y, skin_id, space):
        self.skin_id = skin_id
        self.w = PLAYER_W
        self.h = PLAYER_H

        self.is_dead = False
        self.death_reason = ""
        self.facing_right = True
        self.is_digging = False
        self.dig_timer = 0
        self.anim_tick = 0
        self.on_ground = False
        self.on_wall_l = False
        self.on_wall_r = False

        self.health = 100.0
        self.stamina = 100.0
        self.prev_vy = 0.0

        mass = 5.0
        self.body = pymunk.Body(mass, float('inf'))
        self.body.position = (x, y)
        self.shape = pymunk.Poly.create_box(self.body, (self.w, self.h))
        self.shape.friction = 0.0
        self.shape.elasticity = 0.0
        self.shape.collision_type = 3
        space.add(self.body, self.shape)

    def update(self, up, down, left, right, jump, dt, space, particle_emitter, camera):
        if self.is_dead: return

        self.on_ground = False
        self.on_wall_l = False
        self.on_wall_r = False
        for info in space.shape_query(self.shape):
            if info.shape != self.shape and not getattr(info.shape, 'sensor', False):
                for cp in info.contact_point_set.points:
                    dy = cp.point_a.y - self.body.position.y
                    dx = cp.point_a.x - self.body.position.x
                    if dy > self.h / 2 - 2: self.on_ground = True
                    if dx > self.w / 2 - 2: self.on_wall_r = True
                    if dx < -self.w / 2 + 2: self.on_wall_l = True

        if self.on_ground:
            self.stamina = min(100.0, self.stamina + 40 * dt)
            if self.prev_vy > 380.0:
                dmg = (self.prev_vy - 380.0) * 0.4
                self.health -= dmg
                if self.health <= 0:
                    self.is_dead = True
                    self.death_reason = "РАЗБИЛСЯ НАСМЕРТЬ"
                    camera.add_shake(8.0, 20)
                    particle_emitter(self.body.position.x, self.body.position.y, [(255, 60, 60)], 25)

        move_axis = 0.0
        if left: move_axis -= 1.0
        if right: move_axis += 1.0

        if move_axis > 0: self.facing_right = True
        elif move_axis < 0: self.facing_right = False

        target_vx = move_axis * 110.0
        current_vx = self.body.velocity.x
        self.body.velocity = (current_vx + (target_vx - current_vx) * (0.2 if self.on_ground else 0.1), self.body.velocity.y)

        if jump and self.on_ground:
            self.body.velocity = (self.body.velocity.x, -170.0)
            particle_emitter(self.body.position.x, self.body.position.y + self.h/2, [(220, 225, 235)], 4)

        if (self.on_wall_l and left) or (self.on_wall_r and right):
            if up and self.stamina > 0:
                self.body.velocity = (self.body.velocity.x, -80.0)
                self.stamina -= 25 * dt
                if self.stamina <= 0:
                    self.stamina = 0
            elif not self.on_ground and self.body.velocity.y > 0:
                self.body.velocity = (self.body.velocity.x, self.body.velocity.y * 0.8)

        self.anim_tick += 1
        if self.dig_timer > 0:
            self.dig_timer -= 1
            self.is_digging = True
        else:
            self.is_digging = False

        self.prev_vy = self.body.velocity.y

    def render(self, surface, cam_x, cam_y, asset_mgr):
        if self.is_dead: return
        skin_bundle = f"player_{self.skin_id}"

        if self.is_digging:
            f_idx = min(3, (12 - self.dig_timer) // 3)
            sprite = asset_mgr.get_sprite(skin_bundle, f"dig_{f_idx}")
        elif not self.on_ground:
            sprite = asset_mgr.get_sprite(skin_bundle, "jump" if self.body.velocity.y < 0 else "fall")
        elif abs(self.body.velocity.x) > 10.0:
            f_idx = (self.anim_tick // 4) % 8
            sprite = asset_mgr.get_sprite(skin_bundle, f"walk_{f_idx}")
        else:
            f_idx = (self.anim_tick // 20) % 2
            sprite = asset_mgr.get_sprite(skin_bundle, f"idle_{f_idx}")

        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)

        rx = int(self.body.position.x - cam_x) - (sprite.get_width() // 2)
        ry = int(self.body.position.y - cam_y) - _PLAYER_SPRITE_CY
        surface.blit(sprite, (rx, ry))
