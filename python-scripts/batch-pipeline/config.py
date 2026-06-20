import os, sys, platform
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

FPS = "24000/1001"
PRORES422 = ["-c:v", "prores_ks", "-profile:v", "3"]
PRORES4444 = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
CAPTION_STYLE = {
    "font_size": 60, "top_margin": 858, "max_words": 3,
    "text_color": (255, 255, 255, 255), "shadow_color": (0, 0, 0, 165),
    "shadow_offset": (0, 5), "shadow_blur": 6,
    "preserve_case": {"i": "I", "i'm": "I'm", "i've": "I've", "i'll": "I'll",
                      "i'd": "I'd", "sai": "Sai", "sai's": "Sai's"},
    "punct": ".,!?;:\"()[]{}—–-…",
}

def library_root() -> Path:
    v = os.environ.get("SAI_LIBRARY_ROOT")
    if not v:
        raise RuntimeError("SAI_LIBRARY_ROOT not set (see batch-pipeline .env)")
    return Path(v)

def whisper_backend() -> str:
    return "mlx" if platform.system() == "Darwin" and platform.machine() == "arm64" else "openai"

def font_path() -> Path:
    here = Path(__file__).resolve().parents[2]  # repo root
    return here / "python-scripts" / "sai-captions" / "fonts" / "Montserrat.ttf"
