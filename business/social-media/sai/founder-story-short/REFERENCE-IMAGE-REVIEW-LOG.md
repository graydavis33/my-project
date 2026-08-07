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

---

## Session 2026-08-07 (evening, Mac) — shots 2, 3, 4 regenerated under the new rules

Three chained generations on `nano_banana_pro`, 6 credits total, **842.29 left**. Every one
prompted ONLY the change. Registration held on all three. All saved `-PENDING`, nothing
overwritten, nothing attached to Notion.

**Mac tooling constraint discovered:** the Mac `higgsfield` CLI (v1.1.20) has **no `element`
command** — only `soul-id`. The Elements built on Windows (`Current Sai` 25938a11 etc.) cannot be
created, listed or managed from the Mac CLI. This does not block chained shots, because chaining
carries the face from the source image and needs no element at all. It only blocks **shot 1**,
which needs both Sais in one frame. **Shot 1 stays a Windows job.**

Corollary: the Current Sai identity model was NOT rebuilt on the new photos this session. It would
cost 50 credits and improve zero chained shots. The 15 fresh neutral-light refs sit on disk at
`~/Documents/soul-training/current-sai-v2/` for a Windows rebuild when shot 1 comes up.

### ❌ Venetian blinds are DEAD (Gray, 2026-08-07 evening)

> "ignore the venetian blinds, that an effect i will add in after effects, it was thought off to
> make the videos look more like a video screen. but since its inside a picture, prob not the best
> way to go."

Two reasons this matters beyond shot 3: the effect was **always an After Effects job, never
something a reference frame should show**, and the idea it was serving (make the archival footage
read as a video screen) is defeated by that footage living inside a printed photo. **Do not put
blinds, scan lines or bars in any frame.** The "blinds 20-35%" spec in shot 3's row is superseded —
flag it there, do not delete it.

### Row 2 — RESOLVED, borderless
`shot2-cork-MACRO-v2-borderless-PENDING.png` — chained off v1a, prompted only the removal of the
print's white paper border. Now edge to edge like a real drugstore 4x6. Cork grain, wooden pin,
paper curl, macro framing, warm falloff and the wood frame edge all carried through unchanged.
**Minor open note:** the print now reads slightly GLOSSY (visible specular sheen). Props calls for
matte and the Light column flags glare. Cosmetic on a reference frame, but if the real prints come
back glossy it is a live problem on the day.

### Row 3 — glow good, one honest flaw
`shot3-cork-glow-v3-noblinds-PENDING.png` — chained off the approved shot 2, per the row's
locked-plate rule (do NOT touch the board or camera between 2 and 3). Warm light now spills from
the print onto the cork and falls off within a few inches. No blinds. Registration perfect.

**The flaw:** the glow reads as a halo coming from BEHIND the print, like it is backlit, rather
than the print's own face emitting light. The print surface itself is no brighter than it was in
shot 2. For "archival video playing inside the print" the paper itself should be luminous. Fixable
in one more chained pass that raises only the print's internal brightness.

### Row 4 — RESOLVED, wardrobe fixed
`shot4-bed-scroll-v3-tee-PENDING.png` — chained off v2, prompted only the clothing. Plain dark
charcoal tee and dark sweatpants; suit, dress shirt and orange tie gone. **The whole light design
survived the chain**, which was the point of fixing it this way instead of regenerating: cool
phone-screen key on the face, blue lamp raking from the window side, empty wall behind him two
stops down, straight-on medium-wide from the foot of the bed.

Confirms the split diagnosed earlier: v1 had the right wardrobe and wrong light, v2 had the right
light and wrong wardrobe. **General rule: chain off the version holding the property that is
harder to rebuild (the lighting) and prompt away the easy one (the clothes).**

**Still true of 4 and 5: the room is not Gray's room.** Generic grey bedding and a plain dark
headboard, against a real bedroom with navy sheets, a cream fluted boucle headboard, and round book
shelves plus hexagon shelves on the wall above the bed. Now fixable — 9 room plates are on disk at
`~/Documents/founder-story-refs/room/`. Not done this session; it is a separate change and the
one-at-a-time rule applies.

