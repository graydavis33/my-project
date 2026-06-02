# Sai Ep 1 — Effects & Graphics Placement Study

**Source:** `D:/Sai/02_ACTIVE_PROJECTS/episodes/W05_May-11-17/Ep 1 Reference Claude.mp4`
**Length:** 6:38.2 (398s), 1920×1080, 24fps, h264
**Date studied:** 2026-05-13
**Status:** pre-revisions (Gray's cut, no SFX/music yet, no Sai review)

Study scope per Gray: effect timing/tempo, effect templates, b-roll selection patterns — for eventual auto-replication. Cut mechanics already locked in [feedback_long_form_editing_from_gray_diff.md](../C:/Users/Gray%20Davis/.claude/projects/c--Users-Gray-Davis-my-project/memory/feedback_long_form_editing_from_gray_diff.md).

---

## The Big Numbers

| Visual treatment | Scenes | Total time | Avg duration | % of runtime |
|---|---|---|---|---|
| `a_roll` (pure talking head) | 32 | 122.2s | 3.82s | 30.7% |
| `a_roll` + text overlay | 8 | 24.2s | 3.03s | 6.1% |
| `a_roll` + graphic overlay | 9 | 46.4s | 5.15s | 11.7% |
| `b_roll` (cutaways) | 10 | 39.2s | 3.92s | 9.9% |
| `full_graphic` (HyperFrames/illustration) | 34 | 165.6s | 4.87s | 41.6% |
| **Total** | **93 scenes** | **397.6s** | **4.27s avg** | — |

**Headline finding:** the visual layer is on screen **~59% of the runtime** (full_graphic + overlays). Pure-A-roll is a minority shot. This is graphics-heavy editing.

**Cut cadence:** 93 visual changes in 398s = **one cut every 4.3s on average.** Hook compresses to ~1.5s per cut; storytelling middle relaxes to 4-7s; full-graphic chapter cards stretch to 10-14s.

---

## Effect Template Catalog

Templates Gray uses, sorted by frequency / load-bearing-ness.

### Template 1 — Lower-third dollar/timeframe callout (a_roll + text overlay)
Short white text floats over a-roll during a numerical claim or key phrase. Holds 1-3s, then disappears as the line moves on.

**Triggers on:** dollar amounts, year-counts, follower-counts, named concepts ("Part 2 Stories", "Generational Wealth")

**Examples from ep1:**
- 00:00 "Millions of Dollars" (over the hook: "my business has made millions of dollars")
- 00:05 "And I Currently" (caption animating the spoken line)
- 00:12 "5 years" (over "for the last five years, my life…")
- 01:29 "Part 2 Stories" (over "And then the idea hit. Part 2 stories.")
- 02:40 "Generational Wealth" (over "make me generational wealth")
- 03:01 "$5 Million Profit" (over "projecting to make $5 million")
- 03:27 "$100,000" (over "spent close to $100,000 on this NFT project")
- 05:36 "SHUT PROGRAM / SHUT DOWN [DWY]" — red stamp (over "shut down the coaching program / shut down the done with you model")

**Auto-replicate rule:** Detect spoken phrases that include `$X`, `X years/months`, named concepts in quotes, and any number > 1000. Generate a 1.5-3s lower-third with the exact spoken phrase. Last one uses red `hyperframes-shutdowns` stamp template (already built 2026-05-09).

### Template 2 — Big number callout on a-roll
Massive "1" or "4" or similar number scales in on top of Sai during a counting/year beat. Very short (~0.8s).

**Examples:** 00:10-00:12 "1" then "4" overlaid on Sai during "for the last five years."

**Auto-replicate rule:** When the speaker says a sequence of digits or a year-count, drop a 0.8s number callout per digit beat. Slot-machine-counter look (see `hyperframes-fewer-clients` pattern, 2026-05-09).

### Template 3 — HyperFrames chroma-keyed asset overlaid on a-roll
Sai stays in frame, HyperFrames composition keys in via chroma green. Holds 3-6s.

**Examples from ep1:**
- 00:55 talking stickfigures speech bubble (`hyperframes-talking-stickfigures`, 2026-05-06)
- 01:13 "ONE MONTH" calendar (`hyperframes-calendar-month`, 2026-05-07)
- 04:17 phone screen overlay
- 06:13 "BUILD IN TRUTH" shield + icons + X-marks (`hyperframes-no-break-build-truth`, today 2026-05-11)
- 06:26 "@saikarra Subscribed" CTA button (outro)

**Auto-replicate rule:** Build the HyperFrames asset on chroma green (`#00B140` default, `#0047BB` when asset itself is green per [feedback_hyperframes_chroma_color_choice](../C:/Users/Gray%20Davis/.claude/projects/c--Users-Gray-Davis-my-project/memory/feedback_hyperframes_chroma_color_choice.md)), key it in Premiere on a track above the A-roll. Used when concept needs visual reinforcement but the speaker is still earning his screen presence.

### Template 4 — HyperFrames full-screen asset (no a-roll visible)
Full-canvas HyperFrames composition replaces Sai entirely for 3-14s. Used for the big concept moments and chapter-card lessons.

**Examples from ep1 (chronological, with build provenance):**
- 02:57 (lesson 1) "1. Don't take shortcuts that break trust…" — orange numbered lesson card
- 02:25 phone-mockup "PART THREE" link (`hyperframes-part-cards`, 2026-05-07/08)
- 02:57 "OPPORTUNITY OF A LIFETIME" — orange illustration
- 02:57 NFT hexagon (`hyperframes-nba-ceo-celeb-nft`, 2026-05-07)
- 03:05 equity split breakdown (`hyperframes-free-interns-equity`, 2026-05-07)
- 03:36 "NFT MARKET CRASH" — orange illustration
- 03:51 lesson 2 card "Don't rely on others to scale. Don't overpromise…"
- 03:59 focus diagram (`hyperframes-crazy-future-vs-project`, today 2026-05-11)
- 04:26 split brain icon (`hyperframes-split-brain`, 2026-05-08)
- 04:34 "THEN… A GENIUS IDEA" — `hyperframes-business-right-way` scene-3 lightbulb (2026-05-08)
- 04:48 "TEAMWORK / WE'RE HIRING" — `hyperframes-free-interns-equity` variant
- 04:56 "$16,400" calendar (`hyperframes-clients-to-20k` variant, 2026-05-09)
- 05:25 lesson 3 card "Obsess over your customer. Nothing else matters as much."
- 05:46 lifestyle phones (two-phone collage, orange)
- 05:46 client funnel (`hyperframes-client-funnel`, today 2026-05-11)
- 06:10 text slide "Do truthful work and the universe will reward you accordingly" (`hyperframes-text-slide-truthful-work`, today 2026-05-11)

**Auto-replicate rule:** This is the big lift. Triggers when:
- Speaker says "lesson number N" / "the first lesson" / "rule number" → drop a numbered orange lesson card with the takeaway sentence as the body
- Speaker introduces an abstract concept (focus, brain, opportunity) → metaphor-asset (split-brain, focus-diagram, opportunity-of-a-lifetime)
- Speaker presents structured comparison (equity split, client breakdown, before-vs-after) → HyperFrames structured diagram
- Speaker quotes themselves or delivers an aphorism → text-slide composition

### Template 5 — Orange illustrated stock scenes
Distinct from HyperFrames: cartoon-style flat illustrations on orange backgrounds. Slot-machine jackpot, banking app with $0.00, brand deals call, content-creator-on-bed, basketball game, money vortex, NFT crash newsroom, angry boss, etc. ~14 instances across the ep.

**Origin:** Almost certainly Midjourney/Recraft-style commissioned set, OR a stock pack. The signature is: orange `#F28129`-ish background + flat semi-abstract figures + bold text labels.

**Triggers on:** narrative beats where Sai recounts a specific scene/event ("started doing brand deals", "people were becoming deca-millionaires", "the founder went ballistic on a call")

**Auto-replicate rule:** Generate via Midjourney/Higgsfield with prompt template: `orange background #F28129, flat illustration, [scene description], bold white text label "[KEY PHRASE]"`. Or maintain a growing library of these. Today's session habit: when narrative recounts an EVENT (vs. a concept), prefer this style over HyperFrames.

### Template 6 — Numbered list intro/outro cards
Orange background with white "1, 2, 3" or "1, 2" card. Used as a chapter scaffold.

**Examples:** 00:15 "1, 2" intro (right after the hook); 05:57 "1, 2" outro recap.

**Auto-replicate rule:** Drop at the moment Sai says "three specific lessons" / "let me tell you the three things" → reveal numbered tiles as Sai narrates each.

### Template 7 — Phone-framed photo collage on orange
Two or three phone screenshots framed on orange. Used for trendify product showcase (scene 12) and lifestyle photos (scene 86, 90).

---

## B-Roll Selection Patterns

Only 10 b-roll cutaways in the whole ep (~10% of runtime). Light usage by design — Sai's a-roll carries most of the storytelling.

| Time | Category | Subject | What Sai is saying |
|---|---|---|---|
| 00:29 | action-sport-fitness | teen bench pressing | "started at the age of 16…living every teenager's dream" |
| 01:57 | candid-people | young man in gray Nike hoodie smiling | "I started more accounts, doing the same exact thing" |
| 02:11 | establishing-interior | man in hoodie at desk with laptops + city view | "hoped that I would keep making money with the content" |
| 03:00 | candid-people | young man in gray hoodie at window | "I just knew that I couldn't fail" |
| 03:14 | interview-duo | beige shirt on video call with laptop | NFT project family promotion |
| 04:06 | candid-people | white shirt gesturing on couch | "all you'll feel like doing is talking about it" |
| 04:24 | candid-people | young man with laptop on couch | "had made it the main thing for about a year" |
| 05:02 | insert-hands | mic at desk | "But I had stopped caring because I was so distracted" |
| 05:57 | interview-duo | gray hoodie at microphone | "first to be a-roll" |
| 06:24 | candid-people | young man at desk with laptop | "you'll make way more money than anyone else" |

**B-roll selection rules I can infer:**
1. **Same-subject footage from other shoots** dominates — alt-angle of Sai from interview/podcast/desk shoot days. ~7 of 10 are this category. Reduces visual fatigue without introducing a different person.
2. **Thematic-match cutaways are rare but powerful** — bench-press shot at "age of 16" is the only one that LITERALLY illustrates the spoken line.
3. **B-roll is the fallback** when there's no graphic-concept to attach. Compared with full_graphic (37%), b-roll (11%) is clearly the second-choice option.
4. **No insert-product, no transit-vehicles, no environment-detail used.** The library has these but Gray didn't reach for them.

**Auto-replicate rule:** When the spoken beat doesn't have a graphic-concept and is too long to stay on the primary a-roll angle, pull alt-angle Sai footage from `interview-solo`, `candid-people`, `reaction-listening` categories. If the line contains a CONCRETE TIME/AGE reference, search `action-sport-fitness` and `establishing-exterior` for literal-match shots.

---

## Tempo Rules

Empirical patterns from the timeline:

1. **Hook (0-20s): 1 cut per 1.5-2s.** Six different visual treatments stacked: a_roll → text-overlay → a_roll → number-callout × 2 → text-overlay × 2 → full_graphic jackpot → numbered tiles. **Pack visual density high for the first ~15s.**

2. **Storytelling middle (20-340s): 1 cut per 3-6s.** Long enough to land a thought, short enough to never let the eye get bored.

3. **Lesson cards are the longest holds (5-14s).** They function as chapter markers. Each of the 3 lessons gets a full-screen orange card with the lesson body text held long enough to read.

4. **Outro (340-398s): 1 cut per 4-9s, climbing.** Tempo slackens as we approach the CTA. Last 11 seconds is a_roll + subscribe-button overlay holding through the close.

5. **Text-overlay callouts are ALWAYS short (0.8-3s).** Never lingering. They punctuate, they don't anchor.

6. **Full graphics are ALWAYS longer than the overlay treatments** (avg 4.87s vs 3.03s for text overlay).

7. **Pure a-roll stretches above 5s only when emotion/passion is the load-bearing element** — the spoken delivery is doing the heavy lifting and any graphic would compete with it.

---

## Effect-Per-Spoken-Line Mapping (Triggers)

Distilled rules from observed pairings — what kinds of lines earn what kinds of effects:

| Spoken trigger pattern | Effect template |
|---|---|
| Dollar amount mentioned | Lower-third white text with `$X` |
| Year/timeframe ("5 years", "one month") | Lower-third or full HyperFrames calendar |
| "Lesson number N" / "the first lesson is" / etc. | Full-screen orange numbered lesson card with body text |
| Self-quote / aphorism | HyperFrames text-slide (word-by-word reveal pattern) |
| Concrete scene/event recounted ("brand deals", "going viral", "founder went ballistic") | Orange illustrated scene |
| Abstract concept introduced ("focus", "monkey brain", "split priorities") | HyperFrames metaphor asset (split-brain, focus-diagram) |
| Structured comparison ("we promised 5% to each of 3 friends", "5 clients paying $20k") | HyperFrames structured diagram (equity-split, client-funnel) |
| Negation list ("no competition, no AI, no external forces") | HyperFrames icon-equation with X-stamps (`no-break-build-truth`) |
| List opener ("three specific lessons", "the things I learned") | Numbered intro tiles on orange |
| Big follower/view number ("millions of followers", "240 million views") | HyperFrames slot-machine counter (`millions-followers-views` template, today's build) |
| CTA / outro ("subscribe", "follow") | Subscribed button overlay |
| Killed/shut-down/eliminated item | Red shutdown stamp (`hyperframes-shutdowns`) on a-roll |

---

## Patterns Already Reusable (HyperFrames built between 2026-05-05 and 2026-05-13)

13 of the assets in this episode are HyperFrames compositions we built together this week+:

1. `hyperframes-talking-stickfigures` (2026-05-06) → scene 19 hypothetical-conversation
2. `hyperframes-calendar-month` (2026-05-07) → scene 24 "ONE MONTH"
3. `hyperframes-part-cards` (2026-05-07/08) → scene 46 "Click this link to watch part 3"
4. `hyperframes-nba-ceo-celeb-nft` (2026-05-07) → scene 52 NFT equation
5. `hyperframes-free-interns-equity` (2026-05-07) → scene 55 EQUITY SPLIT + scene 76 TEAMWORK/HIRING
6. `hyperframes-split-brain` (2026-05-08) → scene 73 brain icon
7. `hyperframes-business-right-way` (2026-05-08, v2 today) → scene 75 "THEN… A GENIUS IDEA"
8. `hyperframes-clients-to-20k` (2026-05-09) → scene 79 calendar with $16,400
9. `hyperframes-shutdowns` (2026-05-09) → scene 89 red SHUT DOWN stamp
10. `hyperframes-text-slide-truthful-work` (2026-05-08) → scene 96 "Do truthful work" quote
11. `hyperframes-no-break-build-truth` (today 2026-05-11) → scene 97 BUILD IN TRUTH
12. `hyperframes-client-funnel` (today, v2 today) → scene 92 Client 1-5 + $
13. `hyperframes-crazy-future-vs-project` (today 2026-05-11) → scene 65 FOCUS diagram

**Implication:** the asset-factory approach is working. Each asset we've built in the last 8 days is being USED. Building more reusable HyperFrames primitives for the trigger patterns in the table above directly compounds productivity for future episodes.

---

## What's NOT Yet Reusable (gaps to fill for auto-replication)

1. **Orange illustrated scenes** — we don't have a workflow for these yet. They're third-party-looking flat illustrations. Need to either (a) build a Midjourney/Higgsfield prompt template + folder structure for these, or (b) confirm if Gray is hand-picking from a stock pack.

2. **Numbered lesson body cards** — the "1. Don't take shortcuts…" body-text cards aren't yet a HyperFrames primitive. Worth building a `hyperframes-numbered-lesson-card` template that takes `{number, headline, body}` props.

3. **Numbered intro tiles** — the "1, 2, 3" reveal at the start. Not yet a HyperFrames primitive. Worth building.

4. **Two-phone photo collage on orange** — used 3 times (scenes 12, 41, 90). Trendify product showcase + lifestyle photos. Worth building.

5. **Phone-mockup with notification bubble** — scene 70 phone-screen overlay (different from part-cards). Need a closer look.

6. **Big number floating on a-roll** ("1", "4" callouts) — variant of the slot-machine counter. Could be a HyperFrames primitive that takes `{digits, anchor_pos, duration}` and emits chroma-green MP4.

---

## Recommended Next Builds

If we want to make the visual layer auto-buildable from a transcript:

1. **Build `hyperframes-numbered-lesson-card`** — props: `{number, headline, body, bg_color}`. Renders a full-screen orange (or any) card with big number + bold headline + body text. Used 3+ times per episode.

2. **Build `hyperframes-numbered-tiles-intro`** — props: `{count, labels[], style}`. The "1, 2" intro reveal. Used at intro + outro.

3. **Build `hyperframes-phone-mockup-collage`** — props: `{phones[{image, label}], bg_color}`. Two or three phone screenshots on a bg. Reusable for product showcase, lifestyle proof, before/after.

4. **Decision: orange illustrated scenes** — talk through with Gray whether to:
   - Build a Midjourney/Higgsfield prompt-template library
   - Maintain a stock-pack reference folder
   - Move toward HyperFrames-only and retire this style

5. **Pipeline sketch:** transcript → trigger-pattern detector (regex + Sonnet) → effect-spec JSON → HyperFrames batch renderer → Premiere XML with track placement. The mapping table above is the spec for the trigger-pattern detector.

---

## Files generated by this study

All in `python-scripts/.tmp/ep1-effects-study/`:

- `scene_times.txt` — 99 scene-cut timestamps from ffmpeg scene detect
- `frame_targets.json` — 93 frame extraction targets
- `frames/` — 93 JPG midpoints (~4.6MB)
- `transcript.json` — full Whisper large-v3 transcript with segments + word timestamps
- `words.json` — flat word-level list (1747 words)
- `frame_tags.json` — Haiku Vision tags per frame
- `timeline.json` — merged scene + tag + spoken-line records
- `timeline.txt` — human-readable timeline (used as the study's source-of-truth)

Total spend: ~$0.30 (Haiku Vision 93 calls @ ~$0.003), Whisper free on RTX 5070.
