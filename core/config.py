CANVAS_W = 320
CANVAS_H = 240
DEFAULT_SCALE = 3
INITIAL_SCREEN_W = CANVAS_W * DEFAULT_SCALE
INITIAL_SCREEN_H = CANVAS_H * DEFAULT_SCALE
TILE_SIZE = 20
GRID_W = 48
GRID_H = 120
PANEL_HEIGHT = 32
FPS = 60
EMPTY = 0
WALL = 1
DIRT = 2
ROCK = 3
COIN = 4
STONE = 5
PAL_OUTLINE = (20, 16, 26)
COLOR_TEXT = (245, 240, 225)
COLOR_GOLD = (255, 215, 60)
COLOR_DANGER = (255, 80, 80)
COLOR_SUCCESS = (90, 240, 140)
SKIN_PALETTES = {
    "classic": {
        "suit_main": (42, 124, 235),
        "suit_dark": (24, 78, 168),
        "helmet_main": (255, 210, 30),
        "helmet_light": (255, 245, 150),
        "skin": (255, 212, 172)
    },
    "ruby": {
        "suit_main": (220, 48, 64),
        "suit_dark": (140, 24, 38),
        "helmet_main": (255, 180, 40),
        "helmet_light": (255, 225, 140),
        "skin": (255, 216, 185)
    },
    "emerald": {
        "suit_main": (38, 178, 96),
        "suit_dark": (20, 110, 56),
        "helmet_main": (230, 215, 45),
        "helmet_light": (255, 245, 160),
        "skin": (255, 210, 170)
    },
    "obsidian": {
        "suit_main": (60, 64, 78),
        "suit_dark": (36, 38, 48),
        "helmet_main": (180, 60, 230),
        "helmet_light": (225, 140, 255),
        "skin": (240, 205, 180)
    }
}
