import random
from collections import deque
from core.config import GRID_W, GRID_H, TILE_SIZE, EMPTY, WALL, DIRT, ROCK, COIN, STONE

MAX_JUMP_TILES_VERTICAL = 2
MAX_JUMP_TILES_HORIZONTAL = 3
MAX_CLIMB_TILES_CONTINUOUS = 12


class Level:
    """Procedural cavern map generator with guaranteed passability and Biome 1 metro cavern."""

    def __init__(self, w: int = GRID_W, h: int = GRID_H, seed: int | None = None) -> None:
        """Initialise map dimensions, seed, and generate grid."""
        self.w = w
        self.h = h
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.grid = [[WALL for _ in range(self.w)] for _ in range(self.h)]
        self.spawn_x = 0.0
        self.spawn_y = 0.0
        self.total_coins = 0
        self.cabin_locations: list[tuple[int, int, str]] = []
        self.metro_cavern_rect = (2, 5, self.w - 4, 5)
        self.generate()

    def generate(self) -> None:
        """Generate surface skyline, Biome 1 metro cavern, and deep procedurally carved caves."""
        random.seed(self.seed)
        visited = [[False for _ in range(self.w)] for _ in range(self.h)]
        center_x = self.w // 2

        for y in range(3):
            for x in range(self.w):
                self.grid[y][x] = EMPTY
                visited[y][x] = True

        for x in range(self.w):
            self.grid[3][x] = WALL
            visited[3][x] = True

        spawn_grass_x = max(2, center_x - 3)
        self.grid[3][spawn_grass_x] = WALL
        self.grid[2][spawn_grass_x] = EMPTY
        self.grid[1][spawn_grass_x] = EMPTY
        self.grid[0][spawn_grass_x] = EMPTY

        self.spawn_x = spawn_grass_x * TILE_SIZE + TILE_SIZE / 2.0
        self.spawn_y = 3 * TILE_SIZE - 9.0

        for sx in range(center_x - 1, center_x + 2):
            self.grid[3][sx] = EMPTY
            self.grid[4][sx] = EMPTY
            visited[3][sx] = True
            visited[4][sx] = True

        spine_path: list[tuple[int, int]] = [(spawn_grass_x, 3), (center_x, 3), (center_x, 4)]
        spine_set: set[tuple[int, int]] = set(spine_path)

        for my in range(5, 10):
            for mx in range(2, self.w - 2):
                self.grid[my][mx] = EMPTY
                visited[my][mx] = True
                spine_set.add((mx, my))

        for mx in range(2, self.w - 2):
            self.grid[4][mx] = WALL
            self.grid[10][mx] = DIRT
            visited[4][mx] = True
            visited[10][mx] = True

        cur_x = center_x
        for y in range(10, self.h - 2):
            cur_x = max(3, min(self.w - 4, cur_x + random.choice([-1, 0, 1, 0])))
            for dx in range(-1, 2):
                self.grid[y][cur_x + dx] = DIRT
                visited[y][cur_x + dx] = True
                spine_set.add((cur_x + dx, y))
            spine_path.append((cur_x, y))

            if y % 4 == 0 and y < self.h - 6:
                for direction in [-1, 1]:
                    bx, by = cur_x, y
                    blen = random.randint(8, self.w // 2)
                    for _ in range(blen):
                        bx += direction
                        if not (1 < bx < self.w - 2):
                            break
                        by = max(10, min(self.h - 4, by + random.choice([-1, 0, 1, 0])))
                        for ty in range(2):
                            self.grid[by + ty][bx] = DIRT
                            visited[by + ty][bx] = True
                        if random.random() < 0.22:
                            for rx in range(bx - 1, bx + 2):
                                for ry in range(by - 1, by + 2):
                                    if 0 < rx < self.w - 1 and 9 < ry < self.h - 1:
                                        self.grid[ry][rx] = EMPTY if random.random() < 0.55 else DIRT
                                        visited[ry][rx] = True

        for _ in range(16):
            cliff_x = random.randint(4, self.w - 5)
            cliff_y_start = random.randint(12, self.h - 25)
            cliff_h = random.randint(8, 22)
            cliff_w = random.randint(1, 2)
            for dy in range(cliff_h):
                cy = cliff_y_start + dy
                if cy >= self.h - 2:
                    break
                for cw in range(cliff_w):
                    cx = cliff_x + cw
                    if 0 < cx < self.w - 1 and (cx, cy) not in spine_set:
                        self.grid[cy][cx] = STONE
                        visited[cy][cx] = True
                        if 0 < cx - 1 < self.w - 1 and self.grid[cy][cx - 1] == WALL:
                            self.grid[cy][cx - 1] = EMPTY
                            visited[cy][cx - 1] = True
                        if 0 < cx + 1 < self.w - 1 and self.grid[cy][cx + 1] == WALL:
                            self.grid[cy][cx + 1] = EMPTY
                            visited[cy][cx + 1] = True

        for y in range(10, self.h - 2):
            for x in range(1, self.w - 1):
                if visited[y][x] and self.grid[y][x] == DIRT and (x, y) not in spine_set:
                    if random.random() < 0.22:
                        self.grid[y][x] = STONE

        self.ensure_guaranteed_passability(spawn_grass_x, center_x)

        reachable = self.compute_reachable_set(spawn_grass_x)

        cabin_coords = set()
        for target_d in [25, 55, 85]:
            candidates = [
                (x, y) for (x, y) in reachable
                if abs(y - target_d) <= 6 and y + 1 < self.h - 1 and 2 < x < self.w - 3
            ]
            if candidates:
                candidates.sort(key=lambda pt: (abs(pt[1] - target_d), abs(pt[0] - center_x)))
                best_x, best_y = candidates[0]
            else:
                best_x, best_y = center_x, target_d
            self.grid[best_y][best_x] = EMPTY
            self.grid[best_y - 1][best_x] = EMPTY
            self.grid[best_y + 1][best_x] = WALL
            cid = f"cabin_depth_{target_d}"
            self.cabin_locations.append((best_x, best_y, cid))
            cabin_coords.add((best_x, best_y))
            cabin_coords.add((best_x, best_y - 1))

        ceiling_candidates = [
            (x, y) for (x, y) in reachable
            if 5 < y < self.h - 5 and (x, y) not in cabin_coords and (x, y) not in spine_set
            and self.grid[y][x] == DIRT
            and (self.grid[y + 1][x] in (EMPTY, DIRT))
        ]
        random.shuffle(ceiling_candidates)
        ceiling_rock_count = min(15, len(ceiling_candidates))
        for i in range(ceiling_rock_count):
            cx, cy = ceiling_candidates[i]
            self.grid[cy][cx] = ROCK

        valid_nodes = [
            (x, y) for (x, y) in reachable
            if y > 10 and self.grid[y][x] in (DIRT, EMPTY) and (x, y) not in cabin_coords and (x, y) not in spine_set
        ]
        random.shuffle(valid_nodes)

        num_rocks = min(60, len(valid_nodes) // 8)
        num_coins = min(40, len(valid_nodes) // 10)

        for i in range(min(num_rocks, len(valid_nodes))):
            x, y = valid_nodes[i]
            self.grid[y][x] = ROCK

        offset = min(num_rocks, len(valid_nodes))
        for i in range(offset, min(offset + num_coins, len(valid_nodes))):
            x, y = valid_nodes[i]
            self.grid[y][x] = COIN
            self.total_coins += 1

    def compute_reachable_set(self, start_x: int) -> set[tuple[int, int]]:
        """Compute set of all coordinates reachable through EMPTY and DIRT tiles from spawn."""
        start_node = (start_x, 3)
        q = deque([start_node])
        reachable = {start_node}
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.w and 3 <= ny < self.h - 1:
                    if (nx, ny) not in reachable and self.grid[ny][nx] in (EMPTY, DIRT):
                        reachable.add((nx, ny))
                        q.append((nx, ny))
        return reachable

    def ensure_guaranteed_passability(self, start_x: int, center_x: int) -> bool:
        """Evaluate flood fill reachability and carve bypass corridor if blocked."""
        target_bottom_y = self.h - 4
        reachable = self.compute_reachable_set(start_x)
        max_reached_y = max((y for _, y in reachable), default=3)

        if max_reached_y >= target_bottom_y:
            return True

        frontier = [(x, y) for (x, y) in reachable if y == max_reached_y]
        frontier.sort(key=lambda pt: abs(pt[0] - center_x))
        fx, fy = frontier[0] if frontier else (start_x, 3)

        cur_x = fx
        for cy in range(fy, target_bottom_y + 1):
            if cur_x < center_x:
                cur_x = min(center_x, cur_x + 1)
            elif cur_x > center_x:
                cur_x = max(center_x, cur_x - 1)

            for dx in range(-1, 2):
                bx = max(1, min(self.w - 2, cur_x + dx))
                if self.grid[cy][bx] in (STONE, WALL):
                    self.grid[cy][bx] = DIRT

        reachable = self.compute_reachable_set(start_x)
        return max((y for _, y in reachable), default=3) >= target_bottom_y
