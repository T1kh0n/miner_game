from __future__ import annotations

import math
from typing import Any, Callable
import pygame

from core.audio import AudioManager
from core.config import CANVAS_W, CANVAS_H, COLOR_TEXT, COLOR_GOLD, CAT_OUTLINE
from core.localization import LocalizationManager


class EmoteBubble:
    """Floating expressive pixel-art emote bubble anchored above an entity."""

    def __init__(
        self,
        entity_id: str,
        entity: Any,
        emote_type: str,
        duration: float = 1.5,
        offset_y: float = -20.0,
    ) -> None:
        """Initialise emote bubble attached to an entity."""
        self.entity_id = entity_id
        self.entity = entity
        self.emote_type = emote_type
        self.duration = duration
        self.offset_y = offset_y
        self.elapsed: float = 0.0
        self.is_alive: bool = True

    def update(self, dt: float) -> None:
        """Advance bubble lifetime and vertical floating animation."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.is_alive = False

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw pixel-art speech bubble with tail pointing at entity head."""
        if not self.is_alive:
            return

        cx = 0.0
        cy = 0.0
        if self.entity is not None:
            body = getattr(self.entity, "body", None)
            if body is not None:
                cx = float(body.position.x)
                cy = float(body.position.y)
            else:
                cx = float(getattr(self.entity, "x", 0.0))
                cy = float(getattr(self.entity, "y", 0.0))

        bob = math.sin(self.elapsed * 6.0) * 1.5
        sx = int(cx - cam_x)
        sy = int(cy + self.offset_y + bob - cam_y)

        bw = 18
        bh = 13
        bx = sx - bw // 2
        by = sy - bh // 2

        pygame.draw.rect(surface, CAT_OUTLINE, (bx - 1, by - 1, bw + 2, bh + 2), border_radius=3)
        pygame.draw.rect(surface, (250, 248, 240), (bx, by, bw, bh), border_radius=2)

        tail_pts = [(sx - 2, by + bh), (sx + 2, by + bh), (sx, by + bh + 3)]
        pygame.draw.polygon(surface, (250, 248, 240), tail_pts)
        pygame.draw.line(surface, CAT_OUTLINE, (sx - 2, by + bh), (sx, by + bh + 3), 1)
        pygame.draw.line(surface, CAT_OUTLINE, (sx + 2, by + bh), (sx, by + bh + 3), 1)

        center_x = bx + bw // 2
        center_y = by + bh // 2

        if self.emote_type == "exclamation":
            pygame.draw.line(surface, (220, 40, 40), (center_x, center_y - 4), (center_x, center_y), 2)
            pygame.draw.circle(surface, (220, 40, 40), (center_x, center_y + 3), 1)
        elif self.emote_type == "question":
            pygame.draw.arc(surface, (40, 80, 220), (center_x - 3, center_y - 4, 6, 5), 0, math.pi, 2)
            pygame.draw.line(surface, (40, 80, 220), (center_x + 1, center_y - 1), (center_x, center_y + 1), 2)
            pygame.draw.circle(surface, (40, 80, 220), (center_x, center_y + 3), 1)
        elif self.emote_type == "ellipsis":
            for ox in (-4, 0, 4):
                pygame.draw.circle(surface, (60, 55, 65), (center_x + ox, center_y), 1)
        elif self.emote_type == "heart":
            pygame.draw.circle(surface, (230, 50, 70), (center_x - 2, center_y - 1), 2)
            pygame.draw.circle(surface, (230, 50, 70), (center_x + 2, center_y - 1), 2)
            pygame.draw.polygon(surface, (230, 50, 70), [
                (center_x - 4, center_y),
                (center_x + 4, center_y),
                (center_x, center_y + 4)
            ])
        elif self.emote_type == "rope":
            pygame.draw.circle(surface, (180, 140, 90), (center_x, center_y), 3, 1)
            pygame.draw.line(surface, (180, 140, 90), (center_x - 2, center_y + 2), (center_x + 3, center_y - 3), 1)
        elif self.emote_type == "pickaxe":
            pygame.draw.line(surface, (140, 90, 50), (center_x - 3, center_y + 3), (center_x + 3, center_y - 3), 2)
            pygame.draw.line(surface, (160, 170, 185), (center_x, center_y - 4), (center_x + 4, center_y), 2)


