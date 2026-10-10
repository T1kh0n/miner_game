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
        self._locked_velocity = None

    def lock_velocity(self):
        self._locked_velocity = (self.body.velocity.x, self.body.velocity.y)

    def restore_velocity(self):
        if self._locked_velocity is not None:
            self.body.velocity = self._locked_velocity
            self._locked_velocity = None

    def render(self, surface, cam_x, cam_y, asset_mgr):
        sprite = asset_mgr.get_sprite("tiles", "rock")
        angle_deg = math.degrees(self.body.angle)
        rotated = pygame.transform.rotate(sprite, -angle_deg)
        rx = int(self.body.position.x - cam_x)
        ry = int(self.body.position.y - cam_y)
        rect = rotated.get_rect(center=(rx, ry))
        surface.blit(rotated, rect)

class Player:
    def __init__(self, x, y, skin_id, space):
        self.skin_id = skin_id

        mgr = AssetManager.get()
        sprite = mgr.get_sprite(f"player_{skin_id}", "idle_0")
        mask = pygame.mask.from_surface(sprite)
        rects = mask.get_bounding_rects()
        if rects:
            union = rects[0].unionall(rects[1:])
            self.w = max(8, union.width)
            self.h = max(10, union.height)
            self.offset_x = union.centerx
            self.offset_y = union.centery
        else:
            self.w = sprite.get_width()
            self.h = sprite.get_height()
            self.offset_x = sprite.get_width() // 2
            self.offset_y = sprite.get_height() // 2

        self.is_dead = False
        self.death_reason = ""
        self.facing_right = True
        self.is_digging = False
        self.is_climbing = False
        self.dig_timer = 0
        self.climb_tick = 0
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

    def _get_current_frame_key(self):
        if self.is_climbing:
            f_idx = (self.climb_tick // 6) % 4
            return f"climb_{f_idx}"
        if self.is_digging:
            f_idx = min(3, (12 - self.dig_timer) // 3)
            return f"dig_{f_idx}"
        if not self.on_ground:
            return "jump" if self.body.velocity.y < 0 else "fall"
        if abs(self.body.velocity.x) > 10.0:
            f_idx = (self.anim_tick // 4) % 8
            return f"walk_{f_idx}"
        f_idx = (self.anim_tick // 20) % 2
        return f"idle_{f_idx}"

    def update(self, up, down, left, right, jump, dt, space, particle_emitter, camera):
        if self.is_dead:
            return

        self.on_ground = False
        self.on_wall_l = False
        self.on_wall_r = False
        on_ceiling = False

        for info in space.shape_query(self.shape):
            if info.shape == self.shape:
                continue
            if getattr(info.shape, 'sensor', False):
                continue
            n = info.contact_point_set.normal
            if n.y > 0.5:
                self.on_ground = True
            elif n.y < -0.5:
                on_ceiling = True
            if n.x > 0.5:
                self.on_wall_r = True
            elif n.x < -0.5:
                self.on_wall_l = True

        if on_ceiling and self.body.velocity.y < 0:
            self.body.velocity = (self.body.velocity.x, max(0.0, self.body.velocity.y))

        on_wall = (self.on_wall_l and left) or (self.on_wall_r and right)
        self.is_climbing = on_wall and up and self.stamina > 0 and not on_ceiling and not self.on_ground

        if self.on_ground and not self.is_climbing:
            self.stamina = min(100.0, self.stamina + 40.0 * dt)
            if self.prev_vy > 220.0:
                dmg = (self.prev_vy - 220.0) * 0.5
                self.health -= dmg
                if self.health <= 0:
                    self.is_dead = True
                    self.death_reason = "РАЗБИЛСЯ НАСМЕРТЬ"
                    camera.add_shake(8.0, 20)
                    particle_emitter(self.body.position.x, self.body.position.y, [(255, 60, 60)], 25)

        move_axis = 0.0
        if left:
            move_axis -= 1.0
        if right:
            move_axis += 1.0

        if move_axis > 0:
            self.facing_right = True
        elif move_axis < 0:
            self.facing_right = False

        target_vx = move_axis * 110.0
        current_vx = self.body.velocity.x
        accel = 0.2 if self.on_ground else 0.1
        self.body.velocity = (
            current_vx + (target_vx - current_vx) * accel,
            self.body.velocity.y
        )

        half_h = self.h / 2
        if jump and self.on_ground:
            self.body.velocity = (self.body.velocity.x, -170.0)
            particle_emitter(self.body.position.x, self.body.position.y + half_h, [(220, 225, 235)], 4)

        if on_wall:
            if up and self.stamina > 0 and not on_ceiling:
                self.body.velocity = (self.body.velocity.x, -80.0)
                self.stamina = max(0.0, self.stamina - 30.0 * dt)
                self.climb_tick += 1
            elif not self.on_ground and self.body.velocity.y > 0:
                self.body.velocity = (self.body.velocity.x, self.body.velocity.y * 0.8)

        self.anim_tick += 1
        if self.dig_timer > 0:
            self.dig_timer -= 1
            self.is_digging = True
        else:
            self.is_digging = False

        frame_key = self._get_current_frame_key()
        mgr = AssetManager.get()
        hw, hh = mgr.get_hitbox(f"player_{self.skin_id}", frame_key)
        hw = max(8, hw)
        hh = max(10, hh)
        if hw != self.w or hh != self.h:
            old_pos = self.body.position
            space.remove(self.shape)
            self.w = hw
            self.h = hh
            self.shape = pymunk.Poly.create_box(self.body, (self.w, self.h))
            self.shape.friction = 0.0
            self.shape.elasticity = 0.0
            self.shape.collision_type = 3
            space.add(self.shape)
            self.body.position = old_pos

        self.prev_vy = self.body.velocity.y

    def render(self, surface, cam_x, cam_y, asset_mgr):
        if self.is_dead:
            return
        skin_bundle = f"player_{self.skin_id}"
        frame_key = self._get_current_frame_key()
        sprite = asset_mgr.get_sprite(skin_bundle, frame_key)

        sprite_w = sprite.get_width()
        mask = pygame.mask.from_surface(sprite)
        rects = mask.get_bounding_rects()
        if rects:
            union = rects[0].unionall(rects[1:])
            ox = union.centerx
            oy = union.centery
        else:
            ox = sprite_w // 2
            oy = sprite.get_height() // 2

        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
            ox = sprite_w - ox

        rx = int(self.body.position.x - cam_x) - ox
        ry = int(self.body.position.y - cam_y) - oy
        surface.blit(sprite, (rx, ry))
