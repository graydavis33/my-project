# Editor Team — Folder Structure & File Naming

| Field | Value |
|-------|-------|
| **For** | Sai Karra shorts editing team |
| **From** | Gray Davis (Creative Director) |
| **Last Updated** | 2026-06-24 |
| **Version** | 1.0 |

---

## Google Drive Organization

**Root folder:** `[CUSTOMIZE: "Sai Content — Editor Batches" or your preferred name]`

```
Sai Content — Editor Batches/
├── Week_[##]_[Mon-Date]-[Fri-Date]/
│   ├── Video_01_[CUSTOMIZE: Title]/
│   ├── Video_02_[CUSTOMIZE: Title]/
│   ├── Video_03_[CUSTOMIZE: Title]/
│   ├── Video_04_[CUSTOMIZE: Title]/
│   ├── Video_05_[CUSTOMIZE: Title]/
│   ├── Video_06_[CUSTOMIZE: Title]/
│   ├── Video_07_[CUSTOMIZE: Title]/
│   ├── BATCH_BRIEFING.md (explained below)
│   └── REFERENCE_VIDEOS/ (folder with Sandcastles links + mood boards)
│
├── Week_[##]_[Mon-Date]-[Fri-Date]/
│   └── [same structure]
│
├── _TEMPLATES/ (never changes)
│   ├── BRAND_SPEC.md (see doc #3)
│   ├── Montserrat_Font_Files/
│   └── EXAMPLE_BATCH_BRIEFING.md
```

**Key:** Organize by week, not by date. Makes it easier to batch videos and talk about "this week's batch" without date confusion.

---

## Per-Video Folder Structure

Inside each `Video_NN_Title/`:

```
Video_01_[CUSTOMIZE: Title]/
├── _INFO.txt (what Gray wants from this video)
├── raw_footage/
│   ├── C[CUSTOMIZE: number].mp4
│   ├── C[CUSTOMIZE: number].mp4
│   └── [all source files]
├── REFERENCE/
│   ├── reference_1_sandcastles_link.txt (URL + timestamp)
│   └── reference_2_mood_board.mp4
├── TEMPLATES/ (locked — don't edit)
│   └── [Brand templates, fonts, etc.]
└── [VERSIONS]
    ├── Video_01_DRAFT_V1.mp4 (first full edit)
    ├── Video_01_REV1_V2.mp4 (after revision 1)
    ├── Video_01_REV2_V3.mp4 (after revision 2)
    └── Video_01_FINAL_V3.mp4 (locked, ready to publish)
```

---

## _INFO.txt Template

**Create this file in each video folder. Copy the template below and customize:**

```
VIDEO: [CUSTOMIZE: Video number and title]
RAW FOOTAGE: [CUSTOMIZE: C#### codes]
DURATION TARGET: [CUSTOMIZE: 30-45 sec]

WHAT I WANT:
[CUSTOMIZE: 2-3 sentences describing what this video should be]

MOOD/VIBE:
[CUSTOMIZE: e.g., "Raw, conversational, funny" or "Teaching, but casual"]

REFERENCE VIDEO:
[CUSTOMIZE: Link to Sandcastles outlier or mood board video + timestamp showing desired pacing]

GRAPHIC NOTES:
[CUSTOMIZE: e.g., "Minimal graphics" or "Simple $ icon" or "No graphics"]

ANYTHING ELSE:
[CUSTOMIZE: Any special instructions, warnings, or notes]
```

**Example:**

```
VIDEO: 3 — Money
RAW FOOTAGE: C2702
DURATION TARGET: 30-40 sec

WHAT I WANT:
Sai talks about early money mistakes. This should feel funny/relatable, not preachy.

MOOD/VIBE:
Casual, like he's joking with a friend. Don't over-produce.

REFERENCE VIDEO:
https://www.instagram.com/reel/[LINK] — notice the pacing at 0:15-0:30 (quick cuts, then holds)

GRAPHIC NOTES:
If you use a graphic, keep it simple. Maybe a small $ icon that fades in/out. That's it.

ANYTHING ELSE:
Sai loved the blooper version better — if you find a funny moment where he laughs or stumbles, that might work better than the polished version.
```

---

## Batch Briefing Document (BATCH_BRIEFING.md)

**Location:** Root of each week folder  
**Created by:** Gray Davis each Sunday  
**Purpose:** One-page overview of all videos in the batch

**Template:**

