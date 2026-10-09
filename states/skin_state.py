import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_TEXT, COLOR_GOLD, SKIN_PALETTES
from engine.ui import UIPanel, UIButton, UILabel, UINode
from engine.asset_manager import AssetManager
from states.state_machine import State

class SkinState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_large = pygame.font.Font(None, 28)
        self.font_med = pygame.font.Font(None, 18)
        self.skin_keys = list(SKIN_PALETTES.keys())
        self.current_idx = 0
        
        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 190, 170)
        self.root.add_child(self.panel)
        
        self.panel.add_child(UILabel(0.5, 0.12, "ВЫБОР ЭКИПИРОВКИ", self.font_large, COLOR_GOLD))
        self.lbl_name = UILabel(0.5, 0.65, "", self.font_med, COLOR_TEXT)
        self.panel.add_child(self.lbl_name)
        self.panel.add_child(UIButton(0.15, 0.45, 24, 24, "<", self.font_med, self._prev))
        self.panel.add_child(UIButton(0.85, 0.45, 24, 24, ">", self.font_med, self._next))
        self.panel.add_child(UIButton(0.5, 0.85, 100, 22, "НАЗАД", self.font_med, lambda: self.manager.change("menu")))
        
        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))

    def enter(self):
        self._update_label()

    def _prev(self):
        self.current_idx = (self.current_idx - 1) % len(self.skin_keys)
        self._update_label()

    def _next(self):
        self.current_idx = (self.current_idx + 1) % len(self.skin_keys)
        self._update_label()

    def _update_label(self):
        selected = self.skin_keys[self.current_idx]
        self.lbl_name.set_text(selected.upper())
        self.manager.selected_skin = selected

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def render(self, surface):
        surface.fill((18, 22, 30))
        self.root.render(surface)
        skin = self.skin_keys[self.current_idx]
        sprite = AssetManager.get().get_sprite(f"player_{skin}", "idle_0")
        big = pygame.transform.scale2x(sprite)
        surface.blit(big, big.get_rect(center=(CANVAS_W // 2, CANVAS_H // 2 - 12)))
