"""
watch_delivered.py — watches 03_DELIVERED for newly exported/dropped videos and
runs the `ship` cleanup with Slack approval.

Per new video it sees:
  1. detect a NEW video file in 03_DELIVERED (one that wasn't there when the
     watcher started — it baselines the existing contents on first run)
  2. wait until the file stops growing (Premiere export finished)
  3. build the ship plan (cli_index._ship_plan) — archive the edit project +
     file the raw footage into the library
  4. post the plan to your Slack; you react ✅ to approve or ❌ to skip
  5. on ✅ → move the files + re-index, and report back in Slack

Run it in the foreground first to watch it work:

    cd python-scripts/footage-organizer
    .venv/bin/python watch_delivered.py --client sai

Stop with Ctrl-C. Needs SLACK_BOT_TOKEN + SLACK_USER_ID in .env (the same values
your other tools already use). Test the Slack link first with --self-test.
"""
import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import CLIENT_ROOTS, FOLDER_DELIVERED, VIDEO_EXTENSIONS, INDEX_DB_NAME
import cli_index

STATE_NAME = ".ship-watch-state.json"
DEFAULT_INTERVAL = 30                 # seconds between folder scans
APPROVE_TIMEOUT_SECONDS = 30 * 60     # give up waiting for a reaction after 30 min
REACT_POLL_SECONDS = 15
APPROVE_EMOJI = "white_check_mark"    # ✅
SKIP_EMOJI = "x"                      # ❌


# ---- pure helpers (unit-tested) -------------------------------------------

def _delivered_videos(delivered_root: Path) -> set:
    """Current video files anywhere under 03_DELIVERED, as POSIX paths relative to
    delivered_root. Skips AppleDouble + .DS_Store."""
    out = set()
    if not delivered_root.is_dir():
        return out
    for p in delivered_root.rglob("*"):
        if p.name.startswith("._") or p.name == ".DS_Store":
            continue
        if p.is_file() and p.suffix in VIDEO_EXTENSIONS:
            out.add(p.relative_to(delivered_root).as_posix())
    return out


def _stable_new_items(delivered_root: Path, seen: set, sizes: dict) -> list:
    """Return rel-paths of NEW videos whose size is unchanged since the previous
    scan (export finished). Updates `sizes` in place; a brand-new file is recorded
    this scan and only becomes 'ready' on the next scan if it hasn't grown."""
    ready = []
    current = _delivered_videos(delivered_root)
    for rel in current - seen:
        try:
            sz = (delivered_root / rel).stat().st_size
        except OSError:
            continue
        if sz > 0 and sizes.get(rel) == sz:
            ready.append(rel)
        sizes[rel] = sz
    for rel in list(sizes):              # forget vanished items
        if rel not in current:
            del sizes[rel]
    return ready


def _load_seen(state_path: Path) -> set:
    if state_path.exists():
        return set(json.loads(state_path.read_text()).get("seen", []))
    return set()


def _save_seen(state_path: Path, seen: set) -> None:
    state_path.write_text(json.dumps({"seen": sorted(seen)}, indent=2))


def _plan_text(library: Path, video: str, moves: list, warnings: list) -> str:
    lines = [f"📦 *{video}* was delivered. Clean-up plan:", ""]
    for m in moves:
        lines.append(f"• {m['what']}")
        lines.append(f"   `{m['src'].relative_to(library).as_posix()}`")
        lines.append(f"   → `{m['dest'].relative_to(library).as_posix()}`")
    for w in warnings:
        lines.append(f"⚠️ {w}")
    lines += ["", "React ✅ to do it, ❌ to skip."]
    return "\n".join(lines)


# ---- Slack handshake (needs live creds — tested with --self-test) ---------

