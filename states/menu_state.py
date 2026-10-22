import os
import math
import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_GOLD, COLOR_TEXT
from core.localization import LocalizationManager
from core.save_system import SaveManager
from core.audio import AudioManager
from engine.asset_manager import AssetManager
from engine.ui import UIPanel, UIButton, UILabel, UINode
from states.state_machine import State


class MenuState(State):
    """Post-apocalyptic Metro bunker styled main menu."""

    def __init__(self, manager) -> None:
        """Initialise UI tree, atmospheric background layers, and layout."""
        super().__init__(manager)
        self.loc = LocalizationManager.get()
        self.save_manager = SaveManager()
        self.font_large = self.loc.get_font(22)
        self.font_med = self.loc.get_font(15)
        self.font_small = self.loc.get_font(13)

        self.time = 0.0
        self.cat_frame_idx = 0
        self.cat_anim_timer = 0.0

        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.52, 172, 160, border_color=(75, 82, 98), bg_color=(18, 22, 28))
        self.root.add_child(self.panel)

        self.title_lbl = UILabel(0.5, 0.08, self.loc.get_text("menu_title", "MINER DIGGER"), self.font_large, COLOR_GOLD)
        self.panel.add_child(self.title_lbl)

        self.btn_continue = UIButton(0.5, 0.23, 140, 17, self.loc.get_text("menu_continue", "CONTINUE"), self.font_med, self._continue_game)
        self.panel.add_child(self.btn_continue)

        self.btn_play = UIButton(0.5, 0.38, 140, 17, self.loc.get_text("menu_play", "PLAY"), self.font_med, self._new_game)
        self.panel.add_child(self.btn_play)

        self.btn_skin = UIButton(0.5, 0.53, 140, 17, self.loc.get_text("menu_skins", "SKINS"), self.font_med, lambda: self.manager.change("skin"))
        self.panel.add_child(self.btn_skin)

        self.btn_lead = UIButton(0.5, 0.68, 140, 17, self.loc.get_text("menu_leaderboard", "LEADERBOARD"), self.font_med, lambda: self.manager.change("leaderboard"))
        self.panel.add_child(self.btn_lead)

        self.btn_lang = UIButton(0.5, 0.82, 140, 17, self.loc.get_text("ui_lang", "LANG: EN"), self.font_small, self._toggle_lang)
        self.panel.add_child(self.btn_lang)

        self.btn_quit = UIButton(0.5, 0.94, 140, 17, self.loc.get_text("menu_quit", "QUIT"), self.font_small, self._quit)
        self.panel.add_child(self.btn_quit)

        self.bg_surf = self._create_metro_skyline()
        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))
        self.loc.subscribe(self._refresh_strings)

    def _create_metro_skyline(self) -> pygame.Surface:
        """Pre-render post-apocalyptic Soviet panel buildings and dusk skyline."""
        surf = pygame.Surface((CANVAS_W, CANVAS_H))
        for y in range(CANVAS_H):
            t = y / CANVAS_H
            r = int(14 + 18 * t)
            g = int(18 + 24 * t)
            b = int(26 + 32 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (CANVAS_W, y))

        building_specs = [
            (0, 28, 38), (32, 22, 44), (70, 34, 40), (105, 18, 50),
            (150, 26, 42), (188, 36, 38), (220, 20, 48), (262, 30, 44), (298, 24, 42)
        ]
        bldg_col = (20, 24, 32)
        window_on = (235, 205, 110)
        window_dim = (65, 75, 90)

        for bx, bw, bh in building_specs:
            by = 100 - bh
            pygame.draw.rect(surf, bldg_col, (bx, by, bw, bh + 80))
            pygame.draw.line(surf, (45, 52, 65), (bx + bw // 2, by - 6), (bx + bw // 2, by), 1)
            for wy in range(by + 4, 100, 7):
                for wx in range(bx + 3, bx + bw - 4, 6):
                    wcol = window_on if (wx * 7 + wy * 13) % 5 == 0 else window_dim
                    pygame.draw.rect(surf, wcol, (wx, wy, 2, 3))

        pygame.draw.rect(surf, (16, 18, 22), (0, 100, CANVAS_W, 80))
        for track_x in range(0, CANVAS_W, 14):
            pygame.draw.rect(surf, (48, 38, 32), (track_x, 155, 10, 4))
        pygame.draw.line(surf, (85, 92, 105), (0, 153), (CANVAS_W, 153), 1)
        pygame.draw.line(surf, (85, 92, 105), (0, 160), (CANVAS_W, 160), 1)

        tunnel_arch_col = (10, 12, 16)
        pygame.draw.rect(surf, tunnel_arch_col, (0, 0, 16, CANVAS_H))
        pygame.draw.rect(surf, tunnel_arch_col, (CANVAS_W - 16, 0, 16, CANVAS_H))
        pygame.draw.rect(surf, tunnel_arch_col, (0, 0, CANVAS_W, 10))

        return surf

    def _continue_game(self) -> None:
        """Resume expedition from last saved cabin checkpoint."""
        setattr(self.manager, "load_saved_checkpoint", True)
        self.manager.change("play")

    def _new_game(self) -> None:
        """Start a fresh mining expedition from surface spawn."""
        setattr(self.manager, "load_saved_checkpoint", False)
        self.manager.change("play")

    def _toggle_lang(self) -> None:
        """Toggle active language between EN and RU."""
        self.loc.toggle_locale()

    def _refresh_strings(self) -> None:
        """Update localized strings on all button labels."""
        self.title_lbl.set_text(self.loc.get_text("menu_title", "MINER DIGGER"))
        self.btn_continue.set_text(self.loc.get_text("menu_continue", "CONTINUE"))
        self.btn_play.set_text(self.loc.get_text("menu_play", "PLAY"))
        self.btn_skin.set_text(self.loc.get_text("menu_skins", "SKINS"))
        self.btn_lead.set_text(self.loc.get_text("menu_leaderboard", "LEADERBOARD"))
        self.btn_lang.set_text(self.loc.get_text("ui_lang", "LANG: EN"))
        self.btn_quit.set_text(self.loc.get_text("menu_quit", "QUIT"))

    def enter(self) -> None:
        """Check existing save slots and update continue button status."""
        has_save = self.save_manager.slot_exists(1) or self.save_manager.slot_exists(0)
        self.btn_continue.visible = has_save
        self._refresh_strings()
        AudioManager.get().initialize()

    def _quit(self) -> None:
        """Post SDL quit event to gracefully exit game."""
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        """Route UI events through UINode tree."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def update(self, dt: float) -> None:
        """Advance menu ambient timers and cat breathing cycle."""
        self.time += dt
        self.cat_anim_timer += dt
        if self.cat_anim_timer >= 0.25:
            self.cat_anim_timer = 0.0
            self.cat_frame_idx = (self.cat_frame_idx + 1) % 4

    def render(self, surface: pygame.Surface) -> None:
        """Draw atmospheric metro scene, flickering bulb, cat miner, and UI."""
        surface.blit(self.bg_surf, (0, 0))

        am = AssetManager.get()
        try:
            cat_sprite = am.get_sprite("cat_miner", f"idle_{self.cat_frame_idx}")
            surface.blit(cat_sprite, (22, 132))
            headlamp_x, headlamp_y = 44, 142
            cone_w, cone_h = 40, 16
            glow_surf = pygame.Surface((cone_w, cone_h), pygame.SRCALPHA)
            pygame.draw.polygon(glow_surf, (255, 240, 180, 45), [(0, 8), (cone_w, 0), (cone_w, cone_h)])
            surface.blit(glow_surf, (headlamp_x, headlamp_y - 8))
        except Exception:
            pass

        bulb_x = 284
        bulb_sway = int(math.sin(self.time * 2.0) * 2.0)
        bx = bulb_x + bulb_sway
        pygame.draw.line(surface, (60, 65, 75), (bulb_x, 0), (bx, 20), 1)
        pygame.draw.rect(surface, (50, 45, 40), (bx - 2, 20, 5, 4))
        flicker = 0.85 + 0.15 * math.sin(self.time * 9.0)
        bulb_alpha = int(40 * flicker)
        glow_rad = 22
        glow_bulb = pygame.Surface((glow_rad * 2, glow_rad * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_bulb, (255, 220, 110, bulb_alpha), (glow_rad, glow_rad), glow_rad)
        surface.blit(glow_bulb, (bx - glow_rad, 24 - glow_rad))
        pygame.draw.circle(surface, (255, 240, 160), (bx, 24), 3)

        self.root.render(surface)
