---
name: HyperFrames Usage — Visual Assets + Auto-Editing Training
description: How Gray uses HyperFrames (HeyGen HTML-to-video framework) — generating visual assets for videos and training it to auto-edit his shorts
type: project
originSessionId: 65b89a40-9219-49fa-ba99-8bb57e930be9
---
Gray uses **HyperFrames** (HeyGen's HTML-to-video framework) for two distinct goals:

## Goal 1 — Visual Asset Generator
Use HyperFrames to build **any visual asset for videos** — motion graphics, overlays, animated cards, lower thirds, transitions, etc. Treat it as a parameterized video-asset factory: write the composition in HTML/GSAP, render to MP4 (or transparent ProRes), drop into edits.

This is the same use case as the manual `build_lesson_card.py` work on `D:/Sai/.../lesson_cards/` — but HyperFrames is the generalized framework version of that approach.

## Goal 2 — Auto-Edit Training (in-progress)
Gray is **training HyperFrames to edit his shorts automatically** with no human in the loop, at a beginner-editor level:
- Trimming (cut dead space, trim heads/tails)
- Syncing audio to visuals
- Adding simple B-roll clips

**Scope:** Basic editing only — the goal is to free Gray from low-skill repetitive cuts so he can focus on **advanced editing** (color, sound design, complex pacing, story structure). Auto-edit is NOT meant to replace him on advanced work.

**Why:** Gray's biggest pain point is repetitive content creation eating time. Sai job = 1 short/day minimum. If HyperFrames handles the dumb cuts, he keeps the creative high-value time for himself.

## How to apply

- When Gray asks for a **visual asset** (animated text, motion graphic, lesson card, overlay, lower third), default to HyperFrames composition unless he's explicitly asking for a one-off Python/ffmpeg script
- When Gray asks for **short editing automation**, treat it as the auto-edit training track — keep it simple (trim + sync + B-roll), don't over-engineer it toward advanced editing yet
- HyperFrames projects live in `web-apps/hyperframes/` — currently only `test-onboarding/` is checked in (Mac view as of 2026-05-27). Real productions may live on Windows / not yet pushed
- Skills `/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/website-to-hyperframes`, `/gsap` exist but were not loaded in the Mac session of 2026-05-27 — may need `npx hyperframes skills` on Mac to install them locally
- Always lint compositions with `npx hyperframes lint` before declaring work done (rule from `web-apps/hyperframes/test-onboarding/CLAUDE.md`)
