# /create-plan — Plan Before Building

Use before any non-trivial change: new features, new tools, restructuring, or anything that touches multiple files.

## Variables

request: $ARGUMENTS (describe what you want to build or change)

---

## Instructions

You are creating a PLAN, not building anything yet. Research first, think it through, then write the plan doc.

### Step 1: Research

Before writing anything, investigate:
- Read `CLAUDE.md` and relevant `context/` files
- Check `python-scripts/` for existing tools that relate to the request
- Check `workflows/` for any existing SOPs that apply
- Read the relevant project's `CLAUDE.md` if this touches an existing project
- Understand what already exists before proposing anything new

### Step 2: Write the Plan

Create a file in `plans/` with filename: `YYYY-MM-DD-descriptive-name.md`
- Use today's date
- Keep the name short and clear (e.g., `2026-03-29-content-researcher-v2.md`)

Use this format:

---

```markdown
# Plan: [Title]

**Date:** YYYY-MM-DD
**Status:** Draft
**Request:** One-line summary of what was asked for

---

## What This Does

2-3 sentences. What gets built, what problem it solves, why it matters for Gray's goals.

## Current State

What already exists that's relevant. What's missing or broken that this fixes.

## What We're Building

Bulleted list of every change at a high level:
- New files to create (with path and purpose)
- Existing files to modify (with what changes)
- Anything to delete or replace

## Step-by-Step Tasks

### Step 1: [Task name]
What to do, specifically. Which files to touch.

### Step 2: [Task name]
...

(As many steps as needed. Be specific enough that /implement can execute without asking questions.)

## How to Verify It Works

- [ ] Specific test or check
- [ ] Specific test or check

## Notes

Any trade-offs, risks, or follow-up ideas worth capturing.
```

---

### Step 3: Report Back

After writing the plan:
1. Give a 2-sentence summary of what the plan covers
2. List any open questions that need Gray's input before building
3. Show the plan file path
4. Say: "Run `/implement plans/YYYY-MM-DD-name.md` when ready to build."
