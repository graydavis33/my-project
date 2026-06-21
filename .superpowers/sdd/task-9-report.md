# Task 9 Report — run.py driver + B3_V04 parity config

**Status:** DONE

## Files created

| File | Purpose |
|---|---|
| `python-scripts/batch-pipeline/videos/B3_V04.json` | Per-video parity config (9 ranges, POSIX-relative paths) |
| `python-scripts/batch-pipeline/run.py` | Thin CLI driver wiring Tasks 1-8 |

## Signature verification (pre-write reads)

All four module signatures confirmed against source before writing:

- `config.library_root() -> Path` — reads `SAI_LIBRARY_ROOT` env var
- `cut.build_cut(synced_a, synced_b, lav_wav, words, ranges, out_dir, vid_tag) -> dict` — keys `a`, `b`, `caption_words`, `total_s`, `synced_outs`; `ranges` = list of `(sin, sout, head, tail)`; `words` = flat list of `{start, end, word}`
- `captions.render(caption_words, ref_video, out_mov) -> Path` — `caption_words` is a Path to the JSON cut wrote
- `verify.gate(a_cut, b_cut, lav_wav, synced_outs) -> dict` — key `passed: bool`
- `package.deliver(batch_n, vid_n, title, a_cut, b_cut, captions_mov, info, out_root=None) -> Path` — `info` dict with key `"text"`

## run.py steps (matching spec)

1. `sys.stdout/stderr.reconfigure(encoding="utf-8")` at top
2. Load JSON, resolve all media paths against `config.library_root()`
3. Convert `ranges` entries: JSON `null` → Python `None`
4. Flatten segments→words: `words = [w for s in data["segments"] for w in s["words"]]` — single location
5. Decide `work_dir`: `(out_root or lib/"08_AI_EDITS"/"shorts") / "_work"`; `work_dir.mkdir(parents=True, exist_ok=True)`
6. `vid_tag = f"B{batch_n}_V{vid_n:02d}"`
7. `cut.build_cut(...)` 
8. `captions.render(cut_res["caption_words"], cut_res["a"], captions_mov)`
9. `verify.gate(cut_res["a"], cut_res["b"], lav_wav, cut_res["synced_outs"])`
10. Compose `_INFO.txt` text (title, lav cam, audio note, total_s, segment count); `info = {"text": ...}`
11. `package.deliver(...)` with `out_root=out_root`
12. Print gate dict; if `not gate["passed"]` → FAILED banner + `sys.exit(1)`

## Checks

- `python -c "import ast; ast.parse(...)"` → **syntax OK**
- `json.loads(...)` on B3_V04.json → **parse OK** (9 ranges, all 8 keys present)

## Concerns

None. The driver is intentionally thin — no new behavior beyond wiring. The `null`→`None` conversion for `tail` in the last range (`0.40` is already a float, not null) is handled cleanly by the list comprehension. The `TAIL` default in `cut.plan()` only applies when `tail is None`, so the explicit `0.40` on the last range will be passed through as-is — correct behavior per the spec.

No unit test for `run.py` per plan — this is integration only, to be verified by the controller with `--out-root` pointing at a scratch dir.
