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
