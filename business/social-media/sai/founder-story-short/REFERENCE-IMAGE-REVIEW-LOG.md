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

## ~~STANDING RULE (Gray, 2026-08-06 evening)~~ — SUPERSEDED 2026-08-07

> **This rule is dead. Kept for history only. See the BOARD LOCK below.**
>
> ~~The board in all generated frames is Gray's REAL whiteboard: a free-standing rolling
> whiteboard (white surface, black frame, black X-base stand on casters), standing in the
> MIDDLE of the room — never a wall-mounted board. Magnets are the pushpin-style ball
> magnets (colored plastic, pin-shaped). Gray supplied reference photos of both; keep them
> at ~/Documents/founder-story-refs/ (real apartment photos — NOT in the public repo).~~

Note: those reference photos live on a Mac path and are **not present on the Windows box**.
Moot now that the board changed, but the same trap applies to any future "keep them at
~/Documents/..." instruction — this repo is used from two machines.

---

## ⭐ BOARD LOCK (Gray, 2026-08-07) — applies to EVERY board shot

Gray bought the board. It reverses the previous rule on every axis:

| | Old rule (dead) | **LOCKED** |
|---|---|---|
| Surface | whiteboard, white | **cork, matte dark brown** |
| Mounting | free-standing on casters | **hung flat on the wall** |
| Position | middle of the room | **against a wall (WALL LOCKED 08-07 eve, see below)** |
| Orientation | landscape | **VERTICAL, 36 tall by 24 wide** |
| Fastener | pin-style ball magnets | **wooden push pins** |
| Frame | black | **wood** |

Also on order: 1 skein red yarn, 40 wooden push pins (board ships with 15 more),
Command 15 lb strips for hanging.

**Consequences that are not cosmetic:**

1. **Every board reference frame generated so far is invalid.** All of them show the
   whiteboard. Shots 2, 3, 7, 8, 9, 10, 12, 13, 14, 15 need regenerating.
2. **Lighting gets simpler.** Most board Light notes were written to fight whiteboard
   gloss ("45° off so the gloss doesn't flare", "feather so no hot spot"). Matte cork has
   no specular flare. But cork *absorbs* where white *bounced*, so expect about a stop more
   light, and the 4x6 prints now read as the brightest thing in frame instead of competing
   with a white surface. That is an improvement for the photo-board look.
3. **Shots 9 and 10 break geometrically.** Both are written as board-POV from BEHIND the
   board's dark edge facing Sai. That framing needs a free-standing board. Flat on a wall
   the camera would have to be inside the wall. Proposed fix (NOT yet approved): shoot from
   BESIDE the board, tight to the wall, board edge running down the foreground as a dark
   vertical frame with Sai past it. **Do not regenerate 9 or 10 until Gray confirms.**
4. **The wall choice locks all 10 board shots at once.** A rolling board could be rotated
   per shot; a hung board cannot. Whichever wall it goes on decides whether Gray's note
   "every bulletin board shot on the right side of Sai, facing the bathroom" survives.

Shot 2 status: young-Sai party photo APPROVED (composite v2). Frames A+B are now doubly
stale (wrong board AND wrong fastener) and get regenerated against the cork board.

---

## ⭐⭐ WALL LOCK (Gray, 2026-08-07 evening) — closes open item 4 above

**The board hangs on the wall beside the BATHROOM DOOR** — the segment between the black
floor lamp and the bathroom door frame, dog bed on the floor beneath it, closet return on the
far side. This is where the rolling whiteboard currently parks. Board hangs VERTICAL (36 tall
x 24 wide) on Command 15 lb strips.

Gray's reasons, both verified against his own room photos (supplied this session, saved to
`~/Documents/founder-story-refs/room/`, NOT in this public repo):

1. **Plenty of floor to work with.** The camera sits on the window side and shoots across the
   room's full depth. This is the LONGEST throw available in the apartment.
