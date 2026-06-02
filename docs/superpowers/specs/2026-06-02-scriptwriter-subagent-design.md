# Scriptwriter Subagent — Design Spec

_Date: 2026-06-02_
_Status: Design approved (brainstorm complete). Ready for implementation — to be finished on Mac._

---

## Goal

Build a Claude Code **subagent** ("the AI scriptwriter") that writes viral-video scripts grounded in the
`story-arc-playbook` knowledge base (8 transcribed elite-creator videos — 5 Kallaway, 3 Personal Brand Launch —
distilled into `playbook.md`, `frameworks.md`, and format `templates/`). It writes in either Gray's or Sai's voice
and saves a clean script to the workspace.

## Decisions locked during brainstorm

| Question | Decision |
|---|---|
| Audience | **Both, switchable** — agent takes a "who" (Gray or Sai), loads the right voice corpus + example set |
| Form factor | **Claude Code subagent** — `.claude/agents/scriptwriter.md` (dispatched via the Agent tool) |
| Input modes | **All four**: (a) topic + format, (b) rough idea / voice-memo dump, (c) existing transcript to re-script, (d) proven 5x-outlier to swipe-and-templatize |
| Research | **Yes** — `WebSearch` builds a fact bank, then the playbook's **Shock Score gate** keeps only facts scoring 70+ |
| Output destination | **Markdown file in the workspace** + returned in chat |
| Output content | **Clean script only + 3 hook options per video.** No production notes, no inline citations, no b-roll notes (deferred) |
| Knowledge consumption | **Approach C (Hybrid)** — stable spine baked into the agent prompt; deep reference read from the playbook at runtime (playbook stays single source of truth) |

## Architecture

**One new file:** `.claude/agents/scriptwriter.md`

- **Tools:** `Read`, `Glob`, `Grep`, `WebSearch`, `WebFetch`, `Write`. (No `Edit`/`Bash` — it's a writer, not a code-changer.)
- **Model:** `claude-sonnet-4-6` (reasoning/writing task, not cheap classification).
- **Invocation:** Dispatched via the Agent tool when Gray says e.g. *"write a short for Sai about X"*,
  *"scriptwriter: turn this transcript into a long-form,"* etc. Runs in its own context, writes the file,
  returns the path + the script.

### Baked into the agent prompt (the stable spine)

So the agent is coherent without re-reading everything each run:

- The **11-step writing process** (lock inputs → fact bank → emotion → hook → structure → outline → write →
  audit → jagged-edge → friend test → deliver) — mirrors `playbook.md` "How to actually use this when writing a future script."
- The **5 universal laws** (expectations-vs-reality, topic clarity in first sentence, open loops/curiosity gaps,
  speed-to-value, name your frameworks).
- **Voice-switching logic** (Gray vs Sai — which corpus to read).
- The **output contract** (clean script + 3 hooks, formatting rules below).

### Read at runtime (the deep reference)

- `business/social-media/story-arc-playbook/playbook.md` — always.
- `business/social-media/story-arc-playbook/frameworks.md` — for verbatim framework detail + examples.
- The right template based on format:
  - documentary → `templates/documentary-template.md`
  - sit-down talking head → `templates/talking-head-template.md`
  - short → the 7-factor flow + `templates/shorts-hook-bank.md`
- **Voice corpus** for whoever it's writing for:
  - **Gray:** `C:/Users/Gray Davis/My Drive/Obsidian/Graydient Media/Content/Graydient Media/Voice Style.md`
    + the dated take-session files in `.../Graydient Media/Voice Memos/`.
    _(Mac path differs — see "Cross-machine note" below.)_
  - **Sai:** `python-scripts/sai-linkedin/reference/voice/sai-linkedin-posts-final.md`
    + memory: `feedback_sai_linkedin_voice_revisions`, `feedback_graydient_take_session_edit_rules`.

## Run flow

1. **Detect input mode** — topic+format / idea dump / transcript to re-script / outlier to swipe. Handles all four.
2. **Lock inputs** — confirm format, Story Lens (unique angle), target emotion (from the 6 buckets), working title.
   Ask Gray for any that are missing before writing.
3. **Research + Shock-Score gate** — `WebSearch` builds a fact bank for the topic; rate each fact 1–100
   ("how many of the audience already know this?"); keep only 70+.
4. **Read** playbook + frameworks + the right template + the correct voice corpus.
5. **Write** following the format's architecture, in the chosen person's voice.
6. **Self-audit** — the playbook's 4-question checklist + jagged-edge test + tell-it-to-a-friend test.
7. **Save** to `business/social-media/scripts/YYYY-MM-DD-<who>-<slug>.md` and return path + script.

## Output contract

```
1. <hook one>
2. <hook two>
3. <hook three>

<the single script body — one beat per line, jagged-edge rhythm>
```

- **3 hooks** at the top, numbered 1–3, clean — no asterisks, no quotation marks, no "hook option" labels.
  Gray deletes the two he doesn't use. (This is the one intentional deviation from playbook Step 11's
  "no hook option labels," because Gray explicitly wants three to choose from.)
- **Script body:** one beat per line for jagged-edge rhythm review.
- **Voice rules enforced:** no em-dashes, no AI-essay headers, no invented three-beat parallels,
  sixth-grade vocabulary, active voice, staccato openers.
- **Nothing else** in v1.

## Out of scope (v1 — layer on later)

- Production-notes block (format, hook stack, emotion, structure, CTA trigger, on-screen text).
- Framework citations inline (`[from 04-irresistible-hooks: Context Lean]`).
- B-roll / shot suggestions (would tie into the footage index / `find_visuals` / Higgsfield for gaps).
- The manual IG 5x-outlier swipe-file research — stays a human step.

Rationale (Gray's words): "Start simple, then build up. Right now I just need the clean script with three hooks
for each video. From there I'll add on once I've run a batch and see what I need from the AI editor / script editor."

## Cross-machine note (Mac finish)

- The agent file lives in the repo (`.claude/agents/scriptwriter.md`) so it syncs to Mac on `git pull`.
- **Voice-corpus paths differ by machine.** The Gray corpus is in the Obsidian/Drive vault, not the repo.
  The agent should resolve the vault path per-OS (Windows: `C:/Users/Gray Davis/My Drive/Obsidian/...`;
  Mac: the equivalent Drive mount, e.g. `~/Library/CloudStorage/GoogleDrive-.../My Drive/Obsidian/...`).
  Confirm the Mac vault path during implementation and have the agent try both / use Glob to locate it.
- The Sai corpus (`python-scripts/sai-linkedin/reference/voice/...`) is in-repo and identical on both machines.

## Next step

Run the **writing-plans** skill against this spec to produce the implementation plan, then `/implement`.
The build is small (one agent definition file) — most of the work is getting the system prompt's spine and the
runtime-read instructions exactly right, plus the per-OS voice-path resolution.
