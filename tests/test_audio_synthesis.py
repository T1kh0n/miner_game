import os
import sys
import numpy as np
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.audio import (
    AudioManager,
    _SAMPLE_RATE,
    _to_stereo,
    _normalize_i16,
    _make_pickaxe_clink,
    _make_dirt_crumble,
    _make_shale_crunch,
    _make_screen_knock,
    _make_cat_meow,
    _make_cat_hiss,
    _make_meow_talk,
    _make_train_brake,
    _make_rope_whoosh,
    _make_ui_click,
    _make_ambient_drone,
)


def test_sample_rate_constant() -> None:
    """Verify standard high-fidelity audio synthesis sample rate."""
    assert _SAMPLE_RATE == 44100


def test_to_stereo_shape_and_channels() -> None:
    """Verify mono int16 array conversion to dual-channel stereo."""
    mono = np.array([100, -200, 300], dtype=np.int16)
    stereo = _to_stereo(mono)
    assert stereo.shape == (3, 2)
    assert stereo.dtype == np.int16
    assert np.array_equal(stereo[:, 0], mono)
    assert np.array_equal(stereo[:, 1], mono)


def test_normalize_i16_limits() -> None:
    """Verify float array normalization scales to int16 without clipping."""
    wave = np.array([-5.0, 2.5, 5.0], dtype=np.float64)
    normalized = _normalize_i16(wave, peak=0.9)
    assert normalized.dtype == np.int16
    assert int(np.max(normalized)) == int(0.9 * 32767)
    assert int(np.min(normalized)) == -int(0.9 * 32767)


@pytest.mark.parametrize(
    "name,builder,min_duration_sec,max_duration_sec",
    [
        ("pickaxe_clink", _make_pickaxe_clink, 0.15, 0.40),
        ("dirt_crumble", _make_dirt_crumble, 0.15, 0.40),
        ("shale_crunch", _make_shale_crunch, 0.15, 0.40),
        ("screen_knock", _make_screen_knock, 0.20, 0.50),
        ("cat_meow", _make_cat_meow, 0.25, 0.60),
        ("cat_hiss", _make_cat_hiss, 0.15, 0.50),
        ("meow_talk", _make_meow_talk, 0.04, 0.15),
        ("train_brake", _make_train_brake, 0.70, 1.50),
        ("rope_whoosh", _make_rope_whoosh, 0.10, 0.30),
        ("ui_click", _make_ui_click, 0.02, 0.10),
        ("ambient_drone", _make_ambient_drone, 3.50, 4.50),
    ],
)
def test_all_sfx_waveforms(name: str, builder, min_duration_sec: float, max_duration_sec: float) -> None:
    """Verify that all synthesized acoustic models have rich dynamic profiles and do not clip."""
    wave = builder()
    assert wave.dtype == np.int16, f"{name} must be int16"
    assert wave.ndim == 1, f"{name} must be mono before stereo staging"

    dur = len(wave) / _SAMPLE_RATE
    assert min_duration_sec <= dur <= max_duration_sec, (
        f"{name} duration {dur:.3f}s out of expected bounds [{min_duration_sec}, {max_duration_sec}]"
    )

    peak = int(np.max(np.abs(wave)))
    assert peak <= 32767, f"{name} clipped with peak {peak}"
    assert peak > 15000, f"{name} peak {peak} is too quiet or empty"


def test_ambient_drone_loop_seamlessness() -> None:
    """Verify that the 4-second ambient drone loop wraps smoothly without click discontinuities."""
    drone = _make_ambient_drone()
    dur = len(drone) / _SAMPLE_RATE
    assert dur == 4.0
    step_start = int(drone[1]) - int(drone[0])
    step_wrap = int(drone[0]) - int(drone[-1])
    assert abs(step_wrap - step_start) < 25, "Ambient loop boundary discontinuity detected"


def test_audio_manager_headless_lifecycle() -> None:
    """Verify AudioManager singleton access and harmless headless operation."""
    mgr = AudioManager.get()
    assert mgr is AudioManager.get()
    mgr.initialize()
    assert mgr.is_available() is False

    mgr.set_master_volume(0.8)
    mgr.play("pickaxe_clink")
    mgr.play("shale_crunch")
    mgr.play("train_brake")
    mgr.play_meow_talk(0.5)
    mgr.play_shale_crunch(0.9)
    mgr.play_train_brake(0.7)
    mgr.stop_ambient()