2. **Away from the window.** Most board shots put the window BEHIND camera, so daylight
   arrives as soft frontal fill on the cork and no window ever appears in frame to blow out.

**Correction to an earlier claim in this session:** the door wall was initially assessed as
short on camera pullback. That was measured across the room's narrow axis and is wrong.
Shooting from the window side, this wall has MORE pullback than the triptych wall, not less.
Gray's pick is the better one and the wides on 9, 10 and 12 are not constrained.

**Consequences now settled:**

- Gray's standing note "every bulletin board shot on the right side of Sai, facing the
  bathroom" SURVIVES — the board is literally beside the bathroom door.
- The triptych wall stays as-is. The three abstract panels do not come down.
- ~~Cork is now lit by cool window daylight arriving over the camera's shoulder, against a
  3200K key. Mixed temperature, needs a call on film day.~~ **RESOLVED same evening: Gray has
  BLACKOUT CURTAINS and will kill all daylight.** Every board shot is therefore 100% lamp-lit
  and fully controlled, exactly as the Light columns are already written. No gels, no
  mixed-temperature grade, and the board shots are no longer time-of-day dependent — which
  also means the film-day schedule's "board during the day, bedroom after dark" grouping is a
  convenience, not a constraint.

**Two physical checks before hanging (Gray, this weekend):**

- The outlet at the baseboard where the floor lamp is plugged in — make sure the board's
  bottom edge clears it and the lamp cord is not in frame.
- Whether the bathroom door swings into the room far enough to clip a 24-inch-wide board.

## SHOTS 9 + 10 — UNFROZEN (Gray, 2026-08-07 evening)

Gray rejected the shoot-from-beside proposal and gave a simpler fix that removes the geometry
problem instead of working around it:

> "expression shots will be to the side. window side of room, and camera will point at Sai's
> face. behind him, u will most likely see his desk and closet."

**What this means:** the expression/reaction coverage moves to its own setup. Camera sits on
the WINDOW side of the room pointing back at Sai's face; Sai's background is the DESK and
CLOSET. The board is off-camera behind the lens, so Sai's eyeline past the lens still reads as
"looking at the board" and the cut works.

**Consequences:**

1. **The dark board-edge foreground element is gone from 9 and 10.** Both rows are written
   around it. Their How to Film text needs an additive note, not a rewrite
   ([[feedback-scripts-add-never-delete]] / [[feedback-surgical-edits-only]]).
2. **These two stop being board shots.** They no longer depend on the board being built, so
   they can be filmed in any block on the schedule rather than only in the board window.
3. **Background continuity matters now.** Desk and closet appear behind him, so whatever is on
   that desk on film day is in the shot. Worth a dress pass. See the room plates at
   `~/Documents/founder-story-refs/room/` (IMG_9359, IMG_9363 show the desk/closet wall).
4. Reference frames for 9 and 10 can now be generated. Chain them off a real room plate so the
   desk and closet match the actual location.

---

## Session 2026-08-07 — rows 2 to 5 regenerated against the cork board

### ⭐ MODEL BEHAVIOUR (measured, not assumed) — the tool must encode all three

| Behaviour | Nano Banana 2 | Nano Banana Pro |
|---|---|---|
| `<<<element_id>>>` placeholder | **ignored outright** | registers |
| Image-reference chaining | holds registration | holds registration |

Three traps, and every one of them fails SILENTLY:

1. **The model strings are inverted from the docs.** `nano_banana_2` returns Nano Banana **2**.
   You must pass `nano_banana_pro` to get Pro. A whole batch ran a tier low with no error.
   The tool must pin the string AND assert the returned `model` matches what it asked for.
2. **Elements only register on Pro.** On Nano Banana 2 the placeholder is dropped and you get a
   generic face, with no warning. Shots 4 and 5 came back as two different strangers.
   The tool must never route a shot containing Sai to the cheap tier.