**Next:** Gray's verdict on these three, then chain shot 5 off the approved shot 4.

---

## Session 2026-08-07 (evening, Mac, round 2) — Gray's revisions applied to 2, 3, 4

Gray reviewed round 1 live and rebriefed all three rows. Five more chained generations on
`nano_banana_pro`, 10 credits, **832.29 left**. All `-PENDING`, nothing attached.

### Row 2 — REBRIEFED and rebuilt: `shot2-cork-v3-oppside-centered-PENDING.png`
Gray's four notes, all applied in one chained pass off the borderless macro:
1. **Camera on the opposite side** — angle mirrored.
2. **Photo at the exact center of the board.**
3. **Board on the white wall** — full board now visible, hung flat.
4. **Dimensions double-checked:** board 24w x 36h vertical with wood frame, print 4x6 vertical —
   the print is exactly **one sixth of the board's width**, and the frame now shows that true
   scale (earlier macros made the print read far too big).
Lighting checked against the real rig: blackout curtains = no daylight anywhere; warm 3200K
lamp-only with soft frame shadow on the wall. **Note: this supersedes the TRUE MACRO framing from
round 1** — the row now reads as a full-board composition on the wall.

### Row 3 — REBRIEFED: it is a head-on PULLBACK SERIES, and the money photo is NOT in it
Gray: camera head-on, close-up to medium, moving BACKWARDS; the young-Sai club photo is not this
shot — the print is where OTHER videos of Sai play, inside the real photo's border. Three frames
delivered, each chained off the previous so the pin, cork, paper curl and light never drift:

| Frame | File | Camera | Video inside the print |
|---|---|---|---|
| A | `shot3-pullback-A-closeup-dorm-PENDING.png` | close-up | young Sai talking in his dorm |
| B | `shot3-pullback-B-mid-laptop-PENDING.png` | one step back | Sai working at a laptop at night |
| C | `shot3-pullback-C-medium-team-PENDING.png` | full board | Sai with his team in an office |

**Happy accident kept:** the horizontal videos LETTERBOX inside the vertical 4x6 with black bars
top and bottom — exactly what real horizontal archival will do when comped into the print in AE.
Reads as intentional; left in unless Gray objects.
The round-1 glow flaw (backlit halo) is moot — in this series the print's own face is the screen.

### Row 4 — REBRIEFED and rebuilt: `shot4-bed-scroll-v4-realroom-PENDING.png`
Gray's three notes: book shelves over the bed, bed further from the window, videos displayed on
the wall behind his head like the shotlist reference (the projected-feed frame, previously saved
as `shot5-bed-graphics-ai.png` under old numbering). Built by chaining the approved v3-tee frame
(face, wardrobe, phone-key light) **plus room plate `IMG_9360.JPG` as a second image reference** —
first use of a REAL room photo as a generation reference, and it landed: navy bedding, cream
fluted boucle headboard, round black-metal book shelves camera-left, wood hexagon shelves
camera-right, window pushed to the far left edge with the blue lamp spill, and 4 glowing
social-feed projections (people / party / money clips) on the wall behind his head. Phone stays
the key on his face.

**Technique note for the future tool:** two-reference chaining (approved frame for person+light,
real room plate for the set) is now proven. This is how 5 and 6 should get their room match.

**Next:** Gray's verdicts on v3 (shot 2), the A/B/C series (shot 3), v4 (shot 4). Then shot 5
chains off the approved shot 4 with the same two-reference method.

---

## Session 2026-08-07 (evening, Mac, round 3) — Gray's round-2 verdicts applied

**✅ SHOT 4 v4 APPROVED — Gray: "shot 4 is perfect."** First locked frame of the new process.
Shot 5 chains off it next.

### The dimensions question (Gray asked; answered with math)
Gray asked whether the board/photo scale in the frames is accurate, and if so whether he needs
smaller photos or a bigger board. Answer: **yes, accurate** — 4x6 on 24x36 = exactly 1/6 of board
width; his 8-12 prints cover only ~20-33% of the cork. Recommendation given: **do NOT buy a bigger
board** (photos read even smaller); if anything print **5x7** (~30% bigger, still drugstore
standard); or keep 4x6 and let the wide/macro shot alternation do the work, which the shot list
already does. Awaiting his pick — **this decides the print order size, so it must resolve before
the drugstore run (~Sat 08-09).**

