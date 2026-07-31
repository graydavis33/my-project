# The LLM Council

Six agents that put an idea through independent review, anonymous peer review, and a final call.

Built 2026-07-31. Run it with `/council <your idea>`.

## Provenance — what's borrowed and what isn't

The three-stage structure comes from **Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council)** (23k stars, Nov 2025). His design:

1. **First opinions** — the query goes to every council member independently
2. **Peer review** — each member reads all responses *anonymized* ("Response A, B, C") and ranks them
3. **Chairman** — one model synthesizes everything into the final answer

Two things to keep straight:

- **Karpathy's council is four different companies' models** — GPT 5.1, Gemini 3.0 Pro, Claude Sonnet 4.5, Grok 4, chaired by Gemini, routed through OpenRouter. The independence comes from different *models*. Ours comes from five Claude agents with different *mandates*. That's an adaptation, not the original.
- **Karpathy disclaims it.** His README calls it *"99% vibe coded as a fun Saturday hack"* and says he won't support or improve it. There's no license file. It's a pattern to borrow, not a product to depend on.

Karpathy co-founded OpenAI, ran AI at Tesla, founded Eureka Labs, and joined **Anthropic** in May 2026 to lead a pre-training research team. He did not found Anthropic.

## Why it exists

Cheng et al., published in *Science*: across 11 leading chatbots and ~12,000 prompts, LLMs validated the user **49% more than another human would** (72% vs 22% on advice queries), and avoided challenging the user's framing 88% of the time versus 60% for people.

The study measured *personal and social* advice, not business decisions — but the mechanism is the same one that makes "is this a good idea?" a bad question to ask a single model.

## The five seats

| Seat | Mandate | Verdicts |
|---|---|---|
| **Contrarian** | Only how it fails. Assumes death, works backwards | FALSE PREMISE / FAILS ON EXECUTION / SURVIVES, WITH SCARS / SURVIVES |
| **First Principles** | Strips assumptions, rebuilds from what must be true | SOUND FOUNDATION / RIGHT GOAL, WRONG SHAPE / WRONG PROBLEM / LOAD-BEARING ASSUMPTION UNTESTED |
| **Expansionist** | The upside being missed; does it compound | COMPOUNDS / PLATFORM / FLAT / DEAD END |
| **Outsider** | Knows nothing about the industry; tests plain logic | MAKES SENSE COLD / NEEDS INSIDER CONTEXT / DOESN'T FOLLOW / SOLVING A SYMPTOM |
| **Executor** | What happens Monday morning | START MONDAY / NEEDS SCOPING / NEEDS GUARDRAILS / WON'T SURVIVE CONTACT |

Plus the **Chairman**, who reads all five opinions *and* all five blind rankings, then issues one verdict and one next action.

## What makes it not-a-yes-man

Role labels alone don't stop sycophancy — an agent told "you are the skeptic" still finds ways to agree. These do the work:

1. **Blind parallel opinions.** All five launch in one message and cannot see each other. No bandwagon, no deference to whoever answered first.
2. **Anonymized peer review** (Karpathy's contribution, and the reason this beats five parallel prompts). Each seat re-reads all five answers with authorship stripped — including its own, unmarked — ranks them, and states whether its view changed. Agreement reached without knowing whose argument you're conceding to is worth far more than agreement reached independently.
3. **Forced-choice verdicts.** "It depends" is banned. Hedging is how a model agrees without appearing to.
4. **Mandatory adversarial fields.** Every seat produces a `STRONGEST OBJECTION` and a `KILL CONDITION` — even the ones that like the idea.
5. **The rubber-stamp check.** If four or five seats come back positive, the Chairman must stop and ask whether they actually tested it. Generic objections count as council failure and downgrade confidence. Unanimous approval is treated as a warning sign.

## The Outsider seat — do not "fix" it

It has only a `Read` tool and is explicitly forbidden from reading `CLAUDE.md`, memory files, or project background. That looks like a bug. It isn't. The moment it absorbs context it becomes a fifth insider and the seat is wasted. Its list of undefined terms is a map of the assumed knowledge holding an idea together.

## Cost

Eleven agent runs — five opinions, five reviews, one chairman — roughly 60-100k tokens. Real money against the usage limit. Worth it for "should I spend a week on this"; overkill for small calls.

Seats run on `claude-sonnet-4-6`; the chairman on `claude-opus-5` (one call, and it's the actual product). Downgrade the chairman in `council-chairman.md` if limits get tight.

**Cheap version:** run `council-contrarian` alone via the Agent tool. One run, catches most bad ideas by itself.

## Where the files live

Canonical in this repo (`.claude/agents/council-*.md`, `.claude/commands/council.md`) so they sync Mac ↔ Windows. **Symlinked** into `~/.claude/agents/` and `~/.claude/commands/` so `/council` loads in every session from any folder — editing either location edits both, no drift.

**On Windows:** symlinks don't survive git. After pulling, either copy the files into `%USERPROFILE%\.claude\agents\` and `\commands\`, or run `/council` from inside the project folder where the project-level files load natively.

## Going multi-provider later

To make it faithful to Karpathy's original, replace the five Claude seats with real models from different companies. That needs an OpenRouter account, an API key, and pay-per-token billing on top of the subscription. The three-stage command structure doesn't change — only who occupies the seats. The persona instructions become system prompts for the outside models.

## Tuning

- A seat is too soft → strengthen its Rules section and add a required output field.
- A seat is contrarian for sport → the Contrarian file already warns against this; tighten "a weak objection you can't defend is worse than none."
- New seat → copy any seat file, change the criteria and verdicts, add it to Stage 1 and Stage 2 of `commands/council.md`, and update the Chairman's vote line.
- **Never remove Stage 2.** Without the blind peer review this is just five prompts in a trench coat.

## Superseded

An earlier six-seat council (Investor / Expansionist / Instructor / Creator / Skeptic / Supervisor) was built and removed on the same day in favour of this one. It's in git history at commit `d5486d5` if anything there is worth reclaiming.
