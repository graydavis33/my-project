"""Feature 2 — `pull --curate` planning logic. Given clip rows grouped by a tag
axis, the planner caps each theme at N, routes each theme into its own subfolder,
and (via the cmd path) forces horizontal-only. Tests the PLAN, not the file copy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import index
import cli_index
import pull as pull_mod
from index import ClipRecord


def _seed(db, paths_emotions, orientation="horizontal"):
    for i, (path, emotion) in enumerate(paths_emotions):
        index.upsert(db, ClipRecord(
            path=path, category="b-roll", format="long-form",
            filmed_date="2026-05-12", upload_date="2026-05-13",
            duration_s=3.0, width=1920, height=1080, codec="", sha1=path,
            orientation=orientation, emotion=emotion,
        ))


def test_curate_caps_per_theme_and_groups(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    # 7 focused, 2 stoic, all horizontal
    rows = [(f"b-roll/W05/F{i}.MP4", "focused") for i in range(7)]
    rows += [(f"b-roll/W05/S{i}.MP4", "stoic") for i in range(2)]
    _seed(db, rows)

    plan = cli_index._curate_plan(db, tmp_path, orientation="horizontal",
                                  curate_by="emotion", per_theme=5)
    assert plan["per_theme_count"] == {"focused": 5, "stoic": 2}

    # the stateful subfolder_fn caps live too (mirrors what pull copies)
    fn = plan["subfolder_fn"]
    placed = {}
    for r in plan["records"]:
        sub = fn(r)
        if sub is pull_mod.SKIP:
            continue
        placed.setdefault(sub, []).append(r.path)
    assert len(placed["focused"]) == 5
    assert len(placed["stoic"]) == 2


def test_curate_horizontal_only(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    _seed(db, [("b-roll/W05/H1.MP4", "calm")], orientation="horizontal")
    _seed(db, [("b-roll/W05/V1.MP4", "calm")], orientation="vertical")

    plan = cli_index._curate_plan(db, tmp_path, orientation="horizontal",
                                  curate_by="emotion", per_theme=5)
    assert {r.path for r in plan["records"]} == {"b-roll/W05/H1.MP4"}
    assert plan["per_theme_count"] == {"calm": 1}


def test_curate_group_by_action(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    index.upsert(db, ClipRecord(
        path="b-roll/W05/A.MP4", category="b-roll", format="long-form",
        filmed_date="2026-05-12", upload_date="2026-05-13", duration_s=3.0,
        width=1920, height=1080, codec="", sha1="A", orientation="horizontal",
        action="walking"))
    index.upsert(db, ClipRecord(
        path="b-roll/W05/B.MP4", category="b-roll", format="long-form",
        filmed_date="2026-05-12", upload_date="2026-05-13", duration_s=3.0,
        width=1920, height=1080, codec="", sha1="B", orientation="horizontal",
        action="typing"))

    plan = cli_index._curate_plan(db, tmp_path, orientation="horizontal",
                                  curate_by="action", per_theme=5)
    assert plan["per_theme_count"] == {"walking": 1, "typing": 1}


def test_curate_untagged_theme_and_sanitize(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    _seed(db, [("b-roll/W05/N.MP4", None)], orientation="horizontal")
    _seed(db, [("b-roll/W05/T.MP4", "Times Square")], orientation="horizontal")

    plan = cli_index._curate_plan(db, tmp_path, orientation="horizontal",
                                  curate_by="emotion", per_theme=5)
    assert "untagged" in plan["per_theme_count"]

    assert cli_index._sanitize_theme("Times Square") == "times-square"
    assert cli_index._sanitize_theme(None) == "untagged"
    assert cli_index._sanitize_theme("a/b: c!") == "ab-c"


def test_curate_subfolder_skips_overflow(tmp_path):
    db = tmp_path / "i.sqlite"
    index.init(db)
    _seed(db, [(f"b-roll/W05/F{i}.MP4", "focused") for i in range(4)])

    plan = cli_index._curate_plan(db, tmp_path, orientation="horizontal",
                                  curate_by="emotion", per_theme=2)
    fn = plan["subfolder_fn"]
    results = [fn(r) for r in plan["records"]]
    kept = [x for x in results if x is not pull_mod.SKIP]
    skipped = [x for x in results if x is pull_mod.SKIP]
    assert len(kept) == 2
    assert len(skipped) == 2