class EmoteManager:
    """Manages spawning, updating, and drawing active floating emote bubbles."""

    def __init__(self) -> None:
        """Initialise empty emote manager."""
        self.bubbles: list[EmoteBubble] = []

    def spawn_bubble(
        self,
        entity_id: str,
        entity: Any,
        emote_type: str,
        duration: float = 1.5,
        offset_y: float = -20.0
    ) -> EmoteBubble:
        """Create and register a new floating emote bubble."""
        bubble = EmoteBubble(entity_id, entity, emote_type, duration, offset_y)
        self.bubbles.append(bubble)
        return bubble

    def update(self, dt: float) -> None:
        """Advance lifetime for all active emote bubbles."""
        for b in self.bubbles:
            b.update(dt)
        self.bubbles = [b for b in self.bubbles if b.is_alive]

    def render(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw all living emote bubbles to viewport surface."""
        for b in self.bubbles:
            b.render(surface, cam_x, cam_y)

    def clear(self) -> None:
        """Remove all active emote bubbles."""
        self.bubbles.clear()


class DialogueBox:
    """Pixel-art dialogue UI with typewriter text reveal and procedural meow-talk."""

    def __init__(self) -> None:
        """Initialise closed dialogue box with default properties."""
        self.speaker_id: str = ""
        self.speaker_name: str = ""
        self.text_key: str = ""
        self.full_text: str = ""
        self.portrait_key: str = ""
        self.char_index: int = 0
        self.elapsed_time: float = 0.0
        self.chars_per_second: float = 32.0
        self.is_open: bool = False
        self.is_typing: bool = False
        self.on_close_callback: Callable[[], None] | None = None
        self._last_meow_char: int = -1

    def show_message(
        self,
        speaker_id: str,
        speaker_name: str,
        text_key: str,
        default_text: str = "",
        portrait_key: str = "",
        on_close: Callable[[], None] | None = None
    ) -> None:
        """Open dialogue window and begin typewriter stream."""
        self.speaker_id = speaker_id
        loc = LocalizationManager.get()
        self.speaker_name = loc.get_text(speaker_name, speaker_name)
        self.text_key = text_key
        self.full_text = loc.get_text(text_key, default_text if default_text else text_key)
        self.portrait_key = portrait_key if portrait_key else speaker_id
        self.char_index = 0
        self.elapsed_time = 0.0
        self.is_open = True
        self.is_typing = len(self.full_text) > 0
        self.on_close_callback = on_close
        self._last_meow_char = -1

    def update(self, dt: float) -> None:
        """Advance typewriter stream and play meow chirps for alphanumeric letters."""
        if not self.is_open:
            return

        if self.is_typing:
            self.elapsed_time += dt
            new_index = min(len(self.full_text), int(self.elapsed_time * self.chars_per_second))
            if new_index > self.char_index:
                for i in range(self.char_index, new_index):
                    char = self.full_text[i]
                    if char.isalnum() and i - self._last_meow_char >= 2:
                        AudioManager.get().play_meow_talk()
                        self._last_meow_char = i
                self.char_index = new_index

            if self.char_index >= len(self.full_text):
                self.is_typing = False

    def fast_forward(self) -> None:
        """Instantly reveal full text content without closing."""
        self.char_index = len(self.full_text)
        self.is_typing = False

    def advance(self) -> bool:
        """Handle player interaction: finish typing or close window."""
        if not self.is_open:
            return True
        if self.is_typing:
            self.fast_forward()
            return False
        self.close()
        return True

    def close(self) -> None:
        """Close dialogue window and trigger dismissal callback."""
        self.is_open = False
        self.is_typing = False
        if self.on_close_callback is not None:
            cb = self.on_close_callback
            self.on_close_callback = None
            cb()

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font | None = None,
        font_name: pygame.font.Font | None = None
    ) -> None:
        if not self.is_open:
            return

        if font is None:
            font = LocalizationManager.get().get_font(12)
        """Render dialogue frame, portrait box, speaker name, and typed text."""
        if not self.is_open:
            return

        dw = CANVAS_W - 24
        dh = 52
        dx = 12
        dy = CANVAS_H - dh - 8

        pygame.draw.rect(surface, CAT_OUTLINE, (dx - 1, dy - 1, dw + 2, dh + 2), border_radius=4)
        pygame.draw.rect(surface, (18, 16, 24), (dx, dy, dw, dh), border_radius=3)
        pygame.draw.rect(surface, (45, 40, 58), (dx + 1, dy + 1, dw - 2, dh - 2), 1, border_radius=2)

        portrait_w = 34
        portrait_h = 34
        px = dx + 6
        py = dy + (dh - portrait_h) // 2

        pygame.draw.rect(surface, CAT_OUTLINE, (px - 1, py - 1, portrait_w + 2, portrait_h + 2), border_radius=2)
        pygame.draw.rect(surface, (28, 24, 38), (px, py, portrait_w, portrait_h))

        self._render_portrait(surface, px, py, portrait_w, portrait_h)

        tx = px + portrait_w + 8
        ty = dy + 5

        name_font = font_name if font_name is not None else font
        name_surf = name_font.render(self.speaker_name, True, COLOR_GOLD)
        surface.blit(name_surf, (tx, ty))

        revealed_text = self.full_text[:self.char_index]
        max_line_w = (dx + dw - 10) - tx
        self._render_wrapped_text(surface, revealed_text, font, tx, ty + 15, max_line_w)

        if not self.is_typing:
            blink = int(pygame.time.get_ticks() / 300) % 2 == 0
            if blink:
                arrow_x = dx + dw - 10
                arrow_y = dy + dh - 10
                pygame.draw.polygon(surface, COLOR_GOLD, [
                    (arrow_x - 3, arrow_y - 3),
                    (arrow_x + 3, arrow_y - 3),
                    (arrow_x, arrow_y + 1)
                ])

    def _render_portrait(self, surface: pygame.Surface, px: int, py: int, pw: int, ph: int) -> None:
        """Render speaker portrait icon inside portrait box."""
        cx = px + pw // 2
        cy = py + ph // 2

        if self.portrait_key in ("cat_driver", "driver"):
            pygame.draw.rect(surface, (70, 75, 95), (cx - 10, cy - 8, 20, 16), border_radius=3)
            pygame.draw.circle(surface, (140, 120, 96), (cx, cy - 2), 7)
            pygame.draw.rect(surface, (45, 50, 70), (cx - 8, cy - 9, 16, 5))
            pygame.draw.circle(surface, (255, 230, 110), (cx + 8, cy + 4), 3)
            pygame.draw.circle(surface, (22, 18, 24), (cx - 2, cy - 3), 1)
            pygame.draw.circle(surface, (22, 18, 24), (cx + 2, cy - 3), 1)
        elif self.portrait_key in ("cat_soldier", "soldier"):
            pygame.draw.arc(surface, (40, 160, 60), (cx - 9, cy - 10, 18, 14), 0, math.pi, 3)
            pygame.draw.circle(surface, (180, 140, 110), (cx, cy), 6)
            pygame.draw.circle(surface, (22, 18, 24), (cx - 2, cy - 1), 1)
            pygame.draw.circle(surface, (22, 18, 24), (cx + 2, cy - 1), 1)
        elif self.portrait_key in ("cat_feral", "feral"):
            pygame.draw.circle(surface, (235, 235, 240), (cx, cy), 7)
            pygame.draw.polygon(surface, (235, 235, 240), [(cx - 6, cy - 5), (cx - 3, cy - 12), (cx, cy - 5)])
            pygame.draw.polygon(surface, (235, 235, 240), [(cx, cy - 5), (cx + 3, cy - 12), (cx + 6, cy - 5)])
            pygame.draw.circle(surface, (220, 40, 40), (cx - 2, cy - 1), 1)
            pygame.draw.circle(surface, (40, 120, 240), (cx + 2, cy - 1), 1)
        else:
            pygame.draw.circle(surface, (142, 120, 96), (cx, cy), 7)
            pygame.draw.circle(surface, (240, 190, 30), (cx, cy - 6), 5)
            pygame.draw.circle(surface, (22, 18, 24), (cx - 2, cy - 1), 1)
            pygame.draw.circle(surface, (22, 18, 24), (cx + 2, cy - 1), 1)

    def _render_wrapped_text(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        x: int,
        y: int,
        max_w: int
    ) -> None:
        """Render multi-line wrapped text string fitting within max_w pixels."""
        words = text.split(" ")
        lines: list[str] = []
        cur_line = ""

        for word in words:
            test = f"{cur_line} {word}".strip()
            if font.size(test)[0] <= max_w:
                cur_line = test
            else:
                if cur_line:
                    lines.append(cur_line)
                cur_line = word
        if cur_line:
            lines.append(cur_line)

        line_h = font.get_linesize()
        for idx, line in enumerate(lines[:2]):
            surf = font.render(line, True, COLOR_TEXT)
            surface.blit(surf, (x, y + idx * line_h))
