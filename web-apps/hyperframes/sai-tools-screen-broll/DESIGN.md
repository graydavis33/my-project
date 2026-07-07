# DESIGN — Sai "3 Tools" Screen-Recording B-Roll

**Purpose:** Horizontal (1920×1080) screen-recording-style B-roll to cut under Sai's
"Here's three tools my business can't run without" short. Three standalone clips —
Notion, Slack, Scribe — each ~6–8s showing the software *actually being used*, matched
to what Sai says. Gray drops them in and matches timing himself.

## The one rule that governs everything

**These must read as a genuine 2D screen recording of a computer — NOT a branded
motion graphic.** No orange-glass Sai style here. No floating cards, no dramatic camera
moves, no infographic flourishes. Faithfully recreate each real app's UI with its real
brand colors and layout, then drive it with a realistic mouse cursor. The realism IS the
asset. If it looks "designed," it's wrong.

## Shared: the cursor

A macOS-style pointer sells the "someone is using this" read.

- Black arrow, white 1.5px outline, ~26px tall, `z-index: 9999`, `position: absolute`.
- Moves via GSAP `x`/`y` with `power2.inOut` (real hands ease in and out, never linear).
- Click = quick `scale` dip to 0.86 and back over ~0.12s, optionally a faint expanding
  ring at the click point. Every meaningful UI change is preceded by a click.
- Never teleports. Always travels to a target, clicks, THEN the UI reacts (~0.1s after).

## App: Notion

- **Canvas:** full-bleed app (no browser chrome).
- **Colors:** main bg `#ffffff`; ink `#37352f`; sidebar bg `#f7f6f3`; sidebar text
  `#5f5e5b`; hover/selected `#eceae7`; blue accent `#2383e2`; borders `#e9e9e7`;
  muted `#9b9a97`.
- **Font:** Inter (Notion's stack is system-sans; Inter reads correct).
- **Icons:** simple monochrome line icons in muted gray (document / calendar / people) —
  NOT emoji (emoji render unreliably in the capture engine).
- **Beat:** open on a training-doc/SOP page → cursor clicks "Content Calendar" in the
  sidebar → main swaps to a table of content pieces with status pills + creator
  assignees → cursor opens an assignee cell and picks a creator. Hits "training docs +
  team visibility + creators get assigned content."

## App: Slack

- **Canvas:** full-bleed app.
- **Colors:** sidebar aubergine `#3F0E40`; selected-channel blue `#1164A3`; sidebar text
  `#CFC3CF` (idle) / `#ffffff` (active); main bg `#ffffff`; message ink `#1D1C1D`;
  timestamp `#616061`; green presence `#2BAC76`; hover `#350D36`.
- **Font:** Lato if it embeds, else Inter.
- **Icons:** `#` channel prefix (text), green presence dots, avatar = colored rounded
  square with white initials.
- **Beat:** open on `# content-team` with a few messages → cursor clicks `# editing` in
  the sidebar → header + messages swap → a new message lands (subtle slide/fade in) after
  a brief typing indicator. Hits "all comms live here, dozens of function channels."

## App: Scribe (the hero — Sai calls it a "game changer")

- **Canvas:** a browser window (Scribe is browser-based) → generated guide doc.
- **Colors:** Scribe indigo/purple `#5D3FD3` primary, deeper `#4B31DD`, tint `#EEEAFB`;
  neutral doc bg `#ffffff`, ink `#1A1A2E`, muted `#6B6B80`, borders `#E6E4F0`; capture
  highlight = purple 2px box with soft glow; recording dot `#E53935`.
- **Font:** Inter.
- **Beat (two phases):**
  1. Browser shows a SaaS settings page. A "● Recording · Scribe" pill sits bottom-center
     with a step counter. Cursor clicks 3 elements (Settings → Team → Add member); each
     click flashes a capture highlight box and ticks the counter 1→2→3.
  2. Smooth transition (Scribe "generating") → the auto-built guide: title "How to Add a
     Team Member," Scribe logo, then numbered step cards appearing one-by-one (purple
     number badge + step text + a mini screenshot thumbnail with a highlight box). Hits
     "click through your screen and it stores it as an SOP."

## What NOT to do

- No emoji anywhere (unreliable render).
- No orange/Sai-brand styling — each app keeps its OWN real colors.
- No `Math.random()` / `Date.now()` — seed any pseudo-random.
- No dramatic zooms or floating 3D cards — this is a screen recording, keep the "camera"
  locked like a real capture.
- No captions/audio — these are silent B-roll; Gray matches to Sai's VO himself.
