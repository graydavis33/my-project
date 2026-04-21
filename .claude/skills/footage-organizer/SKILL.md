---
name: footage-organizer
description: Drop a folder of MP4/MOV files and Claude Haiku Vision analyzes 4 frames per clip to auto-organize into subfolders by content. Also archives unused/used footage and auto-deletes RAW. Triggers when Gray says "organize this footage", "sort my clips", "archive this shoot", "mark as used", or points at a footage folder. Wraps python-scripts/footage-organizer/.
---

# Footage Organizer

> ⚠️ SKELETON — fill in when this tool stabilizes at Agent (see `docs/tool-inventory.md`).

## When to use
- After any shoot: organize raw MP4/MOV dump into labeled subfolders
- `--mark-used` — move clips from unused/ to used/ after they ship in a final video
- Archive: auto-move clips into FOOTAGE_LIBRARY/unused/ and delete RAW

## Current stage: Agent (stable on Mac + Windows)
## Target stage: Agent (post-eval, polished)

## Flow

1. Input: path to folder of clips
2. For each clip: extract 4 frames, send to Claude Haiku Vision
3. Haiku categorizes: subject, setting, shot type, usefulness
4. Move into subfolder by primary category
5. Cache results to `.cache.json` (per-folder)
6. **Guardrail (shipped 2026-04-20):** runs `git fetch` + checks if remote has newer `.cache.json` before organize/archive/mark-used; warns + prompts to abort if behind

## Cost
~$0.003/clip

## Commands
```
cd python-scripts/footage-organizer
python main.py /path/to/footage/             # organize
python main.py --mark-used                   # move to used/
python main.py --archive /path/to/folder/    # into FOOTAGE_LIBRARY/unused/
```

## Known gaps
- Test-set.csv from real misses not built → eval.py not exercised
- April 16 clips in misc/ need manual re-sort (Windows cache issue before guardrail)
- Prompt not tightened via eval loop yet

## Ties into
- FOOTAGE_LIBRARY structure (unused/ vs used/ split, format-first Delivered folder)
- Sai Karra deliverables (primary data source)
