"""
Generates voiceover audio via ElevenLabs.
One MP3 per story narration (3 files). Cached by text hash.
"""

import hashlib
import requests
from pathlib import Path
from config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    ELEVENLABS_API_BASE, ELEVENLABS_MODEL, TMP_DIR,
)


def generate_voiceovers(script: dict) -> dict[int, Path]:
    """
    Generate one MP3 per story narration.
    Returns {0: path, 1: path, 2: path}
    Cached by text hash — won't re-call API for identical narration text.
    """
    paths = {}
    for i, story in enumerate(script['stories']):
        text = story['narration']
        out_path = TMP_DIR / f'vo_story_{i}_{_hash(text)}.mp3'

        if out_path.exists():
            print(f"[voiceover] Story {i+1} cache hit")
        else:
            print(f"[voiceover] Generating story {i+1}...")
            audio = _call_elevenlabs(text)
            out_path.write_bytes(audio)

        paths[i] = out_path

    return paths


def _call_elevenlabs(text: str) -> bytes:
    url = f"{ELEVENLABS_API_BASE}/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        'xi-api-key': ELEVENLABS_API_KEY,
        'Content-Type': 'application/json',
    }
    payload = {
        'text': text,
        'model_id': ELEVENLABS_MODEL,
        'voice_settings': {
            'stability': 0.4,           # Lower = more expressive/dynamic
            'similarity_boost': 0.85,
            'speed': 1.05,              # Slightly faster for news pacing
            'style': 0.35,              # Some style expression
        },
        'output_format': 'mp3_44100_128',
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    return r.content


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]
