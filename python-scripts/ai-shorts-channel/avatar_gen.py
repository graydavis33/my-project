"""
Generates talking-head avatar videos via HeyGen API.
Produces two clips: hook (avatar intro) and outro (avatar CTA).
Polls async job until complete. Cached by text hash.
"""

import hashlib
import time
import requests
from pathlib import Path
from config import (
    HEYGEN_API_KEY, HEYGEN_AVATAR_ID,
    HEYGEN_API_BASE, HEYGEN_POLL_INTERVAL, HEYGEN_TIMEOUT,
    VIDEO_WIDTH, VIDEO_HEIGHT, TMP_DIR,
)

_HEADERS = {
    'X-Api-Key': HEYGEN_API_KEY,
    'Content-Type': 'application/json',
}


def generate_avatar_clips(script: dict) -> tuple[Path, Path]:
    """
    Generate hook and outro avatar clips.
    Returns (hook_path, outro_path).
    Cached by text hash — won't re-call API for identical text.
    """
    hook_path  = _generate_clip(script['hook'],  'hook')
    outro_path = _generate_clip(script['outro'], 'outro')
    return hook_path, outro_path


def _generate_clip(text: str, label: str) -> Path:
    out_path = TMP_DIR / f'avatar_{label}_{_hash(text)}.mp4'

    if out_path.exists():
        print(f"[heygen] {label} cache hit")
        return out_path

    print(f"[heygen] Submitting {label} clip generation...")
    video_id = _submit(text)
    print(f"[heygen] Job ID: {video_id} — polling...")
    download_url = _poll(video_id)
    _download(download_url, out_path)
    print(f"[heygen] {label} clip saved: {out_path.name}")
    return out_path


def _submit(text: str) -> str:
    payload = {
        'video_inputs': [{
            'character': {
                'type': 'avatar',
                'avatar_id': HEYGEN_AVATAR_ID,
                'avatar_style': 'normal',
            },
            'voice': {
                'type': 'text',
                'input_text': text,
                'voice_id': '',      # Leave empty to use avatar's default voice
            },
            'background': {
                'type': 'color',
                'value': '#0d0d0d',  # Dark background matching brand
            },
        }],
        'dimension': {
            'width': VIDEO_WIDTH,
            'height': VIDEO_HEIGHT,
        },
        'aspect_ratio': None,
    }

    r = requests.post(
        f'{HEYGEN_API_BASE}/v2/video/generate',
        json=payload,
        headers=_HEADERS,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"HeyGen submit error {r.status_code}: {r.text[:300]}")

    data = r.json()
    video_id = data.get('data', {}).get('video_id') or data.get('video_id')
    if not video_id:
        raise RuntimeError(f"HeyGen returned no video_id: {data}")
    return video_id


def _poll(video_id: str) -> str:
    deadline = time.time() + HEYGEN_TIMEOUT
    while time.time() < deadline:
        r = requests.get(
            f'{HEYGEN_API_BASE}/v1/video_status.get',
            params={'video_id': video_id},
            headers=_HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            time.sleep(HEYGEN_POLL_INTERVAL)
            continue

        data = r.json().get('data', {})
        status = data.get('status')

        if status == 'completed':
            url = data.get('video_url')
            if not url:
                raise RuntimeError("HeyGen completed but no video_url in response")
            return url

        if status == 'failed':
            raise RuntimeError(f"HeyGen generation failed: {data.get('error', 'unknown')}")

        print(f"[heygen] Status: {status} — waiting {HEYGEN_POLL_INTERVAL}s...")
        time.sleep(HEYGEN_POLL_INTERVAL)

    raise TimeoutError(f"HeyGen did not complete within {HEYGEN_TIMEOUT}s")


def _download(url: str, out_path: Path):
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]
