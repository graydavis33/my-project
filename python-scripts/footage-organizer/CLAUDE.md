# Footage Organizer — Working Notes

This tool is in active iteration. The reliability bar: Gray never has to manually re-sort a clip.

## Current state (2026-04-19)
- Format detection: orientation only (horizontal = long-form, vertical = short-form). 4K/1080p doesn't matter.
- 17 mutually-exclusive categories — see README.
- `miscellaneous` is the "I'm not sure" bucket — model uses it whenever two categories could fit. Gray reviews those manually.
- Eval harness in `eval.py` measures accuracy against a hand-labeled CSV. Logs go to `eval_runs/`.
- B-Roll Library archive (`--archive DATE`) drops clips into `06_BROLL_LIBRARY/{category}/{week-of-date}/`. Week = Monday of that ISO week, format `YYYY-MM-DD`.

## When asked to "improve the organizer"
1. Run the latest eval first — never tune blind.
2. Look at the confusion matrix. Find the worst-confused pair.
3. Tighten the prompt definitions for that pair specifically. Don't mass-rewrite.
4. Re-run with a new `--label`. Compare against the previous run.
5. Commit prompt changes incrementally — one tightening per commit.

## When asked to "add a category"
- Adding a category is a last resort. First check whether the missed clips fit `miscellaneous` and just need manual review.
- If you do add one: update `CATEGORIES` in `config.py`, add a strict definition with a primary visual question to the prompt in `analyzer.py`, re-label any test-set clips that are now better described by the new category, re-run the eval.

## Don't
- Don't restore the old 4K-based format detection.
- Don't add a `voiceover` category — Gray explicitly rejected it.
- Don't let the model invent categories or land files in unknown folders. The CATEGORIES list is the contract.