### Row 2 — now a 3-STILL SEQUENCE at 45° on the other side
Gray: angle 45° on the other side of the photo; add 2 stills of Sai placing then pinning the
photo; everything else good.
1. `shot2-cork-v4-still1-placing-PENDING.png` — both hands press the print to the cork, NO pin yet
2. `shot2-cork-v4-still2-pinning-PENDING.png` — thumb pushes the wooden pin at the print's top edge
3. `shot2-cork-v4-45deg-PENDING.png` — end state, pinned, hands gone
Chained end-state → placing → pinning so the board, angle and light never drift. Hands enter from
frame right with a dark tee sleeve (Sai mostly out of frame, per the original hands-only brief).
Minor: the print's position shifts a touch between stills; the club-photo face inside the print
drifted slightly at this distance — both cosmetic at reference scale.

### Row 3 — REAL b-roll now plays inside the prints
Gray: accurate board/photo dimensions + REAL frames from our b-roll, any photos or videos.
**The SSD was mounted**, and a prior session had already pulled the exact archival:
`07_QUERY_PULLS/founder-story-archival/shot3-photo-screen/` (dorm, desk work, notebook clips).
Stills extracted with ffmpeg and fed as a SECOND image reference per frame:

| Frame | Generated file | Real source (saved as `source-real-*`) | Fit |
|---|---|---|---|
| A close-up | `shot3-real-A-closeup-dorm-PENDING.png` | `talking in dorm.MP4` @4s (2022) | horizontal → letterboxed |
| B one step back | `shot3-real-B-mid-desk-PENDING.png` | `desk work.MOV` @1s | vertical → fills the print |
| C full board | `shot3-real-C-fullboard-cafe-PENDING.png` | `06_ASSETS/LinkedIn Photos/DSC01332.JPG` | horizontal → letterboxed |

Honest flags: **B and C still render the print oversized** (~1/4 to 1/3 of board width vs the true
1/6) — the model resists making the glowing print tiny; one more pass each can push it, or accept
since the wide "true scale" answer already exists in shot 2 v3/v4. A has a small curled-flap paper
artifact top-left. `desk work.MOV` is only 2.7s long — a -ss past the end writes nothing while
exiting 0, trap logged.

**ffmpeg traps (Mac):** JPEG writes from this clip hit "Non full-range YUV is non-standard" —
extract to PNG instead; use `-update` semantics or PNG for single frames.

11 generations tonight, 28 credits total, **820.29 left.**

---

## Session 2026-08-07 (evening, Mac, round 4) — cinematic shot 2, reference-matched shot 3

Gray's round-3 notes, plus a phone photo he supplied as the composition reference for shot 3's
final frame (a huge wall-mounted white board with ONE tiny photo pinned at center, shot straight
on and symmetric, doorway visible frame-right — saved nowhere yet, it lives in chat).

**✅ Shot 4 → he said attach it to the shotlist.** BLOCKED this session: the Notion MCP is not
connected on this Mac session (hosted connector absent from the session's server list; the
karramedia API token is Windows-only, not in any Mac .env). **Queued: attach
`shot4-bed-scroll-v4-realroom-PENDING.png` to shot 4's Frame Visual the moment Notion reconnects
— re-send existing attachments by type or they get wiped.**

### Row 2 v5 — CINEMATIC + staged entrance (supersedes the v4 sequence)
Gray: Sai comes from the LEFT side of frame, places and holds the photo with his LEFT hand, pins
with his RIGHT hand; make the lighting more cinematic.
1. `shot2-v5-cine-endstate-PENDING.png` — lighting-only chain off v4: low-key raking 3200K from
   upper right, deep falloff, haze in the beam, vignette, no daylight.
2. `shot2-v5-cine-still1-place-PENDING.png` — Sai enters frame-left, LEFT palm presses the print
   to the cork, no pin yet.