```markdown
# Week [##] — Batch Briefing

**Dates:** [Mon] - [Fri]  
**Videos:** [#]  
**Publish date:** [CUSTOMIZE: date]  

---

## Overview

[CUSTOMIZE: 1-2 sentences about the theme/vibe of this batch]

**Tone:** [CUSTOMIZE: e.g., "Raw, no B-roll. Just Sai talking." or "Storytelling, slower pacing"]  
**Length:** 30–45 sec max  
**Platform:** [CUSTOMIZE: "Instagram Reels primary" or "TikTok first, then Reels"]  

---

## Per-Video Direction

### Video 1: [CUSTOMIZE: Title]
- **Raw footage:** [CUSTOMIZE: C#### codes]
- **What I want:** [CUSTOMIZE: What this video should accomplish]
- **Mood:** [CUSTOMIZE: Tone/vibe]
- **Reference:** [CUSTOMIZE: Link to reference video, with timing note]
- **Special notes:** [CUSTOMIZE: Any graphics, pacing, or structure notes]

### Video 2: [CUSTOMIZE: Title]
[... repeat structure ...]

[Continue for all videos in the batch]

---

## Graphics Style (LOCKED — Don't Change)

- **Colors:** Trendify orange (#F28129), white, dark gray (#1A1A1A)
- **Fonts:** Montserrat ExtraBold (headers), SemiBold (body)
- **Shapes:** Rounded corners only. NO sharp angles.
- **Animation:** Simple fades/slides only. NO bounces/spinning.

[Reference: See `_TEMPLATES/BRAND_SPEC.md` for full detail]

---

## Timeline

- **Now:** You receive this brief + all video folders
- **48 hours:** Deliver all videos (V1 draft)
- **[CUSTOMIZE: Day/time]:** First review call with Gray
- **48 hours after call:** Deliver revised batch (V2)
- **[CUSTOMIZE: Day/time]:** Second review call (if needed)
- **[CUSTOMIZE: Date]:** Publish live

---

## Questions?
Slack in #sai-shorts-editing or @gray

---
**This brief created:** [Auto-timestamp by Gray]  
**Last updated:** [Gray fills in if anything changes mid-batch]
```

---

## File Naming Convention

**Raw footage (Sai's camera):**
```
C2700.mp4
C2701.mp4
```
*Use as-is. Don't rename.*

**Editor's versions:**
```
Video_01_DRAFT_V1.mp4       (first full edit)
Video_01_REV1_V2.mp4        (revision 1 delivery)
Video_01_REV2_V3.mp4        (revision 2 delivery)
Video_01_FINAL_V3.mp4       (locked, ready to publish)
```

**Rules:**
- Format: `Video_[NN]_[DRAFT|REV1|REV2|FINAL]_V[#].mp4`
- Increment version number with each upload: V1 → V2 → V3
- NO dates in filenames — Google Drive sorts by date modified
- NO timestamps — they clutter the filename
- NO custom names — stick to the convention so Gray can find things quickly

---

## How to Update This Doc

**When to update:**
- Every new batch (update the template section with new dates/video count)
- When you change the folder structure (update the directory tree above)
- When naming conventions change (update the file naming section)
- Quarterly (check that paths still match reality)

**What to update:**
- `[CUSTOMIZE: ...]` tags — these are the spots YOU fill in for each batch
- Dates and week numbers — these change each cycle
- Video titles and counts — vary per batch

**What NOT to change:**
- The overall structure (sections, headers, order)
- The folder organization scheme (keep it consistent)
- The `_TEMPLATES/` folder location (that's locked)
- File naming convention (editorial team needs consistency)

**To make updates:**
1. Open this file in Google Docs or your text editor
2. Search for `[CUSTOMIZE: ...]` to find blanks
3. Update BATCH_BRIEFING.md template each week with new details
4. Keep `_TEMPLATES/` folder unchanged (it's the reference system)
5. Commit changes to GitHub (mark as "docs: update folder structure") so you have a record

---

## Questions on Structure?

- "Can I organize videos by date instead of by week?" → No, stick to weeks. Easier to batch 7–10 videos per week.
- "Can I use a different naming convention?" → No, keep it consistent. Version numbers help track edits.
- "Where do I put feedback notes?" → In Slack. Google Drive folders stay clean (video files only).
- "Can I delete old week folders?" → Keep them all. They're a reference library for the editor team to see past examples.

---

**Version history:**
- **v1.0** (2026-06-24): Initial creation, based on Week 26 launch
