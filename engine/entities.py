import pygame
import pymunk
import math
from core.config import (
    TILE_SIZE, CANVAS_W, CANVAS_H, CAT_FRAME_W, CAT_FRAME_H,
    CAT_BODY_W, CAT_BODY_H, ROPE_MAX_LENGTH,
)
from engine.asset_manager import AssetManager
from core.localization import LocalizationManager

PLAYER_BODY_W = CAT_BODY_W
PLAYER_BODY_H = CAT_BODY_H

_PARTICLE_SURF_CACHE: dict[tuple[int, int, int, int, int], pygame.Surface] = {}


def get_cached_particle_surface(color: tuple[int, int, int], alpha: int, size: int) -> pygame.Surface:
    """Return a cached circular particle surface to avoid per-frame allocation."""
    alpha_bin = max(0, min(255, (alpha // 16) * 16))
    key = (color[0], color[1], color[2], alpha_bin, size)
    surf = _PARTICLE_SURF_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, alpha_bin), (size, size), size)
        _PARTICLE_SURF_CACHE[key] = surf
    return surf


def calculate_sprite_hitbox(
    surf: pygame.Surface,
    target_w: float = 12.0,
    target_h: float = 26.0,
) -> tuple[float, float, float, float]:
    """Calculate (w, h, offset_x, offset_y) bounding box from sprite alpha mask."""
    mask = pygame.mask.from_surface(surf)
    rects = mask.get_bounding_rects()
    if not rects:
        return target_w, target_h, surf.get_width() / 2.0, surf.get_height() / 2.0
    union_rect = rects[0]
    for r in rects[1:]:
        union_rect.union_ip(r)
    h = min(target_h, float(union_rect.h))
    w = min(target_w, float(union_rect.w))
    offset_x = float(union_rect.centerx)
    offset_y = float(union_rect.bottom) - h / 2.0
    return w, h, offset_x, offset_y


class Particle:
    """Single pooled particle with linear velocity and lifetime."""

    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], life: int, size: int = 2) -> None:
        """Initialise particle fields."""
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.life = life
        self.max_life = max(1, life)
        self.size = size

    def update(self) -> None:
        """Advance position and decrement lifetime by one tick."""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def render(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw particle to surface using cached alpha surface."""
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            ps = get_cached_particle_surface(self.color, alpha, self.size)
            surf.blit(ps, (int(self.x - cam_x) - self.size, int(self.y - cam_y) - self.size))


class ParticlePool:
    """Pre-allocated ring-buffer particle pool for zero-allocation particle emission."""

    def __init__(self, capacity: int = 180) -> None:
        """Create a pool with a fixed capacity."""
        self.capacity = capacity
        self.particles = [Particle(0.0, 0.0, 0.0, 0.0, (255, 255, 255), 0) for _ in range(capacity)]
        self.next_idx = 0

    def spawn(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], life: int, size: int = 2) -> None:
        """Overwrite the next slot in the ring buffer with new particle data."""
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
        """Advance all live particles by one tick."""
        for p in self.particles:
            if p.life > 0:
                p.update()

    def render(self, surf: pygame.Surface, cam_x: float, cam_y: float, view_w: float, view_h: float) -> None:
        """Render all visible live particles with viewport culling."""
        min_x = cam_x - TILE_SIZE
        max_x = cam_x + view_w + TILE_SIZE
        min_y = cam_y - TILE_SIZE
        max_y = cam_y + view_h + TILE_SIZE
        for p in self.particles:
            if p.life > 0 and min_x <= p.x <= max_x and min_y <= p.y <= max_y:
                p.render(surf, cam_x, cam_y)


class RockEntity:
    """A dynamic rolling rock boulder driven by pymunk physics."""

    def __init__(self, tx: int, ty: int, space: pymunk.Space) -> None:
        """Place a rock entity at tile coordinates (tx, ty) and register with space."""
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
        self._locked_velocity: tuple[float, float] | None = None

    def save_previous_state(self) -> None:
        """Snapshot current position for interpolation."""
        self.prev_x = float(self.body.position.x)
        self.prev_y = float(self.body.position.y)
        self.prev_angle = float(self.body.angle)

    def get_interpolated_pose(self, alpha: float) -> tuple[float, float, float]:
        """Return linearly interpolated (x, y, angle) for sub-tick rendering."""
        alpha = max(0.0, min(1.0, alpha))
        ix = self.prev_x * (1.0 - alpha) + self.body.position.x * alpha
        iy = self.prev_y * (1.0 - alpha) + self.body.position.y * alpha
        iangle = self.prev_angle * (1.0 - alpha) + self.body.angle * alpha
        return ix, iy, iangle

    def lock_velocity(self) -> None:
        """Cache current velocity before a collision pre-solve step."""
        self._locked_velocity = (self.body.velocity.x, self.body.velocity.y)

    def restore_velocity(self) -> None:
        """Restore cached velocity after a collision post-solve step."""
        if self._locked_velocity is not None:
            self.body.velocity = self._locked_velocity
            self._locked_velocity = None

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, asset_mgr: AssetManager, alpha: float = 1.0, view_w: float = 320.0, view_h: float = 240.0) -> None:
        """Draw the rock sprite rotated to match the physics body angle."""
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
    """A checkpoint cabin entity rendered at a fixed world position."""

    def __init__(self, cabin_id: str, tx: int, ty: int) -> None:
        """Initialise cabin at tile coordinates (tx, ty)."""
        self.cabin_id = cabin_id
        self.tx = tx
        self.ty = ty
        self.x = tx * TILE_SIZE + TILE_SIZE / 2.0
        self.y = ty * TILE_SIZE + TILE_SIZE / 2.0
        self.w = 26.0
        self.h = 24.0
        self.activated = False

    def is_near(self, px: float, py: float) -> bool:
        """Return True if player centre (px, py) is within interaction radius."""
        return abs(self.x - px) <= 22.0 and abs(self.y - py) <= 22.0

    def activate(self, emit_particles, camera) -> None:
        """Activate cabin: spawn particles and camera shake."""
        self.activated = True
        camera.add_shake(2.0, 8)
        emit_particles(
            self.x, self.y - 4.0,
            [(255, 215, 60), (255, 240, 180), (180, 140, 90)],
            20
        )

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the cabin sprite with viewport culling."""
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


class HookEntity:
    """Grappling hook projectile with SlideJoint rope physics and pickaxe anchor."""

    MAX_SPEED = 280.0
    GRAVITY_ACCEL = 300.0

    def __init__(self, px: float, py: float, angle_rad: float, space: pymunk.Space, player_body: pymunk.Body) -> None:
        """Launch hook from position (px, py) along angle_rad."""
        self.x = px
        self.y = py
        self.vx = math.cos(angle_rad) * self.MAX_SPEED
        self.vy = math.sin(angle_rad) * self.MAX_SPEED
        self.space = space
        self.player_body = player_body
        self.joint: pymunk.SlideJoint | None = None
        self.attached = False
        self.attached_body: pymunk.Body | None = None
        self.age = 0.0
        self.dead = False
        self.travel_dist = 0.0

    def update(self, dt: float) -> None:
        """Advance the hook projectile and detect collisions via segment query."""
        if self.attached or self.dead:
            return
        self.age += dt
        prev_x, prev_y = self.x, self.y
        self.vy += self.GRAVITY_ACCEL * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.travel_dist += math.hypot(self.x - prev_x, self.y - prev_y)
        if self.travel_dist > ROPE_MAX_LENGTH:
            self.dead = True
            return
        hits = self.space.segment_query(
            (prev_x, prev_y), (self.x, self.y),
            1.0,
            pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
        )
        for hit in hits:
            if hit.shape is None:
                continue
            if hit.shape.body == self.player_body:
                continue
            self._attach(hit.shape.body, hit.point.x, hit.point.y)
            return

    def _attach(self, target_body: pymunk.Body, hx: float, hy: float) -> None:
        """Create a SlideJoint between player and target body at the hit point."""
        self.x = hx
        self.y = hy
        self.attached = True
        self.attached_body = target_body
        if target_body.body_type == pymunk.Body.DYNAMIC:
            target_body.activate()
        dist = math.hypot(
            self.player_body.position.x - hx,
            self.player_body.position.y - hy,
        )
        dist = max(4.0, min(dist, ROPE_MAX_LENGTH))
        self.joint = pymunk.SlideJoint(
            self.player_body, target_body,
            (0, 0),
            target_body.world_to_local((hx, hy)),
            min=0.0,
            max=dist,
        )
        self.space.add(self.joint)

    def retract(self) -> None:
        """Remove the joint and mark the hook as dead."""
        if self.joint is not None and self.joint in self.space.constraints:
            self.space.remove(self.joint)
            self.joint = None
        self.dead = True
        self.attached = False

    def shorten(self, amount: float) -> None:
        """Reduce the rope max length to simulate climbing up."""
        if self.joint is not None:
            new_max = max(8.0, self.joint.max - amount)
            self.joint.max = new_max

    def lengthen(self, amount: float) -> None:
        """Increase the rope max length to simulate sliding down."""
        if self.joint is not None:
            new_max = min(ROPE_MAX_LENGTH, self.joint.max + amount)
            self.joint.max = new_max

    def render_preview(
        self,
        surface: pygame.Surface,
        cam_x: float,
        cam_y: float,
        from_x: float,
        from_y: float,
        angle_rad: float,
    ) -> None:
        """Draw a dotted ballistic parabola preview arc for aiming."""
        steps = 16
        sim_vx = math.cos(angle_rad) * self.MAX_SPEED
        sim_vy = math.sin(angle_rad) * self.MAX_SPEED
        sim_x, sim_y = from_x, from_y
        dt_sim = 0.04
        prev_sx = int(sim_x - cam_x)
        prev_sy = int(sim_y - cam_y)
        for step in range(steps):
            sim_vy += self.GRAVITY_ACCEL * dt_sim
            sim_x += sim_vx * dt_sim
            sim_y += sim_vy * dt_sim
            sx = int(sim_x - cam_x)
            sy = int(sim_y - cam_y)
            if step % 2 == 0:
                pygame.draw.circle(surface, (200, 200, 140), (sx, sy), 1)
            prev_sx, prev_sy = sx, sy

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, from_x: float, from_y: float) -> None:
        """Draw the rope line with pickaxe projectile tip or anchor."""
        if self.dead:
            return
        hx = int(self.x - cam_x)
        hy = int(self.y - cam_y)
        fx = int(from_x - cam_x)
        fy = int(from_y - cam_y)
        pygame.draw.line(surface, (180, 148, 100), (fx, fy), (hx, hy), 1)
        if self.attached:
            ang = math.atan2(hy - fy, hx - fx)
            hx_tail = hx - int(math.cos(ang) * 6)
            hy_tail = hy - int(math.sin(ang) * 6)
            pygame.draw.line(surface, (130, 80, 40), (hx_tail, hy_tail), (hx, hy), 2)
            blade_dx = int(-math.sin(ang) * 4)
            blade_dy = int(math.cos(ang) * 4)
            pygame.draw.line(surface, (180, 190, 205), (hx - blade_dx, hy - blade_dy), (hx + blade_dx, hy + blade_dy), 2)
            pygame.draw.circle(surface, (235, 245, 255), (hx + blade_dx, hy + blade_dy), 1)
            pygame.draw.circle(surface, (220, 200, 140), (hx, hy), 2)
        else:
            ang = math.atan2(self.vy, self.vx)
            hx_tail = hx - int(math.cos(ang) * 6)
            hy_tail = hy - int(math.sin(ang) * 6)
            pygame.draw.line(surface, (130, 80, 40), (hx_tail, hy_tail), (hx, hy), 2)
            blade_dx = int(-math.sin(ang) * 4)
            blade_dy = int(math.cos(ang) * 4)
            pygame.draw.line(surface, (180, 190, 205), (hx - blade_dx, hy - blade_dy), (hx + blade_dx, hy + blade_dy), 2)
            pygame.draw.circle(surface, (235, 245, 255), (hx + blade_dx, hy + blade_dy), 1)


