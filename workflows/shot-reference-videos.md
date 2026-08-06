# Shot Reference Videos — pre-production SOP

Turns the still reference images already sitting in a shotlist into 5-second clips that
show the **camera move**. A still tells the crew the framing; the clip tells them the move.

Tool: `python-scripts/shot-reference-videos/shotvid.py` (wraps the Higgsfield CLI).
Established and measured 2026-08-06 on the Founder Story Short shotlist.

---

## The short version

```
cd ~/Desktop/my-project/python-scripts/shot-reference-videos
./shotvid.py plan   myshots.tsv     # cost preview, spends nothing
./shotvid.py submit myshots.tsv     # fires the queue, returns in seconds
./shotvid.py run                    # hands-off until every clip is downloaded
```

Clips land in `out/` as `shot5-ref.mp4`.

---

## The decisions behind it

### 1. Model: Seedance 2.0 Mini at 480p, audio off

Measured across seven candidates on 2026-08-06:

| Model | Config | Credits | Notes |
|---|---|---|---|
| Seedance 2.0 Mini | 480p / 5s / no audio | **5** | chosen — move reads clearly |
| Veo 3.1 Lite | 4s / no audio | 4 | higher res (720x1280) but the move barely registered |
| Kling 3.0 Turbo | 720p / 5s | 7.5 | |
| Grok Video | 5s | 7.5 | |
| Seedance 2.0 (fast) | 480p / 5s | 7.5 | |
| Wan 2.6 | 720p / 5s | 13 | |
| **Seedance 2.0 (std)** | **720p / 10s / audio on** | **45** | what was used manually before this SOP |

Cost is flat 1 credit per second at 480p. Audio adds nothing to the price but nothing to
the value either — a shot reference is silent, so it stays off.

Veo 3.1 Lite was cheapest per clip but under-delivered motion in an A/B on the same frame:
its push-in was almost imperceptible while Mini's committed. Since communicating the move is
the entire point, Mini wins. Keep Veo Lite in reserve for higher-resolution one-offs.

**The saving that matters:** 5 credits instead of 45. A 16-shot list costs ~80 credits
instead of ~720 — the difference between 3 percent of the balance and two thirds of it.

### 2. Never point this at a shot that ships

This pipeline makes **disposable references** — something a crew glances at to understand a
camera move, then throws away. 480p and a 5-credit model are chosen on that assumption.

If a row says the shot is fully AI-generated and nothing gets filmed, that clip **is the
final asset**, not a reference. It needs a premium model, real prompt iteration, and full
resolution. Sending it through here produces something that looks cheap, because it is.

Learned the hard way on Founder Story row 1 (the black-void showdown), 2026-08-06: the cheap
model rendered a literal stage ceiling into what was supposed to be an empty void, and the
result was rightly rejected. Check the How to Film cell before generating — "fully
AI-generated, nothing filmed" means route it elsewhere.

### 3. Only generate the shots where motion is the point

**OVERRIDDEN for the Founder Story Short (2026-08-06): Sai wants a reference video on
EVERY shot**, so the skip-list below does not apply to Sai deliverables — generate all rows.
Status: 13 of 15 done, links live in the shot list's new `Reference Video` URL column
(Higgsfield CDN; local backups in `out/`; shot 1's link is the premium Seedance test, not a
Mini clip). Shots 11 + 14 pending — their frames are real-Sai archival, Notion-only
attachments with sources on the footage SSD. The skip discipline still applies to
internal/Gray-only shotlists.

The biggest credit saver isn't the model, it's not generating. Skip:

- **Locked-off frames.** No move to show. The still already said it.
- **Effect references** (flicker, RGB split, echo trails). Those are post decisions, and
  ffmpeg composites demo them at zero cost.
- **Shots whose move is obvious** from one word in the Visuals cell.

On the Founder Story list this cut 16 rows down to 7 worth generating.

### 4. Prompt only the motion, never the scene

The start image already carries the look. Re-describing the room or the subject invites the
model to redraw it and drift off the reference you approved.

Formula: **[camera move] + [speed] + [what holds still] + "single continuous take, no cuts"**

Good: `Slow horizontal pan across the wall, constant speed, no push, single continuous take, no cuts`

Bad: `Sai stands at his whiteboard in a warm-lit office as the camera pans across photos…`
— that re-specifies the scene and the model will reinterpret it.

Known behavior: the model adds small subject motion you didn't ask for (a person on a bed
shifts position). Fine for a camera-move reference. Tell the crew the clip demonstrates the
**move**, not the blocking.

### 5. Six jobs at a time — the plan's hard ceiling

Higgsfield Plus rejects a 7th concurrent job outright (`rate_limit_reached`). The script
holds exactly six in flight and starts the next one the moment a slot frees, so a long list
just takes more rounds instead of failing halfway.

### 6. Never wait on a single clip

`submit` returns in seconds. Nothing in the workflow blocks on one render.

**Real timings, measured:** most clips finished in about 90 seconds. One in the batch of
seven took roughly 27 minutes. Render time is genuinely variable, so treat this as a
fire-and-forget step: submit the whole list, go do other work, collect later. `run` will sit
and finish the job hands-off if you'd rather not check back.

---

## Manifest format

Tab-separated, `#` comments ignored:

```
shot_id <TAB> image_path <TAB> motion_prompt <TAB> seconds(optional)
```

Keep the manifest next to the shotlist it belongs to, named after the project.
`founder-story-shots.tsv` is the worked example — it also documents which shots were
deliberately skipped and why.

---

## Where it fits in pre-production

1. Shotlist rows drafted in Notion.
2. Frame Visual reference **images** sourced — per-shot judgment between web-find and
   AI-gen (see the reference-image sourcing rule in memory).
3. **This step:** motion manifest → `plan` → `submit` → `run`.
4. Review clips, reroll the ones that missed (`./shotvid.py reroll shot5 --prompt "..."`).
   Budget one reroll per shot; past that, the still was the wrong starting frame.
5. Host + attach to the Notion row.

## Attaching to Notion

Notion's files property takes an external URL, not a local upload. Two hosts work:

- **Public repo raw URL** — permanent, but the repo `graydavis33/my-project` is public, so
  never put real personal photos or client footage there.
- **Higgsfield's CDN URL** — `higgsfield upload create` and every finished job return a
  public CloudFront link. Zero effort, but treat it as impermanent; re-host anything you
  need to keep.

---

## Costs at a glance

| Shots generated | Credits | Share of a 1,100 balance |
|---|---|---|
| 7 | 35 | 3% |
| 16 | 80 | 7% |
| 16 at the old 45-credit config | 720 | 65% |

## Rerolls

```
./shotvid.py reroll shot5 --prompt "Faster crane descent, stop before the pillow"
```

Reuses the cached upload, so no re-upload and no wasted time. State lives in `state.json`;
completed shots are skipped on re-submit so you can safely add rows to a manifest and
re-run it.
