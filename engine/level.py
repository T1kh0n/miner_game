import random
from collections import deque
from core.config import GRID_W, GRID_H, TILE_SIZE, EMPTY, WALL, DIRT, ROCK, COIN

class Level:
    def __init__(self, w=GRID_W, h=GRID_H):
        self.w = w
        self.h = h
        self.grid = [[WALL for _ in range(self.w)] for _ in range(self.h)]
        self.spawn_x = (self.w // 2) * TILE_SIZE + TILE_SIZE / 2.0
        self.spawn_y = 1 * TILE_SIZE + TILE_SIZE / 2.0
        self.total_coins = 0
        self.generate()

    def generate(self):
        visited = [[False for _ in range(self.w)] for _ in range(self.h)]
        center_x = self.w // 2

        for sx in range(center_x - 1, center_x + 2):
            self.grid[0][sx] = WALL
            self.grid[1][sx] = EMPTY
            self.grid[2][sx] = EMPTY
            visited[1][sx] = True
            visited[2][sx] = True

        cur_x = center_x
        for y in range(1, self.h - 2):
            cur_x = max(3, min(self.w - 4, cur_x + random.choice([-1, 0, 1, 0])))
            for dx in range(-1, 2):
                self.grid[y][cur_x + dx] = DIRT
                visited[y][cur_x + dx] = True

            if y % 5 == 0 and y < self.h - 5:
                for direction in [-1, 1]:
                    bx, by = cur_x, y
                    blen = random.randint(8, self.w // 2)
                    for _ in range(blen):
                        bx += direction
                        if not (1 < bx < self.w - 2): break
                        by = max(2, min(self.h - 3, by + random.choice([-1, 0, 1, 0])))
                        for ty in range(2):
                            self.grid[by + ty][bx] = DIRT
                            visited[by + ty][bx] = True
                        if random.random() < 0.16:
                            for rx in range(bx - 1, bx + 2):
                                for ry in range(by - 1, by + 2):
                                    if 0 < rx < self.w - 1 and 0 < ry < self.h - 1:
                                        self.grid[ry][rx] = EMPTY if random.random() < 0.4 else DIRT
                                        visited[ry][rx] = True

        q = deque([(center_x, 1)])
        reachable = {(center_x, 1)}
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 < nx < self.w - 1 and 0 < ny < self.h - 1:
                    if (nx, ny) not in reachable and visited[ny][nx]:
                        reachable.add((nx, ny))
                        q.append((nx, ny))

        valid_nodes = [(x, y) for (x, y) in reachable if y > 3]
        random.shuffle(valid_nodes)
        num_rocks = min(60, len(valid_nodes) // 8)
        num_coins = min(40, len(valid_nodes) // 10)

        for i in range(num_rocks):
            x, y = valid_nodes[i]
            self.grid[y][x] = ROCK

        for i in range(num_rocks, num_rocks + num_coins):
            x, y = valid_nodes[i]
            self.grid[y][x] = COIN
            self.total_coins += 1

        for sx in range(center_x - 1, center_x + 2):
            self.grid[0][sx] = WALL
            self.grid[1][sx] = EMPTY
            self.grid[2][sx] = EMPTY

        self.spawn_x = center_x * TILE_SIZE + TILE_SIZE / 2.0
        self.spawn_y = 1 * TILE_SIZE + TILE_SIZE / 2.0
