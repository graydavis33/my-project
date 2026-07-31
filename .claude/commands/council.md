# /council — The LLM Council

Put an idea in front of five independent advisors who answer blind, then review each other's work anonymously, then get one verdict from a chairman.

Adapted from Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council). His version gets independence from four different companies' models; this version uses five Claude advisors with distinct mandates. **The three-stage structure — independent opinions, anonymized peer review, chairman synthesis — is his, and it is the part that matters.**

It exists because language models validate the user roughly 49% more than another human would (Cheng et al., *Science*, 11 chatbots / ~12,000 prompts). Ask one model whether your idea is good and you get an agreeable answer. This makes agreement expensive to fake.

## Variables

idea: $ARGUMENTS (the idea, plan, tool, or decision to review)

---

## Stage 0 — Lock the question

Restate the idea in 2-4 sentences so all five advisors review the same thing: what it is, what problem it solves, roughly what building it involves.

If `$ARGUMENTS` is empty, ask what he wants reviewed and stop. If the idea is ambiguous in a way that would change the verdict, ask ONE clarifying question, then proceed — the council's job is to handle uncertainty, not eliminate it.

**Do not offer your own opinion at any point before the chairman reports.** You are the clerk, not a seat. Anything you say ahead of the vote is exactly the bias this was built to remove.

If the idea concerns a specific file, note its path — you'll pass it to the seats that can read it.

---

## Stage 1 — Five opinions, blind and parallel

Launch all five in a **single message with five Agent tool calls** so they run concurrently and cannot see each other:

- `council-contrarian` — only how it fails
- `council-first-principles` — strips assumptions, rebuilds from what must be true
- `council-expansionist` — the upside being missed
- `council-outsider` — knows nothing about the industry, tests the plain logic
- `council-executor` — what happens Monday morning

Give every seat the **same** brief: the restated idea from Stage 0, plus any file path. Add nothing else. Do not tell a seat what you think, do not hint at a preferred answer, do not pass one seat's framing to another.

**The Outsider gets the idea and the file path only** — never repo context, memory files, or background. Its ignorance is the instrument.

---

## Stage 2 — Anonymized peer review

This is the stage that makes it a council instead of five parallel prompts. Do not skip it.

**Anonymize.** Assign the five Stage 1 reports labels `Response A` through `Response E` **in scrambled order** — do not label them in the order the seats are listed above, or A will always be the Contrarian. Strip every `SEAT:` line and any phrasing that identifies the author. Keep the mapping private until the final output.

**Review.** Launch all five seats again in **one message with five Agent tool calls**. Each gets all five anonymized responses — including, unknowingly, its own — and this instruction:

> Below are five anonymized responses to the same question. One may be your own; you are not told which and should not try to guess. Judge them on the merits, ranking by the criterion in your own seat instructions.
>
> Return exactly:
>
> ```
> RANKING: <labels, best to worst>
> STRONGEST: <label> — <why, one sentence>
> WEAKEST: <label> — <why, one sentence>
> WHAT I MISSED: <the point another response raised that I did not, or "nothing">
> REVISED VIEW: <does anything here change my own call? state the new call, or "unchanged">
> ```

---

## Stage 3 — Show the raw result

Before any synthesis, print the unfiltered picture — first the Stage 1 verdicts, then the review, with the label mapping now revealed:

```
Contrarian        <VERDICT>   <one-line call>
First Principles  <VERDICT>   <one-line call>
Expansionist      <VERDICT>   <one-line call>
Outsider          <VERDICT>   <one-line call>
Executor          <VERDICT>   <one-line call>

Blind review — who ranked what (A=<seat>, B=<seat>, ...)
  Contrarian ranked: <order>   revised: <yes/no>
  ...
```

---

## Stage 4 — Chairman

Launch `council-chairman` with all five full Stage 1 reports, all five Stage 2 reviews, and the label mapping. It weighs them, reads what the blind review revealed, resolves the split, and issues the verdict and Monday-morning action.

Print its report exactly as returned.

---

## Stage 5 — Close

End with one line: the full seat reports and reviews are available if he wants to read a specific objection in depth. Do not dump them unless asked — that's thousands of words he didn't request.

Then stop. **Do not start building.** `PROCEED` is information, not permission.

---

## Rules for you as clerk

- Never editorialize on the verdict. If you disagree with the council you may say so in one sentence at the very end, labeled as your own view.
- Never re-run a seat because you didn't like its answer.
- Never let a seat see another seat's identity, in either stage.
- If a seat fails or returns nothing, say which and note the result is incomplete. Do not silently proceed with four.

## Cost

Eleven agent runs — five opinions, five reviews, one chairman — roughly 60-100k tokens. That is real. Worth it for "should I spend a week on this." Overkill for small calls.

**Cheap version:** run `council-contrarian` alone. One agent, and it catches most bad ideas by itself. Suggest this when the question is small.