3. `shot2-v5-cine-still2-pin-PENDING.png` — left hand still holding, RIGHT hand presses the
   wooden pin, both hands in frame.
Minor drift: the print sits slightly left-of-center in stills 1-2 vs the end state.

### Row 3 v3 — smaller prints, medium open, reference-matched wide close
Gray: photos smaller; first frame is a MEDIUM not a close-up; last frame matches his reference
photo. Chained A→B→C:
- `shot3-v3-A-medium-dorm-PENDING.png` — medium, board mostly in frame, dorm clip at true-ish
  scale, curled-flap artifact cleaned.
- `shot3-v3-B-fullboard-desk-PENDING.png` — full board, desk clip, print small.
- `shot3-v3-C-wide-cafe-PENDING.png` — the reference composition: symmetric environmental wide,
  doorway frame-right (reads as the bathroom door per the WALL LOCK), tiny glowing print centered.

**Honest flag:** print orientation/border drifted across the series — A renders the horizontal
dorm clip as a LANDSCAPE print with a white border, B near-vertical with border, C squarish with
border, where round 3 used a vertical borderless 4x6 with letterboxing. Arguably A's landscape
print is what a real horizontal frame printed at the drugstore would look like; needs Gray's call
on which convention the real prints will use — **this is the same decision as the 4x6-vs-5x7
print-size question and should be made together before Saturday's print run.**

17 generations tonight, 40 credits, **808.29 left.**

---

## Session 2026-08-07 (evening, Mac, round 5) — the soft-blue lighting lock

Gray: shot 3 lighting SOFTER with a very faint blue lamp pouring in from frame-left; shot 2
tighter so Sai's face is out of frame, and its lighting must MATCH shot 3; "have to keep lighting
consistent." Everything else called excellent.

**⭐ LIGHTING LOCK for the board world:** soft diffused warm lamp (no harsh contrast, smooth
falloff) + a very faint cool blue lamp glow from FRAME-LEFT, always weaker than the warm. This
also ties the board world to the bedroom world — the blue lamp is the same practical that rakes
shot 4/5. `shot3-v4-A-medium-softblue-PENDING.png` is the lighting MASTER; every subsequent board
frame passed it as a lighting reference.

### Row 3 v4 — relit A/B/C
`shot3-v4-A-medium-softblue` / `-B-fullboard-softblue` / `-C-wide-softblue` — lighting-only chains
off the v3 frames, geometry untouched. Blue reads strongest in the wide (left wall), faintest in
the medium, correct hierarchy.

### Row 2 — one FAILED approach, then the fix
**v6 REJECTED (3 frames, renamed `-REJECTED`):** asking the model to "reframe tighter" made it
INFLATE the print to half the board instead of moving the camera — wrecking the true-scale rule —
and the print's content drifted to a galaxy background. Trap logged: **the model treats "tighter
on the subject" as "make the subject bigger," not as a camera move.**

**v7 method (kept):** relight the good v5 geometry (lighting-only chains, nothing moves), then do
the tighter framing as a **deterministic PIL crop** — identical window on all three frames
(left 27% cut, 9:16 kept). A crop cannot lie about scale, and it removes the face by geometry
instead of by prompt. Zero-judgment task moved into code, per the standing rule.
- `shot2-v7-still1-relit-TIGHT-PENDING.png` — left hand places, face out of frame
- `shot2-v7-still2-relit-TIGHT-PENDING.png` — right hand pins
- `shot2-v7-endstate-relit-TIGHT-PENDING.png` — pinned, hands gone
Un-cropped relit masters also saved (`-relit-PENDING`) in case Gray wants a different window.
Honest flag: the print wanders slightly across the three beats (drift inherited from the v5
relights) — reads as handheld drift; fixable per-frame if Gray objects.

**⚠️ Fal.ai URL trap:** hand-retyping a CloudFront URL corrupted one download (`a0ff` → `a0ef`,
111-byte error file). Recover the exact URL with `higgsfield generate list --json` instead of
retyping. Also: a `curl` for a wrong URL still writes a file — check size before trusting it.