class Player:
    """Tabby Miner Cat player entity with pymunk physics, rope tool, and AFK system."""

    def __init__(self, x: float, y: float, skin_id: str, space: pymunk.Space, asset_mgr: AssetManager | None = None) -> None:
        """Initialise player at world position (x, y) with the given skin identifier."""
        self.skin_id = skin_id

        if asset_mgr is not None:
            try:
                idle_surf = asset_mgr.get_sprite(f"cat_{skin_id}", "idle_0")
                self.w, self.h, self.offset_x, self.offset_y = calculate_sprite_hitbox(
                    idle_surf, PLAYER_BODY_W, PLAYER_BODY_H
                )
            except Exception:
                try:
                    idle_surf = asset_mgr.get_sprite(f"player_{skin_id}", "idle_0")
                    self.w, self.h, self.offset_x, self.offset_y = calculate_sprite_hitbox(
                        idle_surf, PLAYER_BODY_W, PLAYER_BODY_H
                    )
                except Exception:
                    self.w = PLAYER_BODY_W
                    self.h = PLAYER_BODY_H
                    self.offset_x = CAT_FRAME_W / 2.0
                    self.offset_y = 21.0
        else:
            self.w = PLAYER_BODY_W
            self.h = PLAYER_BODY_H
            self.offset_x = CAT_FRAME_W / 2.0
            self.offset_y = 21.0

        self.is_dead = False
        self.death_reason = ""
        self.death_key = ""
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

        self.using_rope = False
        self.ropes = 3
        self.hook: HookEntity | None = None
        self.rope_angle = 0.0

        self.afk_timer = 0.0
        self.afk_phase = 0

        self._was_on_ground = False
        self._just_landed = False
        self._land_frame_timer = 0.0

        mass = 5.0
        self.body = pymunk.Body(mass, float("inf"))
        self.body.position = (x, y)
        self.prev_x = float(x)
        self.prev_y = float(y)
        self.shape = pymunk.Poly.create_box(self.body, (self.w, self.h))
        self.shape.friction = 0.0
        self.shape.elasticity = 0.0
        self.shape.collision_type = 3
        space.add(self.body, self.shape)

    def save_previous_state(self) -> None:
        """Snapshot position for interpolation."""
        self.prev_x = float(self.body.position.x)
        self.prev_y = float(self.body.position.y)

    def get_interpolated_pos(self, alpha: float) -> tuple[float, float]:
        """Return linearly interpolated world position for sub-tick rendering."""
        alpha = max(0.0, min(1.0, alpha))
        ix = self.prev_x * (1.0 - alpha) + self.body.position.x * alpha
        iy = self.prev_y * (1.0 - alpha) + self.body.position.y * alpha
        return ix, iy

    def check_climb_anchor(self, space: pymunk.Space) -> bool:
        """Raycast sideways to detect a climbable wall surface."""
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
        """Return world-space AABB for digging sensor in the given direction."""
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

    def get_flashlight_angle_rad(self, cursor_angle: float | None = None) -> float:
        """Return the flashlight beam angle based on cursor aim or facing direction."""
        if cursor_angle is not None:
            return cursor_angle
        if self.hook is not None and not self.hook.attached and not self.hook.dead:
            return self.rope_angle
        return 0.0 if self.facing_right else math.pi

    def _get_current_frame_key(self) -> str:
        """Determine the correct animation frame key from current player state."""
        if self.afk_phase >= 1:
            idx = min(5, self.afk_phase - 1)
            return f"afk_{idx}"
        if self._just_landed:
            return "land_0"
        if self.is_climbing:
            f_idx = int(self.climb_time / 0.1) % 4
            return f"climb_{f_idx}"
        if self.is_digging:
            progress = min(1.0, max(0.0, 1.0 - (self.dig_time / max(0.001, self.dig_duration))))
            f_idx = min(3, int(progress * 4))
            return f"action_{f_idx}"
        if not self.on_ground:
            return "jump_0" if self.body.velocity.y < 0 else "fall_0"
        if abs(self.body.velocity.x) > 80.0:
            f_idx = int(self.anim_time / 0.06) % 6
            return f"run_{f_idx}"
        if abs(self.body.velocity.x) > 10.0:
            f_idx = int(self.anim_time / 0.08) % 8
            return f"walk_{f_idx}"
        f_idx = int(self.anim_time / 0.35) % 4
        return f"idle_{f_idx}"

    def toggle_tool(self) -> None:
        """Switch between pickaxe and rope tool."""
        self.using_rope = not self.using_rope

    def fire_rope(self, space: pymunk.Space, angle_rad: float) -> None:
        """Launch a new grappling hook if one is not already active."""
        if self.hook is not None and not self.hook.dead:
            return
        self.rope_angle = angle_rad
        self.hook = HookEntity(
            self.body.position.x,
            self.body.position.y,
            angle_rad,
            space,
            self.body,
        )

    def retract_rope(self) -> None:
        """Retract and destroy the active hook."""
        if self.hook is not None:
            self.hook.retract()
            self.hook = None

    def update(
        self,
        up: bool,
        down: bool,
        left: bool,
        right: bool,
        jump: bool,
        climb_held: bool,
        dt: float,
        space: pymunk.Space,
        particle_emitter,
        camera,
        any_input: bool = False,
        afk_knock_seconds: float = 8.0,
        afk_blind_seconds: float = 14.0,
    ) -> None:
        """Update player physics, animation, rope, and AFK state for one fixed tick."""
        if self.is_dead:
            return

        if any_input:
            self.afk_timer = 0.0
            self.afk_phase = 0
        else:
            self.afk_timer += dt
            if self.afk_timer >= afk_blind_seconds:
                self.afk_phase = 4
            elif self.afk_timer >= afk_knock_seconds:
                self.afk_phase = 2
            else:
                self.afk_phase = 0

        self.on_ground = False
        self.on_wall_l = False
        self.on_wall_r = False
        on_ceiling = False

        for info in space.shape_query(self.shape):
            if info.shape == self.shape:
                continue
            if getattr(info.shape, "sensor", False):
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

        self._just_landed = (not self._was_on_ground and self.on_ground)
        if self._just_landed:
            self._land_frame_timer = 0.12
        else:
            self._land_frame_timer = max(0.0, self._land_frame_timer - dt)
        self._just_landed = self._land_frame_timer > 0.0
        self._was_on_ground = self.on_ground

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
                    self.death_key = "death_fall"
                    self.death_reason = LocalizationManager.get().get_text("death_fall", "FELL TO DEATH")
                    camera.add_shake(8.0, 20)
                    particle_emitter(self.body.position.x, self.body.position.y, [(255, 60, 60)], 25)

        if self.hook is not None:
            self.hook.update(dt)
            if self.hook.dead and not self.hook.attached:
                self.hook = None
            elif self.hook is not None and self.hook.attached:
                if up:
                    self.hook.shorten(65.0 * dt)
                    hx, hy = self.hook.x, self.hook.y
                    dx = hx - self.body.position.x
                    dy = hy - self.body.position.y
                    dlen = math.hypot(dx, dy)
                    if dlen > 1.0:
                        self.body.apply_force_at_local_point((dx / dlen * 180.0, dy / dlen * 180.0), (0.0, 0.0))
                if down:
                    self.hook.lengthen(65.0 * dt)
                if self.hook.attached_body is not None and self.hook.attached_body.body_type == pymunk.Body.DYNAMIC:
                    self.hook.attached_body.activate()

        if self.hook is not None and self.hook.attached:
            self.body.apply_force_at_local_point((move_axis * 350.0, 0.0), (0.0, 0.0))
            self.body.velocity = (self.body.velocity.x * 0.992, self.body.velocity.y * 0.995)
        else:
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
        """Draw the cat miner sprite at the interpolated screen position."""
        if self.is_dead:
            return
        bundle = f"cat_{self.skin_id}"
        frame_key = self._get_current_frame_key()

        try:
            sprite = asset_mgr.get_sprite(bundle, frame_key)
        except (KeyError, Exception):
            fallback_bundle = f"player_{self.skin_id}"
            try:
                sprite = asset_mgr.get_sprite(fallback_bundle, frame_key)
            except (KeyError, Exception):
                fallback_frame = "idle_0" if "idle" in frame_key else "walk_0"
                try:
                    sprite = asset_mgr.get_sprite(fallback_bundle, fallback_frame)
                except Exception:
                    return

        ox = self.offset_x
        oy = self.offset_y

        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
            ox = sprite.get_width() - ox

        ix, iy = self.get_interpolated_pos(alpha)
        rx = int(ix - cam_x) - int(ox)
        ry = int(iy - cam_y) - int(oy)
        surface.blit(sprite, (rx, ry))

        if self.hook is not None:
            self.hook.render(surface, cam_x, cam_y, ix, iy)


