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

_(Phase 3+ — scriptwriter handoff + output review — to fill in after transcription completes.)_

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
