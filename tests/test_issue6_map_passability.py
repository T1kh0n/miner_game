import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from engine.level import Level, MAX_JUMP_TILES_VERTICAL, MAX_CLIMB_TILES_CONTINUOUS
from core.config import GRID_H, STONE, WALL, DIRT, EMPTY

def test_passability_across_multiple_seeds() -> None:
    test_seeds = [1, 42, 12345, 99999, 777, 2026, 8888, 54321, 31415, 65432]
    for s in test_seeds:
        lvl = Level(seed=s)
        spawn_tx = int(lvl.spawn_x // 20)
        reachable = lvl.compute_reachable_set(spawn_tx)
        max_depth = max(y for _, y in reachable)
        assert max_depth >= lvl.h - 4

def test_evasive_bypass_carving_on_artificially_blocked_level() -> None:
    lvl = Level(seed=999)
    spawn_tx = int(lvl.spawn_x // 20)

    for x in range(lvl.w):
        lvl.grid[30][x] = STONE
        lvl.grid[31][x] = STONE

    reachable_before = lvl.compute_reachable_set(spawn_tx)
    assert max(y for _, y in reachable_before) < 30

    success = lvl.ensure_guaranteed_passability(spawn_tx, lvl.w // 2)
    assert success is True

    reachable_after = lvl.compute_reachable_set(spawn_tx)
    assert max(y for _, y in reachable_after) >= lvl.h - 4

def test_metrics_constants_defined() -> None:
    assert MAX_JUMP_TILES_VERTICAL == 2
    assert MAX_CLIMB_TILES_CONTINUOUS == 12
