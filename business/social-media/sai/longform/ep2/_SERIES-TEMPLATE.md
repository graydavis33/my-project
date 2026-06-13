# Sai BTS Doc — SERIES TEMPLATE (repeatable format)

The reusable skeleton for EVERY episode. Built from Gray's structure interview (2026-06-13).
Copy this into each new episode folder and fill it in. Don't reinvent the format each week —
swap the specifics, keep the skeleton.

---

## The format in one line

A weekly, cinematic "Netflix-doc" of Sai building Trendify. Each episode is built around ONE
**theme of the week** (a lesson that emerged from the real week), narrated by a **scripted
sit-down interview** filmed after the week, with raw footage cut in around the interview.

---

## The 5 locked decisions (don't re-litigate these)

| Decision | Locked choice |
|---|---|
| **Backbone** | Theme of the week — one throughline per episode; the days are evidence for it |
| **Narration spine** | Post-week sit-down interview — **the interview is the DRIVER** (see below) |
| **Cold open** | Epic ~30-second dramatic recap of the whole week (trailer-style), then title |
| **Body feel** | Cinematic / Netflix-doc — great story + raw beautiful shots, NO flashy/flashing cuts |
| **Length** | 8–12 minutes |
| **Closer** | A quotable Sai line + a next-week cliffhanger |
| **Continuity** | Season-long thread — callback to last week, tease next week, one big question across the season |
| **Music** | Licensed cinematic score (swells under story, dips under talking) |
| **Title** | Theme only (e.g. "Systems Over Stress") — no episode number, no date |

---

## ⭐ The core workflow: the interview drives everything

This is the most important part of the format. Order of operations every week:

1. **Watch/transcribe the week's raw footage** (the `_transcribe.py` pipeline in each ep folder).
2. **Find the theme** — the one lesson the week keeps pointing at.
3. **Write the interview script** — questions built to pull the narration spine out of Sai,
   grouped into the standard blocks below. The interview is scripted, not freeform.
4. **Film the sit-down interview** — controlled light/audio, same look every episode, looser
   "talking to a friend" delivery. This audio is the backbone of the edit.
5. **Build the raw footage around the interview answers** — every clip earns its place by
   illustrating something Sai says in the interview. If it doesn't support an answer, it's a
   B-roll texture moment or it's cut.

---

## The repeatable episode skeleton

```
0:00  COLD OPEN      ~30s epic recap of the week (captioned, scored, fast but not flashy)
0:30  TITLE CARD     theme-only title sequence
              ↓
      WEEK-AHEAD     Sai states the week's plan/intention (fixture)
              ↓
      THE THEME      interview names the lesson the week is about
              ↓
      ACT 1–3        the week's scenes/days that PROVE the theme,
                     interview audio as spine + raw footage cut under it
              ↓
      MIND-DUMP      one honest, raw vulnerability beat (fixture)
              ↓
      THE WHY        the deeper personal payoff behind the theme
              ↓
      FRIDAY WRAP    recap of the week (fixture)
              ↓
      CLOSER         quotable line + next-week cliffhanger + season thread
```

## Fixtures — must appear in every episode

- [ ] **Week-ahead intro** — Sai says the plan at the start
- [ ] **Friday wrap** — recap at the end
- [ ] **One honest mind-dump** — a raw reflection/vulnerability beat (the emotional anchor)
- [ ] **Lesson of the week** — the takeaway, stated clearly (delivered in the story, kept light on graphics)
- [ ] **Season-long thread** — one callback to last week + one tease toward next week

## The standard interview question blocks (reuse every week, swap specifics)

- **Block A — The intention:** What was the plan this week, and why did it matter?
- **Block B — The low point:** Where did it get hard / stressful / uncertain? (the honest beat)
- **Block C — The turn:** What shifted — the realization or decision that became the theme?
- **Block D — The machine:** What did you actually build/do? (the unglamorous work)
- **Block E — The why:** Why does this connect to something deeper/personal for you?
- **Block F — The cliffhanger:** What's still unsolved heading into next week? (season thread)
- **Block G — Connective lines:** Short reset/rehook lines to film explicitly for the edit.

---

## Look & sound rules (the style)

- **On-screen text = minimal.** Let the footage breathe. Cinematic, not a vlog.
- **Captions only where needed:** (a) when Sai is genuinely hard to hear, (b) during the intro
  hype recap, (c) the title-card sequence. NOT burned in throughout.
- **Date / day lower-thirds** as the week progresses (reuse the `date-lowerthird` setup).
- **No flashing / no fast-cut energy.** Restrained, premium pacing. Raw cinematic shots.
- **Licensed cinematic score** under the story; dips under interview answers, returns under montage.

## Standing privacy rules (carry from Ep 1, check every episode)

- **Never name clients on camera** — blur/mute or cut. Refer to them generically.
- Watch for brand names Sai asks to cut mid-clip (Ep 1: a delivery brand).
- Confirm anything personal/sensitive before it goes in.

## Edit order (recommended, every episode)

1. Lock the cold-open recap concept first (it frames everything).
2. Write + film + transcribe the interview (the spine — can't assemble without it).
3. Lay the interview audio as the backbone, in theme order.
4. Cut raw footage under/around each answer (every clip earns its place or it's cut).
5. Build cold open + title + act transitions + closer.
6. Music, sound design, color last.
7. Pull 2–4 vertical shorts from the strongest moments for cross-posting.
