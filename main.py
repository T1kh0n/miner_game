import sys
import pygame
from core.config import CANVAS_W, CANVAS_H, INITIAL_SCREEN_W, INITIAL_SCREEN_H, FPS
from engine.asset_generator import AssetGenerator
from core.leaderboard import LeaderboardManager
from states.state_machine import StateMachine
from states.menu_state import MenuState
from states.play_state import PlayState
from states.skin_state import SkinState
from states.leaderboard_state import LeaderboardState
from states.settings_state import SettingsState


class MinerApp:
    """Main application loop and display manager running in 16:9 fullscreen."""

    def __init__(self) -> None:
        """Initialise window, fullscreen mode, canvas, and game states."""
        pygame.init()
        pygame.display.set_caption("Miner Digger — Cavern Rolling Physics")
        info = pygame.display.Info()
        screen_w = info.current_w if info.current_w > 0 else INITIAL_SCREEN_W
        screen_h = info.current_h if info.current_h > 0 else INITIAL_SCREEN_H

        try:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            self.is_fullscreen = True
        except Exception:
            scale = max(1, min((screen_w - 80) // CANVAS_W, (screen_h - 80) // CANVAS_H))
            win_w = int(CANVAS_W * scale)
            win_h = int(CANVAS_H * scale)
            self.screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
            self.is_fullscreen = False

        self.canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        self.clock = pygame.time.Clock()

        AssetGenerator.generate_all()

        self.state_machine = StateMachine()
        self.state_machine.leaderboard = LeaderboardManager()
        self.state_machine.selected_skin = "classic"
        self.state_machine.mouse_pos = (CANVAS_W // 2, CANVAS_H // 2)

        self.state_machine.add_state("menu", MenuState(self.state_machine))
        self.state_machine.add_state("play", PlayState(self.state_machine))
        self.state_machine.app = self
        self.state_machine.add_state("skin", SkinState(self.state_machine))
        self.state_machine.add_state("leaderboard", LeaderboardState(self.state_machine))
        self.state_machine.add_state("settings", SettingsState(self.state_machine))
        self.state_machine.change("menu")

    def toggle_fullscreen(self) -> None:
        """Toggle between exclusive fullscreen and scaled windowed display."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            try:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            except Exception:
                self.is_fullscreen = False
        else:
            info = pygame.display.Info()
            screen_w = info.current_w if info.current_w > 0 else INITIAL_SCREEN_W
            screen_h = info.current_h if info.current_h > 0 else INITIAL_SCREEN_H
            scale = max(1, min((screen_w - 80) // CANVAS_W, (screen_h - 80) // CANVAS_H))
            win_w = int(CANVAS_W * scale)
            win_h = int(CANVAS_H * scale)
            self.screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.screen = pygame.display.get_surface()

    def get_viewport_rect(self) -> pygame.Rect:
        """Calculate aspect-corrected viewport rectangle centered within window."""
        cur_screen = pygame.display.get_surface()
        if cur_screen:
            self.screen = cur_screen
        win_w, win_h = self.screen.get_size()
        scale = min(win_w / CANVAS_W, win_h / CANVAS_H)
        vw, vh = int(CANVAS_W * scale), int(CANVAS_H * scale)
        return pygame.Rect((win_w - vw) // 2, (win_h - vh) // 2, vw, vh)

    def run(self) -> None:
        """Execute the primary rendering, event handling, and update loop."""
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if dt <= 0.0:
                dt = 1.0 / FPS
            dt = min(dt, 0.1)

            cur_screen = pygame.display.get_surface()
            if cur_screen:
                self.screen = cur_screen
            win_w, win_h = self.screen.get_size()
            if win_w <= 0 or win_h <= 0:
                pygame.time.wait(16)
                continue

            vp = self.get_viewport_rect()
            raw_pos = pygame.mouse.get_pos()
            virtual_pos = (
                int((raw_pos[0] - vp.x) * (CANVAS_W / max(1, vp.w))),
                int((raw_pos[1] - vp.y) * (CANVAS_H / max(1, vp.h)))
            )
            self.state_machine.mouse_pos = virtual_pos

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    cur_screen = pygame.display.get_surface()
                    if cur_screen:
                        self.screen = cur_screen
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                self.state_machine.handle_event(event, virtual_pos)

            self.state_machine.update(dt)
            self.state_machine.render(self.canvas)

            self.screen.fill((0, 0, 0))
            self.screen.blit(pygame.transform.scale(self.canvas, (vp.w, vp.h)), (vp.x, vp.y))
            pygame.display.flip()


if __name__ == "__main__":
    app = MinerApp()
    app.run()
