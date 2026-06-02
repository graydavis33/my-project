# Sai Shorts — Vid 4 (Systems Framework) Brand Spec

Brand identity for the C2498 "Build systems that are bulletproof" short. Matches the locked-in style from the 2026-05-27 tax-shorts batch (bank-vault-deposit, paycheck-30-percent, title-card-business-hack).

## Format
- 1080×1920 vertical
- Chroma green `#00FF00` background (NOT `#00B140` — this batch uses pure green for Premiere Ultra Key)
- 24fps (Sai's source rate)

## Colors
- **Trendify orange** `#F28129` — primary brand color, cards, accents
- **Orange light** `rgba(255, 168, 88, 1)` — top of card gradient
- **Orange mid** `rgba(242, 129, 41, 1)` — middle of card gradient (matches `#F28129`)
- **Orange dark** `rgba(214, 100, 22, 1)` — bottom of card gradient
- **Specular highlight** `rgba(255, 220, 180, 0.55)` — top radial on orange-glass
- **Inner shadow** `rgba(140, 55, 8, 0.45)` — bottom inset on orange-glass
- **White** `#FFFFFF` — text, strokes, icon fills
- **Chroma green** `#00FF00` — background only, NEVER on any visible element

## Orange-Glass Card Recipe (locked)
```css
background:
  radial-gradient(
    ellipse 100% 60% at 50% 0%,
    rgba(255, 220, 180, 0.55) 0%,
    rgba(255, 200, 150, 0.20) 35%,
    rgba(255, 180, 120, 0.0) 65%
  ),
  linear-gradient(
    180deg,
    rgba(255, 168, 88, 1) 0%,
    rgba(242, 129, 41, 1) 35%,
    rgba(214, 100, 22, 1) 100%
  );
border: 2px solid #FFFFFF;
border-radius: 32px;
box-shadow:
  inset 0 2px 0 rgba(255, 240, 215, 0.55),     /* top specular */
  inset 0 -4px 14px rgba(140, 55, 8, 0.45),    /* bottom depth */
  0 0 28px rgba(242, 129, 41, 0.55),           /* outer orange bloom */
  0 8px 24px rgba(0, 0, 0, 0.28);              /* base drop shadow */
```

## Typography
- **Title (top header):** Montserrat 800 (ExtraBold), 72-88px, uppercase, letter-spacing 0.03em, white, text-shadow `0 3px 10px rgba(0,0,0,0.35)`
- **Step label:** Montserrat 800, 32-40px, uppercase, letter-spacing 0.08em, white on orange-glass pill
- **Card label (icon caption):** Montserrat 600, 36-44px, letter-spacing 0.06em, white, text-shadow `0 2px 8px rgba(0,0,0,0.4)`
- **Body lines (clipboard / lists):** Montserrat 600, 32-42px, white

## Motion Defaults
- **Entrance pop:** `back.out(1.6-2.0)`, duration 0.45-0.75s, y-offset +140 or scale 0.7→1
- **Slide-in:** `power3.out`, duration 0.6-0.8s
- **Stroke draw:** `power2.out` on `strokeDashoffset`, duration 0.4-0.8s
- **Stagger between siblings:** 0.08-0.18s
- **First entrance offset:** 0.2-0.4s (never t=0)
- **Step transitions:** crossfade or focal-dot morph at 0.5-0.6s

## Layout Patterns
- **Top-third anchor:** `padding: 380px 80px 0 80px` on `.scene` (matches title-card composition)
- **Bottom-third anchor:** `padding: 0 80px 280px 80px` on `.scene` (matches bank-vault-deposit)
- **Centered:** `padding: 0 80px` + `justify-content: center`
- Headers sit top of the 1080×1920 frame at ~y=240-400
- Hero element (card/icon group) sits in the central band at y=600-1300
- Caption/subtitle if any sits at y=1500-1700

## Stickfigure SVG (locked from talking-stickfigures pattern)
- Head: `<circle cx=70 cy=42 r=28 fill="white" />`
- Body taper: `<path d="M 42 70 Q 70 90 98 70 L 110 180 Q 70 195 30 180 Z" fill="white" />`
- Total: ~140×180 viewBox
- Solid white silhouette, no eyes/mouth unless talking

## Icon Style
- White stroke 4-6px, `stroke-linecap: round`, `stroke-linejoin: round`
- Filled where needed (white fill on key shapes)
- ViewBox sized so the icon nests inside a 80-120px container

## What NOT to Do
- No `#333`, `#3b82f6`, `Roboto`, or any default Tailwind colors
- No gradients on flat dark backgrounds (H.264 bands — use radial or solid + bloom)
- No exit animations except on the final asset (final closer can fade)
- No green on any visible element — chroma keys it out
- No SF Pro / system fonts — Montserrat or Inter only
- No infinite repeats — calculate finite cycle count from composition duration
- No mid-word text breaks via `<br>` — let `max-width` wrap naturally

## Captions (when burning over A-roll)

For the AI captions step downstream of trim+graphics:

- **Font:** Montserrat SemiBold (weight 600)
- **Size:** 64px (single line; 2 lines OK at BOT only)
- **Color:** white `#FFFFFF`
- **Drop shadow:** `0 4px 12px rgba(0,0,0,0.6), 0 2px 4px rgba(0,0,0,0.45)`
- **Letter-spacing:** 0.005em
- **Line-height:** 1.18
- **Max-width:** 960px BOT, 920px TOP
- **No stroke**

### Caption text rules (locked)
- All lowercase by default
- Capitalize: `I'm`, `I've`, `I'll`, `I'd`, names (`Sai`, `Trendify`, `Coach Waddell`), cities (`Manhattan`, `NYC`)
- Standalone `i` stays lowercase
- NO punctuation (`.`, `,`, `;`, `:`, `?`, `!` all stripped)
- Apostrophes OK for contractions (`we're`, `i've`, `don't`)

### Caption position rules
| Graphic position | Caption | y coord |
|---|---|---|
| None | BOT | `top: 1340px` |
| At top | BOT | `top: 1340px` |
| At lower/center-lower | TOP | `top: 200px` |
| At lower-left + lower-right | TOP | `top: 200px` |
| IS the spoken word | REMOVE caption | — |

Caption fade: 80ms in / 80ms out. No entrance beyond fade.

Full SOP: `business/sai-karra/content-os/sai-shorts-editing-sop.md`

---

## This Batch's 5 Assets
1. **01-audit-everything** — Step 1: grid of daily task cards + magnifying glass sweep
2. **02-document-everything** — Step 2: orange-glass clipboard with text lines drawing in
3. **03-hire-walk-through** — Step 3: two stickfigures + document handoff
4. **04-shadow-you** — Step 4: stickfigure with translucent trainee shadow behind
5. **05-repeat-framework** — Closer: circular loop arrow + multiplier counter

Each is 4-5s, standalone composition, renders to MP4 1080×1920 24fps on chroma green for Ultra Key compositing.
