import pygame
import pymunk
import math
from core.config import TILE_SIZE, CANVAS_W, CANVAS_H
from engine.asset_manager import AssetManager

PLAYER_BODY_W = 12.0
PLAYER_BODY_H = 18.0

_PARTICLE_SURF_CACHE: dict[tuple[int, int, int, int, int], pygame.Surface] = {}

def get_cached_particle_surface(color: tuple[int, int, int], alpha: int, size: int) -> pygame.Surface:
    alpha_bin = max(0, min(255, (alpha // 16) * 16))
    key = (color[0], color[1], color[2], alpha_bin, size)
    surf = _PARTICLE_SURF_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, alpha_bin), (size, size), size)
        _PARTICLE_SURF_CACHE[key] = surf
    return surf

class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], life: int, size: int = 2) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.life = life
        self.max_life = max(1, life)
        self.size = size

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def render(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            ps = get_cached_particle_surface(self.color, alpha, self.size)
            surf.blit(ps, (int(self.x - cam_x) - self.size, int(self.y - cam_y) - self.size))

class ParticlePool:
    def __init__(self, capacity: int = 180) -> None:
        self.capacity = capacity
        self.particles = [Particle(0.0, 0.0, 0.0, 0.0, (255, 255, 255), 0) for _ in range(capacity)]
        self.next_idx = 0

    def spawn(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], life: int, size: int = 2) -> None:
        p = self.particles[self.next_idx]
        p.x = float(x)
        p.y = float(y)
        p.vx = float(vx)
        p.vy = float(vy)
        p.color = color
        p.life = life
        p.max_life = max(1, life)
        p.size = size
        self.next_idx = (self.next_idx + 1) % self.capacity

    def update(self) -> None:
        for p in self.particles:
            if p.life > 0:
                p.update()

    def render(self, surf: pygame.Surface, cam_x: float, cam_y: float, view_w: float, view_h: float) -> None:
        min_x = cam_x - TILE_SIZE
        max_x = cam_x + view_w + TILE_SIZE
        min_y = cam_y - TILE_SIZE
        max_y = cam_y + view_h + TILE_SIZE
        for p in self.particles:
            if p.life > 0 and min_x <= p.x <= max_x and min_y <= p.y <= max_y:
                p.render(surf, cam_x, cam_y)

class RockEntity:
    def __init__(self, tx: int, ty: int, space: pymunk.Space) -> None:
        self.radius = 9.0
        mass = 10.0
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (tx * TILE_SIZE + TILE_SIZE / 2.0, ty * TILE_SIZE + TILE_SIZE / 2.0)
        self.prev_x = float(self.body.position.x)
        self.prev_y = float(self.body.position.y)
        self.prev_angle = float(self.body.angle)
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.friction = 0.6
        self.shape.elasticity = 0.1
        self.shape.collision_type = 2
        space.add(self.body, self.shape)
        self._locked_velocity = None

    def save_previous_state(self) -> None:
        self.prev_x = float(self.body.position.x)
        self.prev_y = float(self.body.position.y)
        self.prev_angle = float(self.body.angle)

    def get_interpolated_pose(self, alpha: float) -> tuple[float, float, float]:
        alpha = max(0.0, min(1.0, alpha))
        ix = self.prev_x * (1.0 - alpha) + self.body.position.x * alpha
        iy = self.prev_y * (1.0 - alpha) + self.body.position.y * alpha
        iangle = self.prev_angle * (1.0 - alpha) + self.body.angle * alpha
        return ix, iy, iangle

    def lock_velocity(self) -> None:
        self._locked_velocity = (self.body.velocity.x, self.body.velocity.y)

    def restore_velocity(self) -> None:
        if self._locked_velocity is not None:
            self.body.velocity = self._locked_velocity
            self._locked_velocity = None

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, asset_mgr: AssetManager, alpha: float = 1.0, view_w: float = 320.0, view_h: float = 208.0) -> None:
        ix, iy, iangle = self.get_interpolated_pose(alpha)
        if ix + self.radius < cam_x - TILE_SIZE or ix - self.radius > cam_x + view_w + TILE_SIZE:
            return
        if iy + self.radius < cam_y - TILE_SIZE or iy - self.radius > cam_y + view_h + TILE_SIZE:
            return
        sprite = asset_mgr.get_sprite("tiles", "rock")
        angle_deg = math.degrees(iangle)
        rotated = pygame.transform.rotate(sprite, -angle_deg)
        rx = int(ix - cam_x)
        ry = int(iy - cam_y)
        rect = rotated.get_rect(center=(rx, ry))
        surface.blit(rotated, rect)

