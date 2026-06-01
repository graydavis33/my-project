---
name: Iteration discipline — only change what's asked
description: Rule for surgical edits — never remove or replace something Gray didn't explicitly ask to change
type: feedback
---

Only change exactly what the user asks. If it wasn't mentioned, don't touch it.

**Why:** Gray asked for three specific tweaks to the stat card flip UI (enlarge + blur background when open, move edit button to corner, allow deselecting card #1). Instead the entire flip mechanism was replaced with a modal — removing something he liked without being asked to. This caused a full git revert and frustration.

**How to apply:**
- Before any edit, mentally list exactly what was asked. Only those items get changed.
- If fulfilling a request *requires* removing or replacing something already built, flag it explicitly and ask for confirmation before doing it. Don't assume a rework is better.
- Hover state, animations, layout, colors, copy — if Gray didn't mention it, leave it alone.
- A useful template to suggest to Gray when iterating: "Keep [X]. Change [Y] to [Z]." Encourage him to use this when requests could be ambiguous.
- When scope is unclear, ask one targeted question rather than make a large assumption.
