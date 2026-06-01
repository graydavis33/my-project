# School of Hard Knocks — Reel Study Brief

_Created: 2026-04-27. Goal: extract every replicable pattern from their top 30 reels into a crash course Gray can study + imitate (especially for Sai content)._

## Phase 1 — Data Collection

- **Target:** top 30 reels from `@theschoolofhardknockz` (https://www.instagram.com/theschoolofhardknockz/)
- **Selection:** ranked by view count visible on each reel thumbnail
- **Method:** Gray collects URLs into Notes → pastes into chat → yt-dlp batch download
- **Output:** `urls.txt` + 30 `.mp4` files numbered by popularity rank (`01-...`, `02-...`)

## Phase 2 — Per-Reel Extraction

For each of the 30 reels:

- **Whisper transcript** — full text + word-level timestamps (via existing `python-scripts/content-pipeline/`)
- **Frame analysis (Claude Vision)** — 4 key frames per reel: opening frame, mid-reel frame, peak-engagement frame, closing frame. Tags: on-screen text, framing, host appearance, setting, B-roll presence
- **Edit-cut detection** — scene-change timestamps via ffmpeg `select='gt(scene,0.3)'`
- **Metadata pull** — caption text, post date, view count, like count, hashtags

## Phase 3 — Aggregate Analysis (The Crash Course)

Final `crash-course.md` covers all of these:

1. **Hook patterns (first 3 seconds)** — exact wording, visual, audio, on-screen text
2. **Question library** — every question grouped by archetype (provocative / neutral / follow-up / finance-specific / lifestyle / "gotcha")
3. **Question delivery** — phrasing style, body language, eye contact, pause patterns
4. **Edit timing** — avg cuts per reel, jump-cut frequency, longest single shot, fastest sequence
5. **B-roll / cutaways** — frequency, what they cut to (reaction shots, money, location, none), integration style
6. **On-screen text / captions** — font, color, stroke, position, animation, words-per-frame, sync to speech
7. **Music + sound design** — original audio only? Music bed? SFX on cuts? Volume mix
8. **Camera + framing** — shot sizes (CU/MS/WS), eye contact pattern, handheld vs stable, single-cam vs multi-cam
9. **Host on-camera presence** — wardrobe, posture, energy level, facial expressions, signature mannerisms
10. **Setting / locations** — which places, why, how location is established in-shot
11. **Cold open vs context** — do they tell you who the subject is upfront or reveal later? How?
12. **Outro / CTA** — how each reel ends: punchline, cliffhanger, "follow for more", silence, caption-only
13. **Long-form → short-form pipeline** — clip selection logic: which 15s out of a 30min interview becomes a reel? Pattern recognition.
14. **Posting cadence + caption copy** — frequency, caption length, hashtag style, tags, emoji usage
15. **Outlier analysis** — what the top 5 reels do that the bottom 25 don't (the secret sauce)
16. **Account-level patterns** — multiple sub-accounts, cross-posting strategy, series/recurring segments naming

## Phase 4 — Imitation Playbook

Translate findings into actionable SOP — specifically tuned for **Sai content** (CEO interviews, business commentary):

- **Shot list** Gray follows on-set (exact framings, lens choice, distance)
- **Question bank** — 30+ questions ready to ask, in their proven archetypes
- **Edit recipe** — exact cut cadence, when to add captions, when to cut to B-roll
- **Hook templates** — 5–10 hook patterns with fill-in-the-blank structure
- **Outro templates** — proven endings to copy

## Outputs (final folder structure)

```
school-of-hard-knocks/
├── STUDY-BRIEF.md          ← this file
├── urls.txt                ← Gray's 30 reel URLs
├── reels/                  ← raw .mp4 downloads (01-..., 02-..., 03-...)
├── transcripts/            ← per-reel Whisper transcript JSONs
├── frames/                 ← per-reel frame analyses + extracted JPGs
├── data.csv                ← master queryable table (one row per reel, ~40 columns)
├── crash-course.md         ← the report (sections 1–16 above)
└── playbook.md             ← actionable Sai-content SOP (Phase 4)
```

## Status

- [ ] Phase 1 — URLs collected (waiting on Gray)
- [ ] Phase 1 — yt-dlp downloaded
- [ ] Phase 2 — transcripts extracted
- [ ] Phase 2 — frame analysis done
- [ ] Phase 2 — edit-cut timestamps extracted
- [ ] Phase 3 — crash-course.md written
- [ ] Phase 4 — playbook.md written

## Reusability

This pipeline is generic — same scaffold works for any creator study (e.g. Iman Gadzhi, Alex Hormozi, Caleb Hammer). If we run it twice, promote it to `workflows/competitor-reel-study.md` as a permanent SOP.