def _await_reaction(slack, channel: str, ts: str) -> str:
    """Poll the posted message for the user's ✅ / ❌. Returns approve|skip|timeout."""
    end = time.time() + APPROVE_TIMEOUT_SECONDS
    while time.time() < end:
        try:
            msg = slack.reactions_get(channel=channel, timestamp=ts).get("message", {})
            names = {rx["name"] for rx in msg.get("reactions", [])}
            if APPROVE_EMOJI in names:
                return "approve"
            if SKIP_EMOJI in names:
                return "skip"
        except Exception as e:
            print(f"  [reaction poll error] {e}")
        time.sleep(REACT_POLL_SECONDS)
    return "timeout"


def _handle(library, db_path, slack, channel, delivered_root, rel):
    video = Path(rel).stem
    week = date.today()
    try:
        moves, warnings = cli_index._ship_plan(library, video, None, None, None, None, week)
    except ValueError as e:
        slack.chat_postMessage(channel=channel, text=f"⚠️ Couldn't plan cleanup for *{video}*: {e}")
        return
    if not moves:
        note = "; ".join(warnings) or "no project or footage found"
        slack.chat_postMessage(channel=channel,
                               text=f"📦 *{video}* delivered — nothing to auto-clean ({note}).")
        return

    resp = slack.chat_postMessage(channel=channel, text=_plan_text(library, video, moves, warnings))
    ts = resp["ts"]
    print(f"  posted plan for '{video}' — waiting for your ✅/❌ in Slack…")
    decision = _await_reaction(slack, channel, ts)

    if decision == "approve":
        cli_index._execute_ship(moves)
        added, _, removed = cli_index._reindex(library, db_path)
        slack.chat_postMessage(channel=channel, thread_ts=ts,
                               text=f"✅ Done — moved {len(moves)} item(s); re-indexed ({added} clips, {removed} pruned).")
        print(f"  ✅ executed cleanup for '{video}'")
    elif decision == "skip":
        slack.chat_postMessage(channel=channel, thread_ts=ts, text="🚫 Skipped — left everything as-is.")
        print(f"  🚫 skipped '{video}'")
    else:
        slack.chat_postMessage(channel=channel, thread_ts=ts,
                               text="⌛ No response — left as-is. Run `ship` by hand if you still want it.")
        print(f"  ⌛ timed out on '{video}'")


def _slack_client():
    token = os.getenv("SLACK_BOT_TOKEN")
    user = os.getenv("SLACK_USER_ID")
    if not (token and user):
        print("Error: add SLACK_BOT_TOKEN and SLACK_USER_ID to .env "
              "(the same values your other tools use).")
        sys.exit(1)
    from slack_sdk import WebClient
    return WebClient(token=token), user


def main():
    ap = argparse.ArgumentParser(description="Watch 03_DELIVERED → ship cleanup via Slack approval")
    ap.add_argument("--client", default="sai", choices=list(CLIENT_ROOTS.keys()))
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="seconds between scans")
    ap.add_argument("--self-test", action="store_true", help="post a test Slack message + confirm I can read your reaction, then exit")
    args = ap.parse_args()

    library = cli_index._library(args.client)
    db_path = library / INDEX_DB_NAME
    delivered_root = library / FOLDER_DELIVERED
    state_path = library / STATE_NAME
    slack, channel = _slack_client()

    if args.self_test:
        resp = slack.chat_postMessage(channel=channel,
                                      text="🛠️ Footage watcher test — react ✅ so I know I can read your approvals.")
        print("Posted a test message. React ✅ to it in Slack…")
        print("Result:", _await_reaction(slack, channel, resp["ts"]))
        return

    if not state_path.exists():
        seen = _delivered_videos(delivered_root)
        _save_seen(state_path, seen)
        print(f"Baselined {len(seen)} existing delivered video(s); watching for NEW exports only.")
    else:
        seen = _load_seen(state_path)
        print(f"Resuming — {len(seen)} item(s) already handled.")

    print(f"Watching {delivered_root} every {args.interval}s. Ctrl-C to stop.")
    sizes: dict = {}
    try:
        while True:
            for rel in _stable_new_items(delivered_root, seen, sizes):
                print(f"New delivered video detected: {rel}")
                _handle(library, db_path, slack, channel, delivered_root, rel)
                seen.add(rel)
                _save_seen(state_path, seen)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
