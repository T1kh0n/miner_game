import pygame
from core.config import PAL_OUTLINE, COLOR_TEXT, COLOR_GOLD

class UINode:
    def __init__(self, rx: float, ry: float, rw: float, rh: float, ax: float = 0.5, ay: float = 0.5) -> None:
        self.rx = rx
        self.ry = ry
        self.rw = rw
        self.rh = rh
        self.ax = ax
        self.ay = ay
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.children: list["UINode"] = []
        self.visible = True
        self.parent_w = 0

    def layout(self, prect: pygame.Rect) -> None:
        w = self.rw * prect.w if isinstance(self.rw, float) else self.rw
        h = self.rh * prect.h if isinstance(self.rh, float) else self.rh
        cx = prect.x + self.rx * prect.w
        cy = prect.y + self.ry * prect.h
        self.rect.width = int(w)
        self.rect.height = int(h)
        self.rect.x = int(cx - w * self.ax)
        self.rect.y = int(cy - h * self.ay)
        for c in self.children:
            c.parent_w = self.rect.width
            c.layout(self.rect)

    def update(self, mp: tuple[int, int], clk: bool) -> None:
        if not self.visible:
            return
        for c in self.children:
            c.update(mp, clk)

    def render(self, surf: pygame.Surface) -> None:
        if not self.visible:
            return
        for c in self.children:
            c.render(surf)

    def add_child(self, child: "UINode") -> None:
        self.children.append(child)

class UILabel(UINode):
    def __init__(self, rx: float, ry: float, text: str, font: pygame.font.Font, color: tuple[int, int, int] = COLOR_TEXT, max_width: int | None = None) -> None:
        super().__init__(rx, ry, 0, 0)
        self.text = text
        self.font = font
        self.color = color
        self.max_width = max_width

    def set_text(self, text: str) -> None:
        self.text = text

    def render(self, surf: pygame.Surface) -> None:
        if not self.visible:
            return
        ts = self.font.render(str(self.text), True, self.color)
        mw = self.max_width
        if mw is None and self.parent_w > 0:
            mw = self.parent_w - 12
        if mw and ts.get_width() > mw and ts.get_width() > 0:
            scale = mw / ts.get_width()
            nw = int(ts.get_width() * scale)
            nh = max(1, int(ts.get_height() * scale))
            ts = pygame.transform.smoothscale(ts, (nw, nh))
        pos = ts.get_rect(center=(self.rect.x, self.rect.y))
        surf.blit(ts, pos)
        super().render(surf)

class UIButton(UINode):
    def __init__(self, rx: float, ry: float, rw: float, rh: float, text: str, font: pygame.font.Font, callback=None, accent: tuple[int, int, int] = COLOR_GOLD) -> None:
        super().__init__(rx, ry, rw, rh)
        self.text = text
        self.font = font
        self.callback = callback
        self.accent = accent
        self.hovered = False

    def set_text(self, text: str) -> None:
        self.text = text

    def update(self, mp: tuple[int, int], clk: bool) -> None:
        if not self.visible:
            return
        self.hovered = self.rect.collidepoint(mp)
        if self.hovered and clk and self.callback:
            self.callback()
        super().update(mp, clk)

    def render(self, surf: pygame.Surface) -> None:
        if not self.visible:
            return
        bg_col = (48, 56, 74) if not self.hovered else (68, 80, 104)
        border_col = self.accent if self.hovered else PAL_OUTLINE
        pygame.draw.rect(surf, PAL_OUTLINE, self.rect.inflate(4, 4), border_radius=6)
        pygame.draw.rect(surf, bg_col, self.rect, border_radius=4)
        pygame.draw.rect(surf, border_col, self.rect, 1, border_radius=4)
        ts = self.font.render(self.text, True, COLOR_TEXT)
        mw = self.rect.width - 6
        if ts.get_width() > mw and ts.get_width() > 0:
            scale = mw / ts.get_width()
            nw = int(ts.get_width() * scale)
            nh = max(1, int(ts.get_height() * scale))
            ts = pygame.transform.smoothscale(ts, (nw, nh))
        tr = ts.get_rect(center=self.rect.center)
        surf.blit(ts, tr)
        super().render(surf)

class UIPanel(UINode):
    def __init__(self, rx: float, ry: float, rw: float, rh: float, bg_color: tuple[int, int, int] = (28, 34, 48), border_color: tuple[int, int, int] = COLOR_GOLD) -> None:
        super().__init__(rx, ry, rw, rh)
        self.bg_color = bg_color
        self.border_color = border_color

    def render(self, surf: pygame.Surface) -> None:
        if not self.visible:
            return
        pygame.draw.rect(surf, PAL_OUTLINE, self.rect.inflate(4, 4), border_radius=8)
        pygame.draw.rect(surf, self.bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surf, self.border_color, self.rect, 2, border_radius=6)
        super().render(surf)
