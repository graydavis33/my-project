# Monetization Strategist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standing subagent that maintains a monetization opportunity pipeline — analyzing each session's delta at /save, briefing Gray at /prime, never building anything without approval.

**Architecture:** Pure markdown/JSON — no Python. A subagent definition in `.claude/agents/`, two state files in `business/monetization/` (living pipeline doc + JSON cursor), and small edits to the `/save` and `/prime` command docs. The cursor guarantees delta-only analysis; the one-time historical backfill is explicitly deferred to a separate session on Gray's go.

**Tech Stack:** Claude Code subagents (`.claude/agents/*.md`), slash-command docs (`.claude/commands/*.md`), git.

**Spec:** `docs/superpowers/specs/2026-07-08-monetization-strategist-design.md` — read it before starting any task.

## Global Constraints

- **No dollar amounts, revenue figures, or client terms in any `business/monetization/` file** (repo is public).
- **Strategist never builds** — every recommendation ends in a next action for Gray to approve.
- **Token bounds:** delta-only analysis behind the `state.json` cursor; web research only when promoting a candidate to WATCHLIST/NOW, max ~5 targeted searches per candidate; never re-research already-scored entries.
- **Never auto-backfill:** missing/corrupt `state.json` → report it and reset the cursor to today.
- **Hard gate before scoring:** side-doable. Fails → KILLED, not scored.
- **Doc + code same commit:** each task folds its CLAUDE.md line into its own commit.
- **Model for the subagent:** `claude-sonnet-4-6` (house default).
- **No hour estimates anywhere** — complexity terms only (simple/moderate/gnarly).

---

### Task 1: State scaffold — `business/monetization/`

**Files:**
- Create: `business/monetization/PIPELINE.md`
- Create: `business/monetization/state.json`
- Modify: `CLAUDE.md` (folder map, `business/` bullet)

**Interfaces:**
- Produces: `business/monetization/PIPELINE.md` with exactly the four H2 sections `## NOW`, `## WATCHLIST`, `## RADAR`, `## KILLED` (Task 2's agent edits these; Task 4's /prime step reads them). `business/monetization/state.json` with keys `last_analyzed_commit` (string|null), `last_analyzed_date` (string|null, YYYY-MM-DD), `backfill_complete` (bool), `version` (int).

- [ ] **Step 1: Create `business/monetization/PIPELINE.md`**

````markdown
# Monetization Pipeline

_Maintained by the `monetization-strategist` subagent (spec: `docs/superpowers/specs/2026-07-08-monetization-strategist-design.md`). Written at `/save`, read at `/prime` ("Monetization Watch"). Gray may edit by hand — the strategist preserves manual edits._

**Rules for this file:** no dollar figures, revenue numbers, or client terms (public repo) — pitches and scores only. KILLED is append-only. One candidate max in NOW.

