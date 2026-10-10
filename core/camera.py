import random
from core.config import CANVAS_W, CANVAS_H, PANEL_HEIGHT

class Camera:
    def __init__(self, world_w, world_h):
        self.world_w = world_w
        self.world_h = world_h
        self.x = 0.0
        self.y = 0.0
        self.shake_time = 0
        self.shake_strength = 0.0
        self.current_lead_x = 0.0
        self.current_lead_y = 0.0

    def add_shake(self, strength, duration):
        self.shake_strength = max(self.shake_strength, min(4.0, strength * 0.3))
        self.shake_time = max(self.shake_time, min(15, duration))

    def update(self, target_x, target_y, facing_right, moving_down):
        view_w = CANVAS_W
        view_h = CANVAS_H - PANEL_HEIGHT

        target_lead_x = 10.0 if facing_right else -10.0
        target_lead_y = 12.0 if moving_down else 0.0

        self.current_lead_x += (target_lead_x - self.current_lead_x) * 0.05
        self.current_lead_y += (target_lead_y - self.current_lead_y) * 0.05

        desired_x = target_x - view_w / 2.0 + self.current_lead_x
        desired_y = target_y - view_h / 2.0 + self.current_lead_y

        max_x = max(0.0, self.world_w - view_w)
        max_y = max(0.0, self.world_h - view_h)

        desired_x = max(0.0, min(max_x, desired_x))
        desired_y = max(0.0, min(max_y, desired_y))

        self.x += (desired_x - self.x) * 0.08
        self.y += (desired_y - self.y) * 0.08

        final_x = self.x
        final_y = self.y

        if self.shake_time > 0:
            self.shake_time -= 1
            final_x += random.uniform(-self.shake_strength, self.shake_strength)
            final_y += random.uniform(-self.shake_strength, self.shake_strength)
            self.shake_strength *= 0.8

        return final_x, final_y