3. **Pro inherits the WARDROBE from the element reference, not just the face.** Shot 4 came back
   in the blue suit and orange tie because that is what Current Sai's reference photo wears.
   Any shot where Sai is not dressed like his reference needs an explicit clothing override.

Corollary: the cheap tier is still correct for pure plate variants with no person in them.

Elements live in the workspace (not committed): Current Sai `25938a11-…`, Young Sai `f44a14f8-…`,
and a better-documented **Young Sai 15** `f5945d72-…` built 08-07 with 3 refs.

### Row 2 — Macro: first photo pinned to the board
Status: **RESOLVED — v1a is the pick, pending attach**

Gray's call: **TRUE MACRO**, over the medium framing every prior frame used.

What the earlier frames missed: all of them, including the 08-06 corkboard test, were mediums of
the whole board sitting in a room. The row's How to Film always said "MACRO lens, board fills the
frame."

Why it matters beyond framing: **a macro makes shot 2 wall-independent.** It shows almost no room,
so it is the only board shot that does not wait on the open "which wall" question that locks the
geometry of the other nine at once. It can be approved while the rest stay frozen.

Action: chained off the 08-06 corkboard test so the approved young-Sai print, the cork and the warm
practical light all carried over, and prompted only the reframe plus the fastener and mounting
changes. Delivered `shot2-cork-MACRO-v1a-PENDING.png` (pick) and `-v1b-PENDING.png` (wider alt).
2 generations on Pro.

Open: the generated print carries a white border; a drugstore 4x6 is usually borderless.

### ⚠️ Row 2 hygiene — still live, nothing fixed this session
The live DB still holds the **rejected** frame references (`shot2-magnet-macro-ai.png`,
`shot2-pin-photo-ai.png`) among its 6 attachments. The v2 pair, the 08-06 corkboard test, and now
both macros all sit on disk **unattached**. The crew is currently reading frames the log threw out.

### Row 3 — Photo-as-screen, archival plays inside the print
Status: v2 GOOD, needs a blinds level from Gray

This is a **locked plate** off row 2 ("do NOT touch the board or the camera between shots 2 and 3"),
so it was chained rather than generated fresh. **The chain registered perfectly** — identical cork
grain, print position and size, wooden pin, camera angle and wood frame edge. Further proof the
chain-only-the-change technique is the load-bearing habit of this workflow.

- v1 (Nano Banana 2): ran the venetian blinds at roughly 90% against a row that calls for 20-35%,
  and rendered them cool blue-white against a warm 3200K scene. Rejected.
- v2 (Pro): glow now spills warm from the print onto the cork and falls off correctly.
  **Blinds are now arguably too subtle** — this is a dial-up from here, and needs Gray's level.

### Row 4 — Sai at the foot of the bed, doomscrolling
Status: ONE FIX NEEDED (wardrobe)

Board lock does not touch this row. Right: wall empty and two stops under with no hot spots (it has
to stay a clean surface for the composited success graphics), phone as the dominant cool 6500K key,
blue RGB window lamp raking the mattress camera-left, straight-on medium-wide from the foot of the bed.

Wrong: **he is in the blue suit and orange tie.** See model trap 3 — the Element brought its
reference wardrobe with it. Needs "plain dark tee, casual" stated explicitly.

### Row 5 — Bird's-eye, fallen back on the bed
Status: TWO FIXES NEEDED (exposure, framing)

- v1: had him **tucked under a duvet**, which reads as bedtime rather than collapse. The row's beat
  is that he falls backwards onto the bed straight out of shot 4. Rejected.
- v2: on top of the bedding, fully dressed, arms flung where they landed, phone screen-down beside
  him, true perpendicular top-down. Right on the beat. **About a stop underexposed**, and pulled
  wider than v1 so floor and nightstand are now in frame.

Next move for 4 and 5: get 4's wardrobe right, then **chain 5 off the approved 4** so face and
wardrobe match between two shots that cut directly together. Generating them independently is the
same mistake row 1 already documents.
