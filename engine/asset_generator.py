import os
import json
import math
import pygame
from core.config import TILE_SIZE, PAL_OUTLINE, SKIN_PALETTES

class AssetGenerator:
    @staticmethod
    def generate_all():
        os.makedirs("assets/spritesheets", exist_ok=True)
        os.makedirs("assets/data", exist_ok=True)
        AssetGenerator.generate_tiles()
        AssetGenerator.generate_coin()
        for skin_id, palette in SKIN_PALETTES.items():
            AssetGenerator.generate_player_skin(skin_id, palette)

    @staticmethod
    def generate_tiles():
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
    def generate_coin():
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
    def generate_player_skin(skin_id, pal):
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
    def _render_character_frame(pal, bob, l_leg, r_leg, is_digging, dig_phase, is_falling, is_climbing, climb_phase):
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
