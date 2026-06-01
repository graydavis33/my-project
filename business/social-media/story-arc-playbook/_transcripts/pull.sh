#!/bin/bash
# Pull YouTube auto-captions for the story-arc-playbook reference videos.
# Usage: ./pull.sh
# Outputs cleaned plaintext transcripts to ./<slug>.txt + ./<slug>.meta.txt
set -e

cd "$(dirname "$0")"

declare -a VIDEOS=(
  "01-killer-script|https://www.youtube.com/watch?v=7I50PECz7SU"
  "02-master-storyteller|https://www.youtube.com/watch?v=t5Z-Q1bg1tU"
  "03-cant-stop-watching|https://www.youtube.com/watch?v=0f6_pRAIJjI"
  "04-irresistible-hooks|https://www.youtube.com/watch?v=LmXpbP7dD48"
  "05-10x-faster|https://www.youtube.com/watch?v=_Z11mjFh2zY"
  "06-killer-short|https://www.youtube.com/watch?v=PJWWGq_Yuoo"
  "07-7356-hooks|https://www.youtube.com/watch?v=PG0X3SjEmfU"
  "08-extra|https://www.youtube.com/watch?v=sRutnMnQGo4"
)

for entry in "${VIDEOS[@]}"; do
  slug="${entry%%|*}"
  url="${entry##*|}"
  echo ">>> $slug"

  # 1) Metadata pass (--print suppresses file writes, so do this standalone)
  yt-dlp --skip-download --no-warnings \
    --print "title:%(title)s" \
    --print "duration_string:%(duration_string)s" \
    --print "channel:%(channel)s" \
    --print "upload_date:%(upload_date)s" \
    --print "view_count:%(view_count)s" \
    "$url" > "${slug}.meta.txt" 2>/dev/null || echo "  meta failed"

  # 2) Subtitle pass
  yt-dlp --skip-download --no-warnings \
    --write-auto-sub --write-sub \
    --sub-lang en --sub-format vtt \
    --output "${slug}.%(ext)s" \
    "$url" > /dev/null 2>&1 || echo "  sub failed"

  # Find the VTT file yt-dlp wrote (it appends .en.vtt)
  vtt=$(ls ${slug}*.vtt 2>/dev/null | head -1)
  if [ -n "$vtt" ]; then
    python3 - "$vtt" "${slug}.txt" <<'PY'
import sys, re
vtt_path, out_path = sys.argv[1], sys.argv[2]
with open(vtt_path) as f:
    raw = f.read()
lines = []
for line in raw.splitlines():
    if not line.strip(): continue
    if line.startswith(('WEBVTT','Kind:','Language:','NOTE')): continue
    if '-->' in line: continue
    if re.match(r'^\d+$', line.strip()): continue
    clean = re.sub(r'<[^>]+>', '', line).strip()
    if clean: lines.append(clean)
out=[]
for l in lines:
    if not out or out[-1] != l: out.append(l)
with open(out_path,'w') as f:
    f.write('\n'.join(out))
print(f"  -> {out_path} ({len(out)} lines)")
PY
  else
    echo "  !! no VTT found"
  fi
done

echo ""
echo "Done. Files in $(pwd)"
