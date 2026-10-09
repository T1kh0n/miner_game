import os
import shutil
import subprocess
import signal
import pygame
from datetime import datetime


class VideoRecorder:
    def __init__(self, width, height, fps=60):
        self.width = width
        self.height = height
        self.fps = fps
        self.proc = None
        self.is_recording = False
        self.is_external = False
        self.folder = "recordings"
        os.makedirs(self.folder, exist_ok=True)
        self.start()

    def start(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.folder, f"gameplay_{timestamp}.mp4")

        if shutil.which("ffmpeg"):
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{self.width}x{self.height}",
                "-pix_fmt", "rgba",
                "-r", str(self.fps),
                "-i", "-",
                "-an",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                filepath
            ]
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.is_recording = True
                self.is_external = False
                return
            except Exception:
                self.proc = None

        is_wayland = bool(
            os.environ.get("WAYLAND_DISPLAY") or
            os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        )

        if is_wayland and shutil.which("wf-recorder"):
            try:
                self.proc = subprocess.Popen(
                    ["wf-recorder", "-f", filepath],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.is_recording = True
                self.is_external = True
                return
            except Exception:
                self.proc = None

        if is_wayland and shutil.which("wl-screenrec"):
            try:
                self.proc = subprocess.Popen(
                    ["wl-screenrec", "-f", filepath],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.is_recording = True
                self.is_external = True
                return
            except Exception:
                self.proc = None

    def record_frame(self, surf):
        if not self.is_recording or self.is_external:
            return
        try:
            if hasattr(pygame.image, "tobytes"):
                raw = pygame.image.tobytes(surf, "RGBA")
            else:
                raw = pygame.image.tostring(surf, "RGBA")
            if self.proc and self.proc.stdin:
                self.proc.stdin.write(raw)
                self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            self.is_recording = False

    def stop(self):
        if not self.is_recording and not self.proc:
            return
        self.is_recording = False
        if self.proc:
            try:
                if self.is_external:
                    self.proc.send_signal(signal.SIGINT)
                    self.proc.wait(timeout=3.0)
                else:
                    if self.proc.stdin:
                        self.proc.stdin.close()
                    self.proc.wait(timeout=5.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
