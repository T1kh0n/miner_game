import random
from collections import deque
from core.config import GRID_W, GRID_H, TILE_SIZE, EMPTY, WALL, DIRT, ROCK, COIN, STONE

class Level:
    def __init__(self, w: int = GRID_W, h: int = GRID_H, seed: int | None = None) -> None:
        self.w = w
        self.h = h
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.grid = [[WALL for _ in range(self.w)] for _ in range(self.h)]
        self.spawn_x = 0.0
        self.spawn_y = 0.0
        self.total_coins = 0
        self.cabin_locations: list[tuple[int, int, str]] = []
        self.generate()

    def generate(self) -> None:
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

        for sx in range(center_x - 1, center_x + 2):
            self.grid[3][sx] = EMPTY
            self.grid[4][sx] = DIRT
            visited[3][sx] = True
            visited[4][sx] = True

        cur_x = center_x
        for y in range(4, self.h - 2):
            cur_x = max(3, min(self.w - 4, cur_x + random.choice([-1, 0, 1, 0])))
            for dx in range(-1, 2):
                self.grid[y][cur_x + dx] = DIRT
                visited[y][cur_x + dx] = True

            if y % 4 == 0 and y < self.h - 6:
                for direction in [-1, 1]:
                    bx, by = cur_x, y
                    blen = random.randint(8, self.w // 2)
                    for _ in range(blen):
                        bx += direction
                        if not (1 < bx < self.w - 2):
                            break
                        by = max(4, min(self.h - 4, by + random.choice([-1, 0, 1, 0])))
                        for ty in range(2):
                            self.grid[by + ty][bx] = DIRT
                            visited[by + ty][bx] = True
                        if random.random() < 0.22:
                            for rx in range(bx - 1, bx + 2):
                                for ry in range(by - 1, by + 2):
                                    if 0 < rx < self.w - 1 and 3 < ry < self.h - 1:
                                        self.grid[ry][rx] = EMPTY if random.random() < 0.55 else DIRT
                                        visited[ry][rx] = True

        for _ in range(16):
            cliff_x = random.randint(4, self.w - 5)
            cliff_y_start = random.randint(8, self.h - 25)
            cliff_h = random.randint(8, 22)
            cliff_w = random.randint(1, 2)
            for dy in range(cliff_h):
                cy = cliff_y_start + dy
                if cy >= self.h - 2:
                    break
                for cw in range(cliff_w):
                    cx = cliff_x + cw
                    if 0 < cx < self.w - 1:
                        self.grid[cy][cx] = STONE
                        visited[cy][cx] = True
                        if 0 < cx - 1 < self.w - 1 and self.grid[cy][cx - 1] == WALL:
                            self.grid[cy][cx - 1] = EMPTY
                            visited[cy][cx - 1] = True
                        if 0 < cx + 1 < self.w - 1 and self.grid[cy][cx + 1] == WALL:
                            self.grid[cy][cx + 1] = EMPTY
                            visited[cy][cx + 1] = True

        for y in range(4, self.h - 2):
            for x in range(1, self.w - 1):
                if visited[y][x] and self.grid[y][x] == DIRT:
                    if random.random() < 0.25:
                        self.grid[y][x] = STONE

        q = deque([(center_x, 3)])
        reachable = {(center_x, 3)}
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.w and 3 <= ny < self.h - 1:
                    if (nx, ny) not in reachable and visited[ny][nx] and self.grid[ny][nx] != STONE and self.grid[ny][nx] != WALL:
                        reachable.add((nx, ny))
                        q.append((nx, ny))

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

        valid_nodes = [
            (x, y) for (x, y) in reachable
            if y > 4 and self.grid[y][x] in (DIRT, EMPTY) and (x, y) not in cabin_coords
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

        spawn_grass_x = max(1, center_x - 3)
        self.grid[3][spawn_grass_x] = WALL
        self.grid[2][spawn_grass_x] = EMPTY
        self.grid[1][spawn_grass_x] = EMPTY
        self.grid[0][spawn_grass_x] = EMPTY

        self.spawn_x = spawn_grass_x * TILE_SIZE + TILE_SIZE / 2.0
        self.spawn_y = 3 * TILE_SIZE - 9.0
