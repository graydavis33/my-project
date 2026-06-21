"""v4 Phase 3 — Vision tagging logic (no paid API calls). Tests the pure pieces:
the model-output coercion (analyzer._coerce_tags), writing tags onto a ClipRecord
(cli_index._apply_tags_to_record), the untagged filter, and the tag cache.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analyzer
import cache
import cli_index
import index
from index import ClipRecord


def _rec(path="b-roll/W05/C1.MP4"):
    return ClipRecord(path=path, category="b-roll", format="long-form",
                      filmed_date="2026-05-12", upload_date="2026-05-13",
                      duration_s=3.0, width=1920, height=1080, codec="", sha1="h")


# ── analyzer._coerce_tags ───────────────────────────────────────────────────

def test_coerce_normalizes_and_keeps_person_tags():
    out = analyzer._coerce_tags({
        "person_present": True, "emotion": "Happy ", "action": "Walking",
        "location": "NYC Street", "objects": ["Coffee Cup", "", "Laptop"],
    })
    assert out == {"person_present": True, "emotion": "happy", "action": "walking",
                   "location": "nyc street", "objects": ["coffee cup", "laptop"]}


def test_coerce_drops_emotion_action_when_no_person():
    out = analyzer._coerce_tags({
        "person_present": False, "emotion": "happy", "action": "walking",
        "location": "office", "objects": ["desk"],
    })
    assert out["emotion"] is None and out["action"] is None
    assert out["location"] == "office" and out["objects"] == ["desk"]


def test_coerce_handles_bad_types():
    out = analyzer._coerce_tags({"person_present": True, "objects": "not-a-list"})
    assert out["objects"] == []
    assert out["location"] is None  # missing → None


# ── cli_index._apply_tags_to_record ─────────────────────────────────────────

def test_apply_tags_sets_fields_and_packs_objects():
    rec = _rec()
    cli_index._apply_tags_to_record(rec, {
        "person_present": True, "emotion": "stoic", "action": "talking",
        "location": "times square", "objects": ["mic", "camera"],
    })
    assert rec.emotion == "stoic" and rec.action == "talking"
    assert rec.location == "times square"
    assert rec.objects == "|mic|camera|"
    assert index.unpack_objects(rec.objects) == ["mic", "camera"]


def test_apply_tags_forces_null_when_no_person():
    rec = _rec()
    # even if a stray emotion sneaks through, no person ⇒ no emotion/action
    cli_index._apply_tags_to_record(rec, {
        "person_present": False, "emotion": "happy", "action": "walking",
        "location": "subway", "objects": ["train"],
    })
    assert rec.emotion is None and rec.action is None
    assert rec.location == "subway" and rec.objects == "|train|"


def test_apply_tags_empty_objects_become_none():
    rec = _rec()
    cli_index._apply_tags_to_record(rec, {"person_present": False, "location": "cafe", "objects": []})
    assert rec.objects is None


# ── _is_untagged ────────────────────────────────────────────────────────────

def test_is_untagged():
    assert cli_index._is_untagged(_rec()) is True
    rec = _rec(); rec.location = "office"
    assert cli_index._is_untagged(rec) is False


# ── tag cache ───────────────────────────────────────────────────────────────

def test_tag_cache_roundtrip(tmp_path, monkeypatch):
    clip = tmp_path / "C1.MP4"
    clip.write_bytes(b"x" * 100)
    monkeypatch.setattr(cache, "_TAG_CACHE_FILE", str(tmp_path / ".tag-cache.json"))

    assert cache.get_cached_tags(str(clip)) is None
    tags = {"person_present": True, "emotion": "stoic", "action": None,
            "location": "office", "objects": ["laptop"]}
    cache.store_cached_tags(str(clip), tags)
    assert cache.get_cached_tags(str(clip)) == tags
