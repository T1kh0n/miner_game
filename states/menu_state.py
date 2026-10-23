import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_GOLD
from core.localization import LocalizationManager
from engine.ui import UIPanel, UIButton, UILabel, UINode
from states.state_machine import State

class MenuState(State):
    def __init__(self, manager) -> None:
        super().__init__(manager)
        self.loc = LocalizationManager.get()
        self.font_large = self.loc.get_font(28)
        self.font_med = self.loc.get_font(18)

        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 180, 204)
        self.root.add_child(self.panel)

        self.title_lbl = UILabel(0.5, 0.10, self.loc.get_text("menu_title", "MINER DIGGER"), self.font_large, COLOR_GOLD)
        self.panel.add_child(self.title_lbl)

        self.btn_play = UIButton(0.5, 0.27, 134, 22, self.loc.get_text("menu_play", "PLAY"), self.font_med, lambda: self.manager.change("play"))
        self.panel.add_child(self.btn_play)

        self.btn_skin = UIButton(0.5, 0.42, 134, 22, self.loc.get_text("menu_skins", "SKINS"), self.font_med, lambda: self.manager.change("skin"))
        self.panel.add_child(self.btn_skin)

        self.btn_lead = UIButton(0.5, 0.57, 134, 22, self.loc.get_text("menu_leaderboard", "LEADERBOARD"), self.font_med, lambda: self.manager.change("leaderboard"))
        self.panel.add_child(self.btn_lead)

        self.btn_lang = UIButton(0.5, 0.72, 134, 22, self.loc.get_text("ui_lang", "LANG: EN"), self.font_med, self._toggle_lang)
        self.panel.add_child(self.btn_lang)

        self.btn_quit = UIButton(0.5, 0.87, 134, 22, self.loc.get_text("menu_quit", "QUIT"), self.font_med, self._quit)
        self.panel.add_child(self.btn_quit)

        self.bg_gradient = pygame.Surface((CANVAS_W, CANVAS_H))
        for y in range(CANVAS_H):
            t = y / CANVAS_H
            pygame.draw.line(self.bg_gradient, (int(32 - 20 * t), int(88 - 64 * t), int(100 - 68 * t)), (0, y), (CANVAS_W, y))

        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))
        self.loc.subscribe(self._refresh_strings)

    def _toggle_lang(self) -> None:
        self.loc.toggle_locale()

    def _refresh_strings(self) -> None:
        self.title_lbl.set_text(self.loc.get_text("menu_title", "MINER DIGGER"))
        self.btn_play.set_text(self.loc.get_text("menu_play", "PLAY"))
        self.btn_skin.set_text(self.loc.get_text("menu_skins", "SKINS"))
        self.btn_lead.set_text(self.loc.get_text("menu_leaderboard", "LEADERBOARD"))
        self.btn_lang.set_text(self.loc.get_text("ui_lang", "LANG: EN"))
        self.btn_quit.set_text(self.loc.get_text("menu_quit", "QUIT"))

    def _quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg_gradient, (0, 0))
        self.root.render(surface)
