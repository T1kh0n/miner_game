import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from core.localization import LocalizationManager

def test_localization_manager_loading_and_fallback() -> None:
    loc = LocalizationManager()
    loc.set_locale("en")
    assert loc.get_text("menu_play") == "PLAY"
    assert loc.get_text("win_title") == "VICTORY!"
    assert loc.get_text("non_existent_key", "Fallback Value") == "Fallback Value"

    loc.set_locale("ru")
    assert loc.get_text("menu_play") == "ИГРАТЬ"
    assert loc.get_text("win_title") == "ПОБЕДА!"

def test_dynamic_switching_and_listeners() -> None:
    loc = LocalizationManager()
    notified = False

    def on_change():
        nonlocal notified
        notified = True

    loc.subscribe(on_change)
    loc.set_locale("ru")
    assert notified is True
    assert loc.current_locale == "ru"

    notified = False
    new_loc = loc.toggle_locale()
    assert new_loc == "en"
    assert notified is True
    assert loc.current_locale == "en"

def test_utf8_cyrillic_glyph_rendering() -> None:
    pygame.init()
    loc = LocalizationManager.get()
    font = loc.get_font(20)
    cyrillic_text = "Шахтёр: Копать и Карабкаться"
    surf = font.render(cyrillic_text, True, (255, 255, 255))
    assert surf.get_width() > 50
    assert surf.get_height() > 10
