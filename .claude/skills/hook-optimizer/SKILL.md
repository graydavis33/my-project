---
name: hook-optimizer
description: Score and optimize video hooks — generates title/hook/thumbnail candidates, ranks by curiosity and click potential. Triggers when Gray says "optimize this hook", "score these titles", "pick a hook for [concept]", "batch score hooks", or asks for thumbnail ideas. Wraps python-scripts/hook-optimizer/.
---

# Hook Optimizer

> ⚠️ SKELETON — fill in when this tool graduates from SOP → Agent (see `docs/tool-inventory.md`).

## When to use
- Single concept: "Give me 5 hooks for [video idea]"
- Batch: score a week of candidate hooks at once (not yet built)
- Pre-upload: final sanity check on chosen hook before posting

## Current stage: SOP
## Target stage: Agent

## Flow

1. Input: video concept (or batch CSV of concepts)
2. Claude generates 5 title options + 3 hook options + 1 thumbnail description per concept
3. Score each: curiosity, specificity, emotional pull, platform-fit
4. Cache to `results/` with date prefix
5. Output: top-3 ranked with rationale

## Known gaps
- No batch CLI mode
- No Slack integration
- Not hooked into Content Pipeline's `export_all_formats.py` (pending)

## Run commands
```
cd python-scripts/hook-optimizer && python main.py "your concept"
```

## Ties into
- Hook Bank (`business/social-media/content-playbook.md` Layer 1)
- Content Pipeline (consumer of scored hooks)
