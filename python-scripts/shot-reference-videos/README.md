# shot-reference-videos

Turns shotlist reference **images** into 5-second reference **videos** that show the camera
move. Wraps the Higgsfield CLI.

Full reasoning, costs, and prompt rules: [`workflows/shot-reference-videos.md`](../../workflows/shot-reference-videos.md)

```
./shotvid.py plan   founder-story-shots.tsv   # cost preview, spends nothing
./shotvid.py submit founder-story-shots.tsv   # fire the queue, returns in seconds
./shotvid.py run                              # hands-off until everything downloads
./shotvid.py collect                          # or check in manually
./shotvid.py status
./shotvid.py reroll shot5 --prompt "..."
```

Requires the `higgsfield` CLI, logged in (`higgsfield auth login`).

- 5 credits per clip (Seedance 2.0 Mini, 480p, 5s, audio off)
- 6 concurrent jobs max — the Plus plan ceiling, handled automatically
- `state.json` tracks jobs and cached uploads; `out/` holds the clips

Both are local working files, not committed.