class DriverCatEntity:
    """Interactive NPC Train Driver Cat present at the metro station platform."""

    def __init__(self, x: float, y: float) -> None:
        """Initialise Train Driver Cat coordinates and dialogue state."""
        self.x: float = x
        self.y: float = y
        self.visible: bool = False
        self.has_spoken: bool = False
        self.facing_right: bool = True
        self.anim_state: str = "idle"
        self.anim_time: float = 0.0

    def update(self, dt: float) -> None:
        """Advance animation timer."""
        self.anim_time += dt

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, asset_mgr: AssetManager) -> None:
        """Draw the Train Driver Cat sprite if currently visible."""
        if not self.visible:
            return
        frame_idx = int(self.anim_time * 6.0) % 4
        key = f"{self.anim_state}_{frame_idx}"
        sprite = asset_mgr.get_sprite("cat_driver", key)
        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
        rx = int(self.x - cam_x) - sprite.get_width() // 2
        ry = int(self.y - cam_y) - int(sprite.get_height() * 0.75)
        surface.blit(sprite, (rx, ry))


class SoldierCatEntity:
    """Guarding ally cat in watermelon armor defending the lower barricade post."""

    STATE_GUARD_POST = "guard_post"
    STATE_PATROL = "patrol"
    STATE_DIALOGUE = "dialogue"
    STATE_COMBAT_DEFEND = "combat_defend"
    STATE_PINNED_DOWN = "pinned_down"
    STATE_ALLY_FOLLOW = "ally_follow"

    def __init__(self, x: float, y: float, min_x: float, max_x: float) -> None:
        """Initialise Soldier Cat coordinates, patrol bounds, and default state."""
        self.x: float = x
        self.y: float = y
        self.min_x: float = min_x
        self.max_x: float = max_x
        self.state: str = self.STATE_GUARD_POST
        self.anim_state: str = "idle"
        self.facing_right: bool = True
        self.speed: float = 35.0
        self.anim_time: float = 0.0

    def set_state(self, new_state: str) -> None:
        """Transition Soldier Cat FSM state and synchronise animation name."""
        self.state = new_state
        if new_state == self.STATE_GUARD_POST:
            self.anim_state = "idle"
        elif new_state == self.STATE_PATROL:
            self.anim_state = "walk"
        elif new_state == self.STATE_DIALOGUE:
            self.anim_state = "talk"
        elif new_state == self.STATE_COMBAT_DEFEND:
            self.anim_state = "action_shovel"
        elif new_state == self.STATE_PINNED_DOWN:
            self.anim_state = "pinned"
        elif new_state == self.STATE_ALLY_FOLLOW:
            self.anim_state = "walk"

    def update(self, dt: float) -> None:
        """Advance patrol movement and animation progression."""
        self.anim_time += dt
        if self.state == self.STATE_PATROL:
            if self.facing_right:
                self.x += self.speed * dt
                if self.x >= self.max_x:
                    self.x = self.max_x
                    self.facing_right = False
            else:
                self.x -= self.speed * dt
                if self.x <= self.min_x:
                    self.x = self.min_x
                    self.facing_right = True

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, asset_mgr: AssetManager) -> None:
        """Render Soldier Cat sprite with directional facing."""
        frame_idx = int(self.anim_time * 6.0) % 4
        key = f"{self.anim_state}_{frame_idx}"
        sprite = asset_mgr.get_sprite("cat_soldier", key)
        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
        rx = int(self.x - cam_x) - sprite.get_width() // 2
        ry = int(self.y - cam_y) - int(sprite.get_height() * 0.75)
        surface.blit(sprite, (rx, ry))


