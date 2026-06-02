# HyperFrames Composition Project

## Skills — USE THESE FIRST

**Always invoke the relevant skill before writing or modifying compositions.**

| Skill                | Command         | When to use                                                                                       |
| -------------------- | --------------- | ------------------------------------------------------------------------------------------------- |
| **hyperframes**      | `/hyperframes`  | Creating or editing HTML compositions, captions, TTS, audio-reactive animation, marker highlights |
| **hyperframes-cli**  | `/hyperframes-cli` | Dev-loop CLI: init, lint, inspect, preview, render, doctor                                     |
| **gsap**             | `/gsap`         | GSAP animations for HyperFrames — tweens, timelines, easing, performance                          |

## Commands

```bash
npm run dev          # preview in browser (studio editor)
npm run check        # lint + validate + inspect
npm run render       # render to MP4
```

## Project

5-scene flowing infographic for Sai's "agency model shift" transcription. White on chroma green `#00B140`, single composition (1920×1080, ~22s), crossfade transitions for seamless flow.

Scenes:
1. The agency model (context)
2. Done-for-you (agency → client)
3. Genius idea (lightbulb beat)
4. Teach founders (one-to-many knowledge flow)
5. Done-with-you (bidirectional collaboration — punchline)

See `DESIGN.md` for visual identity rules.

## Key Rules

1. Every timed element needs `data-start`, `data-duration`, `data-track-index`
2. Timed elements **MUST** have `class="clip"`
3. Timelines paused, registered on `window.__timelines`
4. Only deterministic logic — no `Date.now()`, no `Math.random()`
5. Entrance animations only per scene (transitions handle exits)
