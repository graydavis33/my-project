# Workflow: {{Tool or Process Name}}

**Status:** {{LIVE / Built / Deprecated}} — {{where it runs: Mac, Windows, VPS, GitHub Actions}}
**Cost:** {{per-run estimate, caching behavior, or "Free"}}
**Script:** `python-scripts/{{slug}}/` {{or "N/A — process SOP, no code"}}

---

## Objective

{{One or two sentences. What does this tool/process actually accomplish? Why does it exist? Skip architecture — describe the outcome.}}

---

## When to Run
<!-- Use this section for recurring processes (audits, reviews, briefings). Skip for one-shot tools. -->

- {{Trigger condition 1 — e.g. "quarterly," "before every Sai shoot," "whenever a 401 appears"}}
- {{Trigger condition 2}}

---

## Inputs Required
<!-- Use this section for tools that take input. Skip for autonomous/scheduled processes. -->

- {{Required input — file path, CLI arg, env var}}
- {{Optional input — flag name + what it toggles}}

---

## Commands

```bash
cd python-scripts/{{slug}}

# Primary usage
python main.py {{required arg}}

# Common variants
python main.py {{required arg}} --{{flag}}       # what the flag does
python main.py {{subcommand}}                    # what this subcommand does
```

---

## What It Does (Step by Step)

1. {{First meaningful step — what the tool does, not what Python does}}
2. {{Second step — include decisions points, not just sequence}}
3. {{Keep steps to the 3–7 range that actually matter}}

---

## Setup Checklist (First-Time Use)

- [ ] `ANTHROPIC_API_KEY` in `.env`
- [ ] {{Other required env var}}
- [ ] {{External dependency: ffmpeg, Playwright, etc. — with install command}}
- [ ] {{One-time config: OAuth, Sheet ID, vault path}}

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| {{Symptom a user would actually see}} | {{The fix — specific commands or env var to check}} |
| {{Next symptom}} | {{Fix}} |
| {{Edge case worth calling out}} | {{Fix or link to investigation report}} |

---

## Env Vars Required

```
ANTHROPIC_API_KEY
{{OTHER_VAR}}
{{OPTIONAL_VAR}}         # optional — enables {{feature}}
```

---

## Known Constraints / Notes

- {{Hard limit — API quota, file size, supported format}}
- {{Known trade-off the tool makes by design}}
- {{Link to related workflow, investigation report, or decision log entry}}

---

<!--
Template usage — delete this block before committing:

1. Copy this file to workflows/{{slug}}.md
2. Replace every {{placeholder}} with real content
3. Delete sections that don't apply (e.g. "Inputs Required" for pure process SOPs,
   or "When to Run" for user-invoked tools)
4. Keep section order — it's the shape every SOP in workflows/ shares, so
   future Claude sessions know where to find each piece without hunting
5. Reference the SOP from CLAUDE.md folder map if it's a new major workflow
-->
