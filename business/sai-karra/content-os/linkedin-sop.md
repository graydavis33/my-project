# LinkedIn SOP

**Status:** Awaiting Sai's content-direction brain dump (action item from 5/10 recap, due in a few days). This SOP is the scaffolding; the strategy section gets filled in when Sai sends his direction.

**Production tier:** MEDIUM
**Cadence:** Daily target
**Owner:** Sai writes direction → Gray drafts/refines via `python-scripts/sai-linkedin/` → Sai approves before posting

---

## The hard rule

**NO repurposing of Instagram content to LinkedIn.** This was explicit in the 5/10 recap. LinkedIn is business-focused, written for LinkedIn's audience and rhythm, and serves a different funnel than IG.

Quote from the recap: *"LinkedIn should be very, very business-focused, like very business-focused about what we do and trying to find how we're different. And I think that's something that we can definitely do a better job of versus kind of just repurposing what we talk about on Instagram."*

---

## Audience + intent

- LinkedIn audience is **operators, founders, agency owners, prospective Trendify clients**
- LinkedIn intent is **Trendify positioning + Sai-as-founder credibility + talent attraction**
- Not lifestyle. Not relatability. Business.

---

## Format

- Plain text posts (no LinkedIn carousels for now)
- 150-400 words target
- One sharp idea per post
- A first-line hook that rewards the "see more" click
- Sai-voice — see `python-scripts/sai-linkedin/main.py` SYSTEM_PROMPT_CORE for the 12+ voice rules (avoid em-dashes, fabricated 2-3-beat parallels, AI-essay headers, poetic verbs, etc.)

---

## Workflow

1. **Trigger:** A Sai short publishes OR Sai sends a story/idea via voice memo or chat
2. **Transcribe (if from video):** Whisper large-v3 on RTX 5070 (free) → `master.srt`
3. **Draft:** `python-scripts/sai-linkedin/main.py` produces caption + theme + key points + 5 visual ideas
4. **Visual:** `find_visuals.py` auto-pulls top photo candidates from the footage library
5. **Manual revision:** Gray cleans against the voice rules (em-dashes, fabricated parallels, etc.)
6. **Sai review:** before publish
7. **Post:** schedule or manual publish
8. **Capture:** Sai's revisions get appended to `reference/voice/sai-linkedin-posts-final.md` so the cached corpus stays current

---

## What this looks like in practice (examples to come)

| Sai short topic | LinkedIn angle |
|---|---|
| Lost 10K on a client churn | "What I learned about retention pricing from a client we lost last month" — operator angle |
| Hired a senior creative lead | "Why we hired before revenue justified it — the case for hiring on bet" |
| 450 ads/month for one client | "How one client became half our business — the compound interest of agency relationships" |
| Coaching program shutdown | "Why we shut down our coaching program — and what 'focus' actually means" |

**Pattern:** lift the business insight, drop the personal-brand framing, sharpen the operator language.

---

## Awaiting from Sai

- [ ] LinkedIn content direction brain dump
- [ ] Topics he specifically wants to own on LinkedIn
- [ ] Tone latitude — how punchy / contrarian / restrained
- [ ] Whether Trendify the company or Sai the person is the byline

---

## Tracking

- Impressions, engagement rate
- **Profile views per post** — the conversion metric for LinkedIn
- Inbound DMs from prospects (talent or clients) — the actual business outcome
- Weekly pull into the social-media-analytics sheet

---

## Don't

- Don't auto-cross-post IG/TikTok content to LinkedIn — different platform, different post
- Don't write in Instagram-voice. LinkedIn is sharper, more operator-tone
- Don't add emojis (Sai's voice rules) or em-dashes (his voice rules)
- Don't ship a draft past Sai without running the voice-rule pass
