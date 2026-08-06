#!/usr/bin/env python3
"""
shotvid — turn shotlist reference IMAGES into short reference VIDEOS via the Higgsfield CLI.

Why it exists: a still tells the crew the framing. A 5-second clip tells them the MOVE.
This adds that step to pre-production without babysitting a progress bar or burning credits.

The whole design is one idea: SUBMIT EVERYTHING AT ONCE, WALK AWAY, COLLECT LATER.
Nothing here ever blocks waiting on a single clip.

Usage:
    ./shotvid.py plan     shots.tsv        # cost preview, spends nothing
    ./shotvid.py submit   shots.tsv        # fires all jobs, returns in seconds
    ./shotvid.py collect                   # downloads whatever is finished; re-run freely
    ./shotvid.py status                    # what's pending / done / failed
    ./shotvid.py reroll   shot5            # re-run one shot (reuses cached upload)

Manifest (shots.tsv) — tab separated, '#' comments ignored:
    shot_id <TAB> image_path <TAB> motion_prompt [<TAB> seconds]

Prompt rule (important): the image already carries the LOOK. The prompt carries only the
MOTION. Re-describing the scene makes the model redraw it and drift off your reference.
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / "state.json"
OUT_DIR = HERE / "out"

# Locked defaults. Verified 2026-08-06: 1 credit per second, audio is free but useless
# for a silent shot reference, ~2 min turnaround, 496x864 output.
MODEL = "seedance_2_0_mini"
RESOLUTION = "480p"
ASPECT = "9:16"
SECONDS = 5


def run(args, timeout=600):
    """Run the higgsfield CLI and return parsed JSON (or raise with the real error)."""
    proc = subprocess.run(
        args, capture_output=True, text=True, timeout=timeout
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(shlex.quote(a) for a in args)}\n{proc.stderr.strip()}")
    out = proc.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def gen_flags(seconds, aspect=ASPECT):
    return [
        "--aspect-ratio", aspect,
        "--resolution", RESOLUTION,
        "--duration", str(seconds),
        "--generate-audio", "false",
    ]


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"uploads": {}, "jobs": {}}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def parse_manifest(path):
    shots = []
    for lineno, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) < 3:
            sys.exit(f"line {lineno}: need shot_id, image_path, motion_prompt (tab separated)")
        shot_id, image, prompt = parts[0], os.path.expanduser(parts[1]), parts[2]
        seconds = int(parts[3]) if len(parts) > 3 else SECONDS
        if not Path(image).exists():
            sys.exit(f"line {lineno}: image not found — {image}")
        shots.append({"shot_id": shot_id, "image": image, "prompt": prompt, "seconds": seconds})
    return shots


def cmd_plan(args):
    shots = parse_manifest(args.manifest)
    total = 0.0
    print(f"{'SHOT':<12}{'SECS':<6}{'CREDITS':<9}MOTION PROMPT")
    for s in shots:
        cost = run(["higgsfield", "generate", "cost", MODEL, "--prompt", s["prompt"]]
                   + gen_flags(s["seconds"]) + ["--json"])
        credits = float(cost.get("credits", cost)) if isinstance(cost, dict) else float(str(cost).split()[0])
        total += credits
        print(f"{s['shot_id']:<12}{s['seconds']:<6}{credits:<9.1f}{s['prompt'][:60]}")
    bal = run(["higgsfield", "account", "status"])
    print(f"\n{len(shots)} clips = {total:.1f} credits")
    print(f"account: {bal}")
    print("\nNothing was spent. Run `submit` when the prompts look right.")


def cmd_submit(args):
    shots = parse_manifest(args.manifest)
    state = load_state()
    print(f"submitting {len(shots)} jobs (not waiting for any of them)\n")
    for s in shots:
        sid = s["shot_id"]
        if sid in state["jobs"] and state["jobs"][sid].get("status") == "completed" and not args.force:
            print(f"  {sid:<12} already done — skipping (use reroll to redo)")
            continue
        upload_id = upload_once(state, s["image"])
        job = run(["higgsfield", "generate", "create", MODEL, "--prompt", s["prompt"]]
                  + gen_flags(s["seconds"]) + ["--start-image", upload_id, "--json"])
        job_id = job[0] if isinstance(job, list) else job.get("id")
        state["jobs"][sid] = {
            "job_id": job_id, "status": "pending", "prompt": s["prompt"],
            "image": s["image"], "seconds": s["seconds"],
        }
        save_state(state)
        print(f"  {sid:<12} queued  {job_id}")
    save_state(state)
    print("\nAll queued. Go do something else — clips take ~2 min each and run in parallel.")
    print("Come back and run:  ./shotvid.py collect")


def upload_once(state, image_path):
    """Upload an image the first time; reuse the media id forever after (free + instant)."""
    key = str(Path(image_path).resolve())
    cached = state["uploads"].get(key)
    if cached:
        return cached
    res = run(["higgsfield", "upload", "create", image_path, "--json"])
    media_id = res["id"] if isinstance(res, dict) else res
    state["uploads"][key] = media_id
    save_state(state)
    return media_id


def cmd_collect(args):
    state = load_state()
    OUT_DIR.mkdir(exist_ok=True)
    pending = [k for k, v in state["jobs"].items() if v.get("status") != "completed"]
    if not pending:
        print("nothing pending — everything already collected")
        return
    print(f"checking {len(pending)} job(s)\n")
    still_going = []
    for sid in pending:
        job = state["jobs"][sid]
        info = run(["higgsfield", "generate", "get", job["job_id"], "--json"])
        status = info.get("status")
        if status == "completed":
            url = info.get("result_url")
            dest = OUT_DIR / f"{sid}-ref.mp4"
            subprocess.run(["curl", "-sL", "-o", str(dest), url], check=True)
            job.update(status="completed", result_url=url, file=str(dest))
            print(f"  {sid:<12} downloaded -> {dest.name}")
        elif status in ("failed", "canceled"):
            job["status"] = status
            print(f"  {sid:<12} {status.upper()} — reroll it")
        else:
            still_going.append(sid)
            print(f"  {sid:<12} still rendering")
        save_state(state)
    save_state(state)
    if still_going:
        print(f"\n{len(still_going)} still rendering. Run collect again in a minute.")
    else:
        print(f"\nAll done. Clips are in {OUT_DIR}")


def cmd_status(args):
    state = load_state()
    if not state["jobs"]:
        print("no jobs yet")
        return
    for sid, j in state["jobs"].items():
        print(f"  {sid:<12}{j.get('status','?'):<12}{j.get('file','')}")


def cmd_reroll(args):
    state = load_state()
    job = state["jobs"].get(args.shot_id)
    if not job:
        sys.exit(f"no job recorded for {args.shot_id}")
    prompt = args.prompt or job["prompt"]
    upload_id = upload_once(state, job["image"])
    new = run(["higgsfield", "generate", "create", MODEL, "--prompt", prompt]
              + gen_flags(job["seconds"]) + ["--start-image", upload_id, "--json"])
    job_id = new[0] if isinstance(new, list) else new.get("id")
    state["jobs"][args.shot_id] = {**job, "job_id": job_id, "status": "pending", "prompt": prompt}
    save_state(state)
    print(f"{args.shot_id} requeued as {job_id} — run collect in ~2 min")


def main():
    p = argparse.ArgumentParser(description="Shotlist reference videos via Higgsfield")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("plan", help="cost preview, spends nothing")
    sp.add_argument("manifest")
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("submit", help="fire all jobs, return immediately")
    sp.add_argument("manifest")
    sp.add_argument("--force", action="store_true", help="resubmit even if already completed")
    sp.set_defaults(func=cmd_submit)

    sp = sub.add_parser("collect", help="download finished clips")
    sp.set_defaults(func=cmd_collect)

    sp = sub.add_parser("status", help="show job states")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("reroll", help="re-run one shot")
    sp.add_argument("shot_id")
    sp.add_argument("--prompt", help="new motion prompt")
    sp.set_defaults(func=cmd_reroll)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
