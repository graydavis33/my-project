# /implement — Execute a Plan

Executes a plan created by /create-plan. Read it fully, build everything, validate, then close it out.

## Variables

plan_path: $ARGUMENTS (path to the plan file, e.g., `plans/2026-03-29-content-researcher-v2.md`)

---

## Instructions

### Phase 1: Read the Plan

1. Read the entire plan file — don't skim
2. Check for open questions or blockers — if any exist, stop and ask Gray before proceeding
3. Confirm status is "Draft" (not already "Implemented")

### Phase 2: Build

1. Follow the Step-by-Step Tasks in exact order
2. Complete each step fully before moving to the next
3. For every file being created: write the complete file, not a stub
4. For every file being modified: read it first, then make the changes
5. If a step is unclear or something unexpected comes up — stop and ask rather than guess

### Phase 3: Verify

Run through the "How to Verify It Works" checklist from the plan:
- Check off each item
- If something fails, fix it before moving on
- Note anything that couldn't be verified

### Phase 4: Close Out

Update the plan file:
1. Change `**Status:** Draft` → `**Status:** Implemented`
2. Add this section at the end:

```markdown
---

## Implementation Notes

**Implemented:** YYYY-MM-DD

### What Was Built
- (bullet summary of what got created/changed)

### Deviations from Plan
(Any changes made during build, or "None")

### Issues Encountered
(Any problems hit and how they were resolved, or "None")
```

### Phase 5: Report

Provide a final summary:

```
## Done

### Built
- file/path — what it does
- file/path — what it does

### Verified
- [x] check item
- [x] check item

### Deviations
None / (list if any)

### Next Steps
(Any follow-up actions, or "None")
```