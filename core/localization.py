import json
import os
import pygame
from typing import Callable

class LocalizationManager:
    _instance: "LocalizationManager | None" = None

    def __init__(self, base_path: str = "assets/localization") -> None:
        self.base_path = base_path
        self.current_locale = "en"
        self.translations: dict[str, dict[str, str]] = {}
        self._listeners: list[Callable[[], None]] = []
        self._font_cache: dict[int, pygame.font.Font] = {}
        self.load_all()

    @classmethod
    def get(cls) -> "LocalizationManager":
        if cls._instance is None:
            cls._instance = LocalizationManager()
        return cls._instance

    def load_all(self) -> None:
        for loc in ["en", "ru"]:
            path = os.path.join(self.base_path, f"{loc}.json")
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.translations[loc] = json.load(f)
                except Exception:
                    self.translations[loc] = {}
            else:
                self.translations[loc] = {}

    def subscribe(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def set_locale(self, locale: str) -> None:
        if locale not in ("en", "ru"):
            locale = "en"
        self.current_locale = locale
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                pass

    def toggle_locale(self) -> str:
        new_loc = "ru" if self.current_locale == "en" else "en"
        self.set_locale(new_loc)
        return new_loc

    def get_text(self, key: str, default: str | None = None, **kwargs) -> str:
        loc_table = self.translations.get(self.current_locale, {})
        val = loc_table.get(key)
        if val is None:
            en_table = self.translations.get("en", {})
            val = en_table.get(key, default if default is not None else key)
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return val

    def get_font(self, size: int) -> pygame.font.Font:
        if size in self._font_cache:
            return self._font_cache[size]

        font_candidates = ["dejavusans", "freesans", "liberationsans", "arial", "segoeui", "notosans"]
        chosen_font = None
        for name in font_candidates:
            try:
                sys_font = pygame.font.SysFont(name, size)
                test_str = "Шахтёр 123"
                if sys_font and sys_font.render(test_str, True, (255, 255, 255)).get_width() > 0:
                    chosen_font = sys_font
                    break
            except Exception:
                continue

        if chosen_font is None:
            chosen_font = pygame.font.Font(None, size)

        self._font_cache[size] = chosen_font
        return chosen_font
