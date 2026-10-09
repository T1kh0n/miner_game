import sys
import atexit
import pygame
from core.config import CANVAS_W, CANVAS_H, INITIAL_SCREEN_W, INITIAL_SCREEN_H, FPS
from engine.asset_generator import AssetGenerator
from core.recorder import VideoRecorder
from core.leaderboard import LeaderboardManager
from states.state_machine import StateMachine
from states.menu_state import MenuState
from states.play_state import PlayState
from states.skin_state import SkinState
from states.leaderboard_state import LeaderboardState

class MinerApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Miner Digger — Cavern Rolling Physics")
        self.screen = pygame.display.set_mode((INITIAL_SCREEN_W, INITIAL_SCREEN_H), pygame.RESIZABLE)
        self.canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        self.clock = pygame.time.Clock()
        self.is_fullscreen = False
        AssetGenerator.generate_all()
        self.recorder = VideoRecorder(INITIAL_SCREEN_W, INITIAL_SCREEN_H, FPS)
        atexit.register(self.recorder.stop)
        self.state_machine = StateMachine()
        self.state_machine.leaderboard = LeaderboardManager()
        self.state_machine.selected_skin = "classic"
        self.state_machine.add_state("menu", MenuState(self.state_machine))
        self.state_machine.add_state("play", PlayState(self.state_machine))
        self.state_machine.add_state("skin", SkinState(self.state_machine))
        self.state_machine.add_state("leaderboard", LeaderboardState(self.state_machine))
        self.state_machine.change("menu")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((INITIAL_SCREEN_W, INITIAL_SCREEN_H), pygame.RESIZABLE)

    def get_viewport_rect(self):
        win_w, win_h = self.screen.get_size()
        scale = min(win_w / CANVAS_W, win_h / CANVAS_H)
        vw, vh = int(CANVAS_W * scale), int(CANVAS_H * scale)
        return pygame.Rect((win_w - vw) // 2, (win_h - vh) // 2, vw, vh)

    def run(self):
        while True:
            vp = self.get_viewport_rect()
            raw_pos = pygame.mouse.get_pos()
            virtual_pos = (int((raw_pos[0] - vp.x) * (CANVAS_W / max(1, vp.w))), int((raw_pos[1] - vp.y) * (CANVAS_H / max(1, vp.h))))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.recorder.stop()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                self.state_machine.handle_event(event, virtual_pos)

            self.state_machine.update(1.0 / FPS)
            self.state_machine.render(self.canvas)

            self.screen.fill((0, 0, 0))
            self.screen.blit(pygame.transform.scale(self.canvas, (vp.w, vp.h)), (vp.x, vp.y))
            self.recorder.record_frame(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    app = MinerApp()
    app.run()
