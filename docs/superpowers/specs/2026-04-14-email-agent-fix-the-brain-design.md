# Email Agent — Fix the Brain (Approach A)

**Date:** 2026-04-14
**Tool:** `python-scripts/email-agent/`
**Iteration approach:** A — Fix the Brain (context + prompt quality)
**Status:** Design approved, ready for implementation plan

---

## Why

The Email Agent has been live for weeks and works, but its Claude prompts have two concrete problems:

1. **Stale identity context** — `drafter.py` calls Gray *"a social media marketer"*; `classifier.py` says videographer. The two Claude calls disagree about who they work for.
2. **Thin shared context** — each prompt has its own ad-hoc system message. Neither knows about the Sai Karra job, key clients, or Gray's current priorities. Every email is triaged in a vacuum.

The 16-minute video on AI content workflows (transcript at `python-scripts/content-pipeline/output/not-behind-ai-content-transcript-20260414-112732.md`) outlines a framework where every role gets an explicit master prompt ("educate the AI") and every prompt follows a **Role → Context → Command → Format** formula. Applying both to the Email Agent is the smallest high-ROI upgrade we can make, and it produces a reusable `role_context.md` artifact we can apply to future tool upgrades (Morning Briefing, Invoice System, etc.).

## Scope

**In scope:**
- One new file: `python-scripts/email-agent/role_context.md`
- Edits to `classifier.py` and `drafter.py` — rewrite both system prompts using Role-Context-Command-Format formula, load `role_context.md` as shared CONTEXT block
- A `--dry-run` flag on `main.py` for safe testing

**Out of scope (explicitly):**
- No architectural changes — same files, same functions, same output contracts
- No feedback loop on Slack Edit/Skip (that's Approach B — future iteration)
- No skill-file refactor (that's Approach C — future iteration)
- No changes to `voice_profile.txt`, follow-up tracker, Slack bot, Gmail client, or labels

## Architecture

Same as today. One additional file, two prompt rewrites. No new dependencies.

```
python-scripts/email-agent/
├── role_context.md       ← NEW (shared master prompt)
├── classifier.py         ← EDIT (load role_context.md, new prompt structure)
├── drafter.py            ← EDIT (load role_context.md, new prompt structure, kill stale line)
├── main.py               ← EDIT (add --dry-run flag)
├── voice_profile.txt     ← UNCHANGED (tone/style)
├── followup_tracker.py   ← UNCHANGED
├── slack_bot.py          ← UNCHANGED
└── gmail_client.py       ← UNCHANGED
```

## `role_context.md` — contents

Five sections, ~1 page total. Claude reads the whole file on every email, so it must stay tight.

1. **Who Gray is** — name, role, business, timezone.
2. **What the inbox is for** — categories of email that come in (client work, Sai job, leads, personal admin, noise).
3. **Key people / senders** — named list (Sai Karra = always urgent + important; active clients; collaborators; family) + pattern rules for unknowns.
4. **Current priorities** — 2–3 lines about what's hot right now. Marked with an "update when priorities shift" comment so it doesn't rot.
5. **Triage rules** — explicit, toddler-level specific preferences. Example rules:
   - Anything from Sai → always `needs_reply`
   - Invoice / payment confirmations → `fyi_only`
   - Cold agency pitches → `needs_reply` unless clearly spam
   - Instagram/TikTok DMs forwarded to email → `fyi_only`

**Deliberately excluded:**
- Voice / tone (stays in `voice_profile.txt`)
- Detailed project context (belongs in workspace `context/`)
- Anything sensitive (credentials, account numbers, client financials)

## Prompt structure — Role-Context-Command-Format formula

**Classifier (Haiku):**

```
ROLE: You are Gray's inbox triage assistant.

CONTEXT:
{role_context.md loaded here}

COMMAND: Read the email below and classify into exactly one of:
- needs_reply
- fyi_only
- ignore
Use the triage rules in CONTEXT. When in doubt between needs_reply and fyi_only,
choose needs_reply.

FORMAT: One line, lowercase: category|reason (max 8 words)
Example: needs_reply|sai asking about tomorrow's shoot
```

**Drafter (Sonnet):**

```
ROLE: You write email replies on Gray's behalf in his voice.

CONTEXT:
{role_context.md loaded here}

VOICE:
{voice_profile.txt loaded here}

COMMAND: Write a reply body to the email below.

FORMAT:
- Reply body only — no subject line, no "Dear [name]"
- Sign off naturally in Gray's style followed by "Gray"
- Use [placeholder] for specifics you can't know (pricing, dates, links)
```

**What changes vs. today:**
- Both prompts share the same CONTEXT block — single source of truth for identity
- The stale "social media marketer" line in `drafter.py` is removed
- Explicit section labels (the video states this formula produces the best outputs)
- Classifier's triage rules are sourced from CONTEXT, not hard-coded in the prompt string

**What stays the same:**
- Models: Haiku for classify, Sonnet for draft
- Output formats: classifier still returns `category|reason`; drafter still returns a reply body string
- All downstream code in `main.py`, `slack_bot.py`, `gmail_client.py` untouched

## Testing

1. **Dry-run mode** (implemented as part of this iteration): `python main.py --dry-run` fetches the last ~20 unread emails, runs classifier + drafter, prints results, writes nothing to Gmail or Slack.
2. **Before/after classification diff**: compare new classifier output against current Gmail labels on the same sample. Any disagreement reviewed by Gray.
3. **Draft spot-check**: Gray reads 5 drafts, flags anything that sounds wrong. `role_context.md` is iterated until drafts read as "would send with light edits."

## Rollout

1. Commit design doc + implementation to git.
2. **Deployment question to resolve before rollout:** Email Agent is documented as LIVE on Mac launchd AND in VPS systemd docs — if both are running, they'll duplicate-send to Slack. Must confirm which host is authoritative and only deploy to that one.
3. Deploy to authoritative host (copy updated files, restart service).
4. Monitor first 2–3 real runs — verify Slack messages appear, Gmail labels apply, no duplicates, no regressions.

## Rollback

Prompts are pure Python strings today. If the new version misbehaves, `git revert` the commit and redeploy. Zero schema changes, no data migration, no external state mutations.

## Success criteria

- No "social media marketer" language anywhere in the codebase.
- Classifier correctly flags any Sai-sourced email as `needs_reply` in dry-run testing.
- At least 4/5 spot-checked drafts read as something Gray would send with light edits.
- Inbox labels continue to apply correctly; `agent-processed` label prevents duplicate processing.
- `role_context.md` is a reusable template — other tool iterations can fork it as a starting point.

## Open questions (to resolve before or during implementation)

1. **Which host is authoritative for Email Agent deployment — Mac launchd or VPS systemd?** (Docs say both; Section 4 of brainstorm flagged this.) If both are running, we have a duplicate-send bug today, not just a deployment concern.
2. **Initial key-people list for `role_context.md` §3** — Gray will provide names (Sai confirmed; active clients TBD).
3. **Initial triage-rules list for `role_context.md` §5** — Gray to review and expand defaults.

## Next step

Invoke `superpowers:writing-plans` to turn this design into a step-by-step implementation plan with TDD-style verification.
