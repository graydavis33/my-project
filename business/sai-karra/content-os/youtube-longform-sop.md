# YouTube Long-form SOP

**Status:** Gray is finalizing this in a separate working doc before handing off. This file is the operational frame; the deep doc is what gets shared with editors later.

**Production tier:** HIGH (cinematic, full production)
**Cadence:** Weekly target
**Owner:** Gray (with editor team helping where bandwidth requires)

---

## What this is

The cinematic pillar of Sai's content. Every long-form gets the full treatment:

- Premiere timeline assembly
- HyperFrames asset factory for overlays / motion graphics / counters / infographics
- B-roll from the footage library (Footage Organizer v2 + `find_visuals.py` for transcript-driven b-roll matching)
- Cinematic A-roll (multi-cam where applicable)
- Founder Series and "three lessons" style essay long-forms are both this tier

---

## Format conventions

- 1080p (not 4K) — explicitly chosen earlier in the year, still the call
- Horizontal 16:9 unless the piece is a vertical-native experiment
- Length: typically 8-20+ min — no fixed target, length serves the piece
- 60fps render on any HyperFrames asset destined for long-form (matches Premiere ramping needs)
- Cut mechanics: see [[Sai long-form cut mechanics]] — tight dead-space cuts, never mid-word, composite from multiple takes at word boundaries
- Visual-layer cadence: see [[Sai long-form visual-layer placement rules]] — lower-thirds vs. full-graphic vs. b-roll proportions

---

## Workflow (high level)

1. **Pre-production**
   - Topic locked the day before shoot (per the 5/03 → 5/10 carryover principle)
   - Script outline (theme + key beats, not word-for-word)
   - Shotlist mapped to script beats

2. **Production**
   - A-roll on cinema camera, tripod where possible
   - B-roll captured in parallel (Gray's job during talking-head days)
   - Audio: lav mic primary, room mic secondary

3. **Post**
   - Transcribe (Whisper large-v3 on RTX 5070, free)
   - Cut to assembly via take-selection (Claude Sonnet 4.6 or manual)
   - B-roll match via `find_visuals.py` against transcript beats
   - HyperFrames assets built/rendered per visual-layer cadence rules
   - Color grade, sound mix, music pass
   - 3 thumbnail options before publish

4. **Publish**
   - Custom thumbnail (3 options reviewed)
   - Description with timestamps + links
   - Cards + end screen wired

---

## Asset factory cross-reference

HyperFrames asset patterns that apply here (long-form ONLY — none of these go on daily UGC):

- Text-slide captions (`pattern_hyperframes_text_slide.md`)
- Slot-machine counters (single-icon + countdown, dual-counter variants)
- Two-zone comparison infographics
- Continuous-pen slideshow ("follow the drawing")
- Focal-dot morph transitions
- Surgical-patch overlays (chip-digit overlay for editor's flattened motion graphics)
- X-stamp negation
- Shutdown stamp + impact shake + diagonal strike
- Knockout text on chroma green

See `MEMORY.md` Sai Karra section for the full list of locked patterns.

---

## Action item

- [ ] Gray finalizes the deep SOP doc (script + shotlist + edit checklist) before handoff to editor team
- [ ] Once finalized, fold key sections into this file or link out

---

## Don't

- Don't shortcut visual quality on long-form — this is the tier where production budget lives
- Don't move asset-factory patterns into daily UGC shorts (strip-down rule still applies there)
- Don't post a long-form without the 3-thumbnail-option review