class FeralCatEntity:
    """Hostile agile mutated feline stalking the deep tunnels below the barricade."""

    STATE_STALK = "stalk"
    STATE_STUNNED = "stunned"
    STATE_HURT = "hurt"
    STATE_DEFEATED = "defeated"

    def __init__(self, x: float, y: float) -> None:
        """Initialise Feral Cat stats, health, and encounter flags."""
        self.x: float = x
        self.y: float = y
        self.hp: int = 3
        self.state: str = self.STATE_STALK
        self.anim_state: str = "idle"
        self.facing_right: bool = False
        self.stun_timer: float = 0.0
        self.invulnerable_timer: float = 0.0
        self.is_defeated: bool = False
        self.light_exposure_time: float = 0.0
        self.anim_time: float = 0.0

    def update(
        self,
        dt: float,
        target_x: float = 0.0,
        target_y: float = 0.0,
        is_illuminated: bool = False
    ) -> None:
        """Advance Feral Cat AI timers, flashlight stun tracking, and hurt recovery."""
        self.anim_time += dt
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)

        if is_illuminated and not self.is_defeated:
            self.light_exposure_time += dt
            if self.light_exposure_time >= 0.25:
                self.state = self.STATE_STUNNED
                self.stun_timer = 1.5
                self.anim_state = "hurt"
        else:
            self.light_exposure_time = max(0.0, self.light_exposure_time - dt)

        if self.stun_timer > 0.0:
            self.stun_timer = max(0.0, self.stun_timer - dt)
            if self.stun_timer <= 0.0 and not self.is_defeated:
                self.state = self.STATE_STALK
                self.anim_state = "idle"
        elif self.state == self.STATE_HURT and not self.is_defeated:
            if self.invulnerable_timer <= 0.0:
                self.state = self.STATE_STALK
                self.anim_state = "idle"

    def take_damage(self, amount: int, knockback_dir: float = 1.0) -> bool:
        """Apply damage to Feral Cat. Return True if defeated."""
        if self.invulnerable_timer > 0.0 or self.is_defeated:
            return self.is_defeated
        self.hp = max(0, self.hp - amount)
        self.invulnerable_timer = 0.4
        self.x += knockback_dir * 12.0
        if self.hp <= 0:
            self.is_defeated = True
            self.state = self.STATE_DEFEATED
            self.anim_state = "hurt"
            return True
        self.state = self.STATE_HURT
        self.anim_state = "hurt"
        return False

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float, asset_mgr: AssetManager) -> None:
        """Draw the Feral Cat sprite with current combat state animation."""
        frame_idx = int(self.anim_time * 8.0) % 4
        key = f"{self.anim_state}_{frame_idx}"
        sprite = asset_mgr.get_sprite("cat_feral", key)
        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
        rx = int(self.x - cam_x) - sprite.get_width() // 2
        ry = int(self.y - cam_y) - int(sprite.get_height() * 0.75)
        surface.blit(sprite, (rx, ry))

