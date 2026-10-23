from __future__ import annotations

import os
from typing import Optional

import numpy as np

_SAMPLE_RATE = 44100


def _to_stereo(mono: np.ndarray) -> np.ndarray:
    """Convert a mono int16 array of shape (N,) to stereo shape (N, 2)."""
    return np.column_stack((mono, mono))


def _normalize_i16(wave: np.ndarray, peak: float = 0.9) -> np.ndarray:
    """Scale a float64 waveform to int16 with the given peak amplitude."""
    max_val = np.max(np.abs(wave))
    if max_val > 0:
        wave = wave / max_val * peak
    return (wave * 32767).astype(np.int16)


def _sine(freq: float, duration: float, sample_rate: int = _SAMPLE_RATE) -> np.ndarray:
    """Return a float64 sine wave array."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _envelope(length: int, attack: int = 100, decay_frac: float = 1.0) -> np.ndarray:
    """Return a float64 envelope of *length* samples with linear attack/decay."""
    env = np.ones(length, dtype=np.float64)
    env[:attack] = np.linspace(0, 1, attack)
    decay_start = attack
    decay_len = length - decay_start
    env[decay_start:] = np.linspace(1, 0, decay_len) ** decay_frac
    return env


def _make_pickaxe_clink() -> np.ndarray:
    """Synthesise a metallic high-pitched clink (440 Hz + 880 Hz, fast decay)."""
    dur = 0.12
    n = int(_SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    wave = np.sin(2 * np.pi * 440 * t) + 0.5 * np.sin(2 * np.pi * 880 * t)
    env = np.exp(-t * 30)
    return _normalize_i16(wave * env)


def _make_dirt_crumble() -> np.ndarray:
    """Synthesise a brown-noise burst with descending pitch character."""
    dur = 0.18
    n = int(_SAMPLE_RATE * dur)
    rng = np.random.default_rng(42)
    white = rng.standard_normal(n)
    brown = np.cumsum(white)
    brown -= brown.mean()
    t = np.linspace(0, dur, n, endpoint=False)
    mod = np.sin(2 * np.pi * np.linspace(200, 50, n) * t)
    wave = brown * (1 + 0.3 * mod)
    env = np.exp(-t * 12)
    return _normalize_i16(wave * env)


def _make_rope_whoosh() -> np.ndarray:
    """Synthesise a sweeping FM chirp from 200 Hz to 800 Hz over 0.15 s."""
    dur = 0.15
    n = int(_SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(200, 800, n)
    phase = np.cumsum(2 * np.pi * freq / _SAMPLE_RATE)
    wave = np.sin(phase)
    env = np.exp(-t * 8)
    return _normalize_i16(wave * env)


def _make_cat_meow() -> np.ndarray:
    """Synthesise a pitch-sliding sine meow (600 -> 900 -> 600 Hz, 0.3 s)."""
    dur = 0.3
    n = int(_SAMPLE_RATE * dur)
    t = np.linspace(0, 1, n)
    freq = 600 + 300 * np.sin(np.pi * t)
    phase = np.cumsum(2 * np.pi * freq / _SAMPLE_RATE)
    wave = np.sin(phase)
    env = np.sin(np.pi * t) ** 0.5
    return _normalize_i16(wave * env)


def _make_cat_hiss() -> np.ndarray:
    """Synthesise a harsh bandpass noise burst for a cat hiss (0.2 s)."""
    dur = 0.2
    n = int(_SAMPLE_RATE * dur)
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n)
    t = np.linspace(0, dur, n, endpoint=False)
    carrier = np.sin(2 * np.pi * 3000 * t)
    wave = noise * carrier
    env = np.exp(-t * 10)
    return _normalize_i16(wave * env)


def _make_ui_click() -> np.ndarray:
    """Synthesise a short square-wave blip at 880 Hz (0.05 s, fast decay)."""
    dur = 0.05
    n = int(_SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    square = np.sign(np.sin(2 * np.pi * 880 * t))
    env = np.exp(-t * 60)
    return _normalize_i16(square * env)


def _make_screen_knock() -> np.ndarray:
    """Synthesise a low 120 Hz thud with reverb-like ring decay (0.25 s)."""
    dur = 0.25
    n = int(_SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    wave = np.sin(2 * np.pi * 120 * t)
    env = np.exp(-t * 15) + 0.3 * np.exp(-t * 5)
    return _normalize_i16(wave * env)


def _make_ambient_drone() -> np.ndarray:
    """Synthesise a 4-second dark underground ambient loop (60/90/45 Hz + LFO)."""
    dur = 4.0
    n = int(_SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t)
    wave = (
        np.sin(2 * np.pi * 60 * t)
        + 0.6 * np.sin(2 * np.pi * 90 * t) * lfo
        + 0.4 * np.sin(2 * np.pi * 45 * t)
    )
    return _normalize_i16(wave, peak=0.6)


class AudioManager:
    """Singleton manager that synthesises and plays retro SFX using numpy and pygame.

    All waveforms are generated at 44 100 Hz in int16 stereo format and stored as
    :class:`pygame.Sound` objects.  When the pygame mixer is unavailable (e.g.
    ``SDL_AUDIODRIVER=dummy``), all methods silently no-op.
    """

    _instance: Optional["AudioManager"] = None

    def __init__(self) -> None:
        """Initialise an empty, uninitialised AudioManager."""
        self._available: bool = False
        self._sounds: dict[str, object] = {}
        self._master_volume: float = 1.0
        self._ambient_channel: object = None

    @classmethod
    def get(cls) -> "AudioManager":
        """Return the singleton AudioManager, creating it on first call."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self) -> None:
        """Synthesise all SFX waveforms and start the ambient drone loop.

        Attempts to initialise the pygame mixer at 44 100 Hz / 16-bit / stereo.
        If initialisation fails or ``SDL_AUDIODRIVER`` is ``dummy``, the manager
        marks itself unavailable and all subsequent calls become no-ops.
        """
        if os.environ.get("SDL_AUDIODRIVER") == "dummy":
            return
        try:
            import pygame
            import pygame.sndarray
            pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=2, buffer=512)
        except Exception:
            return

        self._available = True

        builders = {
            "pickaxe_clink": _make_pickaxe_clink,
            "dirt_crumble": _make_dirt_crumble,
            "rope_whoosh": _make_rope_whoosh,
            "cat_meow": _make_cat_meow,
            "cat_hiss": _make_cat_hiss,
            "ui_click": _make_ui_click,
            "screen_knock": _make_screen_knock,
            "ambient_drone": _make_ambient_drone,
        }

        for name, builder in builders.items():
            mono = builder()
            stereo = _to_stereo(mono)
            try:
                self._sounds[name] = pygame.sndarray.make_sound(stereo)
            except Exception:
                pass

        drone = self._sounds.get("ambient_drone")
        if drone is not None:
            try:
                self._ambient_channel = drone.play(loops=-1)
            except Exception:
                pass

    def play(self, sound_name: str, volume: float = 1.0) -> None:
        """Play a named SFX at the given *volume* scaled by the master volume.

        Args:
            sound_name: Key matching one of the synthesised sound names.
            volume: Per-call volume multiplier in [0.0, 1.0].
        """
        if not self._available:
            return
        sound = self._sounds.get(sound_name)
        if sound is None:
            return
        try:
            sound.set_volume(volume * self._master_volume)
            sound.play()
        except Exception:
            pass

    def stop_ambient(self) -> None:
        """Stop the looping ambient drone channel, if it is playing."""
        if not self._available:
            return
        drone = self._sounds.get("ambient_drone")
        if drone is not None:
            try:
                drone.stop()
            except Exception:
                pass

    def set_master_volume(self, vol: float) -> None:
        """Set the master volume applied to all subsequent :meth:`play` calls.

        Args:
            vol: New master volume in [0.0, 1.0].
        """
        self._master_volume = max(0.0, min(1.0, vol))

    def is_available(self) -> bool:
        """Return *True* if the pygame mixer was successfully initialised."""
        return self._available
