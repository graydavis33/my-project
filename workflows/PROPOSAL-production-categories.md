# PROPOSAL — Categorizing Production by Function, Not Topic

Status: DRAFT / NOT ADOPTED. Awaiting a council review to decide whether this is worth building.
Date: 2026-07-31
Origin: Gray's idea, developed in conversation with Claude.

---

## The idea in one line

Sort every task by what KIND of work it is, not what project it belongs to — then automatically
spin up the right process, model tier, and agents for that kind.

Today the work is organized by topic (Sai batch, Vault, Payday, health). The proposal is a second
axis: function. A router looks at an incoming task, classifies it, and picks the process.

## Why Gray wants it

Two problems it is meant to solve:

1. Hitting usage limits. Cheap models and scripts should handle the work that does not need
   an expensive model.
2. Repeating himself. Mechanical work gets rebuilt from scratch each time instead of running
   a locked recipe.

## Gray's original framing (two categories)

1. Repetitive work needing SOPs — trimming videos, adding captions, enhancing audio, applying
   color grades, writing invoice emails. Minimal models, strict path, same result every time.
2. Creative and subjective one-offs — scripts, hooks, anything different every time. Higher-tier
   models, but low volume, so token cost stays contained.

## Claude's proposed revision (five categories)

The main change: category 1 splits in half, and three categories are added.

| # | Category | Model tier | What makes it work | Example |
|---|---|---|---|---|
| 1a | Deterministic | NONE — plain code | Correct by construction | ffmpeg trim, caption burn-in, audio normalize, LUT apply |
| 1b | Repeatable + per-item judgment | cheap + locked SOP | The recipe | Cover frame selection, trim points, invoice line items |
| 2 | Creative / one-off | high tier | Gray's voice rules applied in-session | Scripts, hooks, batch docs, LinkedIn captions |
| 3 | Research / synthesis | cheap fan-out + good synthesizer | Parallel reading, one conclusion | Reference video hunting, footage location, competitor research |
| 4 | Judgment / decision | high tier | Independence (no yes-man) | "Should I build this", "which hook is stronger" |
| 5 | Unattended / scheduled | cheap | Failure visibility | Daily AI Read, Plaid sync, invoice send |

### Why 1a and 1b must be separate

Gray's phrasing was "minimal models follow a strict path and get it perfect every single time."
Models are not perfect every time — code is. If a task has exactly one correct output and zero
judgment, it belongs in a script, not an agent. A cheap model wrapped around ffmpeg is slower,
costs tokens, and is right ~97% of the time instead of 100%.

Reserve the cheap model for the fuzzy decision INSIDE the recipe (which frame, which trim point,
which line item), not for the mechanical steps around it.

Note: color grading is not a Claude task at all. The automatable part is applying a saved LUT
via script, which is 1a. The creative grade stays in Resolve/Premiere, by hand.

### Why the three added categories are distinct

- Research (3) fits neither original bucket. The question changes every time, so it is not
  mechanical; but there is a right answer, so it is not creative. Wide input, small output.
- Judgment (4) produces no artifact — the output is a decision. Its failure mode is the opposite
  of creative work: creative fails by being off-voice, judgment fails by being agreeable.
- Unattended (5) is defined by nobody watching. Model tier barely matters; what matters is that
  a failure is surfaced. The Daily AI Read failed silently twice before it was caught.

### What is NOT a category

Project duration. The Vault, longform docs, Batch 3 feel like their own bucket, but a long project
contains tasks from all five categories. What is actually distinct is the failure mode — losing
state across sessions and machines. That is a property of the project, handled by save/resume
discipline and repo-stored notes, not a sixth bucket.

## Where fan-out (orchestrator + parallel workers) actually pays

Assessed against Gray's real workload:

WORTH IT
- Sai Batch 3, Vids 3-13. Eleven items, SOP already written, mostly mechanical per video.
- Any future batch with a locked recipe and five or more similar items.

NOT WORTH IT
- Scripts, batch docs, hooks, captions. Bottlenecked on Gray's taste, not execution speed.
  Worker agents cannot reliably carry the accumulated feedback rules.
- Small edits. Orchestration overhead (spec writing, briefing, reading reports) exceeds the job.

Trigger condition if adopted: five or more similar items with a locked recipe.

## Open risks the council should test

1. Does the router cost more than it saves? Classification has to be a cheap one-line call.
   If deciding which process to use costs more than the process saves, small tasks lose money.
2. Is this new capability, or just discipline? Claude Code already has subagents, parallel
   execution, and worktree isolation. Gray already has four project agents. The proposal may be
   a naming exercise on top of things that already exist.
3. Does it survive contact with a real week? Most of Gray's work is category 2 and 3, which the
   framework does not speed up much. The savings concentrate in 1a/1b, which are already scripted.
4. Maintenance. Five categories, a router, and per-category SOPs is a system Gray has to keep
   current on two machines. What breaks when a category boundary is ambiguous?
5. Cross-machine. Would this live in the repo (syncs) or in ~/.claude (does not)?

## Related context

- Batch 3 pipeline SOP: workflows/batch3-multicam-short-pipeline.md
- Existing project agents: .claude/agents/ (footage-puller, interview-question-designer,
  monetization-strategist, scriptwriter)
- The verified model pricing that motivated the cost argument: Fable 5 is $10/$50 per million
  tokens, Opus 5 is $5/$25, Sonnet 5 is $3/$15, Haiku 4.5 is $1/$5. Gray is on a subscription,
  so these are not literal charges — but the ratio governs how fast each model consumes his limit.
