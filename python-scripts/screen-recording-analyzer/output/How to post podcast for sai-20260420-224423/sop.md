# SOP: Edit and Publish "Building Blocks with Sai Karra" Episode

**Trigger:** Sai sends a new podcast recording via Google Drive; Gray pulls it down and drops it into a folder on his local footage hard drive (`D:/`). Automation reads from that local folder — no Google Drive integration needed. Exact folder path TBD (see Still Open).
**Frequency:** ~1 episode per week (confirm cadence)
**Owner today:** Sai Karra → **Future owner:** AI agent — **fully autonomous, auto-publishes at the end.** No human checkpoint.
**Expected runtime:** ~15 minutes manual today; target ~2 minutes with automation

---

## Inputs

- Raw pod recording — Sai delivers via Google Drive; Gray pulls it to a folder on `D:/` (footage drive); automation reads from there
- "Building Blocks intro" stinger audio — **fixed file, same every episode**. Lives in `D:/Sai/07_ASSETS/` (exact subfolder TBD — candidate: `07_ASSETS/Podcast/intro.mp3`)
- "Building Blocks midway" stinger audio — **fixed file, same every episode**. Same folder as intro (candidate: `07_ASSETS/Podcast/midway.mp3`)
- Episode title (free-form, formula: "What I learned from my $100m mentor"-style)
- Episode notes (formula: 1-sentence premise + "These are the X biggest takeaways" list)
- RSS.com login (Sai will share when handoff happens — reference only, never pasted in chat)

## Tools & Accounts

