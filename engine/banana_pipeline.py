import os
import json
import numpy as np
from PIL import Image
from core.config import (
    CAT_FRAME_W, CAT_FRAME_H, CAT_MINER_ID, TILE_SIZE,
)


def chroma_key(img: Image.Image, tol: int = 60) -> Image.Image:
    """Convert an RGB or RGBA image to RGBA and make the magenta background transparent."""
    img_rgba = img.convert("RGBA")
    arr = np.array(img_rgba)
    r = arr[:, :, 0].astype(float)
    g = arr[:, :, 1].astype(float)
    b = arr[:, :, 2].astype(float)
    diff = np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2)
    is_mag = (diff < float(tol)) | ((r > 160.0) & (b > 160.0) & (g < 100.0))
    arr[is_mag, 3] = 0
    return Image.fromarray(arr)


def normalize_frame(
    clean_crop: Image.Image,
    target_w: int = 36,
    target_h: int = 36,
    baseline_pad: int = 2,
    y_shift: int = 0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> Image.Image:
    """Crop non-empty content, scale with Image.NEAREST, and align to bottom baseline."""
    bbox = clean_crop.getbbox()
    if bbox:
        clean_crop = clean_crop.crop(bbox)
    w, h = clean_crop.size
    max_h = target_h - baseline_pad - 2
    max_w = target_w - 4
    scale = min(max_w / max(1, w), max_h / max(1, h))
    nw = max(1, int(w * scale * scale_x))
    nh = max(1, int(h * scale * scale_y))
    resized = clean_crop.resize((nw, nh), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    paste_x = (target_w - nw) // 2
    paste_y = target_h - baseline_pad - nh + y_shift
    paste_y = max(0, min(target_h - nh, paste_y))
    out.paste(resized, (paste_x, paste_y), resized)
    return out


def process_cat_miner(
    raw_path: str = "assets/raw/cat_miner_raw.jpg",
    out_sheet: str = f"assets/spritesheets/cat_{CAT_MINER_ID}.png",
    out_meta: str = f"assets/data/cat_{CAT_MINER_ID}.json",
) -> None:
    """Slice and pack the 43 standardized frames for Tabby Miner Cat from raw image."""
    raw = Image.open(raw_path)

    idle_boxes = [
        (24, 7, 166, 163),
        (188, 7, 332, 163),
        (361, 7, 505, 163),
        (531, 7, 674, 163),
    ]
    walk_boxes = [
        (21, 173, 157, 337),
        (200, 173, 335, 337),
        (371, 173, 509, 337),
        (542, 173, 683, 337),
        (715, 173, 855, 337),
        (885, 173, 1025, 337),
        (1063, 173, 1199, 337),
    ]
    action_boxes = [
        (12, 378, 174, 550),
        (196, 377, 408, 550),
        (458, 373, 666, 550),
        (684, 380, 890, 550),
    ]
    hurt_boxes = [
        (936, 373, 1102, 550),
        (1142, 373, 1305, 550),
    ]
    climb_boxes = [
        (31, 578, 149, 765),
        (194, 578, 311, 765),
        (359, 575, 473, 765),
        (517, 575, 636, 765),
    ]
    afk_boxes = [
        (825, 589, 978, 766),
        (1013, 588, 1167, 766),
        (1202, 589, 1355, 766),
    ]

    frames_dict: dict[str, Image.Image] = {}

    for i, box in enumerate(idle_boxes):
        frames_dict[f"idle_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            y_shift=(1 if i in (1, 2) else 0),
        )

    for i in range(8):
        box = walk_boxes[i % len(walk_boxes)]
        frames_dict[f"walk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i in range(6):
        box = walk_boxes[i % len(walk_boxes)]
        frames_dict[f"run_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            scale_x=1.04, scale_y=0.96,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    frames_dict["jump_0"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[0])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=0.92, scale_y=1.12,
        y_shift=-3,
    )
    frames_dict["jump_1"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[1])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=0.95, scale_y=1.08,
        y_shift=-2,
    )

    frames_dict["fall_0"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[2])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=1.05, scale_y=0.95,
        y_shift=1,
    )
    frames_dict["fall_1"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[3])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=1.08, scale_y=0.92,
        y_shift=2,
    )

    frames_dict["land_0"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[0])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=1.18, scale_y=0.82,
        y_shift=3,
    )

    for i, box in enumerate(action_boxes):
        frames_dict[f"action_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
        )

    for i, box in enumerate(climb_boxes):
        frames_dict[f"climb_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i, box in enumerate(hurt_boxes):
        frames_dict[f"hurt_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            y_shift=-1,
        )

    for i in range(4):
        box = idle_boxes[i]
        frames_dict[f"talk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i in range(3):
        box = afk_boxes[i]
        frames_dict[f"afk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
        )

    for i in range(3):
        box = afk_boxes[i]
        base_afk = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
        )
        arr = np.array(base_afk)
        glow_alpha = 140 + i * 40
        arr[2:8, 14:22, 0] = np.clip(arr[2:8, 14:22, 0].astype(int) + 60, 0, 255)
        arr[2:8, 14:22, 1] = np.clip(arr[2:8, 14:22, 1].astype(int) + 60, 0, 255)
        arr[2:8, 14:22, 2] = np.clip(arr[2:8, 14:22, 2].astype(int) + 40, 0, 255)
        arr[2:8, 14:22, 3] = np.maximum(arr[2:8, 14:22, 3], glow_alpha)
        frames_dict[f"afk_{3 + i}"] = Image.fromarray(arr)

    ordered_keys = [
        "idle_0", "idle_1", "idle_2", "idle_3",
        "walk_0", "walk_1", "walk_2", "walk_3", "walk_4", "walk_5", "walk_6", "walk_7",
        "run_0", "run_1", "run_2", "run_3", "run_4", "run_5",
        "jump_0", "jump_1",
        "fall_0", "fall_1",
        "land_0",
        "action_0", "action_1", "action_2", "action_3",
        "climb_0", "climb_1", "climb_2", "climb_3",
        "hurt_0", "hurt_1",
        "talk_0", "talk_1", "talk_2", "talk_3",
        "afk_0", "afk_1", "afk_2", "afk_3", "afk_4", "afk_5",
    ]

    total_frames = len(ordered_keys)
    sheet = Image.new("RGBA", (CAT_FRAME_W * total_frames, CAT_FRAME_H), (0, 0, 0, 0))
    frames_meta = {}

    for idx, key in enumerate(ordered_keys):
        f_img = frames_dict[key]
        x_pos = idx * CAT_FRAME_W
        sheet.paste(f_img, (x_pos, 0))
        frames_meta[key] = {
            "x": x_pos,
            "y": 0,
            "w": CAT_FRAME_W,
            "h": CAT_FRAME_H,
            "pivot": [0.5, 0.75],
        }

    os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_meta), exist_ok=True)
    sheet.save(out_sheet)

    meta = {
        "texture": os.path.basename(out_sheet),
        "frame_width": CAT_FRAME_W,
        "frame_height": CAT_FRAME_H,
        "collider": {"w": 12, "h": 26, "offset_x": 0, "offset_y": 5},
        "frames": frames_meta,
    }
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    classic_sheet = "assets/spritesheets/player_classic.png"
    classic_meta = "assets/data/player_classic.json"
    sheet.save(classic_sheet)
    with open(classic_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def process_metro_props(
    raw_path: str = "assets/raw/metro_props_raw.jpg",
    out_sheet: str = "assets/spritesheets/metro_props.png",
    out_meta: str = "assets/data/metro_props.json",
    out_tiles_sheet: str = "assets/spritesheets/tiles.png",
    out_tiles_meta: str = "assets/data/tiles.json",
) -> None:
    """Slice and pack Biome 1 metro station props and tilesets."""
    raw = Image.open(raw_path)

    props_crops = {
        "train_car": ((135, 40, 525, 180), (140, 56)),
        "pipes": ((550, 45, 860, 125), (60, 16)),
        "scaffolding": ((120, 440, 215, 590), (40, 60)),
        "tracks": ((15, 330, 120, 390), (20, 8)),
        "hanging_bulb": ((715, 440, 755, 540), (12, 20)),
        "panelki": ((10, 635, 675, 750), (320, 60)),
    }

    processed_props: dict[str, Image.Image] = {}
    for name, (box, size) in props_crops.items():
        cropped = chroma_key(raw.crop(box))
        scaled = cropped.resize(size, Image.Resampling.NEAREST)
        processed_props[name] = scaled

    total_w = sum(img.size[0] for img in processed_props.values())
    max_h = max(img.size[1] for img in processed_props.values())
    sheet_props = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))
    meta_props_frames = {}

    cur_x = 0
    for name, img in processed_props.items():
        w, h = img.size
        sheet_props.paste(img, (cur_x, 0))
        meta_props_frames[name] = {
            "x": cur_x,
            "y": 0,
            "w": w,
            "h": h,
            "pivot": [0.5, 0.5],
        }
        cur_x += w

    os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_meta), exist_ok=True)
    sheet_props.save(out_sheet)
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump({
            "texture": os.path.basename(out_sheet),
            "frames": meta_props_frames,
        }, f, indent=2)

    tile_crops = {
        "wall_under": (980, 40, 1110, 160),
        "wall_surface": (980, 170, 1110, 220),
        "dirt": (980, 170, 1110, 290),
        "rock": (380, 440, 500, 560),
        "stone": (980, 300, 1110, 420),
        "bg_brick": (1110, 40, 1240, 160),
    }

    tile_order = ["wall_under", "wall_surface", "dirt", "rock", "stone", "bg_brick"]
    tiles_sheet = Image.new("RGBA", (TILE_SIZE * len(tile_order), TILE_SIZE), (0, 0, 0, 0))
    tiles_frames_meta = {}

    for idx, name in enumerate(tile_order):
        box = tile_crops[name]
        c = chroma_key(raw.crop(box))
        c_tile = c.resize((TILE_SIZE, TILE_SIZE), Image.Resampling.NEAREST)
        if name == "bg_brick":
            arr = np.array(c_tile)
            arr[:, :, :3] = (arr[:, :, :3].astype(float) * 0.45).astype(np.uint8)
            arr[:, :, 3] = 255
            c_tile = Image.fromarray(arr)
        x_pos = idx * TILE_SIZE
        tiles_sheet.paste(c_tile, (x_pos, 0))
        tiles_frames_meta[name] = {
            "x": x_pos,
            "y": 0,
            "w": TILE_SIZE,
            "h": TILE_SIZE,
            "pivot": [0.5, 0.5],
        }

    os.makedirs(os.path.dirname(out_tiles_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_tiles_meta), exist_ok=True)
    tiles_sheet.save(out_tiles_sheet)
    with open(out_tiles_meta, "w", encoding="utf-8") as f:
        json.dump({
            "texture": os.path.basename(out_tiles_sheet),
            "frame_width": TILE_SIZE,
            "frame_height": TILE_SIZE,
            "frames": tiles_frames_meta,
        }, f, indent=2)


