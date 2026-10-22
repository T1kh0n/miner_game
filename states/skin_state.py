import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_TEXT, COLOR_GOLD, SKIN_PALETTES
from core.localization import LocalizationManager
from engine.ui import UIPanel, UIButton, UILabel, UINode
from engine.asset_manager import AssetManager
from states.state_machine import State

class SkinState(State):
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.loc = LocalizationManager.get()
        self.font_large = self.loc.get_font(22)
        self.font_med = self.loc.get_font(18)
        self.skin_keys = list(SKIN_PALETTES.keys())
        self.current_idx = 0

        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 200, 170)
        self.root.add_child(self.panel)

        self.title_lbl = UILabel(0.5, 0.12, self.loc.get_text("skin_title", "SELECT EQUIPMENT"), self.font_large, COLOR_GOLD)
        self.panel.add_child(self.title_lbl)

        self.lbl_name = UILabel(0.5, 0.65, "", self.font_med, COLOR_TEXT)
        self.panel.add_child(self.lbl_name)

        self.panel.add_child(UIButton(0.15, 0.45, 24, 24, "<", self.font_med, self._prev))
        self.panel.add_child(UIButton(0.85, 0.45, 24, 24, ">", self.font_med, self._next))
        self.btn_back = UIButton(0.5, 0.85, 100, 22, self.loc.get_text("btn_back", "BACK"), self.font_med, lambda: self.manager.change("menu"))
        self.panel.add_child(self.btn_back)

        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))
        self.loc.subscribe(self._refresh_strings)

    def _refresh_strings(self) -> None:
        self.title_lbl.set_text(self.loc.get_text("skin_title", "SELECT EQUIPMENT"))
        self.btn_back.set_text(self.loc.get_text("btn_back", "BACK"))
        self._update_label()

    def enter(self) -> None:
        self._refresh_strings()

    def _prev(self) -> None:
        self.current_idx = (self.current_idx - 1) % len(self.skin_keys)
        self._update_label()

    def _next(self) -> None:
        self.current_idx = (self.current_idx + 1) % len(self.skin_keys)
        self._update_label()

    def _update_label(self) -> None:
        selected = self.skin_keys[self.current_idx]
        self.lbl_name.set_text(self.loc.get_text(f"skin_{selected}", selected.upper()))
        self.manager.selected_skin = selected

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 30))
        self.root.render(surface)
        skin = self.skin_keys[self.current_idx]
        sprite = AssetManager.get().get_sprite(f"player_{skin}", "idle_0")
        big = pygame.transform.scale2x(sprite)
        surface.blit(big, big.get_rect(center=(CANVAS_W // 2, CANVAS_H // 2 - 12)))
