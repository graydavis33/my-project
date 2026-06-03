# Scriptwriter System — v1 Retro Log

Living doc tracking how the **Scriptwriter system** (story-arc-playbook + scriptwriter subagent + sai-weekly-script-batch SOP) holds up in real use. Append per-run notes. Roll forward into a v2 spec when a pattern emerges.

**v1 components in scope:**
- Story Arc Playbook → [business/social-media/story-arc-playbook/](../../../business/social-media/story-arc-playbook/)
- Scriptwriter subagent → [.claude/agents/scriptwriter.md](../../../.claude/agents/scriptwriter.md)
- Sai weekly batch SOP → [workflows/sai-weekly-script-batch.md](../../../workflows/sai-weekly-script-batch.md)
- Original design spec → [2026-06-02-scriptwriter-subagent-design.md](2026-06-02-scriptwriter-subagent-design.md)

---

## Run 1 — Sai Batch 2 (2026-06-02)

**Input:** ~9 voice memos dumped from Google Drive. First production run.

### Process notes (filled in as we go)

**Phase 1 — Inputs (Drive ingest):**

- **Drive auth gap (CRITICAL).** The Claude Drive MCP is auth'd to `graydavis33@gmail.com` only. Gray dropped the 13 voice memos in `gray@karramedia.com`'s Drive in a folder called `Batch Memos 2`. MCP returned nothing for `title contains 'Batch Memos'` because karramedia's Drive is a separate account. Resolution this run: Gray shared the folder to `graydavis33@gmail.com`; I then re-queried with `sharedWithMe = true`. Friction = ~5 min round-trip.
- **MCP `download_file_content` returns base64 JSON too large for context.** Each call (audio file 0.5–4.8 MB) dumps to a temp `.txt` file in the session's `tool-results/` dir. To convert to .m4a, ran a single Python pass that globs the temp files, parses JSON, base64-decodes, writes to disk. Works but not obvious from the tool description.
- **Filename quirks in source.** Two typos in Drive — `How I manage my money or 2.m4a` (should be `pt 2`), `Redoing Fincance part 2.m4a` (Finance). Handled at decode time via a rename map. Sai-side naming convention would prevent this.
- **Bigger batch than declared.** Gray said ~9 memos; folder had 13. Confirmed all 13 in scope, plus that "Part 2" files are continuations of the matching "Part 1" (recording ended early and was re-started) — so the merge step collapses 13 transcripts → 11 final scripts.
- **Filename parentheticals carry hook intent.** `(great hook)` / `(hook at the end)` in the filename = Sai intentionally delivered a hook in the recording. Other memos = pure topic talk, no baked-in hook. Subagent should honor that signal.

**Phase 2 — Transcription:**

- **`content-pipeline` skill is a skeleton.** Had to read `main.py` + README directly to learn the CLI.
- **`--all` only batches `--meeting-notes`.** Combining `--all` with `--transcribe-only` does not loop; falls through to "no video_path" error. Worked around with a manual `for f in *.m4a; do ... done` bash loop.
- **`--meeting-notes` deletes the source `.m4a`** after extracting Haiku notes (line 174 of `main.py`). Wrong path for batch-script workflow where the .m4a files are inputs we want to retain for scriptwriter context and any re-runs.
- **Windows console encoding bug.** `main.py --help` crashes on cp1252 because the docstring has em-dashes/arrows. Per existing `feedback_windows_utf8_stdout.md` memory, should add `sys.stdout.reconfigure(encoding="utf-8")` at top of `main.py`. Worked around with `PYTHONIOENCODING=utf-8`.

**Phase 3 — Scriptwriter handoff:**

Subagent ran in own context — 1 invocation, 19 tool uses, 134 sec wall-clock, ~105K subagent tokens. Returned 11 scripts to `business/social-media/sai/scripts/2026-06-02-batch-2.md` matching Batch 1's A/B/C hook + blockquoted body format. Self-audit notes below (subagent reported, not yet acted on — these are raw observations, decide which become v2 fixes vs one-off judgment calls):

