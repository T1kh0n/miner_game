import os
import json
import math
import pygame
from core.config import (
    TILE_SIZE, PAL_OUTLINE, SKIN_PALETTES,
    CAT_FRAME_W, CAT_FRAME_H, CAT_MINER_ID, CAT_MINER_PALETTE, CAT_OUTLINE,
)


class AssetGenerator:
    """Procedural sprite and tile generator for all game assets."""

    @staticmethod
    def generate_all() -> None:
        """Generate all game assets: tiles, coins, player skins, and cat miner."""
        os.makedirs("assets/spritesheets", exist_ok=True)
        os.makedirs("assets/data", exist_ok=True)
        AssetGenerator.generate_tiles()
        AssetGenerator.generate_coin()
        for skin_id, palette in SKIN_PALETTES.items():
            AssetGenerator.generate_player_skin(skin_id, palette)
        AssetGenerator.generate_cat_miner()

    @staticmethod
    def generate_tiles() -> None:
        """Generate the tile spritesheet containing wall, dirt, rock, and stone tiles."""
        sheet = pygame.Surface((TILE_SIZE * 4, TILE_SIZE), pygame.SRCALPHA)
        wall_under = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        wall_under.fill((48, 42, 54))
        pygame.draw.rect(wall_under, (172, 148, 122), (1, 1, 8, 8))
        pygame.draw.rect(wall_under, (144, 122, 98), (10, 1, 9, 8))
        pygame.draw.rect(wall_under, (134, 110, 88), (1, 10, 11, 8))
        pygame.draw.rect(wall_under, (162, 138, 114), (13, 10, 6, 8))
        pygame.draw.rect(wall_under, (210, 190, 166), (2, 2, 6, 2))
        pygame.draw.rect(wall_under, (210, 190, 166), (11, 2, 7, 2))
        pygame.draw.rect(wall_under, (210, 190, 166), (2, 11, 9, 2))
        pygame.draw.rect(wall_under, PAL_OUTLINE, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        pygame.draw.line(wall_under, PAL_OUTLINE, (0, 9), (TILE_SIZE, 9), 1)
        pygame.draw.line(wall_under, PAL_OUTLINE, (9, 0), (9, 9), 1)
        pygame.draw.line(wall_under, PAL_OUTLINE, (12, 9), (12, TILE_SIZE), 1)
        pygame.draw.line(wall_under, (34, 30, 38), (3, 4), (6, 7), 1)
        pygame.draw.line(wall_under, (34, 30, 38), (14, 13), (17, 16), 1)
        wall_surface = wall_under.copy()
        for x in range(0, TILE_SIZE, 3):
            h = 3 + (x % 4)
            pygame.draw.rect(wall_surface, PAL_OUTLINE, (x, 0, 3, h + 1))
            pygame.draw.rect(wall_surface, (64, 186, 102), (x, 0, 3, h))
            pygame.draw.rect(wall_surface, (126, 230, 140), (x + 1, 0, 1, h - 1))
        pygame.draw.circle(wall_surface, (255, 88, 128), (5, 2), 2)
        pygame.draw.circle(wall_surface, (255, 240, 120), (5, 2), 1)
        pygame.draw.circle(wall_surface, (255, 88, 128), (15, 3), 2)
        pygame.draw.circle(wall_surface, (255, 240, 120), (15, 3), 1)
        dirt = pygame.Surface((TILE_SIZE, TILE_SIZE))
        dirt.fill((118, 68, 38))
        pygame.draw.rect(dirt, (148, 88, 50), (0, 0, TILE_SIZE, 3))
        pygame.draw.rect(dirt, (88, 48, 24), (0, TILE_SIZE - 2, TILE_SIZE, 2))
        pebbles = [
            ((78, 42, 20), (4, 6), 2),
            ((168, 104, 64), (12, 5), 2),
            ((220, 142, 74), (7, 12), 2),
            ((78, 42, 20), (14, 14), 3),
            ((102, 198, 140), (3, 16), 1),
            ((245, 122, 150), (16, 9), 1)
        ]
        for c, (px, py), sz in pebbles:
            pygame.draw.rect(dirt, c, (px, py, sz, sz))
        pygame.draw.rect(dirt, (64, 34, 16), (0, 0, TILE_SIZE, TILE_SIZE), 1)
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE))
        stone.fill((82, 86, 98))
        pygame.draw.rect(stone, (105, 110, 125), (1, 1, TILE_SIZE - 2, TILE_SIZE - 2))
        pygame.draw.rect(stone, (125, 132, 148), (2, 2, 7, 6))
        pygame.draw.rect(stone, (95, 100, 115), (10, 3, 7, 5))
        pygame.draw.rect(stone, (70, 74, 88), (3, 10, 6, 7))
        pygame.draw.rect(stone, (115, 120, 138), (11, 10, 6, 7))
        pygame.draw.rect(stone, (150, 158, 175), (3, 3, 4, 2))
        pygame.draw.rect(stone, (140, 148, 165), (12, 11, 3, 2))
        pygame.draw.rect(stone, PAL_OUTLINE, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        pygame.draw.line(stone, PAL_OUTLINE, (0, 9), (TILE_SIZE, 9), 1)
        pygame.draw.line(stone, PAL_OUTLINE, (9, 0), (9, 9), 1)
        rock = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        cx, cy = 10, 10
        pygame.draw.circle(rock, PAL_OUTLINE, (cx, cy), 9)
        pygame.draw.circle(rock, (98, 108, 126), (cx, cy), 8)
        pygame.draw.circle(rock, (140, 152, 175), (cx - 1, cy - 1), 6)
        pygame.draw.circle(rock, (215, 230, 250), (cx - 3, cy - 3), 2)
        pygame.draw.polygon(rock, (54, 60, 72), [(cx - 3, cy + 3), (cx + 5, cy + 4), (cx + 1, cy + 7)])
        pygame.draw.line(rock, PAL_OUTLINE, (cx - 1, cy - 3), (cx + 2, cy + 1), 1)
        pygame.draw.line(rock, PAL_OUTLINE, (cx + 2, cy + 1), (cx + 5, cy), 1)
        sheet.blit(wall_under, (0, 0))
        sheet.blit(wall_surface, (TILE_SIZE, 0))
        sheet.blit(dirt, (TILE_SIZE * 2, 0))
        sheet.blit(rock, (TILE_SIZE * 3, 0))
        sheet_wide = pygame.Surface((TILE_SIZE * 5, TILE_SIZE), pygame.SRCALPHA)
        sheet_wide.blit(sheet, (0, 0))
        sheet_wide.blit(stone, (TILE_SIZE * 4, 0))
        pygame.image.save(sheet_wide, "assets/spritesheets/tiles.png")
        meta = {
            "texture": "tiles.png",
            "frame_width": TILE_SIZE,
            "frame_height": TILE_SIZE,
            "frames": {
                "wall_under": {"x": 0, "y": 0, "w": TILE_SIZE, "h": TILE_SIZE, "pivot": [0.5, 0.5]},
                "wall_surface": {"x": TILE_SIZE, "y": 0, "w": TILE_SIZE, "h": TILE_SIZE, "pivot": [0.5, 0.5]},
                "dirt": {"x": TILE_SIZE * 2, "y": 0, "w": TILE_SIZE, "h": TILE_SIZE, "pivot": [0.5, 0.5]},
                "rock": {"x": TILE_SIZE * 3, "y": 0, "w": TILE_SIZE, "h": TILE_SIZE, "pivot": [0.5, 0.5]},
                "stone": {"x": TILE_SIZE * 4, "y": 0, "w": TILE_SIZE, "h": TILE_SIZE, "pivot": [0.5, 0.5]}
            }
        }
        with open("assets/data/tiles.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def generate_coin() -> None:
        """Generate a spinning coin animation spritesheet."""
        num_frames = 10
        sheet = pygame.Surface((TILE_SIZE * num_frames, TILE_SIZE), pygame.SRCALPHA)
        frames_meta = []
        for i in range(num_frames):
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            cx, cy = 10, 10
            angle = (i / num_frames) * math.pi * 2
            cos_val = math.cos(angle)
            scale = abs(cos_val)
            w = max(2, int(8 * scale))
            h = 8
            outer_rect = pygame.Rect(cx - w, cy - h, w * 2, h * 2)
            pygame.draw.ellipse(surf, (140, 80, 15), outer_rect.inflate(2, 2))
            pygame.draw.ellipse(surf, (255, 185, 25), outer_rect)
            if w >= 3:
                inner_rect = pygame.Rect(cx - w + 1, cy - h + 1, (w - 1) * 2, (h - 1) * 2)
                pygame.draw.ellipse(surf, (255, 225, 70), inner_rect)
                edge_col = (255, 245, 160) if cos_val >= 0 else (210, 140, 20)
                pygame.draw.line(surf, edge_col, (cx - w + 1, cy - h + 3), (cx - w + 1, cy + h - 3), 1)
                star_w = max(1, int((w - 2) * 0.7))
                star_h = int((h - 2) * 0.7)
                star_rect = pygame.Rect(cx - star_w, cy - star_h, star_w * 2, star_h * 2)
                pygame.draw.ellipse(surf, (255, 250, 170), star_rect)
                shine_x = cx - w + int(w * 2 * (i / num_frames))
                if cx - w + 1 <= shine_x <= cx + w - 1:
                    pygame.draw.line(surf, (255, 255, 255), (shine_x, cy - 3), (shine_x, cy + 3), 1)
            fx = i * TILE_SIZE
            sheet.blit(surf, (fx, 0))
            frames_meta.append({"x": fx, "y": 0, "w": TILE_SIZE, "h": TILE_SIZE, "pivot": [0.5, 0.5]})
        pygame.image.save(sheet, "assets/spritesheets/coin.png")
        meta = {
            "texture": "coin.png",
            "frame_width": TILE_SIZE,
            "frame_height": TILE_SIZE,
            "fps": 12,
            "frames": frames_meta
        }
        with open("assets/data/coin.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def generate_player_skin(skin_id: str, pal: dict) -> None:
        """Generate a legacy human miner player skin spritesheet."""
        fw = TILE_SIZE + 8
        fh = TILE_SIZE + 4
        total_frames = 20
        sheet = pygame.Surface((fw * total_frames, fh), pygame.SRCALPHA)
        frames_meta = {}
        walk_offsets = [
            (0, -2, 2), (1, -3, 1), (0, -1, 0), (-1, 1, -1),
            (0, 2, -2), (1, 1, -3), (0, 0, -1), (-1, -1, 1)
        ]
        for i in range(8):
            bob, l_leg, r_leg = walk_offsets[i]
            frame_surf = AssetGenerator._render_character_frame(pal, bob, l_leg, r_leg, False, 0.0, False, False, 0)
            sheet.blit(frame_surf, (i * fw, 0))
            frames_meta[f"walk_{i}"] = {"x": i * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.5]}
        for i in range(4):
            dig_phase = i / 3.0
            frame_surf = AssetGenerator._render_character_frame(pal, 0, 0, 0, True, dig_phase, False, False, 0)
            idx = 8 + i
            sheet.blit(frame_surf, (idx * fw, 0))
            frames_meta[f"dig_{i}"] = {"x": idx * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.5]}
        for i in range(2):
            frame_surf = AssetGenerator._render_character_frame(pal, 0, 0, 0, False, 0.0, False, False, 0)
            idx = 12 + i
            sheet.blit(frame_surf, (idx * fw, 0))
            frames_meta[f"idle_{i}"] = {"x": idx * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.5]}
        fall_surf = AssetGenerator._render_character_frame(pal, -2, -2, 2, False, 0.0, True, False, 0)
        sheet.blit(fall_surf, (14 * fw, 0))
        frames_meta["fall"] = {"x": 14 * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.5]}
        jump_surf = AssetGenerator._render_character_frame(pal, 2, 2, -1, False, 0.0, False, False, 0)
        sheet.blit(jump_surf, (15 * fw, 0))
        frames_meta["jump"] = {"x": 15 * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.5]}
        for i in range(4):
            climb_phase = i / 3.0
            frame_surf = AssetGenerator._render_character_frame(pal, 0, 0, 0, False, 0.0, False, True, climb_phase)
            idx = 16 + i
            sheet.blit(frame_surf, (idx * fw, 0))
            frames_meta[f"climb_{i}"] = {"x": idx * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.5]}
        pygame.image.save(sheet, f"assets/spritesheets/player_{skin_id}.png")
        meta = {
            "texture": f"player_{skin_id}.png",
            "frame_width": fw,
            "frame_height": fh,
            "frames": frames_meta
        }
        with open(f"assets/data/player_{skin_id}.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def _render_character_frame(
        pal: dict,
        bob: int,
        l_leg: int,
        r_leg: int,
        is_digging: bool,
        dig_phase: float,
        is_falling: bool,
        is_climbing: bool,
        climb_phase: float,
    ) -> pygame.Surface:
        """Render a single frame of the legacy human miner character."""
        fw = TILE_SIZE + 8
        fh = TILE_SIZE + 4
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        ox = 4
        oy = 2
        base_y = oy + 8 - bob
        leg_l_x = ox + 5
        leg_r_x = ox + 11

        if is_climbing:
            climb_bob = int(math.sin(climb_phase * math.pi * 2) * 1)
            l_off = int(math.sin(climb_phase * math.pi * 2) * 3)
            r_off = -l_off
            pygame.draw.rect(surf, PAL_OUTLINE, (leg_l_x + l_off, oy + 14, 4, 6))
            pygame.draw.rect(surf, (34, 42, 64), (leg_l_x + l_off + 1, oy + 15, 2, 4))
            pygame.draw.rect(surf, PAL_OUTLINE, (leg_l_x + l_off, oy + 18, 5, 2))
            pygame.draw.rect(surf, PAL_OUTLINE, (leg_r_x + r_off, oy + 14, 4, 6))
            pygame.draw.rect(surf, (34, 42, 64), (leg_r_x + r_off + 1, oy + 15, 2, 4))
            pygame.draw.rect(surf, PAL_OUTLINE, (leg_r_x + r_off, oy + 18, 5, 2))
            pack_x = ox + 2
            pygame.draw.rect(surf, PAL_OUTLINE, (pack_x, base_y + 3, 4, 7), border_radius=1)
            pygame.draw.rect(surf, (138, 76, 38), (pack_x + 1, base_y + 4, 2, 5))
            pygame.draw.rect(surf, PAL_OUTLINE, (ox + 4, base_y + 3, 12, 8), border_radius=3)
            pygame.draw.rect(surf, pal["suit_main"], (ox + 5, base_y + 4, 10, 6), border_radius=2)
            pygame.draw.rect(surf, pal["suit_dark"], (ox + 6, base_y + 7, 8, 3))
            pygame.draw.rect(surf, (255, 205, 50), (ox + 9, base_y + 5, 2, 3))
            pygame.draw.rect(surf, PAL_OUTLINE, (ox + 4, base_y - 1, 12, 6), border_radius=2)
            pygame.draw.rect(surf, pal["skin"], (ox + 5, base_y, 10, 4), border_radius=1)
            eye_x = ox + 10
            pygame.draw.rect(surf, (255, 255, 255), (eye_x, base_y + 1, 3, 3))
            pygame.draw.rect(surf, PAL_OUTLINE, (eye_x + 1, base_y + 1, 2, 2))
            pygame.draw.rect(surf, PAL_OUTLINE, (ox + 3, base_y - 5, 14, 6), border_radius=3)
            pygame.draw.rect(surf, pal["helmet_main"], (ox + 4, base_y - 4, 12, 4), border_radius=2)
            pygame.draw.rect(surf, pal["helmet_light"], (ox + 6, base_y - 4, 6, 2))
            lamp_x = ox + 13
            pygame.draw.rect(surf, PAL_OUTLINE, (lamp_x, base_y - 3, 4, 4), border_radius=1)
            pygame.draw.rect(surf, (255, 255, 220), (lamp_x + 1, base_y - 2, 2, 2))
            swing = math.sin(climb_phase * math.pi)
            arm_x = ox + 12
            arm_y = base_y + 5
            angle = -80 + 80 * swing
            rad = math.radians(angle)
            handle_len = 10
            tip_x = arm_x + int(math.cos(rad) * handle_len)
            tip_y = arm_y + int(math.sin(rad) * handle_len)
            pygame.draw.line(surf, (130, 80, 40), (arm_x, arm_y), (tip_x, tip_y), 2)
            head_rad = rad + math.pi / 2
            hx1 = tip_x + int(math.cos(head_rad) * 4)
            hy1 = tip_y + int(math.sin(head_rad) * 4)
            hx2 = tip_x - int(math.cos(head_rad) * 4)
            hy2 = tip_y - int(math.sin(head_rad) * 4)
            pygame.draw.line(surf, PAL_OUTLINE, (hx1, hy1), (hx2, hy2), 3)
            pygame.draw.line(surf, (190, 205, 225), (hx1, hy1), (hx2, hy2), 2)
            pygame.draw.circle(surf, (255, 255, 255), (hx1, hy1), 1)
            return surf

        pygame.draw.rect(surf, PAL_OUTLINE, (leg_l_x + l_leg, oy + 14, 4, 6))
        pygame.draw.rect(surf, (34, 42, 64), (leg_l_x + l_leg + 1, oy + 15, 2, 4))
        pygame.draw.rect(surf, PAL_OUTLINE, (leg_l_x + l_leg, oy + 18, 5, 2))
        pygame.draw.rect(surf, PAL_OUTLINE, (leg_r_x + r_leg, oy + 14, 4, 6))
        pygame.draw.rect(surf, (34, 42, 64), (leg_r_x + r_leg + 1, oy + 15, 2, 4))
        pygame.draw.rect(surf, PAL_OUTLINE, (leg_r_x + r_leg, oy + 18, 5, 2))
        pack_x = ox + 2
        pygame.draw.rect(surf, PAL_OUTLINE, (pack_x, base_y + 3, 4, 7), border_radius=1)
        pygame.draw.rect(surf, (138, 76, 38), (pack_x + 1, base_y + 4, 2, 5))
        pygame.draw.rect(surf, PAL_OUTLINE, (ox + 4, base_y + 3, 12, 8), border_radius=3)
        pygame.draw.rect(surf, pal["suit_main"], (ox + 5, base_y + 4, 10, 6), border_radius=2)
        pygame.draw.rect(surf, pal["suit_dark"], (ox + 6, base_y + 7, 8, 3))
        pygame.draw.rect(surf, (255, 205, 50), (ox + 9, base_y + 5, 2, 3))
        pygame.draw.rect(surf, PAL_OUTLINE, (ox + 4, base_y - 1, 12, 6), border_radius=2)
        pygame.draw.rect(surf, pal["skin"], (ox + 5, base_y, 10, 4), border_radius=1)
        eye_x = ox + 10
        pygame.draw.rect(surf, (255, 255, 255), (eye_x, base_y + 1, 3, 3))
        pygame.draw.rect(surf, PAL_OUTLINE, (eye_x + 1, base_y + 1, 2, 2))
        pygame.draw.rect(surf, PAL_OUTLINE, (ox + 3, base_y - 5, 14, 6), border_radius=3)
        pygame.draw.rect(surf, pal["helmet_main"], (ox + 4, base_y - 4, 12, 4), border_radius=2)
        pygame.draw.rect(surf, pal["helmet_light"], (ox + 6, base_y - 4, 6, 2))
        lamp_x = ox + 13
        pygame.draw.rect(surf, PAL_OUTLINE, (lamp_x, base_y - 3, 4, 4), border_radius=1)
        pygame.draw.rect(surf, (255, 255, 220), (lamp_x + 1, base_y - 2, 2, 2))
        if is_digging:
            swing = math.sin(dig_phase * math.pi)
            arm_x = ox + 12
            arm_y = base_y + 5
            angle = -45 + 105 * swing
            rad = math.radians(angle)
            handle_len = 10
            tip_x = arm_x + int(math.cos(rad) * handle_len)
            tip_y = arm_y + int(math.sin(rad) * handle_len)
            pygame.draw.line(surf, (130, 80, 40), (arm_x, arm_y), (tip_x, tip_y), 2)
            head_rad = rad + math.pi / 2
            hx1 = tip_x + int(math.cos(head_rad) * 4)
            hy1 = tip_y + int(math.sin(head_rad) * 4)
            hx2 = tip_x - int(math.cos(head_rad) * 4)
            hy2 = tip_y - int(math.sin(head_rad) * 4)
            pygame.draw.line(surf, PAL_OUTLINE, (hx1, hy1), (hx2, hy2), 3)
            pygame.draw.line(surf, (190, 205, 225), (hx1, hy1), (hx2, hy2), 2)
            pygame.draw.circle(surf, (255, 255, 255), (hx1, hy1), 1)
        return surf

    @staticmethod
    def generate_cat_miner() -> None:
        """Generate the Tabby Miner Cat spritesheet with all mandatory animation states.

        Frame layout (37 total frames, each CAT_FRAME_W x CAT_FRAME_H):
        idle_0..3, walk_0..7, run_0..5, jump_0..1, fall_0..1, land_0,
        action_0..3, climb_0..3, hurt_0..1, talk_0..3, afk_0..5
        """
        fw = CAT_FRAME_W
        fh = CAT_FRAME_H
        pal = CAT_MINER_PALETTE

        frame_keys: list[tuple[str, dict]] = []
        frames: list[pygame.Surface] = []

        def _add(key: str, surf: pygame.Surface) -> None:
            frames.append(surf)
            idx = len(frames) - 1
            frame_keys.append((key, {"x": idx * fw, "y": 0, "w": fw, "h": fh, "pivot": [0.5, 0.75]}))

        for i in range(4):
            _add(f"idle_{i}", AssetGenerator._cat_idle_frame(pal, i, fw, fh))

        for i in range(8):
            _add(f"walk_{i}", AssetGenerator._cat_walk_frame(pal, i, fw, fh))

        for i in range(6):
            _add(f"run_{i}", AssetGenerator._cat_run_frame(pal, i, fw, fh))

        for i in range(2):
            _add(f"jump_{i}", AssetGenerator._cat_jump_frame(pal, i, fw, fh))

        for i in range(2):
            _add(f"fall_{i}", AssetGenerator._cat_fall_frame(pal, i, fw, fh))

        _add("land_0", AssetGenerator._cat_land_frame(pal, fw, fh))

        for i in range(4):
            _add(f"action_{i}", AssetGenerator._cat_action_frame(pal, i, fw, fh))

        for i in range(4):
            _add(f"climb_{i}", AssetGenerator._cat_climb_frame(pal, i, fw, fh))

        for i in range(2):
            _add(f"hurt_{i}", AssetGenerator._cat_hurt_frame(pal, i, fw, fh))

        for i in range(4):
            _add(f"talk_{i}", AssetGenerator._cat_talk_frame(pal, i, fw, fh))

        for i in range(6):
            _add(f"afk_{i}", AssetGenerator._cat_afk_frame(pal, i, fw, fh))

        total = len(frames)
        sheet = pygame.Surface((fw * total, fh), pygame.SRCALPHA)
        for idx, surf in enumerate(frames):
            sheet.blit(surf, (idx * fw, 0))

        pygame.image.save(sheet, f"assets/spritesheets/cat_{CAT_MINER_ID}.png")

        frames_dict = {k: v for k, v in frame_keys}
        meta = {
            "texture": f"cat_{CAT_MINER_ID}.png",
            "frame_width": fw,
            "frame_height": fh,
            "collider": {"w": 12, "h": 26, "offset_x": 0, "offset_y": 5},
            "frames": frames_dict,
        }
        with open(f"assets/data/cat_{CAT_MINER_ID}.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def _cat_base(pal: dict, fw: int, fh: int) -> pygame.Surface:
        """Render the base cat body (torso + head + tail placeholder) without animation offsets."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        return surf

    @staticmethod
    def _draw_cat_body(
        surf: pygame.Surface,
        pal: dict,
        bx: int,
        by: int,
        tail_phase: float = 0.0,
        ear_flat: bool = False,
        face_front: bool = False,
        eye_squint: bool = False,
        white_flash: bool = False,
        mouth_open: bool = False,
        lamp_angle_deg: float = 0.0,
    ) -> None:
        """Draw the full 4-layer cat miner body at offset (bx, by).

        Layer 0: tail + backpack
        Layer 1: torso/legs/vest
        Layer 2: head/ears/helmet
        Layer 3: foreground paw + pickaxe
        """
        o = CAT_OUTLINE

        tail_ox = int(math.sin(tail_phase) * 3)
        tail_oy = int(math.cos(tail_phase * 0.7) * 1)
        tail_pts = [
            (bx - 4 + tail_ox, by + 14 + tail_oy),
            (bx - 8 + tail_ox, by + 10 + tail_oy),
            (bx - 10 + tail_ox, by + 5 + tail_oy),
            (bx - 7 + tail_ox, by + 0 + tail_oy),
        ]
        for i in range(len(tail_pts) - 1):
            pygame.draw.line(surf, o, tail_pts[i], tail_pts[i + 1], 3)
            pygame.draw.line(surf, pal["coat_primary"], tail_pts[i], tail_pts[i + 1], 2)

        pack_x = bx - 6
        pack_y = by + 4
        pygame.draw.rect(surf, o, (pack_x, pack_y, 5, 9), border_radius=1)
        pygame.draw.rect(surf, (100, 82, 58), (pack_x + 1, pack_y + 1, 3, 7))
        pygame.draw.rect(surf, (80, 64, 42), (pack_x + 1, pack_y + 3, 3, 2))

        torso_x = bx
        torso_y = by + 4
        torso_w = 14
        torso_h = 14
        pygame.draw.rect(surf, o, (torso_x - torso_w // 2 - 1, torso_y - 1, torso_w + 2, torso_h + 2), border_radius=3)
        pygame.draw.rect(surf, pal["coat_primary"], (torso_x - torso_w // 2, torso_y, torso_w, torso_h), border_radius=2)

        vest_x = torso_x - 5
        vest_y = torso_y + 1
        pygame.draw.rect(surf, pal["vest_main"], (vest_x, vest_y, 10, 12), border_radius=2)
        pygame.draw.rect(surf, pal["vest_dark"], (vest_x, vest_y, 10, 12), 1, border_radius=2)
        pygame.draw.rect(surf, pal["vest_pocket"], (vest_x + 1, vest_y + 3, 3, 3))
        pygame.draw.rect(surf, pal["vest_pocket"], (vest_x + 6, vest_y + 3, 3, 3))
        pygame.draw.rect(surf, o, (vest_x + 1, vest_y + 3, 3, 3), 1)
        pygame.draw.rect(surf, o, (vest_x + 6, vest_y + 3, 3, 3), 1)

        pygame.draw.rect(surf, pal["coat_dark"], (torso_x - 4, torso_y + 2, 2, 4))
        pygame.draw.rect(surf, pal["coat_dark"], (torso_x + 2, torso_y + 2, 2, 4))

        leg_y = by + 18
        leg_h = 10
        leg_col = pal["coat_primary"]
        pygame.draw.rect(surf, o, (bx - 7, leg_y, 5, leg_h))
        pygame.draw.rect(surf, leg_col, (bx - 6, leg_y + 1, 3, leg_h - 2))
        pygame.draw.rect(surf, o, (bx + 2, leg_y, 5, leg_h))
        pygame.draw.rect(surf, leg_col, (bx + 3, leg_y + 1, 3, leg_h - 2))

        boot_y = by + 25
        pygame.draw.rect(surf, o, (bx - 8, boot_y, 6, 4), border_radius=1)
        pygame.draw.rect(surf, pal["boot"], (bx - 7, boot_y + 1, 4, 2))
        pygame.draw.rect(surf, o, (bx + 2, boot_y, 6, 4), border_radius=1)
        pygame.draw.rect(surf, pal["boot"], (bx + 3, boot_y + 1, 4, 2))

        head_cx = bx if not face_front else bx
        head_cy = by - 2
        pygame.draw.ellipse(surf, o, (head_cx - 8, head_cy - 6, 16, 13))
        head_col = pal["coat_primary"] if not white_flash else (255, 255, 255)
        pygame.draw.ellipse(surf, head_col, (head_cx - 7, head_cy - 5, 14, 11))

        muzzle_col = pal["belly"] if not white_flash else (255, 255, 255)
        pygame.draw.ellipse(surf, muzzle_col, (head_cx - 4, head_cy + 1, 8, 5))

        if not face_front:
            ear_l_tip_y = head_cy - 9 if not ear_flat else head_cy - 5
            ear_r_tip_y = head_cy - 9 if not ear_flat else head_cy - 5
            pygame.draw.polygon(surf, o, [
                (head_cx - 7, head_cy - 4),
                (head_cx - 5, ear_l_tip_y),
                (head_cx - 1, head_cy - 4),
            ])
            pygame.draw.polygon(surf, pal["coat_primary"], [
                (head_cx - 6, head_cy - 4),
                (head_cx - 5, ear_l_tip_y + 1),
                (head_cx - 2, head_cy - 4),
            ])
            pygame.draw.polygon(surf, o, [
                (head_cx + 1, head_cy - 4),
                (head_cx + 5, ear_r_tip_y),
                (head_cx + 7, head_cy - 4),
            ])
            pygame.draw.polygon(surf, pal["coat_primary"], [
                (head_cx + 2, head_cy - 4),
                (head_cx + 5, ear_r_tip_y + 1),
                (head_cx + 6, head_cy - 4),
            ])
        else:
            for dx_ear, sign in [(-1, -1), (1, 1)]:
                tip_y = head_cy - 10 if not ear_flat else head_cy - 5
                pygame.draw.polygon(surf, o, [
                    (head_cx + sign * 4, head_cy - 4),
                    (head_cx + sign * 7, tip_y),
                    (head_cx + sign * 9, head_cy - 4),
                ])
                pygame.draw.polygon(surf, pal["coat_primary"], [
                    (head_cx + sign * 5, head_cy - 4),
                    (head_cx + sign * 7, tip_y + 1),
                    (head_cx + sign * 8, head_cy - 4),
                ])

        eye_white = (255, 255, 255) if not white_flash else (255, 200, 200)
        if not eye_squint:
            pygame.draw.rect(surf, o, (head_cx - 5, head_cy - 2, 4, 3))
            pygame.draw.rect(surf, eye_white, (head_cx - 4, head_cy - 2, 3, 2))
            pygame.draw.rect(surf, pal["eye_left"], (head_cx - 3, head_cy - 1, 1, 1))
            pygame.draw.rect(surf, o, (head_cx + 1, head_cy - 2, 4, 3))
            pygame.draw.rect(surf, eye_white, (head_cx + 2, head_cy - 2, 3, 2))
            pygame.draw.rect(surf, pal["eye_right"], (head_cx + 3, head_cy - 1, 1, 1))
        else:
            pygame.draw.line(surf, o, (head_cx - 5, head_cy - 1), (head_cx - 2, head_cy - 1), 2)
            pygame.draw.line(surf, o, (head_cx + 1, head_cy - 1), (head_cx + 4, head_cy - 1), 2)

        pygame.draw.rect(surf, pal["nose"], (head_cx - 1, head_cy + 2, 2, 1))

        if mouth_open:
            pygame.draw.line(surf, o, (head_cx - 2, head_cy + 3), (head_cx, head_cy + 5), 1)
            pygame.draw.line(surf, o, (head_cx, head_cy + 5), (head_cx + 2, head_cy + 3), 1)
        else:
            pygame.draw.line(surf, o, (head_cx - 2, head_cy + 3), (head_cx, head_cy + 4), 1)
            pygame.draw.line(surf, o, (head_cx, head_cy + 4), (head_cx + 2, head_cy + 3), 1)

        whisker_col = pal["whisker"]
        pygame.draw.line(surf, whisker_col, (head_cx - 4, head_cy + 2), (head_cx - 9, head_cy + 1), 1)
        pygame.draw.line(surf, whisker_col, (head_cx - 4, head_cy + 3), (head_cx - 9, head_cy + 4), 1)
        pygame.draw.line(surf, whisker_col, (head_cx + 4, head_cy + 2), (head_cx + 9, head_cy + 1), 1)
        pygame.draw.line(surf, whisker_col, (head_cx + 4, head_cy + 3), (head_cx + 9, head_cy + 4), 1)

        tabby_col = pal["coat_dark"]
        pygame.draw.line(surf, tabby_col, (head_cx - 3, head_cy - 5), (head_cx - 2, head_cy - 3), 1)
        pygame.draw.line(surf, tabby_col, (head_cx, head_cy - 6), (head_cx, head_cy - 3), 1)
        pygame.draw.line(surf, tabby_col, (head_cx + 2, head_cy - 5), (head_cx + 3, head_cy - 3), 1)

        pygame.draw.rect(surf, o, (head_cx + 4, head_cy - 6, 10, 8), border_radius=3)
        pygame.draw.rect(surf, pal["helmet_yellow"], (head_cx + 5, head_cy - 5, 8, 6), border_radius=2)
        pygame.draw.rect(surf, pal["helmet_dark"], (head_cx + 5, head_cy - 5, 8, 2))

        lamp_cx = head_cx + 12
        lamp_cy = head_cy - 3
        pygame.draw.rect(surf, o, (lamp_cx, lamp_cy, 4, 4), border_radius=1)
        pygame.draw.rect(surf, pal["lamp_glow"], (lamp_cx + 1, lamp_cy + 1, 2, 2))

        arm_x = bx + 7
        arm_y = by + 8
        tool_angle = math.radians(lamp_angle_deg - 40)
        handle_len = 11
        tip_x = arm_x + int(math.cos(tool_angle) * handle_len)
        tip_y = arm_y + int(math.sin(tool_angle) * handle_len)
        pygame.draw.line(surf, o, (arm_x, arm_y), (tip_x, tip_y), 3)
        pygame.draw.line(surf, pal["pickaxe_handle"], (arm_x, arm_y), (tip_x, tip_y), 2)
        head_angle = tool_angle + math.pi / 2
        hx1 = tip_x + int(math.cos(head_angle) * 4)
        hy1 = tip_y + int(math.sin(head_angle) * 4)
        hx2 = tip_x - int(math.cos(head_angle) * 4)
        hy2 = tip_y - int(math.sin(head_angle) * 4)
        pygame.draw.line(surf, o, (hx1, hy1), (hx2, hy2), 3)
        pygame.draw.line(surf, pal["pickaxe_head"], (hx1, hy1), (hx2, hy2), 2)
        pygame.draw.circle(surf, (240, 248, 255), (hx1, hy1), 1)

    @staticmethod
    def _cat_idle_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the idle breathing cycle (4 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        bob = 1 if frame_idx in (1, 2) else 0
        tail_phase = frame_idx * 0.5
        ear_twitch = frame_idx == 3
        bx = fw // 2
        by = fh // 2 - 2 + bob
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=tail_phase, ear_flat=ear_twitch)
        return surf

    @staticmethod
    def _cat_walk_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the bipedal walk cycle (8 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        phase = frame_idx / 8.0 * math.pi * 2
        bob = int(math.sin(phase * 2) * 1)
        tail_phase = frame_idx * 0.8
        tool_angle = math.sin(phase) * 20.0
        bx = fw // 2
        by = fh // 2 - 1 + bob
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=tail_phase, lamp_angle_deg=tool_angle)
        return surf

    @staticmethod
    def _cat_run_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the forward-leaning run cycle (6 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        phase = frame_idx / 6.0 * math.pi * 2
        bob = int(math.sin(phase * 2) * 1)
        tail_phase = frame_idx * 1.2
        lean = 2
        tool_angle = math.sin(phase) * 30.0
        bx = fw // 2 + lean
        by = fh // 2 - 1 + bob
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=tail_phase, lamp_angle_deg=tool_angle)
        return surf

    @staticmethod
    def _cat_jump_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the jump upward stretch (2 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        stretch_y = -2 if frame_idx == 0 else -1
        bx = fw // 2
        by = fh // 2 - 3 + stretch_y
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=0.3, lamp_angle_deg=-20.0)
        return surf

    @staticmethod
    def _cat_fall_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the falling air-resistance pose (2 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        tail_phase = frame_idx * 1.5 + math.pi
        bx = fw // 2
        by = fh // 2
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=tail_phase, ear_flat=True, lamp_angle_deg=10.0)
        return surf

    @staticmethod
    def _cat_land_frame(pal: dict, fw: int, fh: int) -> pygame.Surface:
        """Render the squash landing impact frame (1 frame)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        bx = fw // 2
        by = fh // 2 + 3
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=0.0, ear_flat=True)
        return surf

    @staticmethod
    def _cat_action_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the pickaxe swing action (4 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        swing = math.sin(frame_idx / 3.0 * math.pi)
        tool_angle = -60.0 + 120.0 * swing
        bx = fw // 2
        by = fh // 2 - 2
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=frame_idx * 0.4, lamp_angle_deg=tool_angle)
        return surf

    @staticmethod
    def _cat_climb_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the wall climbing cycle (4 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        phase = frame_idx / 4.0 * math.pi * 2
        bob = int(math.sin(phase) * 1)
        tool_angle = -70.0 + math.sin(phase) * 30.0
        bx = fw // 2
        by = fh // 2 - 1 + bob
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=phase, lamp_angle_deg=tool_angle)
        return surf

    @staticmethod
    def _cat_hurt_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the knockback hurt flinch (2 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        white = frame_idx == 0
        bx = fw // 2 + (2 if frame_idx == 0 else 0)
        by = fh // 2 - 2
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=2.0, ear_flat=True, eye_squint=True, white_flash=white)
        return surf

    @staticmethod
    def _cat_talk_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the dialogue gesture cycle (4 frames)."""
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        mouth = frame_idx % 2 == 0
        tail_phase = frame_idx * 0.6
        bx = fw // 2
        by = fh // 2 - 2
        AssetGenerator._draw_cat_body(surf, pal, bx, by, tail_phase=tail_phase, mouth_open=mouth)
        bubble_x = bx + 8
        bubble_y = by - 14
        pygame.draw.ellipse(surf, (240, 240, 255), (bubble_x, bubble_y, 12, 8))
        pygame.draw.ellipse(surf, CAT_OUTLINE, (bubble_x, bubble_y, 12, 8), 1)
        return surf

    @staticmethod
    def _cat_afk_frame(pal: dict, frame_idx: int, fw: int, fh: int) -> pygame.Surface:
        """Render one frame of the 4th-wall break AFK sequence (6 frames).

        Frames 0-2: turns toward camera, taps screen, question mark bubble.
        Frames 3-5: headlamp points at screen, full-screen blind pulse buildup.
        """
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        bx = fw // 2
        by = fh // 2 - 2
        face_front = frame_idx >= 1
        lamp_angle = -90.0 if frame_idx >= 3 else 0.0
        AssetGenerator._draw_cat_body(
            surf, pal, bx, by,
            tail_phase=frame_idx * 0.3,
            face_front=face_front,
            lamp_angle_deg=lamp_angle,
            mouth_open=(frame_idx % 2 == 0),
        )
        if frame_idx in (1, 2):
            paw_x = bx + 6
            paw_y = by - 12
            pygame.draw.circle(surf, pal["coat_secondary"], (paw_x, paw_y), 4)
            pygame.draw.circle(surf, CAT_OUTLINE, (paw_x, paw_y), 4, 1)
            pygame.draw.rect(surf, (230, 230, 255), (bx - 4, by - 18, 8, 6))
            pygame.draw.rect(surf, CAT_OUTLINE, (bx - 4, by - 18, 8, 6), 1)
            q_col = (40, 40, 80)
            pygame.draw.rect(surf, q_col, (bx - 1, by - 17, 2, 3))
            pygame.draw.rect(surf, q_col, (bx - 1, by - 13, 2, 2))
        if frame_idx >= 3:
            lamp_cx = bx + 14
            lamp_cy = by - 5
            glow_alpha = min(220, 80 + (frame_idx - 3) * 50)
            glow_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 200, glow_alpha), (5, 5), 5)
            surf.blit(glow_surf, (lamp_cx - 5, lamp_cy - 5))
        return surf
