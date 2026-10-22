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


def test_all_gameplay_and_tool_localization_keys_exist():
    loc = LocalizationManager()
    keys = [
        "skin_classic", "skin_ruby", "skin_emerald", "skin_obsidian",
        "hint_tool_rope", "hint_tool_pickaxe",
        "hud_hook", "hud_rope", "hud_pickaxe",
        "death_fall", "death_cave_in", "soldier_warning",
    ]
    for locale in ("en", "ru"):
        loc.set_locale(locale)
        for k in keys:
            val = loc.get_text(k)
            assert val != k
            assert len(val) > 0

    loc.set_locale("ru")
    assert "feral cats" not in loc.get_text("soldier_warning")


def test_skin_state_localizes_skin_titles():
    from states.state_machine import StateMachine
    from states.skin_state import SkinState
    loc = LocalizationManager.get()
    loc.set_locale("en")
    sm = StateMachine()
    skin_state = SkinState(sm)
    skin_state.enter()
    assert skin_state.lbl_name.text == "CLASSIC"

    loc.set_locale("ru")
    assert skin_state.lbl_name.text == "КЛАССИКА"
    loc.set_locale("en")


def test_player_fall_death_localization():
    import pymunk
    from engine.entities import Player
    from core.camera import Camera
    loc = LocalizationManager.get()
    loc.set_locale("en")

    space = pymunk.Space()
    floor = pymunk.Segment(space.static_body, (50.0, 113.0), (150.0, 113.0), 2.0)
    space.add(floor)
    player = Player(100.0, 100.0, "miner", space)
    player.prev_vy = 500.0
    cam = Camera(320, 180)
    player.update(False, False, False, False, False, False, 0.016, space, lambda *_: None, cam)

    assert player.is_dead is True
    assert player.death_key == "death_fall"
    assert player.death_reason == "FELL TO DEATH"
