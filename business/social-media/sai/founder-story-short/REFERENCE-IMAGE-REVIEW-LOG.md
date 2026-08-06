# Reference Image Review — shot by shot

Gray's pass through all 15 rows of the Founder Story Short shot list, making each Frame Visual
exactly what he wants. Started 2026-08-06.

Purpose is two things at once: get the images right, and learn what "right" means well enough
to script the process later. Every row records the call and the reason, because the reason is
the part a script can be built from. This log is the input to the `/council` review that gates
building the permanent batch tool.

---

## Standing observation (row 1, before any edits)

The Frame Visual column is currently doing **two different jobs at once**, and they are worth
separating:

- **Frame references** — an image of what the finished shot should LOOK like (framing, light,
  mood). This is what the crew and the editor read.
- **Generator inputs** — real photos of Sai fed INTO an AI generation to produce the shot.
  Nobody films from these; they are raw material.

Row 1 has 2 of the first kind and 6 of the second, mixed in one cell with no marking. If that
distinction holds up across the other rows, it is probably the single biggest structural fix
available, and it is the kind of thing a script can enforce.

---

## THE BIG TECHNIQUE (learned on row 2, applies everywhere)

**Never generate a matched pair of frames independently. Chain the second one off the first.**

Shot 2 needs a first frame (bare board) and a last frame (photo placed). Generating both from
scratch produced two different boards, different walls, different framing — useless as a pair,
and the exact same failure already sitting on row 1 (young Sai vs current Sai don't register).

What works: generate ONE frame until it's right, then produce the variant by passing the
approved frame as `--image` and prompting only the *change*:

> "Remove the photograph and the magnet so the board is bare. Keep absolutely everything else
> identical: same board, same frame, same wall texture, same warm lamp light and reflections,
> same camera angle, same framing, same depth of field, same background."

Result registered perfectly on the first try. This is the same principle as the motion-prompt
rule in the video SOP — **describe only what changes, never re-describe the scene** — and it is
probably the single most important habit for this whole workflow.

**Corollary for row 1:** its two selves should be regenerated the same way. Generate current
Sai in the void, approve it, then chain young Sai off it with "same void, same beam, same
framing, same head position, only the person changes." That fixes colour temp, registration
and void quality in one move instead of three.

## Model notes (measured 2026-08-06)

| Model | Credits | Use |
|---|---|---|
| Nano Banana 2 | 1.5 | cheapest drafts |
| **Nano Banana Pro** | **2** | default; handles image-reference chaining well |
| Seedream 5.0 Pro | 3 | |
| GPT Image 2 | 7 | text-heavy work, rarely needed here |

Stills are cheap enough to iterate freely. Iterate rather than settle.

**Prompt calibration:** "the board FILLS the entire frame" overshoots badly — Nano Banana Pro
returned a featureless white rectangle with no board edges and no context. "Board fills most of
the frame" with a named slight angle behaves. Ask for macro by describing what stays *visible*
at the edges, not by demanding the subject fill everything.

## Row-by-row

### Row 1 — AI "next opponent is you" showdown
Status: IN REVIEW

Currently attached (8):

| # | File | Kind |
|---|---|---|
| 1 | shot1-current-medium-ai.png | frame reference |
| 2 | shot1-young-medium-ai.png | frame reference |
| 3 | shot1-REF-current-bluesuit-front-4K.jpg | generator input |
| 4 | shot1-REF-current-bluesuit-medium-4K.jpg | generator input |
| 5 | shot1-REF-current-bluesuit-street.jpg | generator input |
| 6 | shot1-REF-young-sai-age16-BEST.png | generator input |
| 7 | shot1-REF-young-sai-age16-alt.png | generator input |
| 8 | shot1-REF-young-sai-2022-dorm.jpg | generator input |

**Claude's findings on the two frame references (they do not match each other):**

The row's Light column says: cool white ~5600K, black void, *"keep identical in both selves'
generations so the flicker matches."* The two frames currently break that four ways.

1. **Colour temperature is opposite.** Young = warm yellow beam. Current = cool teal beam.
   A flicker between them reads as the LIGHT changing, not the person changing. Directly
   contradicts the Light note.
2. **Registration is off** — the most damaging one. The heads sit at different heights and
   sizes in frame. A flicker only works if the two heads land in the same place; otherwise
   it reads as a jump cut. The How to Edit note already anticipates this ("parent BOTH selves
   to one Null... moving them separately is what makes a flicker look pasted") but the source
   frames themselves are misregistered.
3. **Wardrobe contrast is inverted.** Young = light grey tee that catches the light. Current
   = dark tee that sinks into the void. On each flicker the torso pops bright-to-dark, pulling
   the eye to the shirt instead of the face.
4. **Void quality differs.** Current is a true black void. Young shows a lit floor/haze where
   the beam lands, which weakens the mind-void look.

Gray's call:

What he wanted that the image missed:

Why:

Action taken:

---

### Row 2 — Macro: magnet places first photo on the board
Status: v2 PAIR GENERATED, awaiting Gray's call on framing

**Gray's brief (2026-08-06, verbatim intent):**
- Magnets on a WHITEBOARD (settles the board question for this shot)
- This is the FIRST photo on the board, nothing else on it
- FIRST frame: empty board, no hands
- LAST frame: hands appear, place the photo with a magnet, hands leave frame
- Camera on the RIGHT side of the person, not the left as in the old reference

**What was wrong with the original reference (shot2-magnet-macro-ai.png):**
board was packed with photos when How to Film says it must be nearly empty; the pinned image
was a stock woman's portrait, not young Sai's party/money shot; no visible magnet mechanic;
camera on the wrong side.

**Delivered:**
- `shot2-v2-frameA-board-empty.png` — first frame, bare board
- `shot2-v2-frameB-photo-placed.png` — last frame, one photo held by one magnet, no hands
- Registered pair (A derived from B by chaining), so they cut together.
- Cost: 4 generations, ~8 credits including the two discarded attempts.

**Still open:** the pair reads as a medium of the board rather than a true MACRO, and the
camera-side question needs Gray's eye on it with the person implied. Hands entering and
leaving is a motion beat — it belongs in the reference VIDEO built from this pair as
start_image/end_image, not in the stills.


---

## STANDING RULE (Gray, 2026-08-06 evening) — applies to EVERY whiteboard shot

The board in all generated frames is Gray's REAL whiteboard: a free-standing rolling
whiteboard (white surface, black frame, black X-base stand on casters), standing in the
MIDDLE of the room — never a wall-mounted board. Magnets are the pushpin-style ball
magnets (colored plastic, pin-shaped). Gray supplied reference photos of both; keep them
at ~/Documents/founder-story-refs/ (real apartment photos — NOT in the public repo).

Shot 2 status: young-Sai party photo APPROVED (composite v2). Frames A+B must be
regenerated on the real standing board per this rule.