class CabinEntity:
    def __init__(self, cabin_id: str, tx: int, ty: int) -> None:
        self.cabin_id = cabin_id
        self.tx = tx
        self.ty = ty
        self.x = tx * TILE_SIZE + TILE_SIZE / 2.0
        self.y = ty * TILE_SIZE + TILE_SIZE / 2.0
        self.w = 26.0
        self.h = 24.0
        self.activated = False

    def is_near(self, px: float, py: float) -> bool:
        return abs(self.x - px) <= 22.0 and abs(self.y - py) <= 22.0

    def activate(self, emit_particles, camera) -> None:
        self.activated = True
        camera.add_shake(2.0, 8)
        emit_particles(
            self.x, self.y - 4.0,
            [(255, 215, 60), (255, 240, 180), (180, 140, 90)],
            20
        )

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        rx = int(self.x - self.w / 2.0 - cam_x)
        ry = int(self.y - self.h / 2.0 - cam_y)
        if rx + self.w < -TILE_SIZE or rx > CANVAS_W + TILE_SIZE:
            return
        if ry + self.h < -TILE_SIZE or ry > CANVAS_H + TILE_SIZE:
            return

        pygame.draw.rect(surface, (70, 42, 24), (rx, ry + 8, int(self.w), int(self.h - 8)), border_radius=2)
        pygame.draw.polygon(surface, (120, 60, 30), [
            (rx - 2, ry + 9),
            (rx + int(self.w // 2), ry),
            (rx + int(self.w) + 2, ry + 9)
        ])
        door_col = (40, 25, 15) if not self.activated else (90, 60, 30)
        pygame.draw.rect(surface, door_col, (rx + 8, ry + 12, 10, 12), border_radius=1)
        lantern_col = (255, 230, 100) if self.activated else (160, 140, 80)
        pygame.draw.circle(surface, lantern_col, (rx + 4, ry + 14), 2)

class Player:
    def __init__(self, x: float, y: float, skin_id: str, space: pymunk.Space) -> None:
        self.skin_id = skin_id

        self.w = PLAYER_BODY_W
        self.h = PLAYER_BODY_H
        self.offset_x = 14
        self.offset_y = 12

        self.is_dead = False
        self.death_reason = ""
        self.facing_right = True
        self.is_digging = False
        self.is_climbing = False
        self.climb_anchor_point: tuple[float, float] | None = None
        self.dig_timer = 0
        self.climb_tick = 0
        self.anim_tick = 0
        self.anim_time = 0.0
        self.climb_time = 0.0
        self.dig_time = 0.0
        self.dig_duration = 0.2
        self.on_ground = False
        self.on_wall_l = False
        self.on_wall_r = False

        self.health = 100.0
        self.stamina = 100.0
        self.prev_vy = 0.0

        mass = 5.0
        self.body = pymunk.Body(mass, float('inf'))
        self.body.position = (x, y)
        self.prev_x = float(x)
        self.prev_y = float(y)
        self.shape = pymunk.Poly.create_box(self.body, (self.w, self.h))
        self.shape.friction = 0.0
        self.shape.elasticity = 0.0
        self.shape.collision_type = 3
        space.add(self.body, self.shape)

    def save_previous_state(self) -> None:
        self.prev_x = float(self.body.position.x)
        self.prev_y = float(self.body.position.y)

    def get_interpolated_pos(self, alpha: float) -> tuple[float, float]:
        alpha = max(0.0, min(1.0, alpha))
        ix = self.prev_x * (1.0 - alpha) + self.body.position.x * alpha
        iy = self.prev_y * (1.0 - alpha) + self.body.position.y * alpha
        return ix, iy

    def check_climb_anchor(self, space: pymunk.Space) -> bool:
        start_x = self.body.position.x
        start_y = self.body.position.y - 2.0
        reach = (self.w / 2.0) + 8.0
        direction = 1.0 if self.facing_right else -1.0
        end_x = start_x + direction * reach
        end_y = start_y
        hits = space.segment_query(
            (start_x, start_y),
            (end_x, end_y),
            1.0,
            pymunk.ShapeFilter()
        )
        for hit in hits:
            if hit.shape != self.shape and not getattr(hit.shape, "sensor", False):
                self.climb_anchor_point = (hit.point.x, hit.point.y)
                return True
        self.climb_anchor_point = None
        return False

    def get_dig_sensor_bounds(self, dir_x: int, dir_y: int) -> tuple[float, float, float, float]:
        cx = self.body.position.x
        cy = self.body.position.y
        hw = self.w / 2.0
        hh = self.h / 2.0
        reach_x = hw + 8.0
        reach_y = hh + 8.0
        if dir_y > 0:
            return (cx - hw, cy + hh, cx + hw, cy + reach_y)
        elif dir_y < 0:
            return (cx - hw, cy - reach_y, cx + hw, cy - hh)
        elif dir_x > 0:
            return (cx + hw, cy - hh, cx + reach_x, cy + hh)
        else:
            return (cx - reach_x, cy - hh, cx - hw, cy + hh)

    def _get_current_frame_key(self) -> str:
        if self.is_climbing:
            f_idx = int(self.climb_time / 0.1) % 4
            return f"climb_{f_idx}"
        if self.is_digging:
            progress = min(1.0, max(0.0, 1.0 - (self.dig_time / max(0.001, self.dig_duration))))
            f_idx = min(3, int(progress * 4))
            return f"dig_{f_idx}"
        if not self.on_ground:
            return "jump" if self.body.velocity.y < 0 else "fall"
        if abs(self.body.velocity.x) > 10.0:
            f_idx = int(self.anim_time / 0.08) % 8
            return f"walk_{f_idx}"
        f_idx = int(self.anim_time / 0.35) % 2
        return f"idle_{f_idx}"

    def update(self, up: bool, down: bool, left: bool, right: bool, jump: bool, climb_held: bool, dt: float, space: pymunk.Space, particle_emitter, camera) -> None:
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

        move_axis = 0.0
        if left:
            move_axis -= 1.0
        if right:
            move_axis += 1.0

        if move_axis > 0:
            self.facing_right = True
        elif move_axis < 0:
            self.facing_right = False

        has_anchor = self.check_climb_anchor(space) if (climb_held or self.is_climbing) else False
        on_wall = (self.on_wall_l and not self.facing_right) or (self.on_wall_r and self.facing_right) or (self.on_wall_l and left) or (self.on_wall_r and right) or has_anchor
        self.is_climbing = on_wall and climb_held and self.stamina > 0 and not on_ceiling and not self.on_ground

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
            if climb_held and self.stamina > 0 and not on_ceiling:
                if up:
                    self.body.velocity = (self.body.velocity.x, -80.0)
                    self.stamina = max(0.0, self.stamina - 30.0 * dt)
                    self.climb_time += dt
                    self.climb_tick = int(self.climb_time * 60)
                elif down:
                    self.body.velocity = (self.body.velocity.x, 60.0)
                    self.climb_time += dt
                    self.climb_tick = int(self.climb_time * 60)
                else:
                    self.body.velocity = (self.body.velocity.x, 0.0)
                    self.stamina = max(0.0, self.stamina - 5.0 * dt)
            elif not self.on_ground and self.body.velocity.y > 0:
                self.body.velocity = (self.body.velocity.x, self.body.velocity.y * 0.8)

        self.anim_time += dt
        self.anim_tick = int(self.anim_time * 60)
        if self.is_climbing:
            self.is_digging = False
            self.dig_time = 0.0
            self.dig_timer = 0
        elif self.dig_time > 0.0:
            self.dig_time = max(0.0, self.dig_time - dt)
            self.dig_timer = int(self.dig_time * 60)
            self.is_digging = True
        else:
            self.is_digging = False

        self.prev_vy = self.body.velocity.y

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, asset_mgr: AssetManager, alpha: float = 1.0) -> None:
        if self.is_dead:
            return
        skin_bundle = f"player_{self.skin_id}"
        frame_key = self._get_current_frame_key()
        sprite = asset_mgr.get_sprite(skin_bundle, frame_key)

        ox = self.offset_x
        oy = self.offset_y

        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
            ox = sprite.get_width() - ox

        ix, iy = self.get_interpolated_pos(alpha)
        rx = int(ix - cam_x) - ox
        ry = int(iy - cam_y) - oy
        surface.blit(sprite, (rx, ry))
