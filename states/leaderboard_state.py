import pygame
from core.config import CANVAS_W, CANVAS_H, COLOR_TEXT, COLOR_GOLD
from engine.ui import UIPanel, UIButton, UILabel, UINode
from states.state_machine import State

class LeaderboardState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_large = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 16)
        
        self.root = UINode(0.5, 0.5, 1.0, 1.0)
        self.panel = UIPanel(0.5, 0.5, 220, 200)
        self.root.add_child(self.panel)
        
        self.panel.add_child(UILabel(0.5, 0.1, "ЗАЛ СЛАВЫ", self.font_large, COLOR_GOLD))
        self.panel.add_child(UIButton(0.5, 0.9, 90, 20, "МЕНЮ", self.font_small, lambda: self.manager.change("menu")))
        
        self.root.layout(pygame.Rect(0, 0, CANVAS_W, CANVAS_H))

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.root.update(mouse_pos, True)
        else:
            self.root.update(mouse_pos, False)

    def render(self, surface):
        surface.fill((16, 20, 28))
        self.root.render(surface)
        records = self.manager.leaderboard.entries
        start_y = CANVAS_H // 2 - 58
        for i, rec in enumerate(records[:7]):
            txt = self.font_small.render(f"{i+1}. Счёт: {rec['score']} | {rec['depth']}м | {rec['skin']}", True, COLOR_TEXT)
            surface.blit(txt, (CANVAS_W // 2 - 95, start_y + i * 18))
