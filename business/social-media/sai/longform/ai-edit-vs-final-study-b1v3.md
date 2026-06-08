# Study: How Gray Edits the AI Cut (Longform Pod B1V3 - "Money Management at 17")

Comparison of the AI selects cut vs Gray's final Premiere export, to teach the
longform AI edit pipeline (video-use + multicam-mirror) how to land closer to
Gray's final on the first pass.

## Files compared
- **AI cut:** `08_AI_EDITS/long-form/Longform-Pod/SYNCED/Video 3 - Money Management at 17/V3_Acam_FRONT.mp4` (336.6s)
- **Gray's final:** `02_ACTIVE_PROJECTS/episodes/Longform Pod B1V3.aac` (321.8s)
- Both transcribed with mlx-whisper large-v3 (Mac, free) and diffed.

## Headline finding: pacing tightening dominates

| | AI cut | Final |
|---|---|---|
| Total length | 336.6s | 321.8s |
| Silence (gaps > 0.35s, < -30dB) | 60.5s | 7.3s |
| Actual speech | ~276s | ~314s |

Gray removed **~53s of silence** (60.5 -> 7.3, about 90% of the dead air) and
ADDED ~38s of new speech, netting 15s shorter. The single biggest edit is
ruthless inter-sentence gap tightening. The AI cut left long pauses/breaths
between sentences; the final has almost none.

## What Gray ADDED (the AI cut had dropped these)

1. **Standard show intro / credentials block** - placed right after the hook,
   before the disclaimer: "After my brother and I personally created thousands
   of pieces of content, built over 10 million followers, managed millions in
   mobile app spend... working with companies like Y Combinator, Mindvalley, and
   Cloak, we decided to start this podcast... I hope you share with a fellow
   mobile app founder and enjoy."
2. **Mid-roll CTA** - placed at the natural break before the investing section:
   "Really quick, guys, my brother and I spend a ton of time putting together
   free content like this... leave a review and share this with a fellow mobile
   app founder... Come back to the show."

Both are reused boilerplate every episode. video-use treated them as off-topic
chatter and cut them; Gray puts them back.

## What Gray CLEANED (false starts / stutters the AI cut kept)

- "And I still believe that to be true." -> cut (redundant with the line after)
- "...a portfolio of money that I'm going to spend every month" -> cut (garbled
  false start before the 30/40/30 split)
- "you won't be home. You're homeless" -> "you won't be homeless"
- The taxes-vault stumble, the weekly-budget stumble, the "monthly basis" repeat
  -> all smoothed
- Cut "Peace." off the very end

## What Gray did NOT touch

Structure and clip order are identical: hook -> disclaimer -> story -> tracking
-> investing -> vaults -> automation -> close. No reordering. He trusted the
AI's selects and ordering; his work was tightening + boilerplate, not
restructuring.

## Action items for the longform AI edit pipeline

1. **Tighten inter-sentence silence aggressively** - target ~0.25s max between
   sentences, do not leave 60s of gaps. This is the highest-impact change.
2. **Auto-insert boilerplate** - keep Sai's intro-credentials block and mid-roll
   CTA as reusable inserts and splice them in (after the hook; at the mid break).
3. **Cut stutters / false starts harder** - including trailing sign-offs like
   "Peace."
4. Keep trusting selects/order - no need to reorder.