def process_ui_icons(
    raw_path: str = "assets/raw/ui_icons_raw.jpg",
    out_sheet: str = "assets/spritesheets/ui_icons.png",
    out_meta: str = "assets/data/ui_icons.json",
) -> None:
    """Slice and pack 24x24 HUD tool icons (Pickaxe and Rope)."""
    raw = Image.open(raw_path)
    p_crop = raw.crop((51, 297, 482, 726))
    r_crop = raw.crop((542, 297, 973, 726))

    icon_sz = 24
    p_clean = chroma_key(p_crop).resize((icon_sz, icon_sz), Image.Resampling.NEAREST)
    r_clean = chroma_key(r_crop).resize((icon_sz, icon_sz), Image.Resampling.NEAREST)

    sheet = Image.new("RGBA", (icon_sz * 2, icon_sz), (0, 0, 0, 0))
    sheet.paste(p_clean, (0, 0))
    sheet.paste(r_clean, (icon_sz, 0))

    os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_meta), exist_ok=True)
    sheet.save(out_sheet)

    meta = {
        "texture": os.path.basename(out_sheet),
        "frame_width": icon_sz,
        "frame_height": icon_sz,
        "frames": {
            "pickaxe": {"x": 0, "y": 0, "w": icon_sz, "h": icon_sz, "pivot": [0.5, 0.5]},
            "rope": {"x": icon_sz, "y": 0, "w": icon_sz, "h": icon_sz, "pivot": [0.5, 0.5]},
        },
    }
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def run_pipeline() -> None:
    """Execute all asset extraction jobs from raw images into assets/ directories."""
    process_cat_miner()
    process_metro_props()
    process_ui_icons()
