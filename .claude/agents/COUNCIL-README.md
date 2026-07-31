# The Council

Six agents that stress-test an idea before Gray spends real time on it.

Built 2026-07-31. Run it with `/council <your idea>`.

## Why it exists

Gray's diagnosis, in his words: language models are yes-men. They are too agreeable and too biased toward whoever is talking to them. Ask Claude "should I build X?" while Claude is already helping you build X, and you get a biased answer — not because it's lying, but because agreement is the path of least resistance in a conversation.

The council fixes that structurally, not with prompting alone.

## The five seats

| Seat | Judges | Verdicts |
|---|---|---|
| **Investor** | Money, time, opportunity cost | FUND / FUND SMALL / DEFER / PASS |
| **Expansionist** | Does it compound, is there a product here | COMPOUNDS / PLATFORM / FLAT / DEAD END |
| **Instructor** | Can Gray run, fix, and maintain it | HE CAN RUN IT / NEEDS GUARDRAILS / TOO FRAGILE / ALREADY SOLVED |
| **Creator** | Craft, brand fit, does the work get better | RAISES THE WORK / NEUTRAL, FASTER / QUALITY RISK / OFF-BRAND |
| **Skeptic** | Pure red team, fact-checks the premise | FALSE PREMISE / FAILS ON EXECUTION / SURVIVES, WITH SCARS / SURVIVES |

Plus the **Supervisor**, who chairs: reads all five, resolves the split, issues one verdict and one next action.

## The four things that make it not-a-yes-man

Role labels alone don't stop sycophancy — an agent told "you are the skeptic" will still find a way to agree. These do the actual work:

1. **Blind parallel voting.** All five seats launch in one message and cannot see each other. No bandwagon, no deference to whoever answered first. This is the single most important mechanism.

2. **Forced-choice verdicts.** Every seat must land on one of four named options. "It depends" is banned. Hedging is how a model agrees without appearing to — removing the hedge forces a real position.

3. **Mandatory adversarial fields.** Every seat must produce a `STRONGEST OBJECTION` and a `KILL CONDITION` — the observable signal that means stop. A seat that likes the idea still has to name how it dies. This is what stops "great idea, minor caveats."

4. **The rubber-stamp check.** If four or five seats come back positive, the Supervisor must stop and ask whether they actually tested the idea or just pattern-matched on something that sounds good. Generic objections ("scope might creep") are treated as evidence the council failed, and confidence gets downgraded. Unanimous approval is a warning sign.

Supporting rules in every seat file: no opening validation, no praise language, attack the idea and never Gray, label speculation as speculation, and if you land positive spend most of the answer on what has to go right.

## Cost

Six agent runs, roughly 30–60k tokens for a normal review. Worth it for "should I build this thing that takes a week." Overkill for small calls.

**Cheap version:** run just the Skeptic (`Agent` → `council-skeptic`). One agent, and it catches most bad ideas on its own.

All seats run on `claude-sonnet-4-6` to keep the cost down. If a decision is big enough to want the best synthesis, change `model:` in `council-supervisor.md` to `claude-opus-5` — that one upgrade improves the final report most per token.

## Where the files live

Canonical copies are in this repo (`.claude/agents/council-*.md`, `.claude/commands/council.md`) so they sync between Mac and Windows.

They are **symlinked** into `~/.claude/agents/` and `~/.claude/commands/` so the council loads in every session from any folder — not just when working inside the project.

Because they're symlinks, editing either location edits both. There is no drift. (This is different from the claude-voice setup, where the repo copy is a dead backup.)

**On Windows:** symlinks don't carry through git. After pulling, either copy the files into `%USERPROFILE%\.claude\agents\` and `\commands\`, or just run `/council` from inside the project folder, where the project-level files load natively.

## Tuning it

- A seat is too soft → strengthen its `Rules that make you worth having` section and add a required field to its output block.
- A seat is being contrarian for sport → the Skeptic file already warns against this; tighten "a weak objection you can't defend is worse than no objection."
- Want a new seat (a Client seat? a Legal seat?) → copy any seat file, change the judging criteria and verdicts, add it to Step 2 of `commands/council.md`.
- The Creator seat enforces Gray's standing brand rules (no disparaging others, Sai-is-not-the-expert, no IG automation, plain text for copy-paste). Update that list when the rules change.
