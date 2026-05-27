---
name: LinkedIn Visual Selection — ffmpeg Screenshots, Not Video Copies
description: When matching footage to LinkedIn visual_ideas.txt concepts, extract still frames with ffmpeg instead of duplicating full video files
type: feedback
originSessionId: 636ac229-cf80-45a4-aad1-3147996d8c11
---
When the sai-linkedin pipeline produces `visual_ideas.txt` and Gray asks for matching footage, **use ffmpeg to screenshot the best frame from each candidate clip** instead of copying the entire video file into the linkedin folder.

**Why:** On 2026-04-30 I copied 13 full clips (~5.6GB total) from the footage library into the linkedin folder for the "2026-04-27 Schedule V6" post. Gray flagged this as wasteful — he only needs a still image to attach to the LinkedIn post. Full video duplicates eat drive space and slow the workflow.

**How to apply:**
- For each visual concept in `visual_ideas.txt`, pick the best candidate clip(s) from the footage-organizer SQLite index
- Extract a single best-frame .jpg with ffmpeg (e.g. mid-clip frame, or scrub the clip and pick a frame Claude Vision rates highest)
- Save the .jpg into the same `linkedin/` folder where `caption.txt` lives, named `visualN-concept-CXXXX.jpg`
- Do NOT copy the full .mp4

**ffmpeg one-liner pattern:**
```
ffmpeg -ss <seconds> -i <source.mp4> -frames:v 1 -q:v 2 "<dest>/visualN-concept-CXXXX.jpg"
```

For multi-frame candidates per clip, extract 3–4 evenly-spaced frames and let Gray (or Vision) pick the best one — still way smaller than the full video.
