# Founder Story Short (Sai)

Theme: the money and fame dream → the emptiness → the culture mission. **15-shot** vertical short told through a red-yarn photo board + a dark-stage face-off between young Sai and current Sai.

**Sections:** Hook 1–2 · Body 3–10 · Conclusion 11–15.

_(Corrected 2026-08-06 from "16-shot / Conclusion 11–16" — verified against the live DB, which returns 15 rows. The header had not been updated after the 2026-08-05 deletion + renumber.)_

## Shoot schedule

Film **Tue 2026-08-11** (one day, ~13 shots filmed — shot 1 is fully AI, shot 11 is archival).
Edit 08-12 → 08-15, review 08-16, **post Mon 2026-08-17**.

Dedicated Google Calendar **"Founder Story Short — Shoot"** on gray@karramedia.com, built by
`.make_shoot_calendar.py` (idempotent — it finds the calendar by name and rebuilds the events,
so changing the dates in the script and re-running is safe). Gray shares it with Sai by hand.
Film day is grouped by SETUP, not shot order: board during the day, bedroom after dark.

## Canonical shot list — READ THIS BEFORE WRITING

There are **TWO** databases named "Shot List — Founder Story Short", in two different workspaces. Only one is real.

| | Workspace | Integration / token | Data source | URL |
|---|---|---|---|---|
| ✅ **REAL** | Gray Davis's Space | **Karra Automation** / `NOTION_KARRAMEDIA_TOKEN` | `d589d846-464f-4822-bd38-b50c7d3aa99b` | https://app.notion.com/p/01053269c0ae435b8205842af6d5eb8b |
| ❌ dead duplicate | Gray Davis's Notion | Graydient Automation / `NOTION_TOKEN` | `3cddfd3e-935b-411f-8335-5cf13e5f8686` | https://app.notion.com/p/d9ae3bfac16646379068dec6c95b60d0 |

**Always verify the data source id before any write.** On 2026-08-05 a whole session's edits (16 reconstructed rows, a renumber, a Rig column, 8 content edits) went into the duplicate and none of it reached Gray's actual list.

Columns: Section · Shot # · Frame Visual · Voiceover Script · Visuals · How to Film · How to Edit · Music/SFX · Light · Tags · Rig · FPS · Location · Gathered · Shot · Description (title).

**Script:** written 2026-07-28 in a Mac chat session — NOT yet pasted into the Notion page. The other part lives in a gray@karramedia Google Doc that gdocs-cli cannot see (its token is `drive.file` scope — only sees docs it created itself).

## Local files

- `reference-frames/` — reference frames (Higgsfield AI + internet refs), dragged into the DB's Frame Visual column. The Notion database IS the working view (no separate preview).

⚠️ **Frame filenames are off by one for the Conclusion.** Most files still use pre-renumber numbering from 2026-08-04, so `shotN-*.png` for N ≥ 11 is usually shot N+1 in the DB. Only `shot12-board-wide-ots-ai.png` and `shot16-team-photo-pushin-ai.png` (both generated 2026-08-05) match the real numbers. Rename pending.

## Change history

- **2026-08-04** (Mac) — frames generated + Notion scaffold built; the list text lived only in chat.
- **2026-08-05** (Windows) — rows rebuilt from the frames + commit messages, pushed to Notion. If a beat label reads wrong, that's why — correct it in Notion.
- **2026-08-05** (later) — Conclusion renumbered +1 (duplicate shot 10); "PENDING RE-EDIT" stripped from the last four shots; Rig column added.
- **2026-08-05** (evening) — shot 12 rewritten as an explicit OTS-with-person (the reference frame was a board-only stock photo that contradicted the text) with a new generated frame. Shot 17 restructured from the photo-swap into a subtle close-up push-in on the team photo as the final image. **Old shot 15 (photos-come-alive effect pan) deleted** — it had no VO line, duplicated shot 13's pan, and was the most expensive shot to build; the effect was folded into shot 13 as a 1–2 photo moment playing under that shot's existing line. Shots 16→15 and 17→16 renumbered. Stale cross-references fixed (shot 3 → 13, shot 6 self-ref → 5, shot 13 Light → 12, shot 15 How to Film → 2).

- **2026-08-06** — Shot 3 How to Edit: appended glow and venetian-blinds recipes for the archival videos inside the pinned photo (the effects Gray had already named in Visuals). **After Effects only** at Gray's call: build the shot in AE and Dynamic Link the comp into Premiere. Two things do NOT work in Premiere and were cut on purpose: Venetian Blinds is a clip-to-clip transition there, not a holdable effect, and there are no expressions for luminance-driven glow (hand-keyframe the opacity bump instead). Gray's original five bullets untouched. **Standing rule from this session: script and shot-list edits are additive only, never delete or rewrite Gray's text** (memory `feedback-scripts-add-never-delete`).

- **2026-08-06** (later) — **Props filled on all 15 shots, and the column converted multi-select -> rich text** at Gray's call so notes can carry quantities and per-shot usage (tags could not). The old multi-select options, including the never-placed "Blue suit", are gone with the type change. Notes now specify counts (~8-12 4x6 prints, 1 roll red yarn, ~25-30 push pins, 3-4 magnets) and shot-specific calls: same print size on shot 8 or the match cuts break, matte print on shot 15 because the Light column flags glare, overhead rig on shot 5 that the Rig column does not cover. Board shots carry a standing "CORK/BULLETIN BOARD REQUIRED" flag from shot 7 on. Shot 3's How to Edit condensed 2756 -> 1261 chars so its row height matches the rest of the table.

