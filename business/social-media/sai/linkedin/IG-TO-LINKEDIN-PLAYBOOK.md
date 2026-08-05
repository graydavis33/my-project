# IG → LinkedIn Repurposing Playbook (Sai)

Built 2026-07-29. How we turn Sai's posted Instagram reels into engaging LinkedIn content.
AUTHORIZED 2026-08-05: Content OS hard rule #2 reversed by Gray ("Repurpose your own content
to LinkedIn" — see content-os/README.md + decisions/log.md). Current mode: Lane 2 (text post +
still) is the primary lane; carousels (Lane 1) deferred. Production context: ~2-3 high-production
shorts/week per platform now, not daily volume — every shipped reel is a LinkedIn candidate.
Output is always a DRAFT PACKAGE Gray pastes manually — no auto-posting, no IG scraping.
Source material always comes from Gray (original export files, never re-downloads from IG —
Instagram compresses on upload and re-downloading strips quality again).

---

## What actually performs on LinkedIn right now (researched 2026-07)

- Document posts (PDF carousels) are the #1 format: ~6.6% average engagement,
  and carousel posts dramatically outperform plain text posts.
- Native video is #2 (~5.6%) and growing — LinkedIn has had three straight quarters
  of double-digit video upload growth. Talking-head with captions BEATS overproduced.
  60-90 seconds, single insight.
- Text posts still work when they carry a strong first line + whitespace, ideally
  paired with one authentic photo.
- The first 60 minutes decide reach. Sai (or Gray) replying to early comments
  within ~15 minutes measurably boosts distribution.
- The algorithm rewards person-not-brand voice. Everything ships in Sai's
  first-person voice per the locked rules in sai-linkedin/main.py.

## The core insight

One reel does not equal one LinkedIn post format. Each reel gets routed to the
format that fits its content shape. That routing decision is the whole system —
everything downstream is already built.

---

## The format router

For every posted reel, classify the content shape, then produce the matching package:

1. FRAMEWORK / LIST reel (numbered steps, "3 things", a system)
   → DOCUMENT CAROUSEL (PDF). One idea per slide, hook slide first,
   brand style from `business/sai-karra/editor-onboarding/03-brand-template-spec.md`.
   Plus a short text caption (hook + one-line setup). This is the highest-engagement
   format and Sai's framework reels map to it perfectly.
   Question CTA allowed here (framework-shaped = the one case Sai keeps it).

2. STORY / LESSON reel (one anecdote, one punchline — most talking-head shorts)
   → TEXT POST + STILL IMAGE. Caption in Sai's voice (the existing sai-linkedin
   engine), ends on the punchline, NO question CTA. Image = best frame from the
   reel or a matched library still (ffmpeg JPG, never the full mp4 copied around).

3. HIGH-PERFORMER or VISUAL reel (strong hook, visual effects, b-roll heavy)
   → NATIVE VIDEO. Upload the original 9:16 export (not an IG re-download),
   captions burned in (they already are), with a 1-2 line text hook above it.
   Native upload beats linking out — never link to the IG post.

4. RAW / BUILD-IN-PUBLIC moment (candid, in-progress, day-in-life)
   → TEXT POST, short (~500-800 chars), optionally with a candid photo.
   These humanize the feed between the heavier formats.

Default mix if unsure: alternate 2 → 1 → 2 → 3. Carousels are the growth engine,
stories are the volume, video roughly weekly.

## What every draft package contains

`<reel-name>/linkedin/` folder with:
- `format.txt` — which router lane and why (one paragraph)
- `caption.txt` — paste-ready post text (Sai voice rules enforced)
- `visual/` — the still JPG(s), or the carousel PDF, or a pointer to the video file
- `post-notes.txt` — best posting window + reminder: reply to comments in the
  first 15-60 min; that reply window is part of the format, not optional

## Pipeline (per reel, ~5 min each, Gray involvement ≈ zero until paste)

1. Gray drops posted reel exports in a folder (AirDrop / SSD / Drive)
2. Transcribe locally with mlx-whisper (free, on this Mac)
3. Run the sai-linkedin engine on the transcript → caption + theme + visual ideas
4. Route the format (above) and build the visual (frame extract / carousel PDF)
5. Gray reviews, pastes, posts. Any edit Sai makes gets logged to the
   feedback loop (`memory: feedback-sai-linkedin-voice`) so drafts keep improving.

## Standing rules carried over

- Sai is a "founder", never "CEO"; no AI-tell phrasing (full AVOID list lives in
  `python-scripts/sai-linkedin/main.py` SYSTEM_PROMPT_CORE — 25+ rules from
  Sai's actual edits)
- No em-dashes anywhere in captions
- Never put down other people/brands (no "most founders get this wrong")
- Not-the-expert voice: "here's what's worked for me", not prescriptive authority
- No IG scraping or automation of any kind; no auto-posting (manual paste;
  LinkedIn API posting is a maybe-later)

## v2 upgrades to build once v1 proves out (not now)

- Carousel PDF generator (HTML template → PDF, brand fonts/colors) — build after
  the first 2-3 manual carousels validate the slide format
- `format` + `carousel_slides` keys added to the sai-linkedin JSON output so the
  router runs inside the same API call
- Batch mode: point at a folder of reels, get all packages at once
