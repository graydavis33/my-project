# Footage Organizer — Future Ideas

Ideas for future versions of this tool. Not implemented yet. See [[README]] for current state.

---

## Hand Symbol Tagging System (2026-04-14)

**Origin:** Gray saw a videographer use hand symbols on the last frame of each clip as a tagging system. Premiere Pro's thumbnail view shows the last frame by default, so at a glance he could see which clips were good/bad/etc.

**Concept:** Instead of Claude Vision guessing what a clip contains or whether it's a good take, the videographer *signals* intent at capture time. The last frame of each clip shows a hand symbol that means something specific.

### Example Symbol Library (Gray to finalize during shoot)
- **Thumbs up** — good take, use this
- **Thumbs down** — bad take, don't use
- **Open palm** — okay, maybe use
- **1–5 fingers** — rating scale OR take number
- **Pointing right** — short clip
- **Pointing down** — long clip
- **Peace sign** — specific player / subject (assigned per shoot)
- **Fist** — specific trick / action (assigned per shoot)
- Dual-hand combos — compose meanings (left = rating, right = category)

### Why This Beats the Current Approach

| Current | Hand-symbol upgrade |
|---|---|
| Analyzes 4 frames per clip, infers content | Analyzes 1 frame (last), reads explicit intent |
| ~$0.003/clip (4 Vision calls) | ~$0.0005/clip (1 Vision call) — **6x cheaper** |
| Guesses "is this a good take" | Knows — you told it with a symbol |
| Accurate on content, weak on meta-judgments | Accurate on both |
| Fails on empty/dark/ambiguous shots | Works regardless — symbol is deterministic |

### Implementation Plan (when we build it)

1. **Extract last frame** via ffmpeg (`-vf "select=eq(n\,X)"` where X = last frame index)
2. **Run Claude Haiku Vision** on just that frame with a structured prompt:
   > "Detect any hand gesture. Return JSON: `{hand: 'left'|'right'|'both'|'none', gesture: 'thumbs_up'|...|'none', confidence: 0-1}`"
3. **Map gesture → tag** via a config file (user-editable symbol library)
4. **Fallback:** if no symbol detected (confidence < 0.7), fall back to current 4-frame content analysis — **backwards compatible with untagged footage**
5. **Output:** instead of rigid folder assignment, store tags as metadata (JSON sidecar or filename suffix) so one clip can have multiple tags (good + trick + player-name)

### Prerequisites Before Building

- [ ] Current footage-organizer tested in production on real footage folders
- [ ] Gray decides on final symbol library (start with 4–6 symbols, expand later)
- [ ] Gray drills the habit of flashing symbols at end of every take

### Why NOT Build This Yet

- Current tool isn't battle-tested yet — don't add complexity to an untested base
- Discipline needs to be in place first (no symbols = falls back to current behavior anyway)
- Better to validate current tool works for Gray's footage volume before investing in v2

### Design Suggestion
Think of symbols as **metadata tags, not folder assignments.** One clip can be `good` + `player=Sai` + `trick=barspin`. Stored as JSON sidecar or structured filename. Gives flexibility that rigid folders can't.

---

## Other Future Ideas

_(add more as they come up)_
