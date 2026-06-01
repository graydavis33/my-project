"""
Disk-based caching utilities. 7-day TTL, keyed by MD5 hash of concept.
"""
import hashlib
import json
import os
import time

_DIR = os.path.dirname(__file__)
_CACHE_FILE = os.path.join(_DIR, "results", ".cache.json")
_CACHE_TTL = 7 * 24 * 3600  # 7 days


def concept_key(concept: str) -> str:
    return hashlib.md5(concept.strip().lower().encode()).hexdigest()


def _load() -> dict:
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(cache: dict):
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    tmp = _CACHE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp, _CACHE_FILE)


def get_cached(concept: str):
    """Return cached result string if < 7 days old, else None."""
    cache = _load()
    entry = cache.get(concept_key(concept))
    if entry and time.time() - entry.get("cached_at", 0) < _CACHE_TTL:
        return entry["result"]
    return None


def store_cached(concept: str, result: str):
    cache = _load()
    cache[concept_key(concept)] = {
        "concept": concept,
        "result": result,
        "cached_at": time.time(),
    }
    _save(cache)
