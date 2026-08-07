# Photo Print Process — Founder Story Short

## TL;DR
Collect 2-3 photo candidates per story beat, narrow to 8-12 with Sai's approval,
prep every image to an exact 4x6 shape at print quality, print them all MATTE
(drugstore is the easy path), then keep them flat and safe until the shoot.

## You'll Need
- The approved AI photo: `/Users/graydavis28/Documents/founder-story-plates/APPROVED-youngsai-party-photo.png`
- Access to Sai's shared Google Drive "All B-roll" folder
- Sai's phone photos (AirDrop) and any old drives he has
- A CVS or Walgreens account (Path A) OR an inkjet printer + the Canon/HP 4x6 matte paper (Path B)
- Roughly $10-20 for prints
- A folder or envelope to store finished prints

## BLOCKED ON SAI — ask him for these first
1. **Team photo (Shots 14/15):** does not exist yet. Only Google Meet screenshots exist, and those won't work. Sai must take or find a real team photo.
2. **Archival photos (Shots 7/8):** old photos from his phone, family albums, or old drives. Real photos are strongly preferred over AI fills.

Text him for both before starting Phase 1 so they arrive while you work.

---

## Phase 1 — COLLECT

Goal: 2-3 candidate photos for each of the 6 story beats, all in one folder.

- [ ] 1. Make the folder: `~/Documents/founder-story-prints/candidates/`
- [ ] 2. Copy in the already-approved party photo (Shot 2) from the path above.
- [ ] 3. Hunt through the shared Google Drive "All B-roll" folder and download anything that fits a beat.
- [ ] 4. Have Sai AirDrop photos from his phone (AirDrop = Apple's wireless file send; he selects photos, taps Share, taps your Mac's name).
- [ ] 5. Ask Sai to check old hard drives / family photos for younger-years material.
- [ ] 6. Drop everything into the candidates folder. Don't judge quality yet — collect first.

What makes a good candidate, per beat (Shots 7/8, one printed photo per beat):
1. **Money** — cash, first paycheck, first sale screenshot printed as a photo
2. **Followers** — early social growth moment, a milestone screenshot, phone-in-hand
3. **Success** — a visible win: award, event, handshake, celebration
4. **Laptop grind** — Sai working late, messy desk, coffee-and-laptop energy
5. **Milestone** — graduation, first office, first hire, launch day
6. **Moving city** — packed boxes, airport, new apartment, skyline

Aim for 2-3 candidates per beat so you can pick the best in Phase 2.

## Phase 2 — SELECT

Goal: narrow to 8-12 finals, approved by Sai, before spending money on prints.

- [ ] 1. Pick at least one photo per beat. Cut duplicates of the same moment.
- [ ] 2. Check variety: mix of ages and settings, not six photos from the same year.
- [ ] 3. Faces should be visible and the emotion should match the beat (grind photo looks tired, milestone photo looks proud).
- [ ] 4. Ask Claude to make a contact sheet (one image showing all picks in a grid, labeled by beat) and send it to Sai.
- [ ] 5. Get Sai's yes/no on each. Swap anything he vetoes. Do NOT print without his approval.
- [ ] 6. Only if a beat has zero real coverage: ask Claude to generate an AI fill for that beat, and get Sai's approval on it too.

## Phase 3 — PREP

Goal: every final image is sharp enough to print and shaped exactly 4x6.

- [ ] 1. Check resolution on each final. In Finder, click the file, press Cmd+I, look at "Dimensions." You need at least **1200 x 1800 pixels** for a clean 4x6 (that's 300 DPI — dots per inch, the standard for sharp photo prints).
- [ ] 2. Anything smaller or soft (old screenshots, tiny phone pics): upscale it with the Real-ESRGAN tool at `~/Tools/realesrgan`. Easiest way — ask Claude: "upscale the low-res photos in my candidates folder."
- [ ] 3. Crop everything to an exact 4x6 shape (2:3 ratio). Easiest way — ask Claude: "batch-crop my final photos to 4x6 at 1200x1800 minimum." Claude will do it with a small Python script; you don't need to open any editor.
- [ ] 4. Optional: a light color pass (brightness/contrast) on anything that looks dull. Ask Claude, or skip it — the board reads fine with imperfect photos.
- [ ] 5. Put finished files in `~/Documents/founder-story-prints/final/` named by beat, e.g. `beat1-money.jpg`.

Why the strict 4x6 rule: Shot 8 is a match cut between photos on the board. If one print is a different size, the cut visibly jumps and the effect breaks. **Everything prints at 4x6. No exceptions, including the team photo.**

## Phase 4 — PRINT

Two paths. Path A is recommended — no printer needed and matte is a checkbox.

### Path A — Drugstore prints (recommended)
- [ ] 1. Go to the **Walgreens** Photo website or app. (NOT CVS — verified 2026-08-07: CVS same-day 4x6 is glossy-only; matte there is mail-delivery. Walgreens does same-day matte 4x6.)
- [ ] 2. Upload everything in your `final/` folder.
- [ ] 3. Size: 4x6. Finish: **MATTE** — this is the important one. Gloss reflects the key light on camera; matte does not.
- [ ] 4. Quantity: **2 copies of every photo** (macro shots crease prints fast — spares save the shoot).
- [ ] 5. Team photo (once Sai delivers it): same order, best quality option offered, matte, 4x6, extra copies (3-4). Still 4x6 — no 5x7, per the match-cut rule.
- [ ] 6. Pick up same day. Cost is roughly $0.35-0.50 per print, so a full order runs $10-15.

### Path B — Home inkjet (only if you own or buy an inkjet printer)
- [ ] 1. Confirm your printer is an **inkjet** (sprays liquid ink). A **laser** printer uses heat and will ruin inkjet photo paper — do not try it.
- [ ] 2. Load the Canon/HP 4x6 matte photo paper, glossy-feeling side down or up per the paper box's instructions.
- [ ] 3. In the print dialog: paper size 4x6, paper type "Matte Photo Paper," quality "Best," borderless if offered.
- [ ] 4. Print one test photo first. Check sharpness and color before running the whole batch.
- [ ] 5. Print 2 copies of everything. Let each print dry a few minutes before stacking.

## Phase 5 — AFTER PICKUP

- [ ] 1. Flatness check: if any print is curled, press it under a stack of heavy books overnight. Curled prints look bad pinned to the board.
- [ ] 2. Store all prints flat in a folder or rigid envelope. Do not rubber-band or fold.
- [ ] 3. Label the spare set so it doesn't get mixed into the board build.
- [ ] 4. Bring BOTH sets to the shoot. If a print creases during the macro shots, swap the spare in.

## Quick Recap of Counts
- Shot 2: young Sai party photo — 2 copies (already approved, just prep + print)
- Shots 7/8: 8-12 beat photos — 2 copies each
- Shots 14/15: team photo — waiting on Sai, then 3-4 matte copies at best quality
- Everything: 4x6, matte, no other sizes
