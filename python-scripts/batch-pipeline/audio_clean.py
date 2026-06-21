"""Audio cleanup — remove background noise from lav mic recording.

Wraps ElevenLabs Audio Isolation API (already on Gray's account).
Interface: clean(in_wav: Path) -> Path to cleaned WAV (cached by input hash).
"""
import hashlib, json, os
from pathlib import Path
import requests

CACHE_DIR = Path(__file__).parent / ".tmp" / "audio_clean_cache"
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

def _hash_file(path: Path) -> str:
    """SHA256 of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:12]

def clean(in_wav: Path) -> Path:
    """Clean lav audio via ElevenLabs Audio Isolation API.

    Returns path to cleaned WAV file (in-place if cache hit).
    Raises RuntimeError if API key missing or API fails.
    """
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not in environment")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # --- Check cache ---
    file_hash = _hash_file(in_wav)
    cache_path = CACHE_DIR / f"{file_hash}_clean.wav"
    if cache_path.exists():
        print(f"  [cache hit] {in_wav.name} → {cache_path}")
        return cache_path

    # --- Call ElevenLabs API ---
    print(f"  [ElevenLabs API] cleaning {in_wav.name}...")
    url = "https://api.elevenlabs.io/v1/audio_isolation"

    with open(in_wav, "rb") as f:
        files = {"audio": ("audio.wav", f, "audio/wav")}
        headers = {"xi-api-key": ELEVENLABS_API_KEY}

        resp = requests.post(url, files=files, headers=headers, timeout=60)

    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error {resp.status_code}: {resp.text}")

    # --- Save to cache ---
    with open(cache_path, "wb") as f:
        f.write(resp.content)
    print(f"  → cached: {cache_path}")

    return cache_path