- **CapCut** (Mac desktop app) — edit + export audio — login not required
- **RSS.com** (`https://dashboard.rss.com/`) — podcast host — login via email/password
- **ChatGPT** (optional, Sai's personal workflow) — SEO-optimized episode notes from transcript — swap for Claude Sonnet in the automation

---

## Steps

### Stage A — Edit in CapCut

1. **Open CapCut and create a new project**
   - Action: launch CapCut → start a new project
   - Frame reference: `frames/frame_00001.jpg` @ 00:24 (CapCut menu bar visible)
   - Expected result: empty CapCut workspace with Media panel on the right

2. **Import the three source files**
   - Action: in the Media panel, click **Import** and select:
     - The raw pod recording (`pod.mp3` or similar)
     - The Building Blocks **intro** stinger
     - The Building Blocks **midway** stinger
   - Frame reference: `frames/frame_00003.jpg` @ 00:26 (Import button visible in Media panel)
   - Expected result: all three files appear in the media bin

3. **Drop the podcast on the timeline and locate the hook**
   - Action: drag the main pod onto the timeline. Scrub to just after the opening hook sentence ("I was fortunate enough to get lunch today with my mentor…")
   - Expected result: playhead sits immediately after the hook line ends

4. **Split the pod and insert the intro stinger — always right after the hook**
   - Action: split (cut) the pod at the end of the opening hook sentence → drop the **intro stinger** in the split
   - **Rule (locked):** intro ALWAYS goes immediately after the hook — never before, never later. No judgment call.
   - Transcript reference: **[01:06]** "And then you find the intro, like, right after the hook. You cut it, and then drag that intro in there."
   - Expected result: timeline order is `hook → intro stinger → rest of pod`

5. **Find a mini-hook mid-podcast and insert the midway stinger**
   - Action: scrub into the middle of the pod → find an engaging "mini hook" moment (a line that makes you want to keep listening) → split → drop the **midway stinger** in
   - **Rule (locked):** the midway placement is at a **mini-hook / engaging moment somewhere in the middle** of the episode — not the exact midpoint, but a narrative peak in the middle third
   - Transcript reference: **[01:58]** "find a midway point, somewhere where it's, like, tension-causing"
   - Expected result: midway stinger plays at an engaging mid-episode moment

6. **Cut dead space throughout**
   - Action: scrub through the full timeline and delete obvious silence / dead air. No creative edits, no music, no effects.
   - Transcript reference: **[02:29]** "make sure you just cut out the dead space. And that's pretty much it."
   - Expected result: tight cut with no long gaps

7. **Export as audio**
   - Action: click **Export** → choose audio-only export (MP3)
   - Transcript reference: **[02:34]** "You click export... I'm going to export it as audio."
   - Expected result: a single `.mp3` file of the edited episode on disk

### Stage B — Publish on RSS.com

8. **Open rss.com and sign in**
   - Action: browser → `https://rss.com` → Sign In → enter Sai's credentials
   - Frame references: `frames/frame_00006.jpg` @ 02:59 (rss.com homepage), `frames/frame_00007.jpg` @ 03:01 (sign-in page)
   - Expected result: land on the "Building Blocks with Sai Karra" podcast dashboard (see `frames/frame_00010.jpg` @ 03:08)

9. **Click "New episode"**
   - Action: click the orange **+ New episode** button on the podcast dashboard
   - Frame reference: `frames/frame_00010.jpg` @ 03:08 (New episode button visible)
   - Expected result: navigate to `dashboard.rss.com/podcasts/{show-slug}/new-episode/`

10. **Upload the exported audio**
    - Action: drag-and-drop the exported MP3 into the **Episode audio file** zone (2 GB limit)
    - Frame reference: `frames/frame_00011.jpg` @ 04:59 (audio upload section with file attached)
    - Expected result: audio file attached, duration shown, "Replace audio file" option appears

11. **Set the Episode Title**
    - Action: paste/type a descriptive title — formula Sai uses: `What I learned from my $100m mentor`
    - Max 250 chars; his examples trend to 35 chars
    - Frame reference: `frames/frame_00011.jpg` — title field visible with the example filled in
    - Expected result: title saved in field

12. **Fill in Episode Notes**
    - Action: write description with this formula:
      - 1-sentence premise: *"I got lunch with a mentor today whose agency does over $100m a year."*
      - Hook line: *"These are the 3 biggest takeaways."*
      - Bullet points for each takeaway (Sai's usual pattern is 3)
    - Sai's preferred method: paste transcript into a ChatGPT project tuned for SEO podcast descriptions. For automation: use Claude Sonnet with the same intent.
    - Transcript reference: **[03:50]** "what I usually do is I get the transcript of the actual audio and then I put it in the chat GPT. I build out like a project or a bot that's specific for thumbnail title or podcast descriptions that are like optimized for SEO"
    - Expected result: episode notes filled in, 116+/4000 chars

13. **Cover art — leave default**
    - Action: leave the existing "Building Blocks with Sai Karra" cover art; do NOT replace per episode
    - Frame reference: `frames/frame_00011.jpg` — cover art visible on right rail
    - Expected result: no change

14. **Save Draft**
    - Action: click **Save Draft** (bottom right)
    - Frame reference: `frames/frame_00011.jpg` — Save Draft button
    - Expected result: draft saved, Publish button appears

15. **Publish (auto)**
    - Action: click **Publish** immediately after Save Draft — the automation does this end-to-end with no human stop
    - **Rule (locked):** once the pipeline kicks off, it runs all the way through to Publish. No draft-and-wait step.
    - Transcript reference: **[05:04]** "Once you save draft, you're going to get a button that says publish. You click publish and then you export that shit to the internet."
    - Expected result: URL changes to `?status=published`, episode goes live, distributes to Apple Podcasts / Spotify / etc. via RSS.com's automatic distribution

---

## Success Criteria

- Published episode appears on the dashboard with `?status=published` in URL (see `frames/frame_00013.jpg`)
- Audio plays end-to-end without dead-space gaps
- Intro stinger plays immediately after the opening hook
- Midway stinger plays at a tension point
- Episode distributes to Apple Podcasts and Spotify within ~1–2 hours (RSS.com handles this automatically)

---

## Failure Modes

- **Intro/midway stinger in the wrong place** → the narrative beat is wrong. Recovery: delete episode, re-edit, re-upload.
- **Published with the wrong title/notes** → RSS.com allows post-publish edits on the episode page.
- **Audio file > 2 GB** → compress with `ffmpeg -i in.mp3 -b:a 128k out.mp3` before upload.
- **Login expired / 2FA prompt** → tutorial doesn't show 2FA being used; flag this the first time it happens.

---

## Automation Hooks

- **Fully automatable — end-to-end, no human checkpoint:**
  - **Input pickup:** watch a folder on `D:/` (footage drive) for the latest raw pod file, or pass it as an arg on run. No Google Drive API in the automation — Gray manually moves the file from Drive to `D:/`.
  - **Step 6 — cut dead space:** ffmpeg silence-detect → auto-trim (`silencedetect` + `atrim` filters)
  - **Step 3 — find the hook end:** Whisper transcript + Claude Sonnet pass to find the exact timestamp where the opening hook sentence ends. Deterministic splice point once we have it.
  - **Step 4 — insert intro stinger:** ffmpeg concat at the hook-end timestamp. No judgment — rule is fixed.
  - **Step 5 — insert midway stinger:** Claude Sonnet pass on the transcript to score candidate "mini-hook" lines in the middle third of the pod → pick the top scorer → ffmpeg concat at that timestamp.
  - **Step 7 — export:** ffmpeg encode → MP3
  - **Step 11 — title:** Claude Sonnet prompt on transcript, constrained to "What I learned from…"-style formula
  - **Step 12 — episode notes:** Claude Sonnet prompt: premise + "X biggest takeaways" + bullet list. Replaces ChatGPT/Sai's project — we already have `ANTHROPIC_API_KEY`.
  - **Step 15 — publish:** Playwright drives through Save Draft AND Publish. No draft-and-wait.
- **No public API — Playwright required:**
  - Steps 8–15 on RSS.com (no public API; scrape/drive via Playwright like `social-media-analytics/meta_scraper.py` does for Meta)
- **Iteration plan:**
  - v1 ships as auto-publish end-to-end. Gray audits the first few published episodes against what Sai would have shipped manually. If Claude's mini-hook picks or title/notes miss, update THIS SOP with the refinement and retune the prompts.
- **Next script to build:** `python-scripts/podcast-publisher/main.py`
  - Inputs: (optional) path to raw pod override; otherwise auto-pull from Drive folder
  - Outputs: edited MP3 at `output/{episode}.mp3` + generated title/notes + published episode URL logged to Slack

---

## Resolved (2026-04-20)

- **Raw pod delivery:** Sai sends via Google Drive → Gray manually pulls to a folder on `D:/` (footage drive) → automation reads from local path. Keeps the code simple: no Google Drive API, no OAuth.
- **Stinger storage:** intro.mp3 + midway.mp3 are **fixed static assets** — same files every episode. They live in the existing `D:/Sai/07_ASSETS/` folder (subfolder TBD). Only the incoming-pod folder ever gets new files.
- **Intro placement:** always immediately after the hook. Locked rule, no judgment.
- **Midway placement:** at a mini-hook / engaging moment in the middle of the pod. Claude picks the timestamp.
- **Auto-publish:** yes. Once the automation kicks off it runs all the way to Publish.
- **SOP ownership:** Gray and Claude update this doc together as rules evolve. This file is the source of truth.

## ⚠ Still Open

1. **Canonical local folder on `D:/` for incoming pods** — needs to be set before the first run. Candidate: `D:/Sai/Podcasts/Incoming/` (fits the existing `D:/Sai/` structure).
2. **Canonical local paths for intro + midway stingers** — Gray is placing the two fixed files in the existing `D:/Sai/07_ASSETS/` folder (subfolder name TBD; candidate: `07_ASSETS/Podcast/intro.mp3` + `07_ASSETS/Podcast/midway.mp3`). Static assets, never change.
3. **Is the ChatGPT project for episode notes something we should replicate in Claude** (simpler, we have the key) — confirm with Sai. Default assumption: yes, replicate in Claude.
4. **RSS.com has no documented public API** — before committing to Playwright, inspect network traffic during a manual upload for an undocumented internal endpoint.
5. **2FA / session handling on RSS.com** — unknown; will surface on first Playwright run.
6. **Cadence** — how often does a new episode drop? Weekly? Daily? Sets automation priority.