23 generations tonight, 52 credits, **~796 left** (v7 relights + crop = free after generation).

---

## Session 2026-08-07 (evening, Mac, round 6) — approvals + shot 5 first pass

**✅ APPROVED by Gray: shot 2 (v7 TIGHT sequence, 3 frames) and shot 3 (v4 soft-blue series,
3 frames).** With shot 4 that is 7 frames approved and cleared to attach.

**⚠️ Notion attach still blocked from this Mac** — connector absent from the session, karramedia
token nowhere on this machine (verified: no .env, no shell rc, no env var). Gray has been given
both unblock paths: `/mcp` reconnect as gray@karramedia.com, or export NOTION_KARRAMEDIA_TOKEN in
his own terminal (never pasted in chat, per [[feedback_secrets_handling]]).
**`.attach_frames.py` written and ready** (this folder): additive-only, re-sends existing Frame
Visual entries before appending, targets the REAL data source `d589d846-…`, has `--dry-run`.
Run: `NOTION_KARRAMEDIA_TOKEN=... python3 .attach_frames.py`. NOT yet run.

**Shot 5 first pass: `shot5-v3-bev-realroom-PENDING.png`** — chained off approved shot 4 + room
plate IMG_9357: true perpendicular bird's-eye, on TOP of the navy bedding fully dressed (the beat
v1 missed), arms flung, phone screen-down beside his hand, eyes open at camera, blue-lamp wash
from the window side, exposure lifted a stop from the rejected v2, framed tight on the bed.
Awaiting Gray.