1. **List-format memos need a cleanup pre-pass.** Script 1 (`10 truths about ads`) — Sai stuttered through each list item 2–3× in the recording. Subagent had to interpret each truth from fragmented attempts; felt closer to editing than transcribing. If list-format memos recur, consider a Haiku pre-pass that consolidates duplicate list-item attempts before the scriptwriter sees the transcript.

2. **Voice-attribution rule ambiguity.** Script 2 (`Accept your passion`) Hook A — "The thing you don't have will always be the thing you want the most" — actually came from Gray brainstorming mid-recording, not Sai's mouth. Subagent used it because Sai responded "Right, I like that." Agent contract says "use Sai's actual words"; does verbal endorsement count? **Rule needs clarification in `sai-script-style-guide.md`.**

3. **Parable structure missing from playbook.** Script 4 (`Fire sirens`) is a parable, not a framework explainer. Subagent built it as "scene → realization → universal takeaway" — felt like freestyling. Closest playbook match was the basketball-coach pattern (In Medias Res Personal Story) but didn't quite map. **Candidate v2 addition: a parable/anecdote template in the shorts arc section.**

4. **Self-redaction handling.** Script 5 (`How I manage my money`) had a literal cut-self-off — "watches, jewelry. No, I don't want to mention that." Subagent softened to generic "physical assets." Worth a rule: when Sai self-redacts in the recording, the script honors the redaction (generic substitute) rather than transcribing the cut.

5. **Invented payoff line.** Script 8 (`Landed a Fortune 500 client`) — the transcript implies the win heavily but Sai never explicitly says they got the contract. Subagent added "We won." as a 1-line payoff. **The only invented copy in the batch.** Flagged for Gray/Sai verification before filming.

6. **3-beat parallel rule needs nuance.** Script 11 (`Turn you creativity into a system`) preserves a 3-beat parallel ("creativity without structure / structure without creativity") because Sai literally said it that way. Style guide warns against INVENTING 3-beat parallels — not against PRESERVING when Sai naturally speaks them. **Rule should be more specific: "Don't invent 3-beat parallels. Do preserve when Sai delivers one organically."**

7. **Voice slip self-catch.** Subagent almost wrote "Here's the thing" as a connector — caught it because the style guide already flags it as a pattern Sai cuts. Good — proves the style guide is doing its job at runtime.

8. **NEW pattern candidate for the style guide: "Authority-Anchor Opener".** Both intentional-hook recordings (Scripts 1, 8) opened with **dollar-scale credibility** ("tens of millions in ad spend" / "two $100M mentors"). That's a recurring Sai move — name it in the style guide and add it as a hook variant in the shorts arc.

**Phase 3 v2 additions to the running list (numbering continues from above):**

8. **Add a list-format cleanup pre-pass** for transcripts that contain numbered/lettered enumerations with multiple restart attempts per item. Light Haiku call that produces a "cleaned list draft" before scripting.
9. **Clarify the "Sai's actual words" rule** in `sai-script-style-guide.md` — does it include lines Gray/others say that Sai verbally endorses?
10. **Add a parable/anecdote shorts template** to `business/social-media/story-arc-playbook/templates/`.
11. **Rule: when Sai self-redacts ("No, I don't want to mention that"), honor the redaction.**
12. **Refine the 3-beat parallel rule:** invent → no, preserve when organic → yes.
13. **Name "Authority-Anchor Opener"** as a hook variant in the style guide (dollar-scale credibility line as opener).
14. **Verification flag for invented payoffs:** when the subagent adds copy that isn't in the transcript, return a structured "verify_before_filming" list — Gray confirms each before locking the batch.

**Phase 3 outputs:**
- ✅ Batch file: `business/social-media/sai/scripts/2026-06-02-batch-2.md` (~16 KB, 11 scripts)
- ⏳ Sai's revision pass — pending
- ⏳ Visuals doc (modeled on `Sai Batch Scripts Visuals 2026-05-26.gdoc`) — not in scope for this run; layer in if Gray asks

---

### ⏸ Paused 2026-06-02 — resume state

Gray called pause after Drive ingest + retro Phase 2 notes. Tool tooling needs polish before pushing further through this batch.

