#!/usr/bin/env bash
# Manual sanity check for the footage organizer.
# SAFE: everything runs in a throwaway sandbox in /tmp — your real footage drive
# is never touched. Run it from the tool folder:
#
#     bash tests/manual_test.sh
#
set -u

TOOL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="$TOOL_DIR/.venv/bin/python"
SANDBOX="/tmp/fo-sandbox"

# Point the tool at the sandbox for THIS run only (does not change your .env or
# leak into your terminal). The placeholder key is fine — indexing/moving never
# call the API.
export SAI_LIBRARY_ROOT="$SANDBOX"
export ANTHROPIC_API_KEY="placeholder-not-used"

ok=0; bad=0
say_ok(){  echo "  ✅ $1"; ok=$((ok+1)); }
say_bad(){ echo "  ❌ $1"; bad=$((bad+1)); }

echo "Building a throwaway sandbox at $SANDBOX (your real footage is untouched)…"
rm -rf "$SANDBOX"
mkdir -p "$SANDBOX/01_ORGANIZED/shoot-day"
for c in C0001 C0002 C0003 C0004 C0005; do
  ffmpeg -loglevel error -f lavfi -i testsrc=duration=1:size=320x240:rate=10 \
         -pix_fmt yuv420p "$SANDBOX/01_ORGANIZED/shoot-day/$c.MP4" -y
done

echo
echo "TEST 1 — batch: file 5 clips into 2 videos (1+2 → Vid_01, 3+4 → Vid_02, 5 unmapped)"
"$PY" "$TOOL_DIR/cli_index.py" --client sai batch --num 1 \
   --from "01_ORGANIZED/shoot-day" --map "1:C0001-C0002 2:C0003-C0004" >/dev/null
B="$SANDBOX/01_ORGANIZED/Batch_01"
if [ -f "$B/Vid_01/C0001.MP4" ] && [ -f "$B/Vid_01/C0002.MP4" ]; then say_ok "Vid_01 has C0001 + C0002"; else say_bad "Vid_01 missing clips"; fi
if [ -f "$B/Vid_02/C0003.MP4" ] && [ -f "$B/Vid_02/C0004.MP4" ]; then say_ok "Vid_02 has C0003 + C0004"; else say_bad "Vid_02 missing clips"; fi
if [ -f "$SANDBOX/01_ORGANIZED/shoot-day/C0005.MP4" ]; then say_ok "unmapped C0005 left safely in place"; else say_bad "C0005 went missing"; fi
TAGGED="$("$PY" - <<PY
import sqlite3
c = sqlite3.connect("$SANDBOX/.footage-index.sqlite")
print(c.execute("SELECT COUNT(*) FROM clips WHERE batch_num=1").fetchone()[0])
PY
)"
if [ "$TAGGED" = "4" ]; then say_ok "index tagged all 4 clips as batch 1"; else say_bad "index tagged $TAGGED clips (expected 4)"; fi

echo
echo "TEST 2 — promote: move a finished project ACTIVE → DELIVERED → ARCHIVE"
mkdir -p "$SANDBOX/02_ACTIVE_PROJECTS/shorts/My Test Edit"
echo x > "$SANDBOX/02_ACTIVE_PROJECTS/shorts/My Test Edit/final.mp4"
"$PY" "$TOOL_DIR/cli_index.py" --client sai promote --item "My Test Edit" --to delivered >/dev/null
if [ ! -d "$SANDBOX/02_ACTIVE_PROJECTS/shorts/My Test Edit" ]; then say_ok "left ACTIVE"; else say_bad "still in ACTIVE"; fi
if find "$SANDBOX/03_DELIVERED/shorts" -name final.mp4 | grep -q .; then say_ok "arrived in DELIVERED/shorts/<week>"; else say_bad "not in DELIVERED"; fi
"$PY" "$TOOL_DIR/cli_index.py" --client sai promote --item "My Test Edit" --to archive >/dev/null
if find "$SANDBOX/04_ARCHIVE/shorts" -name final.mp4 | grep -q .; then say_ok "moved on to ARCHIVE"; else say_bad "not in ARCHIVE"; fi

echo
echo "TEST 3 — safety: refuses to act on a missing item (won't silently do nothing)"
ERR="$("$PY" "$TOOL_DIR/cli_index.py" --client sai promote --item "Does Not Exist" --to delivered 2>&1)"
if echo "$ERR" | grep -qi "not found"; then say_ok "clear error on a missing item"; else say_bad "no clear error"; fi

echo
echo "TEST 4 — ship: after delivery, archive the edit project + file the footage in one step"
V="Batch 9 Vid 1 - Demo"
mkdir -p "$SANDBOX/03_DELIVERED/shorts" "$SANDBOX/02_ACTIVE_PROJECTS/shorts/$V" "$SANDBOX/01_ORGANIZED/Batch_09/Vid_01"
echo x > "$SANDBOX/03_DELIVERED/shorts/$V.mp4"
echo x > "$SANDBOX/02_ACTIVE_PROJECTS/shorts/$V/edit.prproj"
ffmpeg -loglevel error -f lavfi -i testsrc=duration=1:size=320x240:rate=10 \
       -pix_fmt yuv420p "$SANDBOX/01_ORGANIZED/Batch_09/Vid_01/C9001.MP4" -y
"$PY" "$TOOL_DIR/cli_index.py" --client sai ship --video "$V" --yes >/dev/null
if [ ! -d "$SANDBOX/02_ACTIVE_PROJECTS/shorts/$V" ]; then say_ok "edit project left ACTIVE"; else say_bad "project still in ACTIVE"; fi
if find "$SANDBOX/04_ARCHIVE/shorts" -name edit.prproj | grep -q .; then say_ok "project archived"; else say_bad "project not archived"; fi
if find "$SANDBOX/05_FOOTAGE_LIBRARY" -name C9001.MP4 | grep -q .; then say_ok "footage filed into the library"; else say_bad "footage not filed"; fi

echo
echo "── Result: $ok passed, $bad failed ──"
echo "Cleaning up the sandbox…"
rm -rf "$SANDBOX"
if [ "$bad" = "0" ]; then
  echo "ALL GOOD ✅  batch + promote + index all work end-to-end."
  exit 0
else
  echo "Something failed ❌  — copy the output above and send it to me."
  exit 1
fi
