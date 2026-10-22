import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_TEXT, COLOR_GOLD
from core.localization import LocalizationManager
from core.save_system import SaveManager, EngineSettingsDTO
from core.audio import AudioManager
from engine.ui import UIPanel, UIButton, UILabel, UINode
from states.state_machine import State


class SettingsState(State):
    """Configuration menu for master, music, sfx volume, locale, and display mode."""

    def __init__(self, manager) -> None:
        """Initialise settings UI components and default configuration."""
        super().__init__(manager)
        self.loc = LocalizationManager.get()
        self.save_manager = SaveManager()
        self.settings: EngineSettingsDTO = self.save_manager.load_settings()

        self.font_large = self.loc.get_font(20)
        self.font_med = self.loc.get_font(13)
        self.font_small = self.loc.get_font(11)

        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 230, 204, border_color=(75, 82, 98), bg_color=(18, 22, 28))
        self.root.add_child(self.panel)

        self.title_lbl = UILabel(0.5, 0.08, self.loc.get_text("menu_settings", "SETTINGS"), self.font_large, COLOR_GOLD)
        self.panel.add_child(self.title_lbl)

        self.lbl_master = UILabel(0.38, 0.22, "", self.font_med, COLOR_TEXT)
        self.panel.add_child(self.lbl_master)
        self.btn_master_dec = UIButton(0.72, 0.22, 20, 16, "<", self.font_med, lambda: self._adjust_master(-0.1))
        self.btn_master_inc = UIButton(0.86, 0.22, 20, 16, ">", self.font_med, lambda: self._adjust_master(0.1))
        self.panel.add_child(self.btn_master_dec)
        self.panel.add_child(self.btn_master_inc)

        self.lbl_music = UILabel(0.38, 0.36, "", self.font_med, COLOR_TEXT)
        self.panel.add_child(self.lbl_music)
        self.btn_music_dec = UIButton(0.72, 0.36, 20, 16, "<", self.font_med, lambda: self._adjust_music(-0.1))
        self.btn_music_inc = UIButton(0.86, 0.36, 20, 16, ">", self.font_med, lambda: self._adjust_music(0.1))
        self.panel.add_child(self.btn_music_dec)
        self.panel.add_child(self.btn_music_inc)

        self.lbl_sfx = UILabel(0.38, 0.50, "", self.font_med, COLOR_TEXT)
        self.panel.add_child(self.lbl_sfx)
        self.btn_sfx_dec = UIButton(0.72, 0.50, 20, 16, "<", self.font_med, lambda: self._adjust_sfx(-0.1))
        self.btn_sfx_inc = UIButton(0.86, 0.50, 20, 16, ">", self.font_med, lambda: self._adjust_sfx(0.1))
        self.panel.add_child(self.btn_sfx_dec)
        self.panel.add_child(self.btn_sfx_inc)

        self.btn_locale = UIButton(0.5, 0.64, 170, 17, "", self.font_med, self._toggle_locale)
        self.panel.add_child(self.btn_locale)

        self.btn_fullscreen = UIButton(0.5, 0.78, 170, 17, "", self.font_med, self._toggle_fullscreen)
        self.panel.add_child(self.btn_fullscreen)

        self.btn_back = UIButton(0.5, 0.92, 110, 18, self.loc.get_text("btn_back", "BACK"), self.font_med, self._back)
        self.panel.add_child(self.btn_back)

        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))
        self.loc.subscribe(self._refresh_strings)
        self._update_all_labels()

    def _adjust_master(self, delta: float) -> None:
        """Adjust master volume level within bounds."""
        self.settings.master_volume = round(max(0.0, min(1.0, self.settings.master_volume + delta)), 1)
        AudioManager.get().set_master_volume(self.settings.master_volume)
        self.save_manager.save_settings(self.settings)
        self._update_all_labels()

    def _adjust_music(self, delta: float) -> None:
        """Adjust music volume level within bounds."""
        self.settings.music_volume = round(max(0.0, min(1.0, self.settings.music_volume + delta)), 1)
        AudioManager.get().set_music_volume(self.settings.music_volume)
        self.save_manager.save_settings(self.settings)
        self._update_all_labels()

    def _adjust_sfx(self, delta: float) -> None:
        """Adjust sound effect volume level within bounds."""
        self.settings.sfx_volume = round(max(0.0, min(1.0, self.settings.sfx_volume + delta)), 1)
        AudioManager.get().set_sfx_volume(self.settings.sfx_volume)
        self.save_manager.save_settings(self.settings)
        self._update_all_labels()

    def _toggle_locale(self) -> None:
        """Switch active language between Russian and English."""
        new_loc = "ru" if self.settings.locale == "en" else "en"
        self.settings.locale = new_loc
        self.loc.set_locale(new_loc)
        self.save_manager.save_settings(self.settings)
        self._refresh_strings()

    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen display configuration flag."""
        self.settings.fullscreen = not self.settings.fullscreen
        self.save_manager.save_settings(self.settings)
        app = getattr(self.manager, "app", None)
        if app is not None and hasattr(app, "toggle_fullscreen"):
            app.toggle_fullscreen()
        self._update_all_labels()

    def _back(self) -> None:
        """Persist settings and return to previous state or main menu."""
        self.save_manager.save_settings(self.settings)
        self.manager.change("menu")

    def enter(self) -> None:
        """Load persistent settings and synchronize audio and strings."""
        self.settings = self.save_manager.load_settings()
        AudioManager.get().set_master_volume(self.settings.master_volume)
        AudioManager.get().set_music_volume(self.settings.music_volume)
        AudioManager.get().set_sfx_volume(self.settings.sfx_volume)
        self._refresh_strings()

    def _refresh_strings(self) -> None:
        """Update localized text across settings controls."""
        self.title_lbl.set_text(self.loc.get_text("menu_settings", "SETTINGS"))
        self.btn_back.set_text(self.loc.get_text("btn_back", "BACK"))
        self._update_all_labels()

    def _update_all_labels(self) -> None:
        """Format and update numeric percentage displays for audio settings."""
        master_pct = int(round(self.settings.master_volume * 100))
        music_pct = int(round(self.settings.music_volume * 100))
        sfx_pct = int(round(self.settings.sfx_volume * 100))
        master_str = self.loc.get_text("settings_master", "MASTER")
        music_str = self.loc.get_text("settings_music", "MUSIC")
        sfx_str = self.loc.get_text("settings_sfx", "SFX")
        self.lbl_master.set_text(f"{master_str}: {master_pct}%")
        self.lbl_music.set_text(f"{music_str}: {music_pct}%")
        self.lbl_sfx.set_text(f"{sfx_str}: {sfx_pct}%")

        cur_lang = self.settings.locale.upper()
        self.btn_locale.set_text(self.loc.get_text("ui_lang", f"LANG: {cur_lang}"))

        fs_key = "settings_fullscreen"
        fs_str = self.loc.get_text(fs_key, "FULLSCREEN")
        on_off = self.loc.get_text("settings_on", "ON") if self.settings.fullscreen else self.loc.get_text("settings_off", "OFF")
        self.btn_fullscreen.set_text(f"{fs_str}: {on_off}")

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple[int, int]) -> None:
        """Dispatch input events to UI tree."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def update(self, dt: float) -> None:
        """Advance timers."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        """Draw settings menu background and controls."""
        surface.fill((18, 22, 30))
        self.root.render(surface)