- **2026-08-06** (later still) — **AFTER EFFECTS blocks appended to the 9 VFX shots**: 1 (glitch/RGB split), 2 (bloom + party overlays), 4 (wall composite), 5 (3D floating photos + light wrap), 6 (reuse shot 5's rig), 8 (match-cut stabilize), 9 (Echo), 11 (whip transition), 13 (freeze-into-motion). Shots 7, 10, 12, 14, 15 deliberately skipped as plain A-roll (14 explicitly says "no effects"). Every append was additive and verified. **Shot 9's unnamed effect identified: it is Echo** (Effect > Time > Echo), with Posterize Time and Pixel Motion Blur given as the lighter alternatives.

- **2026-08-07** — **BOARD LOCKED: cork, wall-hung, vertical, wooden push pins.** Reverses the 2026-08-06 standing rule (free-standing rolling whiteboard + ball magnets) on every axis. Appended an additive, guarded `BOARD LOCKED 2026-08-07` block to 16 fields across shots 2, 3, 7, 8, 9, 10, 12, 13, 14, 15 (Props on all ten; Location on 2; Light on 2, 7, 9, 10, 12). Every write was guarded on the field's existing opening text and nothing was deleted or rewritten. Resolved shot 7's internal contradiction (its own row said yarn between MAGNETS above and push pins below: it is push pins). Lighting notes updated because matte cork has no gloss to fight but absorbs roughly a stop more than white. **Model conflict resolved and it was already solved:** both Sais exist as Higgsfield **Elements** (`Current Sai` 25938a11, `Young Sai` f44a14f8), which run natively on Nano Banana Pro and accept multiple `<<<uuid>>>` placeholders per prompt, so frame-chaining works and shot 1 can hold both selves. Soul V2 is not needed; no test credits were spent.

- **2026-08-07** (later) — **Shots 2, 3, 4, 5 reference frames regenerated against the cork board.** Shot 2 reframed to a **TRUE MACRO** at Gray's call, which makes it the one board shot that is **wall-independent** and can lock before the wall question is answered (`shot2-cork-MACRO-v1a-PENDING.png` is the pick). Shot 3 chained off it and registered perfectly, as its locked-plate row requires. Shots 4 and 5 each need one more pass (4 is wearing the element reference's blue suit; 5 is a stop dark and framed wide). **Three silent Higgsfield traps measured and recorded in the review log:** the model strings are inverted (`nano_banana_pro` is required to get Pro), `<<<element>>>` placeholders are ignored outright on Nano Banana 2, and Pro inherits the element's WARDROBE along with the face. All frames saved as `-PENDING`; nothing attached to Notion, nothing overwritten. Review page: https://claude.ai/code/artifact/3b234d7d-aa9d-4b3c-84f1-0b9d72f79a0a

## Open

- ⚠️ **Shot 2's Frame Visual still holds the REJECTED frames** (see hygiene section below) — the two new macros, the v2 pair and the corkboard test are all on disk and unattached, so the crew is reading frames the review log threw out.
- ⚠️ **Shots 9 and 10 are geometrically broken by wall-mounting.** Both are written as board-POV from behind the board's dark edge. Impossible on a wall-hung board. Proposed fix logged in both rows and in the review log: shoot from beside the board, edge as a dark foreground frame. **Awaiting Gray. Do not regenerate these two frames until confirmed.**
- ⚠️ **Which wall does the board go on?** A hung board cannot be rotated per shot, so this one choice locks the geometry of all 10 board shots and decides whether "every board shot on the right side of Sai, facing the bathroom" survives.
- ⚠️ **All board reference frames are stale** (they show the whiteboard). Shots 2, 3, 7, 8, 9, 10, 12, 13, 14, 15 need regenerating against the cork board.
- Shot 14 (hiring beat) has **no Voiceover Script and no Location** — needs Gray's script. Rig also unset.
- Shots 10 and 11 have **no How to Edit**.
- The photo-swap payoff (unpin money-and-fame, pin the team in the same spot — the mirror of shot 2) was removed with the shot 17 rewrite and has no home.
- The dead duplicate DB is still live and still able to cause confusion.

### Frame Visual hygiene (found 2026-08-07 in the live DB)

- **Shot 2 still shows REJECTED frames.** The v2 pair (`shot2-v2-frameA-board-empty.png`, `shot2-v2-frameB-photo-placed.png`) and the corkboard test exist on disk but were never attached; the DB still carries the frames the review log rejected (packed board, stock woman's portrait, no magnet mechanic, wrong camera side).
- **Frame Visual mixes two jobs with no marking** — frame references (what the shot should look like) vs generator inputs (raw photos fed into the AI). Shot 1 = 2 + 6, shot 2 = 2 + 4, shot 8 = 3 AI + 5 archival. Nobody films from a generator input. The review log calls this the biggest structural fix available.
- **Filenames disagree with shot numbers in BOTH directions**, and it starts at shot 4, not shot 11 as previously documented: shot 4 holds `shot5-*`, shot 6 holds `shot7-*`, shot 7 holds `shot8-*`, but shot 13 holds `shot12-*`.
- **Two frames are named `image.png`** (shots 5 and 14).
- **Shots 4 and 6 carry only one frame each**, against the multi-frame-per-shot plan.
