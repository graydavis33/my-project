"""
sync_usage.py
Reads ~/.my-project-usage.json, computes stats per project,
writes usage-stats.json to the repo root, and commits + pushes.

Run from ANYWHERE with the shell alias:  usage
Or manually:  cd ~/Desktop/my-project && python sync_usage.py
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta


_LOG_PATH  = os.path.expanduser("~/.my-project-usage.json")
_STATS_OUT = os.path.join(os.path.dirname(__file__), "usage-stats.json")

# Friendly display names for each project key
_PROJECT_NAMES = {
    "email-agent":            "AI Email Agent",
    "invoice-system":         "Invoice & Accounting System",
    "morning-briefing":       "Daily Morning Briefing",
    "content-researcher":     "Content Researcher",
    "social-media-analytics": "Social Media Analytics",
}


def _load_log():
    if not os.path.exists(_LOG_PATH):
        return []
    with open(_LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _compute_stats(entries):
    now  = datetime.now(timezone.utc)
    week = now - timedelta(days=7)

    # Separate run entries (no cost_usd) from cost entries (have cost_usd)
    by_project_runs  = {}  # project → list of datetimes
    by_project_costs = {}  # project → {"this_week": float, "all_time": float}

    for e in entries:
        key = e.get("project")
        if not key:
            continue
        if "cost_usd" in e:
            dt   = datetime.fromisoformat(e["ts"])
            cost = e.get("cost_usd", 0) or 0
            tokens = e.get("tokens_in", 0) + e.get("tokens_out", 0)
            rec  = by_project_costs.setdefault(key, {"this_week": 0.0, "all_time": 0.0, "tokens_all_time": 0})
            rec["all_time"] += cost
            rec["tokens_all_time"] += tokens
            if dt >= week:
                rec["this_week"] += cost
        else:
            by_project_runs.setdefault(key, []).append(datetime.fromisoformat(e["ts"]))

    stats = {}
    for project in _PROJECT_NAMES:
        dts   = by_project_runs.get(project, [])
        costs = by_project_costs.get(project, {"this_week": 0.0, "all_time": 0.0})
        if not dts:
            stats[project] = {
                "last_used": None, "this_week": 0, "all_time": 0,
                "tokens_all_time":  costs.get("tokens_all_time", 0),
                "cost_this_week":   round(costs["this_week"], 4),
                "cost_all_time":    round(costs["all_time"], 4),
            }
            continue
        last_dt = max(dts)
        stats[project] = {
            "last_used":        last_dt.isoformat(),
            "this_week":        sum(1 for dt in dts if dt >= week),
            "all_time":         len(dts),
            "tokens_all_time":  costs.get("tokens_all_time", 0),
            "cost_this_week":   round(costs["this_week"], 4),
            "cost_all_time":    round(costs["all_time"], 4),
        }

    return stats


def _fmt_last_used(ts):
    """Return a human-friendly string like '2 days ago' or 'Today'."""
    if ts is None:
        return None
    dt  = datetime.fromisoformat(ts)
    now = datetime.now(timezone.utc)
    diff = now - dt
    days = diff.days
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days}d ago"
    if days < 30:
        return f"{days // 7}w ago"
    return f"{days // 30}mo ago"


def main():
    print("\n  Usage Stats Sync")
    print("  -----------------")

    entries = _load_log()
    if not entries:
        print(f"  No log found at {_LOG_PATH}")
        print("  Run a live script first to generate data.\n")
        # Still write an empty stats file so the dashboard doesn't fail
        stats_raw = {p: {"last_used": None, "this_week": 0, "all_time": 0,
                         "tokens_all_time": 0, "cost_this_week": 0.0, "cost_all_time": 0.0}
                     for p in _PROJECT_NAMES}
    else:
        stats_raw = _compute_stats(entries)
        print(f"  {len(entries)} total log entries found.\n")

    # Print summary table
    print(f"  {'Project':<35} {'Last Used':<14} {'Runs':>6} {'Tokens':>10} {'Cost (All)':>12}")
    print(f"  {'-'*35} {'-'*14} {'-'*6} {'-'*10} {'-'*12}")
    for project, s in stats_raw.items():
        name      = _PROJECT_NAMES.get(project, project)
        last_str  = _fmt_last_used(s["last_used"]) or "Never"
        cost      = s.get("cost_all_time", 0)
        cost_str  = f"${cost:.4f}" if cost else "—"
        tokens    = s.get("tokens_all_time", 0)
        tok_str   = f"{tokens:,}" if tokens else "—"
        print(f"  {name:<35} {last_str:<14} {s['all_time']:>6} {tok_str:>10} {cost_str:>12}")

    # Build the JSON output (add human-friendly last_used_label)
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "projects": {}
    }
    for project, s in stats_raw.items():
        output["projects"][project] = {
            "last_used":        s["last_used"],
            "last_used_label":  _fmt_last_used(s["last_used"]),
            "this_week":        s["this_week"],
            "all_time":         s["all_time"],
            "tokens_all_time":  s.get("tokens_all_time", 0),
            "cost_this_week":   s.get("cost_this_week", 0),
            "cost_all_time":    s.get("cost_all_time", 0),
        }

    with open(_STATS_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Wrote {_STATS_OUT}")

    # Git commit + push
    repo = os.path.dirname(__file__)
    try:
        subprocess.run(["git", "add", "usage-stats.json"], cwd=repo, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo
        )
        if result.returncode == 0:
            print("  No changes to commit — stats already up to date.")
        else:
            subprocess.run(
                ["git", "commit", "-m", "Update usage stats"],
                cwd=repo, check=True
            )
            subprocess.run(["git", "push"], cwd=repo, check=True)
            print("  Pushed to GitHub — dashboard updates in ~60s.")
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