**State at pause:**
- ✅ 13 .m4a files downloaded to `C:/Users/Gray Davis/My Drive/Voice memos/Batch 2/` (sizes verified against Drive)
- ❌ 0 transcripts produced — `python main.py --transcribe-only` loop was stopped mid-batch (no transcripts written, no API calls made — local Whisper only)
- ✅ Retro doc has Phase 1 (Drive ingest) + Phase 2 (transcription setup) notes + 7 v2 candidates
- Scriptwriter subagent NOT invoked yet

**To resume:**
1. (Optional, recommended first) Fix top-friction v2 items so resume isn't gated on the same gaps:
   - Add `sys.stdout.reconfigure(encoding="utf-8")` to `python-scripts/content-pipeline/main.py`
   - Add `--transcribe-only --all` batch support to `main.py` (currently only `--meeting-notes` batches)
   - Decide on karramedia Drive access pattern (second gdrive MCP vs Python helper) — only matters for *future* batches, not this resume since the .m4a files are already on disk locally
2. Run the transcription loop again:
   ```
   cd "C:/Users/Gray Davis/my-project/python-scripts/content-pipeline"
   export PYTHONIOENCODING=utf-8
   for f in "C:/Users/Gray Davis/My Drive/Voice memos/Batch 2/"*.m4a; do
     python main.py "$f" --transcribe-only
   done
   ```
3. Move resulting transcripts from `python-scripts/content-pipeline/output/` to `My Drive/Voice memos/Batch 2/`
4. Merge the 2 finance pairs at the transcript level: `How I manage my money pt 1 + pt 2` → one; `Redoing Finance part 1 + part 2` → one. Net: 11 transcripts.
5. Invoke scriptwriter subagent with the 11 transcripts as input, honoring the `(great hook)` / `(hook at the end)` parentheticals on `Landed a Fortune 500 client` and `Accept your passion`.
6. Save batch output to `business/social-media/sai/scripts/2026-06-02-batch-2.md` (or refile date if it slides to the next day).
7. Append Phase 3+ notes to this retro.

### Categories to watch
- **Voice slips** — did Sai sound like an AI? Specific lines Gray rewrote?
- **Playbook gaps** — info the subagent needed that wasn't in playbook.md / frameworks.md / a reference?
- **Spec gaps** — inputs the subagent should have asked for upfront but didn't (per scriptwriter.md Step 2)?
- **Output contract drift** — asterisks, hook labels, em-dashes, AI-essay headers that slipped through?
- **Transcription friction** — file paths, prefix conventions, batch numbering, handing memos to the subagent?
- **Cost** — how many tokens did the subagent burn? Was the playbook+corpus read efficient?
- **Time to deliverable** — voice memos in → 9 scripts out, wall clock?

### v2 candidates (running list)

_(Add as patterns emerge across runs — don't fix on a single data point.)_

**From Run 1 (single data point — confirm with Run 2 before acting):**

1. **Second gdrive MCP authed to `karramedia.com`** OR a Python helper that uses `gdocs-cli`'s karramedia OAuth to download by Drive folder ID. This is the highest-friction issue and will recur every batch unless solved.
2. **Add `--transcribe-only --all` batch mode to `content-pipeline/main.py`.** Currently only `--meeting-notes` batches.
3. **Add `--keep-audio` flag (or default) for `--meeting-notes`.** Deleting the .m4a after notes extraction is wrong for the batch-script flow.
4. **Fix Windows stdout encoding in `main.py`.** Add `sys.stdout.reconfigure(encoding="utf-8")` per the existing `feedback_windows_utf8_stdout.md` rule.
5. **Flesh out `content-pipeline` SKILL.md** with the actual CLI surface (it's currently a placeholder).
6. **Drive naming convention SOP for Sai voice memos.** No typos, no "or 2" / "pt 2" ambiguity, `(great hook)` / `(no hook)` parentheticals standardized.
7. **Scriptwriter subagent voice handoff:** confirm it knows to merge "part 1 + part 2" transcripts by filename pattern before scripting, or pre-merge them in the orchestration layer (i.e. me, before calling the subagent).

---

## Run N — _(future)_
