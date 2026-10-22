import os
import pygame
from core.save_system import SaveManager, EngineSettingsDTO
from core.audio import AudioManager
from states.state_machine import StateMachine
from states.menu_state import MenuState
from states.settings_state import SettingsState

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

def test_settings_state_and_volume_configuration():
    pygame.init()
    pygame.display.set_mode((320, 240))

    sm = StateMachine()
    menu = MenuState(sm)
    settings_state = SettingsState(sm)

    sm.add_state("menu", menu)
    sm.add_state("settings", settings_state)
    sm.change("menu")

    assert sm.current_state == menu
    assert hasattr(menu, "btn_settings")

    menu.btn_settings.callback()
    assert sm.current_state == settings_state

    settings_state.settings.master_volume = 1.0
    settings_state.settings.music_volume = 0.8
    settings_state.settings.sfx_volume = 0.8

    settings_state._adjust_master(-0.1)
    assert round(settings_state.settings.master_volume, 1) == 0.9
    assert round(AudioManager.get().get_master_volume(), 1) == 0.9

    settings_state._adjust_music(0.1)
    assert round(settings_state.settings.music_volume, 1) == 0.9
    assert round(AudioManager.get().get_music_volume(), 1) == 0.9

    settings_state._adjust_sfx(-0.2)
    assert round(settings_state.settings.sfx_volume, 1) == 0.6
    assert round(AudioManager.get().get_sfx_volume(), 1) == 0.6

    init_loc = settings_state.settings.locale
    settings_state._toggle_locale()
    assert settings_state.settings.locale != init_loc
    settings_state._toggle_locale()
    assert settings_state.settings.locale == init_loc

    init_fs = settings_state.settings.fullscreen
    settings_state._toggle_fullscreen()
    assert settings_state.settings.fullscreen != init_fs

    settings_state._back()
    assert sm.current_state == menu

    saved = SaveManager().load_settings()
    assert round(saved.master_volume, 1) == 0.9
    assert round(saved.music_volume, 1) == 0.9
    assert round(saved.sfx_volume, 1) == 0.6
    assert saved.locale == settings_state.settings.locale
    assert saved.fullscreen == settings_state.settings.fullscreen

    render_surf = pygame.Surface((320, 240))
    settings_state.render(render_surf)
    settings_state.handle_event(pygame.event.Event(pygame.MOUSEMOTION), (100, 100))
    SaveManager().save_settings(EngineSettingsDTO())
    from core.localization import LocalizationManager
    LocalizationManager.get().set_locale("en")
