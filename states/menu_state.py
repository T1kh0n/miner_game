import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_GOLD
from engine.ui import UIPanel, UIButton, UILabel, UINode
from states.state_machine import State

class MenuState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_large = pygame.font.Font(None, 34)
        self.font_med = pygame.font.Font(None, 20)
        
        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 170, 160)
        self.root.add_child(self.panel)
        
        self.panel.add_child(UILabel(0.5, 0.15, "MINER DIGGER", self.font_large, COLOR_GOLD))
        self.panel.add_child(UIButton(0.5, 0.35, 130, 24, "ИГРАТЬ", self.font_med, lambda: self.manager.change("play")))
        self.panel.add_child(UIButton(0.5, 0.55, 130, 24, "СКИНЫ", self.font_med, lambda: self.manager.change("skin")))
        self.panel.add_child(UIButton(0.5, 0.75, 130, 24, "РЕКОРДЫ", self.font_med, lambda: self.manager.change("leaderboard")))
        self.panel.add_child(UIButton(0.5, 0.95, 130, 24, "ВЫХОД", self.font_med, self._quit))
        
        self.bg_gradient = pygame.Surface((CANVAS_W, CANVAS_H))
        for y in range(CANVAS_H):
            t = y / CANVAS_H
            pygame.draw.line(self.bg_gradient, (int(32 - 20*t), int(88 - 64*t), int(100 - 68*t)), (0, y), (CANVAS_W, y))
            
        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))

    def _quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def render(self, surface):
        surface.blit(self.bg_gradient, (0, 0))
        self.root.render(surface)
