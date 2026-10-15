import math
import random
from core.config import CANVAS_W, CANVAS_H, PANEL_HEIGHT

class Camera:
    """Sub-pixel smoothed camera with target leading and shake support."""

    def __init__(self, world_w: float, world_h: float) -> None:
        self.world_w = float(world_w)
        self.world_h = float(world_h)
        self.x = 0.0
        self.y = 0.0
        self.shake_time = 0.0
        self.shake_strength = 0.0
        self.current_lead_x = 0.0
        self.current_lead_y = 0.0

    def add_shake(self, strength: float, duration: float) -> None:
        self.shake_strength = max(self.shake_strength, min(4.0, strength * 0.3))
        self.shake_time = max(self.shake_time, float(min(15, duration)))

    def update(self, target_x: float, target_y: float, facing_right: bool, moving_down: bool, dt: float = 1.0 / 60.0) -> tuple[float, float]:
        view_w = CANVAS_W
        view_h = CANVAS_H - PANEL_HEIGHT

        target_lead_x = 10.0 if facing_right else -10.0
        target_lead_y = 12.0 if moving_down else 0.0

        lead_blend = 1.0 - math.exp(-5.0 * dt)
        self.current_lead_x += (target_lead_x - self.current_lead_x) * lead_blend
        self.current_lead_y += (target_lead_y - self.current_lead_y) * lead_blend

        desired_x = target_x - view_w / 2.0 + self.current_lead_x
        desired_y = target_y - view_h / 2.0 + self.current_lead_y

        max_x = max(0.0, self.world_w - view_w)
        max_y = max(0.0, self.world_h - view_h)

        desired_x = max(0.0, min(max_x, desired_x))
        desired_y = max(0.0, min(max_y, desired_y))

        cam_blend = 1.0 - math.exp(-8.0 * dt)
        self.x += (desired_x - self.x) * cam_blend
        self.y += (desired_y - self.y) * cam_blend

        final_x = self.x
        final_y = self.y

        if self.shake_time > 0.0:
            self.shake_time -= dt * 60.0
            final_x += random.uniform(-self.shake_strength, self.shake_strength)
            final_y += random.uniform(-self.shake_strength, self.shake_strength)
            self.shake_strength *= math.pow(0.8, dt * 60.0)

        return final_x, final_y
