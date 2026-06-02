# Founder Series SOP

**Production tier:** HIGH (cinematic, interview format)
**Cadence:** Ad-hoc, guest-dependent (NOT weekly)
**Owner:** Gray (full production), Sai (host + outreach)

---

## What this is

The Founder Series is interview-format long-form content where Sai sits with another founder. It's the **highest-performing IG long-form format** in Sai's catalog and is locked to continue for at least the next several months.

---

## Why ad-hoc

The constraint is guest scheduling. Most guests need ~4 weeks of lead time. Trying to force a weekly cadence either burns out the guest pipeline or drops production quality. Ad-hoc means "publish when a great guest is ready" — not "publish every Friday no matter what."

---

## Outreach (Sai)

- Sai sources guests from his network — founders he respects, peers in adjacent businesses
- Outreach goes 4+ weeks before target shoot date
- Once locked, Sai shares logistics with Gray (location, date, available time window)

---

## Pre-production (Gray)

When a guest is locked:
1. **Research the guest** — `python-scripts/founders-series/debrief.py` produces `debrief.md` + `interview-questions.md` on Drive. Sonnet 4.6 + web search. ~5-10 min runtime.
2. **Share debrief with Sai** at least 24h before shoot so he can read in and adjust questions
3. **Location scout / confirm** — Trendify office, guest's office, or third location
4. **Camera prep** — A-cam + B-cam locked to same fps + audio sample rate to prevent drift (see [[Sai long-form A-roll fps lock]] lesson)

---

## Production

- Two cameras minimum (A-cam on Sai, B-cam on guest, or wide + tight)
- Lav mics on both
- 45-90 min raw runtime typical; cut down to 15-30 min finished
- Plan for additional B-roll capture of the location (5-10 min before/after the sit-down)

---

## Post

- Transcribe via Whisper large-v3
- Long-form-A-roll AI cut: `multicam-mirror/longform_rerender.py` for dual-cam sync + AI take selection
- B-roll inserted at transcript-driven moments (location shots, hand gestures, context cuts)
- HyperFrames assets where appropriate (lower-thirds, callouts, key-quote text slides)
- Color grade, sound mix, music bed
- 3 thumbnail options

---

## Asset patterns that apply

Founder Series episodes can use any of the HyperFrames long-form patterns:
- Lower-third name + title introduction
- Key-quote text slides (Montserrat ExtraBold 80px white on chroma green keyed in Premiere)
- Counters when discussing numbers ($X revenue, Y clients, etc.)
- Transition stings between segments

See [[Sai long-form visual-layer placement rules]] for cadence.

---

## Publishing

- **Primary distribution:** Instagram (long-form Reels or IG Video)
- **Cross-post:** YouTube long-form channel
- **Promotion:** clip 3-5 sharp moments for daily UGC short-form (TikTok / IG Reels / YT Shorts) — these are exempt from the "no production" short-form rule because they're sourced from the cinematic interview, not phone-shot UGC. They still ship as strip-down edits (title + caption + cut to the punch).
- **LinkedIn:** Sai writes a custom post about a key business takeaway from the interview — NOT a "watch the new episode" repurpose

---

## Action item

- [ ] Edit the in-flight Founder Series long-form (raw footage available, no time-cost noted in the recap)
- [ ] Build a guest pipeline doc in this folder (`founder-series-pipeline.md`) once 3+ guests are queued

---

## Don't

- Don't force a weekly cadence — accept the ad-hoc nature
- Don't cut corners on production quality — this is the highest-performing format and earns the budget
- Don't skip the debrief / questions doc — the AI research saves hours
- Don't reuse the same lower-thirds template across episodes without iteration — each episode is a chance to refine
