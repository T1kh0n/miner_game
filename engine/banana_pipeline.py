import os
import json
import numpy as np
from PIL import Image
from core.config import (
    CAT_FRAME_W, CAT_FRAME_H, CAT_MINER_ID, TILE_SIZE,
)


def chroma_key(img: Image.Image, tol: int = 70) -> Image.Image:
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
    target_center_x: int = 18,
    target_foot_y: int = 33,
    y_shift: int = 0,
    x_shift: int = 0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> Image.Image:
    """Anchor-normalize sprite frame by anchoring feet baseline and central torso axis."""
    bbox = clean_crop.getbbox()
    if bbox:
        clean_crop = clean_crop.crop(bbox)
    w, h = clean_crop.size

    scale = 30.0 / max(1, h)
    nw = max(1, int(w * scale * scale_x))
    nh = max(1, int(h * scale * scale_y))
    resized = clean_crop.resize((nw, nh), Image.Resampling.NEAREST)

    arr = np.array(resized)
    alpha = arr[:, :, 3]
    y_idx, x_idx = np.where(alpha > 50)
    if len(y_idx) == 0:
        return Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

    foot_y = int(np.max(y_idx))
    leg_y_thresh = foot_y - max(2, int(nh * 0.22))
    leg_mask = (y_idx >= leg_y_thresh)
    if np.any(leg_mask):
        char_cx = int(np.mean(x_idx[leg_mask]))
    else:
        char_cx = nw // 2

    out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    paste_x = target_center_x - char_cx + x_shift
    paste_y = target_foot_y - foot_y + y_shift

    src_x1 = max(0, -paste_x)
    src_y1 = max(0, -paste_y)
    dst_x1 = max(0, paste_x)
    dst_y1 = max(0, paste_y)

    copy_w = min(nw - src_x1, target_w - dst_x1)
    copy_h = min(nh - src_y1, target_h - dst_y1)

    if copy_w > 0 and copy_h > 0:
        cropped_piece = resized.crop((src_x1, src_y1, src_x1 + copy_w, src_y1 + copy_h))
        out.paste(cropped_piece, (dst_x1, dst_y1), cropped_piece)
    return out


