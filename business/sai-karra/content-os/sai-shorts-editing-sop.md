# Sai Shorts — Editing SOP

End-to-end automation spec for batch-editing Sai's vertical short-form videos. Designed to be machine-readable so this can move from manual → semi-automated → fully automated over time.

**Owner:** Gray Davis
**Last updated:** 2026-05-28
**Pipeline status:** manual w/ tooling assists (Whisper, HyperFrames, Premiere). Target: automated trim → automated captions → manual graphic placement → automated render.

---

## 0. Pipeline overview

```
Raw shoot (D:/Sai/01_ORGANIZED/Batch N/)
   │
   ▼
[STEP 1] AI trim → D:/Sai/06_ASSETS/AI Trim/Batch {N}/Vid {M}/c{NNNN}_trim_v{N}.mp4
   │
   ▼
[STEP 2] Premiere review + tightening (optional) → no-captions delivered
   │
   ▼
[STEP 3] Manual graphic placement in Premiere → D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} no captions.mp4
   │
   ▼
[STEP 4] AI captions → D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} final.mp4
   │
   ▼
[STEP 5] Publish
```

Each step is documented below with exact inputs, outputs, rules, and tooling.

---

## STEP 1 — AI Trim

**Goal:** Take a raw multi-take session and output a tight, vertical 1080×1920 cut at 24fps with only the last-clean takes spliced together.

### Inputs
- Raw clip: `D:/Sai/01_ORGANIZED/Batch {N}/C{NNNN}.MP4`
  - Typically 1920×1080 horizontal with `rotation=90` metadata (auto-rotates to vertical 1080×1920 on extract)
  - 23.976 fps source
  - Camera-scratch audio (PCM)

### Process
1. **Probe** the source for resolution, duration, rotation:
   ```
   ffprobe -show_entries stream=codec_name,width,height,r_frame_rate \
           -show_entries stream_side_data=rotation \
           -show_entries format=duration source.MP4
   ```
2. **Extract mono 16kHz audio** for Whisper:
   ```
   ffmpeg -i source.MP4 -vn -ac 1 -ar 16000 -c:a pcm_s16le source.wav
   ```
3. **Transcribe with Whisper large-v3 on GPU**, word-level timestamps:
   ```python
   import whisper
   model = whisper.load_model('large-v3', device='cuda')
   result = model.transcribe('source.wav', language='en', word_timestamps=True)
   ```
4. **Identify clean takes** using these rules (in order of precedence):
   1. **Skip "Fuck.", "No.", "Yep.", "All right."** false starts and verbal vetoes
   2. **Skip mid-sentence restarts** — when Sai begins a sentence then stumbles and re-starts, take the LAST clean attempt
   3. **Default to last clean take** when multiple full takes of same line exist
   4. **Drop "And" interior connectors** at sentence STARTS ("And here's a little hack" → "Here's a little hack")
   5. **Keep "And" bridging** connectors that link to the previous beat ("And once I changed it" — keeps "And" because it bridges from prior beat)
   6. **Check for hidden restarts inside Whisper segments** — if a single Whisper word is labeled >1.5s duration, do an RMS energy scan to detect silent gaps. Use the clean half (typically the second attempt after a pause).
   7. **Cut frame-precise at word boundaries** — never mid-word