_Last strategist run: none yet_
_Backfill: pending (runs on Gray's explicit go — see spec)_

---

## NOW

_(empty — no candidate has cleared the bar yet)_

## WATCHLIST

_(empty)_

## RADAR

_(empty)_

## KILLED

_(none)_
````

- [ ] **Step 2: Create `business/monetization/state.json`**

```json
{
  "last_analyzed_commit": null,
  "last_analyzed_date": null,
  "backfill_complete": false,
  "version": 1
}
```

- [ ] **Step 3: Add the folder to CLAUDE.md's folder map**

In `CLAUDE.md`, find the `business/` bullet in the **Folder map** (it begins `- \`business/\` — contracts, leads, reference docs (Sai job notes). Includes \`sai-karra/content-os/\``). Append this sentence to the end of that bullet:

```
Also `business/monetization/` — the monetization-strategist's opportunity pipeline (PIPELINE.md + state.json cursor; written at /save, read at /prime).
```

- [ ] **Step 4: Verify**

Run: `python -c "import json; d=json.load(open('business/monetization/state.json')); assert d['version']==1 and d['backfill_complete'] is False; print('state.json OK')"`
Expected: `state.json OK`

Run: `python -c "s=open('business/monetization/PIPELINE.md',encoding='utf-8').read(); assert all(h in s for h in ['## NOW','## WATCHLIST','## RADAR','## KILLED']); print('PIPELINE.md OK')"`
Expected: `PIPELINE.md OK`

- [ ] **Step 5: Commit**

```bash
git add business/monetization/ CLAUDE.md
git commit -m "feat: monetization pipeline state scaffold (PIPELINE.md + state.json cursor)"
```

---

### Task 2: The subagent — `.claude/agents/monetization-strategist.md`

**Files:**
- Create: `.claude/agents/monetization-strategist.md`
- Modify: `CLAUDE.md` (folder map, `.claude/agents/` bullet)

**Interfaces:**
- Consumes: `business/monetization/PIPELINE.md` + `state.json` from Task 1 (exact section names and JSON keys as defined there).
- Produces: an agent invocable as subagent_type `monetization-strategist` whose **daily-run prompt contract** is: a prompt containing `Daily run. Session date: YYYY-MM-DD.` + a `SESSION SUMMARY:` block + a `FILES CHANGED THIS SESSION:` block + a `DISCUSSION-ONLY SIGNALS:` block, and whose **deep-dive prompt contract** is: a prompt starting `Deep-dive: <idea name>`. Both return a short text report (≤10 lines). Tasks 3 and 4 rely on these contracts.

- [ ] **Step 1: Create `.claude/agents/monetization-strategist.md`** with exactly this content:

````markdown
---
name: monetization-strategist
description: Gray's monetization strategist. Maintains the sellable-opportunity pipeline at business/monetization/PIPELINE.md. Invoked automatically at /save (daily run — analyze the session delta, update the pipeline), and on demand when Gray says "develop [idea]", "deep-dive [idea]", or "pull [idea] back up" (deep-dive mode — full product brief). Strategist ONLY — plans and recommends; never builds anything. Runs in its own context so the main session stays lean.
tools: Read, Glob, Grep, Write, Edit, WebSearch, WebFetch
model: claude-sonnet-4-6
---

# Monetization Strategist

Your only job: find and develop things Gray can **sell** — products, templates, services, features — out of the work he does every day. The long-term goal is income that doesn't require Gray's hours: Graydient Media shifting from pure time-for-money (Sai job + freelance) toward products that sell while he's out filming.

This is a long-term watch. Nothing may surface for six months; three things may surface in a month. "Nothing new" is a valid, expected outcome — never force a pick.

Talk like a teammate: lead with the answer, no filler, no emojis. Your final message is a report, not a conversation.

## Hard rules (do not violate)

1. **Cursor first.** Read `business/monetization/state.json` before anything else. Only analyze material newer than the cursor. When done, set `last_analyzed_date` to the session date and `last_analyzed_commit` to the current HEAD hash (`git log -1 --format=%H` via the file list you were given — if you can't determine it, leave the commit field unchanged and update the date only). If `state.json` is missing or corrupt: say so in your report, recreate it with today's date and `backfill_complete: false`, and analyze ONLY the input you were handed. NEVER rescan history to compensate. NEVER run the backfill yourself.
2. **Strategist only — never build.** No code, no landing pages, no scaffolds. Every NOW recommendation ends in a concrete next action *for Gray to approve*.
3. **Side-doable hard gate.** Gray's time budget is a few hours a week around the Sai job. Anything that needs full-time Gray, ongoing support duty he can't carry, or a hard launch window goes straight to KILLED — no matter how good the idea. Apply this BEFORE scoring.
4. **Bounded research.** Web research (WebSearch/WebFetch) is allowed ONLY when you are promoting a candidate to WATCHLIST or NOW — max ~5 targeted searches per candidate (Reddit threads, competitor products + pricing pages, news, social signals). RADAR jottings get zero research. Already-scored entries never get re-researched. In deep-dive mode you may go broader, but stay purposeful — verify or kill, don't wander.
5. **Market check before WATCHLIST.** A candidate cannot enter WATCHLIST without a market check. If the check says dead (saturated, strong free alternatives, no demand signal), it goes straight to KILLED with the evidence links — Gray never hears it pitched.
6. **KILLED is append-only and binding on you, not on Gray.** Never re-pitch a killed idea unless materially new evidence appears. If Gray says "pull X back up", treat it as a deep-dive request — his call overrides the kill.
7. **Public repo.** No dollar amounts, revenue figures, income details, or client contract terms in ANY file you write. Pitches, scores, links, and complexity terms only. No hour estimates ever — simple/moderate/gnarly.
8. **Report kills.** Every idea you kill (this run) appears in your report by name with a one-line reason. They also stay in the KILLED section with date + reason + evidence links so Gray can resurrect them.
9. **Quiet sessions are cheap.** If the session contains nothing monetization-relevant, bump the cursor, touch nothing else, and report "nothing monetization-relevant this session."
10. **Preserve manual edits.** Gray may have edited PIPELINE.md by hand. Never rewrite the file wholesale — make targeted edits.

## Scoring model

Score each candidate 0–3 on five dimensions (after it passes the side-doable gate):

1. **Demand evidence** — has anyone shown they'd pay? Verified against the real market (Reddit, competitor pricing, news, social), not intuition.
2. **Effort to ship** — Gray-effort to a sellable v1 (simple=3, moderate=2, gnarly=0–1).
3. **Maintenance burden** — ongoing support/updates (near-zero=3, SaaS-with-support=0–1).
4. **Distribution fit** — can Gray's existing channels (@graydient_media audience, content brand, network) reach this buyer?
5. **Price potential** — revenue shape; at equal scores, template/structure/info-product beats SaaS (support burden).

Record scores inline like `[D2 E3 M3 F2 P1 = 11/15]`.

## PIPELINE.md editing rules

- **NOW** — at most ONE candidate: what it is, why now, the score line, the concrete next action for Gray, and your current take (1–2 sentences). May be empty ("no candidate meets the bar").
- **WATCHLIST** — a handful of scored ideas, ruthlessly pruned. Each entry: `**Name** [score line] (added YYYY-MM-DD)` + one-line pitch + one line on what evidence would promote it to NOW. Evidence links from the market check.
- **RADAR** — one-liners: weak signals worth watching, not yet scored, no research spent.
- **KILLED** — append-only: `**Name** (killed YYYY-MM-DD)` + reason + evidence links.
- Update the `_Last strategist run:` line at the top with the session date on every run.

## Daily run procedure

Your prompt contains: `Daily run. Session date: YYYY-MM-DD.`, a SESSION SUMMARY block, a FILES CHANGED THIS SESSION block, and a DISCUSSION-ONLY SIGNALS block.

1. Read `business/monetization/state.json`, then `business/monetization/PIPELINE.md`.
2. Scan the summary + signals for monetization material: new tools/systems built, pain Gray hit repeatedly (his pain = market pain), things Gray said about selling/audience/products, external validation that appeared naturally.
3. If something new is worth tracking: add to RADAR (no research) or, if it's strong enough to score, run the bounded market check and place it in WATCHLIST / promote to NOW / kill it.
4. Re-evaluate NOW/WATCHLIST only against the new information from this session — no re-research.
5. Make your targeted PIPELINE.md edits, bump the cursor in state.json.
6. Report (≤10 lines): what changed in the pipeline this run · every kill by name + reason · current NOW + its next action (or "quiet") · if `backfill_complete` is false, end with "(backfill still pending)".

## Deep-dive mode

Trigger: prompt starts `Deep-dive: <idea>`. Produce a product brief at `business/monetization/briefs/YYYY-MM-DD-<idea-slug>.md` covering: the buyer and their pain (with real evidence links) · competitor/comp landscape with pricing links · positioning (why Gray's version wins) · offer shape (template / info-product / service / SaaS — with your recommendation) · pricing approach (structure, not Gray's revenue projections) · Gray-effort as simple/moderate/gnarly per component · a validation plan (cheapest test of real demand BEFORE building) · the single first step. Update the idea's WATCHLIST/NOW entry to link the brief. Report a ≤10-line digest. Still zero building.
````

- [ ] **Step 2: Add the agent to CLAUDE.md's folder map**

In `CLAUDE.md`, find the `.claude/agents/` bullet in the **Folder map** (begins `- \`.claude/agents/\` — custom subagents.`). Append this sentence to the end of that bullet:

```
`monetization-strategist` (maintains the sellable-opportunity pipeline in `business/monetization/`; auto-runs at /save, deep-dives on "develop [idea]"; strategist only — never builds; implements `docs/superpowers/specs/2026-07-08-monetization-strategist-design.md`).
```

- [ ] **Step 3: Verification test A — relevant session updates the pipeline**

Freshly created agents may not be registered as a subagent_type until the session reloads. Use whichever works: spawn subagent_type `monetization-strategist`, or fall back to subagent_type `general-purpose` with this prefix added to the prompt: `You are the monetization-strategist. Read ".claude/agents/monetization-strategist.md" and follow it exactly as your instructions for this input:`

Spawn with this prompt:

```
Daily run. Session date: 2026-07-08.
SESSION SUMMARY:
Built a "thumbnail-pattern-analyzer" script that pulls a creator's top-10 thumbnails and decodes them into a reusable checklist. Gray said "honestly other creators would pay for this checklist" during the session. Also fixed a typo in dashboard.html.
FILES CHANGED THIS SESSION:
python-scripts/thumbnail-analyzer/main.py
dashboard.html
DISCUSSION-ONLY SIGNALS: none
```

Expected agent behavior (verify after it returns):
- `business/monetization/PIPELINE.md` gained a RADAR or WATCHLIST entry about the thumbnail checklist (WATCHLIST only if it ran a market check — either is acceptable)
- `state.json` now has `"last_analyzed_date": "2026-07-08"`
- The returned report is ≤10 lines and mentions the addition
- Nothing was built; no files outside `business/monetization/` were modified

- [ ] **Step 4: Verification test B — irrelevant session only bumps the cursor**

First note the current content: `git diff --stat business/monetization/` should be the baseline. Spawn (same fallback rule) with:

```
Daily run. Session date: 2026-07-08.
SESSION SUMMARY:
Re-synced the footage index and fixed a broken symlink in the Obsidian vault. No new tools, no product discussion.
FILES CHANGED THIS SESSION: none
DISCUSSION-ONLY SIGNALS: none
```

Expected: report says nothing monetization-relevant; `PIPELINE.md` unchanged except possibly the `_Last strategist run:` line; `state.json` cursor still `2026-07-08`.

- [ ] **Step 5: Verification test C — killed ideas are not re-pitched**

Manually append to the KILLED section of `PIPELINE.md`:

```
**Preset-pack marketplace** (killed 2026-07-08) — saturated market, race-to-the-bottom pricing. (test entry)
```

Spawn (same fallback rule) with:

```
Daily run. Session date: 2026-07-08.
SESSION SUMMARY:
Gray spent an hour organizing his color-grading presets and mentioned the preset-pack marketplace idea again in passing, with no new information.
FILES CHANGED THIS SESSION: none
DISCUSSION-ONLY SIGNALS: none
```

Expected: report does NOT re-pitch the preset-pack idea (at most it notes the mention adds no new evidence); the idea does NOT appear in NOW/WATCHLIST/RADAR.

- [ ] **Step 6: Reset the pipeline to clean state**

The tests wrote synthetic entries. Reset both files so no test junk leaks into the real pipeline:

```bash
git checkout -- business/monetization/PIPELINE.md business/monetization/state.json
git status --short business/monetization/
```

Expected: no output from `git status` (files match the Task 1 commit).

- [ ] **Step 7: Commit**

```bash
git add .claude/agents/monetization-strategist.md CLAUDE.md
git commit -m "feat: monetization-strategist subagent (daily delta runs + deep-dive briefs)"
```

---

### Task 3: /save integration — the write path

**Files:**
- Modify: `.claude/commands/save.md` (insert new Step 5; renumber old Steps 5–6 to 6–7)
- Modify: `CLAUDE.md` (Session Commands list, `/save` line)

**Interfaces:**
- Consumes: the daily-run prompt contract from Task 2 (exact block labels `SESSION SUMMARY:`, `FILES CHANGED THIS SESSION:`, `DISCUSSION-ONLY SIGNALS:`).

- [ ] **Step 1: Insert the new step into `.claude/commands/save.md`**

Immediately after the Step 4 section (Obsidian note) and its closing `---`, and before the current `## Step 5: Push to GitHub` heading, insert:

````markdown
## Step 5: Run the Monetization Strategist

Spawn the `monetization-strategist` subagent (Agent tool). If that subagent type isn't available in this session (fresh registry), spawn `general-purpose` instead with this prefix: `You are the monetization-strategist. Read ".claude/agents/monetization-strategist.md" and follow it exactly as your instructions for this input:`

Prompt (fill the placeholders):

```
Daily run. Session date: <YYYY-MM-DD>.
SESSION SUMMARY:
<the session-note content you just wrote in Step 4>
FILES CHANGED THIS SESSION:
<file paths changed this session — from the session's commits (git log) or git status; write "none" if none>
DISCUSSION-ONLY SIGNALS: <1-3 bullets of monetization-relevant things that were TALKED about but left no file trace, or "none">
```

It updates `business/monetization/PIPELINE.md` + `state.json` and returns a short report — include that report in the Step 7 confirmation. **Never let this step block the save:** if the strategist errors or hangs, note it and continue to Step 6 — the cursor didn't move, so the missed delta is analyzed automatically next session.

---
````

- [ ] **Step 2: Renumber the old steps**

In the same file: change `## Step 5: Push to GitHub` → `## Step 6: Push to GitHub`, and `## Step 6: Confirm` → `## Step 7: Confirm`. In the (now) Step 7 bullet list, add one bullet: `- The monetization-strategist's report (or "strategist skipped/errored" if it didn't run)`.

- [ ] **Step 3: Update CLAUDE.md Session Commands**

In `CLAUDE.md` under **Session Commands**, change the `/save` line from:

```
- `/save` — session end: commits + pushes + updates dashboard.
```

to:

```
- `/save` — session end: commits + pushes + updates dashboard + runs the monetization-strategist on the session delta.
```

- [ ] **Step 4: Verify**

Run: `python -c "s=open('.claude/commands/save.md',encoding='utf-8').read(); assert 'Step 5: Run the Monetization Strategist' in s and 'Step 6: Push to GitHub' in s and 'Step 7: Confirm' in s and s.count('## Step') == 7; print('save.md OK')"`
Expected: `save.md OK`

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/save.md CLAUDE.md
git commit -m "feat: /save runs the monetization-strategist on the session delta"
```

---

### Task 4: /prime integration — the read path

**Files:**
- Modify: `.claude/commands/prime.md`
- Modify: `CLAUDE.md` (Session Commands list, `/prime` line)

**Interfaces:**
- Consumes: `business/monetization/PIPELINE.md` section names from Task 1 (`## NOW`, `## WATCHLIST`, `## RADAR`, `## KILLED`) and the `_Last strategist run:` line.

- [ ] **Step 1: Add the pipeline to the /prime reading list**

In `.claude/commands/prime.md` Step 1, append to the file list (after `- \`context/goals.md\``):

```
- `business/monetization/PIPELINE.md`
```

- [ ] **Step 2: Add the Monetization Watch section to the briefing**

In the same file, in Step 3's briefing format, insert between the `**My suggestion for today:**` block and the `**Top 3 MCP servers to add:**` block:

```markdown
**Monetization Watch:**
From `business/monetization/PIPELINE.md` — read-only, no subagent, no analysis. 3–6 lines:
- The NOW candidate + its next action and your recommended course of action (or "quiet — still watching")
- Anything added to WATCHLIST/RADAR since the previous session (use the entries' added-dates)
- Any ideas KILLED since the previous session — named, with the reason (Gray can pull any back up)
If the pipeline is empty and backfill is pending, say so in one line.
```

- [ ] **Step 3: Update CLAUDE.md Session Commands**

In `CLAUDE.md` under **Session Commands**, change the `/prime` line from:

```
- `/prime` — run at session start. Loads context, checks recent commits, briefs on priorities.
```

to:

```
- `/prime` — run at session start. Loads context, checks recent commits, briefs on priorities + Monetization Watch.
```

- [ ] **Step 4: Verify by rendering the section**

Read `business/monetization/PIPELINE.md` and compose the Monetization Watch section exactly as prime.md now specifies. With the clean scaffold it should render as one line, e.g.: `Monetization Watch: pipeline empty — backfill pending (runs on your go); quiet, still watching.` Confirm nothing in the instructions forces a subagent spawn or web call.

Run: `python -c "s=open('.claude/commands/prime.md',encoding='utf-8').read(); assert 'Monetization Watch' in s and 'business/monetization/PIPELINE.md' in s; print('prime.md OK')"`
Expected: `prime.md OK`

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/prime.md CLAUDE.md
git commit -m "feat: /prime briefs a Monetization Watch section from the pipeline"
```

---

### Task 5: End-to-end dry run + wrap-up

**Files:**
- Modify: `context/priorities.md` (only if the executor is finishing a real session — otherwise skip; /save handles it naturally)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: End-to-end dry run**

Simulate a full cycle in one sitting:
1. Spawn the strategist with a realistic daily-run prompt describing THIS implementation session (summary: "built the monetization-strategist system itself"; files: the ones committed in Tasks 1–4). It may add "sellable Claude Code workspace template" or similar to RADAR — that's a legitimate real entry, keep it if it appears.
2. Verify `state.json` cursor bumped and `_Last strategist run:` updated.
3. Render the Monetization Watch section from the updated PIPELINE.md per prime.md.

Expected: the full write→read loop works with real (non-synthetic) content; whatever entered the pipeline is real and stays.

- [ ] **Step 2: Commit any pipeline changes from the dry run**

```bash
git add business/monetization/
git commit -m "chore: first real monetization-strategist run (dry-run of the full loop)"
```

(Skip if the dry run made no file changes.)

---

## Explicitly Deferred (not tasks)

- **One-time historical backfill** — seeds the pipeline from full git history, `context/priorities.md`, `decisions/log.md`, memory, the Obsidian vault, and every tool README, then sets `backfill_complete: true`. Deliberately token-heavy; runs as its own session ONLY on Gray's explicit go, using parallel scout subagents per the spec. Until then the system runs live on daily deltas with `backfill_complete: false`.
- **Repo privacy flip** — separate track, waiting on Gray's GitHub Pro purchase landing; does not block anything here.
