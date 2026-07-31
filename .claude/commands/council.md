# /council — Put an Idea Through the Council

Run any idea past five independent, critical reviewers before spending real time on it.

The council exists because Claude — like every language model — drifts toward agreeing with whoever is talking to it. Five seats voting **blind** (none can see the others' answers) removes the pile-on effect and forces disagreement to surface instead of dissolving.

## Variables

idea: $ARGUMENTS (the idea, plan, tool, or decision to review)

---

## Instructions

### Step 1 — Lock the question

Restate the idea in 2-4 sentences as you understand it, so the seats all review the same thing. Include:
- what it is
- what problem it's supposed to solve
- roughly what building it would involve

If `$ARGUMENTS` is empty, ask Gray what he wants reviewed and stop.

If the idea is genuinely ambiguous in a way that would change the verdict, ask ONE clarifying question, then proceed. Do not interrogate him — the council's job is to handle uncertainty, not eliminate it.

**Do not offer your own opinion at this stage.** You are the clerk here, not a seat. Anything you say ahead of the vote is exactly the bias the council was built to remove.

### Step 2 — Convene the five seats (in parallel, blind)

Launch all five in a **single message with five Agent tool calls** so they run concurrently and cannot see each other's output:

- `council-investor` — money, time, opportunity cost
- `council-expansionist` — leverage, does it compound, is there a product here
- `council-instructor` — can Gray run, fix, and maintain it
- `council-creator` — craft, brand fit, does the work get better
- `council-skeptic` — pure red team, fact-checks the premise

Give every seat the **same** brief: the restated idea from Step 1, plus any relevant file paths or context Gray provided. Add nothing else. Do not tell a seat what you think, do not hint at a preferred answer, and do not pass one seat's framing to another.

### Step 3 — Show the raw vote

Before any synthesis, print a compact table so Gray sees the unfiltered result:

```
Investor      <VERDICT>   <one-line call>
Expansionist  <VERDICT>   <one-line call>
Instructor    <VERDICT>   <one-line call>
Creator       <VERDICT>   <one-line call>
Skeptic       <VERDICT>   <one-line call>
```

### Step 4 — Chair the council

Launch `council-supervisor` with all five full seat reports pasted in. It weighs them, resolves the split, and issues the final verdict and next action.

Print the supervisor's report exactly as returned.

### Step 5 — Offer the details

End with one line: the full seat reports are available if he wants to read a specific objection in depth. Do not dump all five reports unless he asks — that's thousands of words he didn't request.

Then stop. **Do not start building.** A verdict of `PROCEED` is information, not permission — Gray decides when work starts.

---

## Rules for you as clerk

- Never editorialize on the verdict. If you disagree with the council, you may say so in one sentence at the very end, labeled as your own view.
- Never re-run a seat because you didn't like its answer.
- If a seat fails or returns nothing, say which one and note that the vote is incomplete. Do not silently proceed with four.
- Keep your own commentary minimal. The seats' words are the product.

## Cost note

A full council is six agent runs. That is not free — a rough review is maybe 30-60k tokens of Gray's budget. Worth it for "should I build this thing that will take a week." Overkill for "should I use blue or orange."

For a cheap version, run only the `council-skeptic` seat — one agent, and it catches most bad ideas on its own. Suggest this when the question is small.