### Breath / pause rules
- **+0.35s breath after every sentence end** (default — Gray's current preference)
- **Cap the breath** when the next clean take starts within 0.35s (don't bleed into the next word audibly)
- **Never tighten the breath to 0s** — captions and pacing need the landing room
- **Don't artificially compress natural pauses inside a single continuous take** — keep Sai's rhythm

### Output
- **Path:** `D:/Sai/06_ASSETS/AI Trim/Batch {N}/Vid {M}/c{NNNN}_trim_v1.mp4`
- **Specs:** 1080×1920, 23.976fps, H.264 CRF 18, AAC 192kbps, +faststart
- **Encoder:** ffmpeg `filter_complex` with `trim/atrim/concat` per segment

### Vid numbering convention
- "Vid N" maps to the order Sai shot take sessions, not the file number.
- Batch 1: Vid 1=C2493 (tax payers), Vid 2=C2495, Vid 3=C2496, Vid 4=C2498, Vid 5=C2499, Vid 6=C2502, Vid 7=C2503

### Common pitfalls
- **Whisper compresses repetitions into one long "word"** — always RMS-check suspicious word durations.
- **Don't trust segment-level Whisper boundaries** for chunk start/end — use word-level timestamps.
- **Rotation=90 metadata** means file dims are 1920×1080 but display is 1080×1920. Verify before assuming horizontal.

---

## STEP 2 — Premiere review

Optional. Gray tightens or restructures the AI trim if needed (e.g., dropping extra beats, re-ordering takes). Output saved as no-captions delivered file.

---

## STEP 3 — Graphic placement (manual)

Gray composites HyperFrames-rendered graphics over the A-roll trim in Premiere using Ultra Key (chroma key). Graphic style is locked — see `web-apps/hyperframes/sai-shorts-vid4-systems/DESIGN.md` for full brand spec.

**Quick reference (locked brand):**
- 1080×1920 vertical chroma green `#00FF00` backgrounds
- Trendify orange `#F28129`, orange-glass cards
- Montserrat ExtraBold 72-92px headers, SemiBold 36-44px body labels
- `back.out(1.6)` entrances, finite repeats only
- All graphics produced via `npx hyperframes render --fps 24`

Graphics in a typical Sai short:
- Hook visual (B-roll, screen recording, OR title card)
- Step/beat illustrations (cards, counters, segmented bars, stickfigures)
- Closer / payoff visual

### Output
`D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} no captions.mp4`

---

## STEP 4 — AI Captions

**Goal:** Burn caption chunks on top of the no-captions delivered file, positioned to avoid blocking graphics or Sai's face.

### Inputs
- `D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} no captions.mp4`

### Caption style (LOCKED)
- **Font:** Montserrat SemiBold (weight 600)
- **Size:** 64px
- **Color:** White `#FFFFFF`
- **Drop shadow:** `0 4px 12px rgba(0,0,0,0.6), 0 2px 4px rgba(0,0,0,0.45)` (for readability over A-roll backgrounds)
- **Letter-spacing:** 0.005em
- **Line-height:** 1.18
- **Max-width:** 960px (BOT), 920px (TOP)
- **No stroke**
- **Single line preferred; 2 lines OK for long chunks (BOT only — TOP single-line required to clear Sai's head)**

### Text rules (CRITICAL — applies to every caption)
1. **All lowercase by default** — even sentence-starts
2. **Capitalize:**
   - **Standalone `I`** — ALWAYS capitalize (looks broken lowercase)
   - `I'm`, `I've`, `I'll`, `I'd` (contractions starting with I)
   - Names: `Sai`, `Trendify`, `Coach Waddell`, brand names
   - Cities, states: `Manhattan`, `NYC`, `New York`, `California`
   - Anything Gray explicitly capitalized in his script
3. **NO punctuation** — strip `.`, `,`, `;`, `:`, `?`, `!`
4. **Apostrophes ALLOWED** — for contractions: `we're`, `they're`, `I've`, `you'll`, `don't`, `isn't`
5. **Quotation marks ALLOWED** but rarely used
6. **NO filler `and` at chunk starts** when previous chunk doesn't need the bridge.
   Example: "and if you actually wanna" → "if you actually wanna". KEEP `and` when it bridges two adjacent ideas: "for planning your work AND executing on your work".

### Chunk rules
- **3-5 words per chunk** (sweet spot — matches Vid 1 tax-payers reference)
- **Break at natural phrase boundaries** (where commas would have been, conjunctions, sentence ends)
- **Chunk duration:** 0.5-1.5s typical, never <0.4s
- **Time-sync to Whisper word boundaries** — start time = first word's start, end time = last word's end
- **Double-line if too wide:** if chunk width > 880px (rendered at 64px Montserrat SemiBold), break to 2 lines via `<br>`. Single-line bias to keep tight, but width > UI safe zone is unacceptable.
  - Example: "in my career than ever before" → `in my career<br>than ever before`
  - Example: "my business changed when" → `my business<br>changed when`

### Position rules (DYNAMIC PER CHUNK)
Caption position depends on where the on-screen graphic sits at that moment. Default behavior:

| Graphic position | Caption position |
|---|---|
| None (clean A-roll) | **BOT** (default) |
| Graphic at TOP | **BOT** |
| Graphic at LOWER / CENTER-LOWER | **TOP** |
| Graphic at LOWER-LEFT + something at LOWER-RIGHT | **TOP** (clear lower half entirely) |
| Graphic IS the spoken word (e.g. "40/60" text on B-roll) | **REMOVE CAPTION** (redundant) |
| Sai's face would be covered | **Move further up or down** — never on face |

**Exact pixel positions (LOCKED in v3):**
- `cap-bot`: anchor to BOTTOM, `bottom: 470px` (text BOTTOM lands at y=1450 regardless of single/2-line) — below chest, above bottom UI safe zone
- `cap-top`: `top: 300px` (single line spans y=300-375; 2-line spans y=300-450)
  - Clears IG top UI safe zone (220px)
  - Leaves space between caption and Sai's hat brim in typical sitting shots (hat brim usually y=400+)
  - For 2-line TOP captions: verify hat brim is below y=470 in that shot; otherwise split into 2 single-line chunks instead

**Position discipline:**
- Caption MUST NOT touch Sai's face/hat — always visible gap
- Caption MUST NOT cover graphics — always opposite end
- Caption MUST NOT enter IG/TikTok UI zones (top 220px, bottom 400px)
- When in doubt: move the caption further from the head, accept smaller margin from UI

### Graphic timeline mapping (per video)
For each new video, manually sample frames at 1fps and map graphic positions across the timeline. Then assign each caption chunk's position based on the graphic at that timestamp. Document the map in the project's `index.html` header comment.

### Animation
- **Fade in:** 80ms `power1.out`
- **Fade out:** 80ms `power1.in`, begins ~60ms before chunk end
- **No entrance animation beyond fade** (matches Vid 1 reference — clean appearance/disappearance)

### Implementation
HyperFrames composition at `web-apps/hyperframes/sai-vid{M}-captions/`:
- `source.mp4` — copy of the no-captions file
- `index.html` — full-frame `<video>` on track 0, `<audio>` on track 2, captions overlay on track 1
- Each caption chunk is a `<div class="cap cap-{bot|top}">` pre-rendered in DOM with `opacity: 0`
- GSAP timeline fades each chunk in/out at its scheduled time

### Output
- `D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} final.mp4`
- Render: `npx hyperframes render --fps 24`
- Specs: 1080×1920, 23.976fps, H.264, AAC audio preserved

---

## STEP 5 — Publish

(Out of scope for this SOP — covered by per-platform SOPs in this folder: `instagram-reels-sop.md`, `tiktok-sop.md`, `youtube-shorts-sop.md`.)

---

## Caption corrections log (training data for automation)

Each correction Gray makes becomes a rule. Future automated runs should never repeat these mistakes.

### Vid 2 (C2495) — banked corrections

| Mistake | Correction | Rule learned |
|---|---|---|
| Showed "60/40" caption while "40/60" graphic visible | Removed caption — redundant with on-screen text | When a graphic literally shows the spoken word/number, hide the caption for that chunk |
| Wrote "i" lowercase as standalone pronoun | Capitalize to "I" | Standalone `I` always capitalized — looks broken lowercase |
| Wrote "i've made more strides" over growth-chart graphic at BOT | MOVE to TOP (chart is at bottom) — NOT remove. Removal mistake corrected in v4. | When caption overlaps a graphic, move to opposite end. Only remove a caption if the graphic literally shows the spoken words (e.g. "40/60" text on screen). |
| "in my career than ever before" single-line full width over chart | Move to TOP + double-line via `<br>` | When too wide AND over a center graphic, move position AND double-line |
| "my business changed when" single-line at the absolute width limit | Double-line via `<br>` so it sits inside safe zone | When chunk width >880px, force 2-line break |
| TOP captions at y=200 (too close to top UI; also no breathing room from head) | Lowered to y=300 | TOP captions need space FROM TOP UI (>220px) AND space ABOVE HEAD (caption bottom < hat brim minus 25px) |
| Kept "and" prefix on "and if you actually wanna" | Dropped to "if you actually wanna" | Drop leading `and` at chunk start when it's filler. Keep `and` only when bridging two adjacent ideas (e.g., "for planning your work AND executing on your work") |

### Vid 1 (C2493, tax payers) — the original reference
- Captions are lower-third only (BOT)
- White Montserrat SemiBold 64px, lowercase, no punctuation
- No entrance animation beyond a quick fade

---

## Naming conventions

| Asset type | Path |
|---|---|
| Raw source | `D:/Sai/01_ORGANIZED/Batch {N}/C{NNNN}.MP4` |
| AI trim | `D:/Sai/06_ASSETS/AI Trim/Batch {N}/Vid {M}/c{NNNN}_trim_v{N}.mp4` |
| No-captions delivered | `D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} no captions.mp4` |
| Final captioned | `D:/Sai/03_DELIVERED/shorts/Batch{N} Vid {M} final.mp4` |
| Graphics MP4s | `D:/Sai/06_ASSETS/Visual Effects/Sai-VFX-{ConceptName}.mp4` |
| Graphics source | `web-apps/hyperframes/sai-shorts-{vid-or-date-slug}/{NN-{concept}/index.html` |

---

## Automation roadmap

| Step | Current | Next | Goal |
|---|---|---|---|
| Trim | Whisper + manual rule-application in build_cut.py | Auto-apply all rules in script | Full auto from raw → trim MP4 |
| Captions | Manual chunk mapping + graphic position mapping | Auto-detect graphic positions via per-second frame analysis | Full auto from no-captions → captioned MP4 |
| Graphics | Manual HyperFrames builds per beat | Reusable beat templates parameterized by transcript | Auto-generated graphics from beat detection |
| Publish | Manual | Scheduled push via platform APIs | Auto-publish |

---

## Open questions / decisions deferred

- Graphic auto-positioning: how to detect graphic regions per-frame (color heuristics? OpenCV? CLIP vision?)
- Caption-position auto-detection: should depend on graphic map (Step 4 rules)
- Whether to include a hook title card by default or rely on the spoken hook + first graphic only

---

## Reference materials

- Brand spec: `web-apps/hyperframes/sai-shorts-vid4-systems/DESIGN.md`
- Voice/script style: `Obsidian/Graydient Media/Content/Graydient Media/Voice Style.md` (Graydient brand, related)
- Pattern library: `web-apps/hyperframes/sai-shorts-2026-05-27/` (yesterday's tax-shorts batch)
- Pattern library: `web-apps/hyperframes/sai-shorts-vid4-systems/` (systems-framework batch)
- Take-selection rules memory: `feedback_sai_short_form_ai_edit_lessons.md`
- Long-form cut mechanics: `feedback_long_form_editing_from_gray_diff.md`
