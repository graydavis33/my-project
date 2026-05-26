# Sai — Weekly Script Batch (SOP)

Repeatable workflow for ideating + drafting 7 talking-head shorts per week for Sai to batch-film in one day.

**Cadence:** Run this every week, ideally Sunday or Monday morning. Sai films Tuesday (or whichever day is "filming day" that week).

**Output:** One file at `business/social-media/sai/scripts/YYYY-MM-DD-batch.md` containing 7 scripts + research provenance + filming notes.

---

## Inputs (read these every run)

These are the corpus we draw from. Re-read before drafting — Sai's lanes evolve.

1. **Sai's LinkedIn finals** → `python-scripts/sai-linkedin/reference/voice/sai-linkedin-posts-final.md`
2. **Sai's collected newsletters** → `python-scripts/sai-linkedin/reference/voice/sai-newsletters-collected.md`
3. **Sai-edition hook templates** → `business/social-media/hook-templates-sai.md`
4. **Voice feedback log** → `~/.claude/projects/-Users-graydavis28/memory/feedback-sai-linkedin-voice.md`
5. **Format/shooting scripts library** → `plans/2026-04-16-sai-format-shooting-scripts.md`
6. **Winning patterns** (once populated) → `business/social-media/winning-patterns.md`
7. **Killed archive** (avoid resurrecting failed angles) → `business/social-media/killed-archive.md`

---

## Default Mix (confirm with Gray each week — may shift with strategy)

- **5 scripts in-lane** (75%) — proven topics from Sai's existing voice
- **2 scripts new territory** (25%) — topics he has high-conviction takes on in writing but hasn't said on video yet

Adjust the split if Gray says otherwise that week.

---

## Sai's Established Lanes (the 75%)

Pull from these for in-lane scripts. Updated as Sai's voice evolves.

| Lane | Source | Conviction |
|---|---|---|
| Time horizon / 3-5-10 year thinking | LinkedIn 2026-04-23 | High |
| Discipline / schedule / meditation | LinkedIn 2026-04-27, 2026-05-03 | High |
| Inputs over outputs | LinkedIn 2026-04-16 | High |
| Ethical business / scaling DOWN to scale up | Newsletter 1, 4 | High (his deepest moral conviction) |
| Above-and-beyond customer obsession (with TACTICS) | Newsletter 3 | High |
| Brother / Srikar partnership | Strategy doc + Newsletter 6 | High but underused on video — keep mining |
| BuiltGen → Trendify story arc | Strategy doc — "2nd agency" framing | High |
| Healthy vs unhealthy ego | Newsletter 1 | Medium |
| Game theory / playing the long game (dice roll story) | Newsletter 2 | Medium |
| Guaranteed success: clarity + purity | Newsletter 4 | Medium |

## New Territory Pool (the 25%)

Topics Sai has strong takes on in his newsletters but hasn't said on short-form yet. Rotate through these — once aired on video, they move into the "lane" list above.

- Fear is useless (Newsletter 6)
- AI-proofing by going more human (Newsletter 7)
- Mortality / "should you think about death" (Newsletter 2)
- Politics + psychology of attention (Newsletter 4 — Charlie Kirk analysis)
- "Learning from strangers" / knocking on dorms (Newsletter 1)
- Game theory dice roll metaphor told as a single story (Newsletter 2)

---

## Weekly Process — Step by Step

### Step 1 — Confirm scope with Gray (2 min)

- Default 5+2 mix, or does this week shift?
- Filming day confirmed?
- Any topic the strategy/voice memo says to lean into or avoid?

### Step 2 — Re-read the inputs (10–15 min)

Don't skip this. Sai's voice drifts — the latest LinkedIn post may reveal a fresh conviction, the newsletter you read last week may hit different now.

### Step 3 — Pick 7 topics (10 min)

- 5 from lanes — avoid repeating any topic that's been on video in the last 30 days (cross-check `video-log.csv`)
- 2 from new territory pool
- Cross-check against `killed-archive.md` — don't resurrect a failed angle without a real reason

### Step 4 — Draft each script (45–60 min total)

Per script, decide:
- **Hook style** — which V-template from `hook-templates-sai.md`
- **Visual style** — which Vis-template (Eye-Lock / Walk-and-Talk / Object Reveal etc.)
- **Length target** — 30–60s
- **B-roll asks** — anything to grab during the filming day
- **Source citation** — which newsletter / LinkedIn post the conviction came from

Then write the script in Sai's voice. Apply the AVOID rules from voice feedback log every time:

- "Founder" never "CEO"
- No "most founders…" punching down
- No AI-flavored summary closers
- No invented copywriter specifics (real numbers only)
- No 3-beat "no X, no Y, no Z" — cap at 2 with intensifier
- No identity-wrapped restatements ("for a founder, that's a cheat code")
- Question CTAs optional; default to landing on punchline
- Don't drop the verb in callbacks

### Step 5 — Write the batch file

Save to `business/social-media/sai/scripts/YYYY-MM-DD-batch.md` with sections:

1. Header (date, format, split, filming day, posting cadence)
2. Ideation Method — sources consulted + any decisions about NOT running fresh research
3. Voice Rules Applied (paste the AVOID list)
4. The 7 Scripts — each with Source / Format / Visual / Length / script body
5. Filming Notes — batching order, outfit changes, locations, B-roll asks, hook alternates
6. Tracking instructions — how to populate `video-log.csv` post-publish
7. Open Questions for Sai — anything to confirm before camera rolls

### Step 6 — Hand off to Sai (5 min)

- Drop the file link in Slack / wherever Sai reviews
- Flag the "Open Questions" section — those gate the shoot
- Confirm filming day + which scripts need Srikar / specific locations

### Step 7 — After Posting (ongoing)

For each script that ships:

1. Add row to `business/social-media/video-log.csv`:
   - `video_id`: `YYYY-MM-DD-slug`
   - `series`: e.g. `Sai Talking Head Batch 2026-05-26`
   - `pillar`: which lane/territory
   - `hook_style`: V-template number
   - `format`: `talking-head-short`
   - Leave `performance_tier` and 7-day metrics blank until they're in

2. After 7 days, fill in metrics. Compare to Sai's rolling average.

3. Promote winners to `winning-patterns.md`. Demote floppers to `killed-archive.md` with a retrospective note.

---

## Cost / Tool Notes

**Default workflow uses ZERO API spend.** All inputs are local files.

When to escalate to `content-researcher` or `creator-intel`:
- Sai's lane list feels exhausted (haven't added a new lane in 6+ weeks)
- A new niche or platform is being tested
- Sai asks for trending-topic reactive content
- Strategy shift introduces a completely new audience

Otherwise: Sai's own writing is a deeper well than any external research. Re-read first.

---

## Why This Workflow Exists

Batching 7 scripts at once is 4–5x more efficient than ad-hoc daily ideation, AND ensures topic diversity (no two consecutive shorts about the same lane). The weekly cadence forces a continuous read of Sai's evolving voice — which keeps drafts in his voice instead of drifting back to AI-flavored generic founder content.

The 75/25 lane/new-territory split is the iteration mechanism: in-lane content compounds his existing audience's expectations, new territory tests whether a topic should join the lanes for the next iteration.