Next shots in line after 5: shot 6 (bedroom, reuses 5's rig) then the remaining board shots
7, 8, 12, 13, 15 under the soft-blue lighting lock, and 9, 10 as the new window-side expression
setup (desk/closet background — see the UNFROZEN block above). Shot 1 remains a Windows job
(needs Elements).

---

## Session 2026-08-07 (evening, Mac, round 7) — ✅ ALL 7 APPROVED FRAMES ATTACHED TO NOTION

Gray reconnected the Notion MCP mid-session. Workspace verified as **Gray Davis's Space /
gray@karramedia.com** via fetch self before any write (per [[notion-karramedia-account]]).

**Method that worked on the MCP connector (differs from the Windows raw-API path):**
`notion-create-file-upload` (returns a signed upload URL + bearer) → `curl -F file=@...` to that
URL → `update-page insert_content` appending an image block per frame under a
`## Reference Frames — APPROVED 2026-08-07` heading at each row's page end. Same pattern as the
08-06 reference-video embeds, so each row now reads: Reference Video → Reference Frames.
**Trap: MCP uploads cap at 5 MiB** (free-plan URL-download limit applies to uploads too) — the 2k
PNGs are 1.4-7.8 MiB, so each was re-encoded to JPEG q92 (0.3-1.2 MiB) before upload. PNG
originals stay canonical in this repo folder.

Attached: shot 2 (place / pin / end state), shot 3 (A medium / B full board / C wide),
shot 4 (real-room). Verified by re-fetching shot 2's page — all three images render.

**RESOLVED same session — the frames ARE in the Frame Visual COLUMN now.** Gray flagged he
couldn't see them (he reads the column/gallery, not the page body). **⭐ The MCP CAN write the
files property additively:** `update_properties` with the array of existing entries' verbatim
`file://` URI strings PLUS new entries as plain `"attachment:<file_upload_id>:<filename>"`
strings. A file_upload id already consumed by a body embed can be REUSED in the property.
Verified by count: shot 2 = 9 files (6 old + 3 new), shot 3 = 7 (4 old + 3 new), shot 4 = 2.
Recipe: fetch the page first, copy every existing `file://` string exactly, append the new
attachment strings, send the full array. **Omitting an existing entry deletes it — never write
this property without a fresh fetch.**

**Still open, needs Gray's call:** shot 2's column still carries its two REJECTED references
(`shot2-magnet-macro-ai`, `shot2-pin-photo-ai`) among the 6 old files. Removing them is a
DELETE — his word or his drag. Print lock note: **all prints VERTICAL** (Gray, this round);
horizontal archival letterboxes inside the vertical print. Size stays 4x6 per Props.
Shot 3 frames A and C were regenerated to vertical prints (`shot3-v5-A/C-vertical-print`) AFTER
the v4 set was approved+attached — swap in the column pending his eye.

---

## Session 2026-08-07 (evening, Mac, round 8) — ⚡ THE SPEED RUN: whole shotlist covered

Gray: "we need to speed run reference image process... make reference images for the rest of the
shotlist to the best of ur ability while staying in the guidelines." Explicit batch authorization,
superseding one-at-a-time for this run. Twelve generations, fire-and-poll (two batches so chains
resolve: 9→10, 5→6, 14→15). Row specs pulled live from the Notion DB first so every frame was
generated against its actual How to Film / Light / Props text.

| Shot | File | Chain ancestor | Note |
|---|---|---|---|
| 3A fix | `shot3-v5-A-vertical-print` | 3-v4-A | vertical print per print lock; ⚠️ clip content drifted |
| 3C fix | `shot3-v5-C-vertical-print` | 3-v4-C | vertical print, clean |
| 5 | `shot5-v4-bev-vertical` | 5-v3 | Gray's note: body VERTICAL in frame, head top |
| 6 | `shot6-floating-memories` | 5-v4 | floating college/friends/city/dorm/laptop stills, brightest in frame |
| 7 | `shot7-yarn-hands` | 2-v7-pin | 6 prints + yarn web forming, hand mid-pull |
| 8 | `shot8-macro-matchcut` | 2-v7-end + real desk still | the match-cut template composition |
| 9 | `shot9-expression-confused` | 4-v4 + room plate 9359 | Gray's window-side setup: desk/closet bg |
| 10 | `shot10-expression-smile` | 9 | expression-only chain; ⚠️ face drifted slightly younger |
| 12 | `shot12-ots-fullboard` | 3-v4-B + 4-v4 | OTS silhouette, full yarn web, even light |
| 13 | `shot13-faces-yarn` | real cafe still + 2-v7-end | slider-pan framing, 3 face prints on the yarn line |
| 14 | `shot14-pin-teamphoto` | 2-v7-pin | full board, hand pins the NEW team print; ⚠️ team = stand-in |
| 15 | `shot15-team-pushin` | 14 | final image; matte, brightest in frame; ⚠️ same stand-in team |

Skipped by design: shot 1 (Windows, needs both-Sai Elements), shot 11 (pure archival, no frame).
Review page: https://claude.ai/code/artifact/ef077f89-4833-4e77-9de9-0f1dc896c25f
Session total ~84 credits, **764.29 left**. Nothing attached to Notion — awaiting kill/keep per
frame, then the keepers go into the Frame Visual columns with the proven additive recipe.

---

## Session 2026-08-07 (evening, Mac, round 9) — 5/6 rotated, 3A+3C approved, column bug fixed

**✅ APPROVED: shot 3 v5 A and C** (vertical prints). Attached to the column alongside B (v4).

**Shots 5 + 6 rebriefed:** Gray called the visuals "incredible" but wants body, floating videos
and camera ROTATED 90° right so head and feet sit at opposite ends of the BED — continuity with
shot 4 (he sat on the foot of the bed, falls back ALONG the mattress). Delivered:
- `shot5-v5-along-bed-PENDING.png` — fluted headboard at top of frame, body along the bed, head
  toward headboard, phone beside his hand
- `shot6-v2-floating-alongbed-PENDING.png` — chained off it, six floating memory stills (college,
  friends, city, dorm, laptop) glowing around his head and shoulders
Gray goes ONE AT A TIME for the rest of the speed-run frames (7-15), 5/6 excepted.

**✅ SHOTS 5 + 6 APPROVED AND ATTACHED (round 9 continued).** Gray approved the versions pictured
in his screenshot of the speed-run page: `shot5-v4-bev-vertical` (body vertical, head top) and
`shot6-floating-memories`. Note the sequence: he first asked for the along-bed rotation (v5/v6-
window-pinned were generated), then approved the ORIGINAL vertical pair from the screenshot — the
rotated variants stay on disk unattached if he changes his mind. Attached via the full proven
pipeline: fetch row → fresh JPEG upload → additive column write preserving existing entries →
verified by count (shot 5 = 4 files, shot 6 = 2 files).

**🐛🐛 ROUND 10 — THE REAL FIX. The round-9 "fix" was ALSO broken and Gray caught it live.**
The invented `attachment:<file_upload_id>:<filename>` property format is a dead end entirely:
the API accepts it and echoes it back on fetch (which is why count-verification lied), but the
UI cannot render it — fresh upload or not. **Verifying by count is NOT verifying; the entry
must be a format the UI provably renders.**

**The method that actually works — and was the project's own documented recipe all along**
([[feedback-reference-image-sourcing]]: host via public-repo raw URLs): commit the frames to the
public repo (auto-push had already done it), verify every raw.githubusercontent URL returns 200
with curl, then write the Frame Visual array using the SAME encoded `file://{"source":"<raw
url>","permissionRecord":{...page id...}}` entry format the original 75 working references use.
All five columns rewritten this way: every pre-existing GOOD entry preserved verbatim, every
broken `attachment:` entry from rounds 8-9 dropped, approved frames in as raw-URL externals.
Shot 2 = 9 entries, shot 3 = 7, shot 4 = 2, shot 5 = 4, shot 6 = 2.

**Rule for the future tool: Frame Visual gets external raw-GitHub URLs, never MCP file uploads.**
File uploads remain fine for page-BODY image blocks (those render), not for the files property.

---

## Round 11 — FULL SHOTLIST TRANSFER COMPLETE + the final trap measured

Gray approved everything wholesale ("sai needs references now"). All rows 2-15 filled.

**⚠️ TRAP #3 (the one that ate the round-10 entries): on a files-property rewrite, Notion
asynchronously RE-DOWNLOADS every entry and silently drops what it cannot fetch** — re-sent
`attachment:` references AND external files over the free plan's **5 MiB** cap. The round-10
full-size PNGs (5-9 MiB) survived the write, passed the count check, then fell out during
revalidation. Count-checks lie twice over.

**Final architecture (verified):** `reference-frames/web/` in the repo holds a **≤5 MiB JPEG
(q90)** of every column frame; every Frame Visual entry is an encoded external raw-GitHub URL to
one of those. 30 JPEGs pushed, every URL curl-200-verified, all 13 rows rewritten, counts match
intent: 2=3, 3=4, 4=2, 5=3, 6=2, 7=3, 8=1, 9=6, 10=1, 12=2, 13=3, 14=3, 15=2. Old still-valid
AI references restored as JPEGs where they'd been dropped (shot 3 board-center, shot 4 wall-
graphics ref, shot 5 old BEV pair, shot 6 old floating ref, shot 9 all five, shot 12 old OTS).
Real-frame attachments (s13/s14) preserved verbatim where they survived.

**LOST from the columns, restorable only from Windows** (files are real photos, banned from the
public repo, local copies not on the Mac): shot 2's four real-photo REFs (yacht-moneyfame,
sunglasses-car, feetup-mall, casino) and shot 3's three s3-archival young-Sai photos. The
Windows raw-API File-Upload path stamped working attachment entries before — **restore them from
the Windows session**, or Gray drags them in by hand from the drive. Body-embed "Reference
Frames — APPROVED" sections on shots 2/3/4 still hold their images and were never touched.

**~~🐛 COLUMN ATTACHMENT BUG FOUND AND FIXED~~ (superseded by the above — kept for history):** a
file_upload id already consumed by a page-body embed CANNOT be reused in the Frame Visual files
property — Notion binds the file's permission record to its first attach point, so the property
copy renders broken. **Correction to the round-8 recipe: every attach point needs its OWN fresh
file upload.** Fixed by uploading fresh JPEGs (`col-shot2-place/pin/pinned`, `col-shot3-A/B/C`,
`col-shot4`) and rewriting the three properties: old entries preserved verbatim, broken entries
replaced, shot 3's column now carries the approved v5-A / v4-B / v5-C set. Body embeds were
always fine and stay untouched.