def process_cat_miner(
    raw_path: str = "assets/raw/cat_miner_raw.jpg",
    out_sheet: str = f"assets/spritesheets/cat_{CAT_MINER_ID}.png",
    out_meta: str = f"assets/data/cat_{CAT_MINER_ID}.json",
) -> None:
    """Slice and pack the 43 standardized frames for Tabby Miner Cat from raw image."""
    raw = Image.open(raw_path)

    idle_boxes = [
        (35, 14, 155, 178),
        (168, 14, 289, 179),
        (300, 14, 421, 179),
        (433, 14, 554, 179),
    ]
    walk_boxes = [
        (35, 197, 157, 364),
        (171, 196, 300, 364),
        (311, 196, 443, 364),
        (457, 196, 589, 364),
        (600, 196, 741, 364),
        (755, 196, 894, 364),
        (906, 196, 1039, 364),
        (1051, 196, 1182, 362),
        (1199, 196, 1338, 364),
    ]
    action_boxes = [
        (29, 385, 187, 554),
        (207, 385, 387, 554),
        (403, 385, 585, 554),
        (602, 385, 785, 554),
    ]
    climb_boxes = [
        (802, 385, 983, 554),
        (997, 382, 1131, 555),
        (1178, 382, 1311, 555),
        (997, 382, 1131, 555),
    ]
    hurt_boxes = [
        (32, 584, 195, 760),
        (212, 583, 350, 760),
    ]
    talk_boxes = [
        (384, 583, 525, 760),
        (679, 584, 842, 760),
        (851, 585, 1003, 760),
        (1019, 584, 1173, 760),
    ]
    afk_boxes = [
        (1019, 584, 1173, 760),
        (1181, 584, 1345, 760),
        (851, 585, 1003, 760),
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
            x_shift=1,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    frames_dict["jump_0"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[0])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=0.96, scale_y=1.06,
        y_shift=-2,
    )
    frames_dict["jump_1"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[1])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=0.98, scale_y=1.04,
        y_shift=-1,
    )

    frames_dict["fall_0"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[2])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=1.02, scale_y=0.98,
        y_shift=0,
    )
    frames_dict["fall_1"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[3])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=1.04, scale_y=0.96,
        y_shift=1,
    )

    frames_dict["land_0"] = normalize_frame(
        chroma_key(raw.crop(idle_boxes[0])),
        CAT_FRAME_W, CAT_FRAME_H,
        scale_x=1.08, scale_y=0.92,
        y_shift=1,
    )

    for i, box in enumerate(action_boxes):
        frames_dict[f"action_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            CAT_FRAME_W, CAT_FRAME_H,
            y_shift=0,
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
            y_shift=0,
        )

    for i, box in enumerate(talk_boxes):
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

    # Palette enhancement for idle_0 features
    arr_0 = np.array(frames_dict["idle_0"])
    arr_0[4:8, 14:22, :3] = [230, 185, 40]
    arr_0[4:7, 21:24, :3] = [255, 245, 170]
    arr_0[16:22, 15:21, :3] = [85, 105, 55]
    frames_dict["idle_0"] = Image.fromarray(arr_0)

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
        "collider": {"w": 12, "h": 26, "offset_x": 18, "offset_y": 21},
        "frames": frames_meta,
    }
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    classic_sheet = "assets/spritesheets/player_classic.png"
    classic_meta = "assets/data/player_classic.json"
    sheet.save(classic_sheet)
    with open(classic_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    skin_tints = {
        "ruby": (220, 50, 60),
        "emerald": (40, 190, 80),
        "obsidian": (120, 60, 150),
    }
    arr = np.array(sheet, dtype=np.float32)
    rgb = arr[:, :, :3]
    lum = 0.299 * rgb[:, :, 0:1] + 0.587 * rgb[:, :, 1:2] + 0.114 * rgb[:, :, 2:3]
    for skin_name, (tr, tg, tb) in skin_tints.items():
        tint_rgb = np.zeros_like(rgb)
        tint_rgb[:, :, 0] = lum[:, :, 0] * (tr / 255.0) * 1.3
        tint_rgb[:, :, 1] = lum[:, :, 0] * (tg / 255.0) * 1.3
        tint_rgb[:, :, 2] = lum[:, :, 0] * (tb / 255.0) * 1.3
        blended = np.clip(0.4 * rgb + 0.6 * tint_rgb, 0, 255)
        out = np.dstack([blended, arr[:, :, 3]]).astype(np.uint8)
        skin_img = Image.fromarray(out, "RGBA")
        skin_img.save(f"assets/spritesheets/player_{skin_name}.png")
        skin_meta = dict(meta)
        skin_meta["texture"] = f"player_{skin_name}.png"
        with open(f"assets/data/player_{skin_name}.json", "w", encoding="utf-8") as f:
            json.dump(skin_meta, f, indent=2)


def process_cat_driver(
    raw_path: str = "assets/raw/cat_driver_raw.jpg",
    out_sheet: str = "assets/spritesheets/cat_driver.png",
    out_meta: str = "assets/data/cat_driver.json",
) -> None:
    """Slice and pack 16 standardized frames for Train Driver Cat from raw image."""
    raw = Image.open(raw_path)
    fw, fh = 32, 36

    idle_boxes = [
        (22, 21, 175, 182),
        (191, 21, 344, 182),
        (359, 21, 512, 182),
        (526, 21, 679, 182),
    ]
    walk_boxes = [
        (26, 196, 195, 370),
        (213, 196, 382, 370),
        (399, 196, 580, 370),
        (598, 196, 774, 370),
    ]
    action_boxes = [
        (26, 382, 217, 559),
        (246, 382, 474, 559),
        (495, 382, 693, 559),
        (714, 382, 918, 559),
    ]
    talk_boxes = [
        (79, 573, 260, 763),
        (295, 573, 476, 763),
        (510, 573, 688, 763),
        (717, 573, 894, 763),
    ]

    frames_dict: dict[str, Image.Image] = {}

    for i, box in enumerate(idle_boxes):
        frames_dict[f"idle_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, target_center_x=16,
            y_shift=(1 if i in (1, 2) else 0),
        )

    for i, box in enumerate(walk_boxes):
        frames_dict[f"walk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, target_center_x=16,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i, box in enumerate(action_boxes):
        frames_dict[f"action_lantern_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, target_center_x=16,
        )

    for i, box in enumerate(talk_boxes):
        frames_dict[f"talk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, target_center_x=16,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    # Feature enhancement for driver
    arr_0 = np.array(frames_dict["idle_0"])
    arr_0[5:8, 15:18, :3] = [245, 210, 45]
    arr_0[8:12, 10:13, :3] = [185, 175, 165]
    frames_dict["idle_0"] = Image.fromarray(arr_0)

    arr_act = np.array(frames_dict["action_lantern_2"])
    arr_act[12:18, 20:26, :3] = [255, 235, 130]
    frames_dict["action_lantern_2"] = Image.fromarray(arr_act)

    ordered_keys = [
        "idle_0", "idle_1", "idle_2", "idle_3",
        "walk_0", "walk_1", "walk_2", "walk_3",
        "action_lantern_0", "action_lantern_1", "action_lantern_2", "action_lantern_3",
        "talk_0", "talk_1", "talk_2", "talk_3",
    ]

    sheet = Image.new("RGBA", (fw * len(ordered_keys), fh), (0, 0, 0, 0))
    frames_meta = {}

    for idx, key in enumerate(ordered_keys):
        f_img = frames_dict[key]
        x_pos = idx * fw
        sheet.paste(f_img, (x_pos, 0))
        frames_meta[key] = {
            "x": x_pos,
            "y": 0,
            "w": fw,
            "h": fh,
            "pivot": [0.5, 0.75],
        }

    os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_meta), exist_ok=True)
    sheet.save(out_sheet)

    meta = {
        "texture": os.path.basename(out_sheet),
        "frame_width": fw,
        "frame_height": fh,
        "collider": {"w": 12, "h": 26, "offset_x": 16, "offset_y": 21},
        "frames": frames_meta,
    }
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def process_cat_soldier(
    raw_path: str = "assets/raw/cat_soldier_raw.jpg",
    out_sheet: str = "assets/spritesheets/cat_soldier.png",
    out_meta: str = "assets/data/cat_soldier.json",
) -> None:
    """Slice and pack 24 standardized frames for Watermelon Soldier Cat from raw image."""
    raw = Image.open(raw_path)
    fw, fh = 36, 36

    idle_boxes = [
        (22, 6, 194, 180),
        (200, 6, 368, 180),
        (375, 20, 543, 180),
        (550, 20, 718, 180),
    ]
    walk_boxes = [
        (21, 188, 198, 364),
        (205, 203, 375, 364),
        (376, 203, 551, 364),
        (559, 203, 731, 364),
    ]
    action_boxes = [
        (25, 391, 201, 559),
        (214, 391, 406, 559),
        (412, 391, 607, 559),
        (622, 391, 845, 559),
    ]
    hurt_boxes = [
        (905, 393, 1063, 559),
        (1144, 391, 1347, 558),
        (860, 6, 1080, 180),
        (1080, 6, 1356, 180),
    ]
    talk_boxes = [
        (26, 571, 166, 767),
        (223, 586, 362, 767),
        (419, 586, 557, 767),
        (26, 571, 166, 767),
    ]
    pinned_boxes = [
        (694, 571, 900, 767),
        (918, 571, 1120, 766),
        (1145, 633, 1341, 766),
        (918, 571, 1120, 766),
    ]

    frames_dict: dict[str, Image.Image] = {}

    for i, box in enumerate(idle_boxes):
        frames_dict[f"idle_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=(1 if i in (1, 2) else 0),
        )

    for i, box in enumerate(walk_boxes):
        frames_dict[f"walk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i, box in enumerate(action_boxes):
        frames_dict[f"action_shovel_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh,
        )

    for i, box in enumerate(hurt_boxes):
        frames_dict[f"hurt_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh,
        )

    for i, box in enumerate(talk_boxes):
        frames_dict[f"talk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i, box in enumerate(pinned_boxes):
        frames_dict[f"pinned_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=2,
        )

    # Feature enhancement for soldier
    arr_0 = np.array(frames_dict["idle_0"])
    arr_0[4:10, 14:22, :3] = [60, 145, 55]
    arr_0[10:12, 14:22, :3] = [230, 60, 75]
    frames_dict["idle_0"] = Image.fromarray(arr_0)

    arr_act = np.array(frames_dict["action_shovel_1"])
    arr_act[14:20, 24:30, :3] = [195, 205, 220]
    frames_dict["action_shovel_1"] = Image.fromarray(arr_act)

    ordered_keys = [
        "idle_0", "idle_1", "idle_2", "idle_3",
        "walk_0", "walk_1", "walk_2", "walk_3",
        "action_shovel_0", "action_shovel_1", "action_shovel_2", "action_shovel_3",
        "hurt_0", "hurt_1", "hurt_2", "hurt_3",
        "talk_0", "talk_1", "talk_2", "talk_3",
        "pinned_0", "pinned_1", "pinned_2", "pinned_3",
    ]

    sheet = Image.new("RGBA", (fw * len(ordered_keys), fh), (0, 0, 0, 0))
    frames_meta = {}

    for idx, key in enumerate(ordered_keys):
        f_img = frames_dict[key]
        x_pos = idx * fw
        sheet.paste(f_img, (x_pos, 0))
        frames_meta[key] = {
            "x": x_pos,
            "y": 0,
            "w": fw,
            "h": fh,
            "pivot": [0.5, 0.75],
        }

    os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_meta), exist_ok=True)
    sheet.save(out_sheet)

    meta = {
        "texture": os.path.basename(out_sheet),
        "frame_width": fw,
        "frame_height": fh,
        "collider": {"w": 12, "h": 26, "offset_x": 18, "offset_y": 21},
        "frames": frames_meta,
    }
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def process_cat_feral(
    raw_path: str = "assets/raw/cat_feral_raw.jpg",
    out_sheet: str = "assets/spritesheets/cat_feral.png",
    out_meta: str = "assets/data/cat_feral.json",
) -> None:
    """Slice and pack 24 standardized frames for Wild Chaos Feral Cat from raw image."""
    raw = Image.open(raw_path)
    fw, fh = 36, 36

    idle_boxes = [
        (29, 15, 135, 144),
        (199, 15, 304, 144),
        (372, 15, 477, 144),
        (543, 15, 648, 144),
    ]
    run_boxes = [
        (14, 162, 169, 257),
        (185, 162, 339, 257),
        (354, 162, 511, 257),
        (525, 162, 681, 253),
    ]
    pounce_boxes = [
        (27, 287, 157, 384),
        (180, 291, 311, 384),
        (338, 279, 484, 384),
        (504, 265, 674, 379),
    ]
    action_boxes = [
        (312, 398, 476, 514),
        (509, 401, 680, 514),
        (704, 398, 859, 514),
        (877, 398, 1030, 514),
    ]
    talk_boxes = [
        (29, 526, 131, 642),
        (164, 526, 266, 642),
        (296, 527, 401, 642),
        (430, 526, 536, 642),
    ]
    hurt_boxes = [
        (31, 654, 144, 768),
        (169, 654, 278, 768),
        (303, 654, 408, 768),
        (435, 656, 535, 768),
    ]

    frames_dict: dict[str, Image.Image] = {}

    for i, box in enumerate(idle_boxes):
        frames_dict[f"idle_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=(1 if i in (1, 2) else 0),
        )

    for i, box in enumerate(run_boxes):
        frames_dict[f"run_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, x_shift=1,
            y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i, box in enumerate(pounce_boxes):
        frames_dict[f"pounce_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=-1,
        )

    for i, box in enumerate(action_boxes):
        frames_dict[f"action_slash_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh,
        )

    for i, box in enumerate(talk_boxes):
        frames_dict[f"talk_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh, y_shift=(-1 if i % 2 == 1 else 0),
        )

    for i, box in enumerate(hurt_boxes):
        frames_dict[f"hurt_{i}"] = normalize_frame(
            chroma_key(raw.crop(box)),
            fw, fh,
        )

    for i in range(4):
        y_off = 1 if i in (1, 2) else 0
        arr_i = np.array(frames_dict[f"idle_{i}"])
        arr_i[10 + y_off:14 + y_off, 14:22, :3] = [250, 250, 250]
        arr_i[15 + y_off:18 + y_off, 15:21, :3] = [215, 45, 50]
        frames_dict[f"idle_{i}"] = Image.fromarray(arr_i)

    red_iris = [245, 40, 50]
    blue_iris = [45, 140, 245]
    for key, f_img in frames_dict.items():
        arr = np.array(f_img)
        rows = np.where(arr[:, :, 3] > 100)[0]
        if len(rows) == 0:
            continue
        top_y = rows[0]
        head_mask = arr[top_y:top_y + 10, :, 3] > 100
        head_cols = np.where(head_mask)[1]
        center_x = int(np.mean(head_cols)) if len(head_cols) > 0 else 18
        ey = top_y + 5
        lx1 = max(0, center_x - 4)
        lx2 = min(fw, center_x - 2)
        rx1 = max(0, center_x)
        rx2 = min(fw, center_x + 2)
        arr[ey:ey + 2, lx1:lx2, :3] = red_iris
        arr[ey:ey + 2, rx1:rx2, :3] = blue_iris
        arr[ey:ey + 2, lx1:lx2, 3] = 255
        arr[ey:ey + 2, rx1:rx2, 3] = 255
        frames_dict[key] = Image.fromarray(arr)

    ordered_keys = [
        "idle_0", "idle_1", "idle_2", "idle_3",
        "run_0", "run_1", "run_2", "run_3",
        "pounce_0", "pounce_1", "pounce_2", "pounce_3",
        "action_slash_0", "action_slash_1", "action_slash_2", "action_slash_3",
        "talk_0", "talk_1", "talk_2", "talk_3",
        "hurt_0", "hurt_1", "hurt_2", "hurt_3",
    ]

    sheet = Image.new("RGBA", (fw * len(ordered_keys), fh), (0, 0, 0, 0))
    frames_meta = {}

    for idx, key in enumerate(ordered_keys):
        f_img = frames_dict[key]
        x_pos = idx * fw
        sheet.paste(f_img, (x_pos, 0))
        frames_meta[key] = {
            "x": x_pos,
            "y": 0,
            "w": fw,
            "h": fh,
            "pivot": [0.5, 0.75],
        }

    os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
    os.makedirs(os.path.dirname(out_meta), exist_ok=True)
    sheet.save(out_sheet)

    meta = {
        "texture": os.path.basename(out_sheet),
        "frame_width": fw,
        "frame_height": fh,
        "collider": {"w": 14, "h": 24, "offset_x": 18, "offset_y": 21},
        "frames": frames_meta,
    }
    with open(out_meta, "w", encoding="utf-8") as f:
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
        "shale": (980, 300, 1110, 420),
    }

    tile_order = ["wall_under", "wall_surface", "dirt", "rock", "stone", "bg_brick", "shale"]
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
        elif name == "shale":
            arr = np.array(c_tile)
            arr[:, :, 0] = (arr[:, :, 0].astype(float) * 0.6).astype(np.uint8)
            arr[:, :, 1] = (arr[:, :, 1].astype(float) * 0.65).astype(np.uint8)
            arr[:, :, 2] = (arr[:, :, 2].astype(float) * 0.75).astype(np.uint8)
            arr[2:4, :, :3] = np.clip(arr[2:4, :, :3].astype(float) * 1.3, 0, 255).astype(np.uint8)
            arr[8:10, :, :3] = (arr[8:10, :, :3].astype(float) * 0.7).astype(np.uint8)
            arr[14:16, :, :3] = np.clip(arr[14:16, :, :3].astype(float) * 1.2, 0, 255).astype(np.uint8)
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
    process_cat_driver()
    process_cat_soldier()
    process_cat_feral()
    process_metro_props()
    process_ui_icons()
