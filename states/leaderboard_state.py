import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_TEXT, COLOR_GOLD
from core.localization import LocalizationManager
from engine.ui import UIPanel, UIButton, UILabel, UINode
from states.state_machine import State

class LeaderboardState(State):
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.loc = LocalizationManager.get()
        self.font_large = self.loc.get_font(22)
        self.font_small = self.loc.get_font(15)

        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 230, 166)
        self.root.add_child(self.panel)

        self.title_lbl = UILabel(0.5, 0.1, self.loc.get_text("leaderboard_title", "HALL OF FAME"), self.font_large, COLOR_GOLD)
        self.panel.add_child(self.title_lbl)

        self.btn_menu = UIButton(0.5, 0.88, 90, 18, self.loc.get_text("btn_menu", "MENU"), self.font_small, lambda: self.manager.change("menu"))
        self.panel.add_child(self.btn_menu)

        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))
        self.loc.subscribe(self._refresh_strings)

    def _refresh_strings(self) -> None:
        self.title_lbl.set_text(self.loc.get_text("leaderboard_title", "HALL OF FAME"))
        self.btn_menu.set_text(self.loc.get_text("btn_menu", "MENU"))

    def enter(self) -> None:
        self._refresh_strings()

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((16, 20, 28))
        self.root.render(surface)
        records = self.manager.leaderboard.entries
        start_y = CANVAS_H // 2 - 46
        for i, rec in enumerate(records[:5]):
            txt = self.font_small.render(f"{i+1}. {rec['skin'][:7]} | {rec['score']}pts | {rec['depth']}m", True, COLOR_TEXT)
            max_w = 200
            if txt.get_width() > max_w:
                scale = max_w / txt.get_width()
                txt = pygame.transform.smoothscale(txt, (int(txt.get_width() * scale), int(txt.get_height() * scale)))
            surface.blit(txt, (CANVAS_W // 2 - txt.get_width() // 2, start_y + i * 16))
