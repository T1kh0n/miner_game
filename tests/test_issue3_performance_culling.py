import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import tracemalloc
import pygame
import pymunk
from engine.asset_generator import AssetGenerator
from engine.asset_manager import AssetManager
from engine.entities import ParticlePool, RockEntity, get_cached_particle_surface
from states.play_state import PlayState
from states.state_machine import StateMachine

def test_particle_pool_allocation_free() -> None:
    pool = ParticlePool(50)
    orig_instances = list(pool.particles)

    for i in range(120):
        pool.spawn(float(i), float(i), 1.0, 1.0, (255, 200, 50), 30)

    assert list(pool.particles) == orig_instances

def test_particle_surface_cache_reuse() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    s1 = get_cached_particle_surface((255, 100, 50), 200, 2)
    s2 = get_cached_particle_surface((255, 100, 50), 205, 2)
    assert s1 is s2

def test_rock_frustum_culling() -> None:
    pygame.init()
    surf = pygame.Surface((320, 240))
    AssetGenerator.generate_all()

    space = pymunk.Space()
    rock_on = RockEntity(1, 1, space)
    rock_off = RockEntity(40, 100, space)

    mgr = AssetManager.get()
    rock_on.render(surf, 0.0, 0.0, mgr, 1.0, 320.0, 208.0)
    rock_off.render(surf, 0.0, 0.0, mgr, 1.0, 320.0, 208.0)

def test_memory_profile_below_target() -> None:
    tracemalloc.start()
    pygame.init()
    pygame.display.set_mode((320, 240))
    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    for _ in range(60):
        ps.update(1.0 / 60.0)
        ps.render(ps.play_view)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    assert peak_mb < 80.0


def test_darkness_cone_surfaces_zero_allocation() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    sm = StateMachine()
    ps = PlayState(sm)
    ps.enter()

    s1 = ps._build_smooth_cone_mask(320, 180, 100, 100, 0.0)
    s2 = ps._build_smooth_cone_mask(320, 180, 100, 100, 0.0)
    assert s1 is s2

    c1 = ps._build_cone_mask(320, 180, 100, 100, 0.0, 0.0)
    c2 = ps._build_cone_mask(320, 180, 100, 100, 0.0, 0.0)
    assert c1 is c2


def test_ui_surface_caching() -> None:
    from engine.ui import UILabel, UIButton

    pygame.init()
    pygame.font.init()
    real_font = pygame.font.Font(None, 16)

    class FontWrapper:
        def __init__(self, f):
            self.f = f
            self.call_count = 0

        def render(self, *args, **kwargs):
            self.call_count += 1
            return self.f.render(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.f, name)

    font = FontWrapper(real_font)
    label = UILabel(0.5, 0.5, "CachedLabel", font)
    label.rect = pygame.Rect(10, 10, 50, 20)
    surf = pygame.Surface((100, 100))

    for _ in range(5):
        label.render(surf)
    assert font.call_count == 1

    label.set_text("UpdatedLabel")
    label.render(surf)
    assert font.call_count == 2

    btn_font = FontWrapper(real_font)
    btn = UIButton(0.5, 0.5, 50, 20, "CachedBtn", btn_font)
    btn.rect = pygame.Rect(10, 10, 50, 20)
    for _ in range(5):
        btn.render(surf)
    assert btn_font.call_count == 1
