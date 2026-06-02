"""Watch captions.json — auto-run rebuild.py whenever it changes.

Run this in a separate terminal alongside `npx hyperframes preview`.
Edit captions.json -> save -> browser hot-reloads in ~1s.

Usage:
    python watch.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).parent
CAPTIONS = ROOT / "captions.json"
REBUILD = ROOT / "rebuild.py"
POLL_S = 0.5


def main() -> int:
    if not CAPTIONS.exists():
        print(f"ERROR: {CAPTIONS} not found")
        return 1
    if not REBUILD.exists():
        print(f"ERROR: {REBUILD} not found")
        return 1

    print(f"Watching {CAPTIONS.name} (poll every {POLL_S}s). Ctrl+C to stop.")
    print(f"Edit + save captions.json -> rebuild.py runs -> HyperFrames hot-reloads.")
    last_mtime = CAPTIONS.stat().st_mtime
    # Initial build
    subprocess.run([sys.executable, str(REBUILD)], cwd=str(ROOT))

    while True:
        try:
            time.sleep(POLL_S)
            mtime = CAPTIONS.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                # debounce — wait for editor to finish writing
                time.sleep(0.10)
                print(f"\n[{time.strftime('%H:%M:%S')}] captions.json changed — rebuilding...")
                r = subprocess.run([sys.executable, str(REBUILD)], cwd=str(ROOT))
                if r.returncode != 0:
                    print(f"  ! rebuild failed (rc={r.returncode}) — fix and re-save")
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0
        except FileNotFoundError:
            print(f"captions.json disappeared — waiting...")
            time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())
