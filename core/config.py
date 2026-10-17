CANVAS_W = 320
CANVAS_H = 240
DEFAULT_SCALE = 3
INITIAL_SCREEN_W = CANVAS_W * DEFAULT_SCALE
INITIAL_SCREEN_H = CANVAS_H * DEFAULT_SCALE
TILE_SIZE = 20
GRID_W = 48
GRID_H = 120
PANEL_HEIGHT = 0
FPS = 60
FIXED_DT = 1.0 / 60.0
MAX_ACCUMULATOR = 0.2
EMPTY = 0
WALL = 1
DIRT = 2
ROCK = 3
COIN = 4
STONE = 5
PAL_OUTLINE = (20, 16, 26)
CAT_OUTLINE = (22, 18, 24)
COLOR_TEXT = (245, 240, 225)
COLOR_GOLD = (255, 215, 60)
COLOR_DANGER = (255, 80, 80)
COLOR_SUCCESS = (90, 240, 140)
CAT_MINER_ID = "miner"
CAT_FRAME_W = 36
CAT_FRAME_H = 36
CAT_BODY_W = 12.0
CAT_BODY_H = 26.0
FLASHLIGHT_ANGLE = 65.0
FLASHLIGHT_SELF_GLOW = 22
AFK_KNOCK_SECONDS = 8.0
AFK_BLIND_SECONDS = 14.0
ROPE_MAX_LENGTH = 110.0
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
CAT_MINER_PALETTE = {
    "coat_primary": (142, 120, 96),
    "coat_secondary": (188, 168, 140),
    "coat_dark": (72, 58, 44),
    "belly": (210, 192, 168),
    "vest_main": (130, 128, 88),
    "vest_dark": (92, 90, 58),
    "vest_pocket": (108, 106, 70),
    "helmet_yellow": (240, 190, 30),
    "helmet_dark": (180, 138, 18),
    "lamp_glow": (255, 245, 180),
    "eye_left": (180, 100, 30),
    "eye_right": (180, 100, 30),
    "nose": (220, 130, 120),
    "whisker": (230, 220, 200),
    "boot": (58, 46, 34),
    "pickaxe_handle": (130, 80, 40),
    "pickaxe_head": (160, 168, 180),
}
