import os, sys, platform
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

def test_library_root_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SAI_LIBRARY_ROOT", str(tmp_path))
    assert config.library_root() == tmp_path

def test_library_root_missing_raises(monkeypatch):
    monkeypatch.delenv("SAI_LIBRARY_ROOT", raising=False)
    try:
        config.library_root(); assert False, "expected error"
    except RuntimeError:
        pass

def test_whisper_backend_values():
    assert config.whisper_backend() in ("mlx", "openai")

def test_fps_constant():
    assert config.FPS == "24000/1001"
