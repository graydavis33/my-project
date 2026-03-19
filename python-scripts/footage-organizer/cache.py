"""
cache.py
Permanent file-based cache for footage analysis results.
Cache key: MD5(basename + filesize) — same clip from any location hits the cache.
No TTL: footage analysis never expires.
"""
import hashlib
import json
import os

_DIR = os.path.dirname(__file__)
_CACHE_FILE = os.path.join(_DIR, ".cache.json")


def make_key(filepath: str) -> str:
    """MD5 of filename + filesize. Path-independent so same clip hits cache anywhere."""
    filename = os.path.basename(filepath)
    filesize = str(os.path.getsize(filepath))
    raw = filename + "|" + filesize
    return hashlib.md5(raw.encode()).hexdigest()


def _load() -> dict:
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(cache: dict):
    """Atomic write: write to .tmp then replace — prevents corrupt cache on crash."""
    tmp = _CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp, _CACHE_FILE)


def get_cached(filepath: str) -> str | None:
    """Return category string if this file was already analyzed, else None."""
    cache = _load()
    entry = cache.get(make_key(filepath))
    if entry:
        return entry["category"]
    return None


def store_cached(filepath: str, category: str):
    cache = _load()
    cache[make_key(filepath)] = {
        "filename": os.path.basename(filepath),
        "filesize": os.path.getsize(filepath),
        "category": category,
    }
    _save(cache)
