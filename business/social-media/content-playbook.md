# Graydient Media — Creative Director Playbook

This is the full system. Top to bottom, pre to post, research to upload. Built around what you already have, what needs to be built, and how to wire it all together.

---

## THE BIG PICTURE

Your niche is the intersection of **videography + AI workflow**. That intersection is:
- Underserved (most creators are either pure filmmakers OR pure AI nerds, not both)
- Trending (AI content is exploding, videography tips always perform)
- Commercially valuable (videographers and editors will actually pay to learn this)
- Uniquely yours (your daily Sai Karra work gives you real professional footage others can only fake)

Your goal: own that intersection. Every piece of content either shows the craft, shows the AI workflow, or connects both. That's your brand identity.

---

## CAPACITY & CONSTRAINTS

This playbook is designed around reality, not a fantasy production schedule.

### Time budget
- Sai Karra job: ~40h/week (varies with his schedule) — primary income, non-negotiable
- Content production for Graydient: estimated 5-10h/week realistic ceiling
- No daily uploads. Cadence is volume-capped, not ambition-capped.

### Posting rule (one-video-all-platforms)
Every short-form video gets posted to ALL three short platforms:
- TikTok
- Instagram Reels
- YouTube Shorts

No platform-specific variants. No per-platform re-cuts. Same video, three uploads. Captions can vary, video cannot.

### Burnout rule
If a week hits its capacity ceiling, we cut content — never Sai, never sleep, never research. Missed uploads < burned-out creator.

### Automation target
Every stage in Layers 1-7 aims to run without human input except where human-in-loop is explicitly required (filming myself, on-camera talking, creative decisions). The goal is not "Gray does less." The goal is "Gray does only what Gray uniquely can do."

---

## LAYER 1 — RESEARCH SYSTEM

This runs before any content gets made. Without this, you're guessing. With it, every video has a reason to exist.

### Daily Research (15 min, automated)

**What to watch:**
- TikTok Creative Center → trending sounds in your niche
- YouTube trending in "Creator Economy" + "Video Production" categories
- Reddit: r/videography, r/premiere, r/editors, r/tiktokgrowth
- X: search "videography" + "video editing" sorted by latest

**Automate this with your Content Researcher:**

Right now it has an agent loop + Reddit layer. Extend it to:
1. Pull Reddit top posts from r/videography, r/premiere, r/editors daily
2. Pull trending topics from YouTube (Google Trends API — free, no auth needed)
3. Run output through Claude → identify what questions are being asked, what pain points are surfacing
4. Output a daily Slack DM: "Today's 3 best video topics + why"

Add a new function to `content-researcher/agent.py`:
```python
def daily_trend_brief():
    # Reddit top posts (3 subreddits, top 10 each)
    # Google Trends (keywords: videography, CapCut, video editing, AI editing)
    # Claude synthesizes → 3 topic recommendations with rationale
    # Slack DM to Gray
```

### Weekly Competitor Analysis (30 min, automated)

Use Creator Intel to pull your top 5 competitor channels weekly and identify:
- Which videos gained the most views that week (outlier detection — find anything 3x their average)
- What topics those videos covered
- What hooks they used in the first 3 seconds

Build a new report in Creator Intel: `weekly_outlier_report.py` — Slack DM every Sunday at 9am with the top 5 outlier videos from the past 7 days across your tracked creators.

Creators to track:
- Jordy Vandeput (Cinecom) — YouTube tutorial king
- Parker Walbeck — full-time filmmaker advice
- Mango Street — aesthetic/cinematic
- Isaiah Photo — editing on TikTok
- Peter McKinnon — aspirational photographer/filmmaker
- Add 2-3 smaller creators (under 100k) in the AI + video space — those are your direct competitors

### Hook Bank System

A hook is the first 1-3 seconds of any video. It's the most important part. 80% of views are lost or kept in the first 3 seconds.

Build a running `hook-bank.md` document. Structure:
```
## Problem Hooks
- "This ONE editing mistake is costing you views..."
- "Why your videos look cheap (and how to fix it in 30 seconds)"
- "Every videographer making under $5k/mo makes this mistake"

## Curiosity Hooks
- "I let AI edit my entire video. Here's what happened."
- "I filmed for a CEO for 30 days. Here's what I learned."
- "What $6,500/mo in videography looks like behind the scenes"

## Counter-intuitive Hooks
- "Stop learning more camera settings. Do this instead."
- "The best editing tool isn't Premiere. It's this."
- "Your gear doesn't matter. Here's what does."
```

Use your Hook Optimizer to test hooks before committing. Run the top 3 candidates for each video through it, pick the winner.

Target: maintain a bank of 50+ hooks at all times. Add 5 new hooks every Friday based on what performed that week.

---

## LAYER 2 — CONTENT STRATEGY

### The Platform Stack

| Platform | Format | Frequency | Goal |
|----------|--------|-----------|------|
| TikTok | 15s-3min vertical | 1-2x/day | Volume + discovery |
| Instagram Reels | 15s-90s vertical | 1x/day | Reach + aesthetic brand |
| Instagram Carousels | 5-10 slides | 3x/week | Save rate + evergreen |
| YouTube Shorts | 60s vertical | 1x/day (repurpose TikTok) | Search discovery |
| YouTube Long-form | 8-15 min | 1x/week | Deep audience + revenue |
| X (Twitter) | Text threads | 3x/week | Thought leadership + SEO |

**The repurposing rule:** Every TikTok gets posted to Instagram Reels and YouTube Shorts. Same video. Zero extra work. That's 3x the distribution for 1x the effort.

### Content Pillars (5 pillars, rotate weekly)

**Pillar 1: AI + Camera (30% of content)**
- Most unique, highest shareability, newest content space
- Shows Claude Code workflows applied to video editing
- Examples: "I used AI to write my entire shot list", "AI analyzed my last 10 videos and told me what to change", "Let Claude pick my best clips from 2 hours of footage"
- This is your differentiator. No other videographer creator is showing this.

**Pillar 2: Behind the Scenes with Sai (20% of content)**
- Your daily work is content. Film 30-60 seconds of setup, location, or the final video playing on screen
- Aspirational — shows you working at a real professional level
- "A day filming for a NYC CEO", "The setup behind this LinkedIn video"
- This builds credibility that you're not just a hobbyist

**Pillar 3: Tutorials and Tips (25% of content)**
- Specific, actionable, searchable — "CapCut effect in 60 seconds", "How I color grade in 3 clicks"
- These are your evergreen long-tail content — they get found for years via search
- Short-form version on TikTok/Reels, long-form version on YouTube
- Each tutorial short = teaser for the YouTube full version

**Pillar 4: Before/After Transformations (15% of content)**
- Highest engagement format in video editing — people cannot scroll past a good before/after
- Show raw footage → graded/edited footage. Split screen or back-to-back
- Can use Sai's footage (with permission), or your own practice footage
- No talking required — music + visuals only. Fastest to produce.

**Pillar 5: Journey / Transparency (10% of content)**
- Income, clients, lessons learned, mistakes made
- "Month 1 as a professional videographer in NYC — here's the reality"
- This builds parasocial connection and loyalty faster than any other format
- Post monthly as a recap — raw, honest, no polish required

### Content Series (long-term compounders)

Series create return viewers. Someone who watches Episode 1 will come back for Episode 2. These are your audience retention machines.

| # | Series | Format | Cadence | Production Style | Long-form Path |
|---|---|---|---|---|---|
| 1 | **Claude Edits** | Short-form | Weekly | Script pulled from Obsidian vault session history ("one quick Claude edit I did") | 10 episodes → long-form: "I automated my [workflow]" |
| 2 | **60-Second Effect** | Short-form | Capacity-based | Screen recording, no narration, music-only | N/A (standalone shorts) |
| 3 | **Videographer's Week** | Short-form | Weekly (Friday) | Phone-at-self, "what I filmed / what I learned / what I'm testing" | 4 weeks → "Month One" long-form |
| 4 | **Month One as NYC Videographer** | Long-form | Monthly | Phone-at-self + B-roll, minimal editing | Cut DOWN into 4-6 follow-up shorts |
| 5 | **Tool Report** | Long-form primary, occasional short teaser | Bi-weekly | Review one tool (CapCut, Claude Code plugins, gear, AI editing) | Long-form base → cut into shorts |
| 6 | **BTS as Personal Videographer** | Short-form | Weekly (from Sai shoot days) | Film-style tutorial shot during/after Sai shoots | Every 10 episodes → long-form "Filming for a CEO: what I learned" |
| 7 | **Social Media Growth Update** | Short-form | Weekly | Phone-at-self, "here's my growth this week + what I tried" | Quarterly → "Growing from 0 to Xk" long-form recap |

### Cross-series rules

- **One-video-all-platforms** — every short posts to TikTok + IG Reels + YouTube Shorts
- **Bi-directional repurposing:**
  - 10 related shorts → 1 long-form compilation
  - Any standalone long-form → cut DOWN into follow-up shorts

### Series Flex Rules

This series list is a living design. Expect it to change.

**Triggers that prompt a series change:**
- **Performance:** flops 3x in a row → tagged for review via Layer 7
- **Capacity:** if a series takes too long to produce AND isn't pulling weight, it gets cut or paused — no guilt
- **Trend-hop:** a trending topic/sound can spawn a TEMPORARY series (2-week duration cap) without joining the permanent list
- **Fatigue:** if Gray no longer enjoys making it, that alone is valid reason to cut — burnt-out creator > missed format

**Each series has 4 possible states:** Active / Testing / Paused / Killed

**When a series is Killed:**
- Tagged in Layer 7 registry with reason + performance data
- Never auto-suggested again by agents (see Layer 7)
- A candidate from the "Pending Series Ideas" list rotates in

**Monthly review** (last Sunday of month, 15 min):
- Check performance of every Active series
- Move stragglers to Testing or Paused
- Promote a Testing series to Active if it's earning its slot
- Pull one from Pending if a slot opens

### Pending Series Ideas

_(Empty — populated as ideas emerge. Candidates rotate in when an Active slot opens.)_

### Killed Series Archive

_(Empty — populated when a series is killed. Links to Layer 7 registry once that system exists.)_

### Sai Karra Content

Sai Karra has his own content playbook, strategy, and series list.
See: `business/sai/content-playbook.md` (sub-project B — in progress).

Graydient Media and Sai Karra content are separate brands with separate strategies. Cross-pollination (BTS from Sai shoots for Graydient's "BTS as Personal Videographer" series) is encouraged, but the content calendars, analytics, and iteration systems are independent.

---

## LAYER 3 — PRODUCTION SYSTEM

### Weekly Production Schedule

**Sunday — Planning (1 hour)**
- Pull weekly trend brief from Content Researcher (automated, Slack)
- Pull competitor outlier report from Creator Intel (automated, Slack)
- Review Social Media Analytics — what performed last week
- Set 7 videos for the week. Write topic + hook for each.
- Build shot list for any Sai Karra days that need specific B-roll

**Monday/Wednesday/Friday — Batch Filming (1-2 hours)**
- Film 3-5 short-form videos in one session
- Screen record tutorials during this time (fastest content to produce)
- Capture B-roll during Sai shoots — dedicate 10 minutes at start/end of every Sai day to filming for your brand

**Tuesday/Thursday — Edit and Upload (2-3 hours)**
- Use Content Pipeline for transcription + clip selection
- Batch edit same-format videos together (set templates once, reuse)
- Schedule uploads (Buffer or Later for TikTok/IG, YouTube native scheduler)

**Saturday — Engagement + Analytics (30 min)**
- Reply to all comments from the week
- Check analytics — note what worked, add hooks to bank if something hit
- Identify any collab opportunities

### Templates to Build (one-time investment, saves hours weekly)

**CapCut templates:**
- Tutorial template: hook (3s) → screen recording with cursor highlight → result clip → CTA (3s)
- Before/After template: split screen with transition, consistent font/color
- BTS template: quick cuts + text overlays + trending audio

**Premiere Pro templates:**
- Color grade preset (Sai Karra professional footage look)
- Intro/outro bumper (3 seconds each)
- Lower thirds for text callouts

**Instagram carousel template (Canva or Figma):**
- Slide 1: bold hook/question
- Slides 2-6: one tip per slide, consistent layout
- Slide 7: CTA ("follow for more")
- Build 3 color variants — rotate them

### Content Pipeline — How to Use It for This

Your Content Pipeline already does: raw video → transcription → clip picking → captions.

Extend it to also output:
- **Title suggestions** — Claude generates 5 title options per video (hook style)
- **Caption text** — formatted for TikTok (with line breaks), Instagram, YouTube
- **X thread** — 5-tweet thread based on the video's main lesson
- **YouTube description** — with timestamps, gear links, related videos

Add a new `export_all_formats.py` function that takes one processed video and outputs all of the above to a `content-pipeline/drafts/YYYY-MM-DD-video-title/` folder.

### Long-Form Production Paths

**Path 1: Shorts → Long-form (compilation)**
Record a mini-series of 8-12 shorts on one theme. Once complete, stitch into a single long-form with:
- New intro (30s, re-contextualize the journey)
- Original shorts as chapters (light re-edit for flow)
- New outro with takeaway + CTA

Example: 10 episodes of "Claude Edits" on editing automation → one YouTube video: "I automated my entire editing workflow"

**Path 2: Long-form → Shorts (repurpose down)**
Film a standalone long-form (Tool Report, Month One recap, etc.). After publishing, cut 4-6 highlight clips as follow-up shorts. These shorts drive traffic BACK to the long-form.

**Rule:** never film a long-form that can't produce at least 3 shorts as a byproduct. If it can't, it's too narrow.

---

## LAYER 4 — DISTRIBUTION SYSTEM

### Upload Workflow

**TikTok** — upload first. This is your primary discovery platform.
- Optimal times: 7-9am, 12-3pm, 7-10pm (EST)
- Caption: 1-2 sentences max. Keywords naturally in the sentence (not a hashtag dump).
- Hashtags: 3-5 max — one broad (#videography), one niche (#capcut), one trending if relevant
- Pin your 3 best performing videos

**Instagram** — upload same video 30-60 min after TikTok. Remove TikTok watermark (use SnapTik or the native no-watermark download).
- Reels: same video, slightly different caption written for Instagram audience
- Carousels: post 3x/week — best performing long-form advice repackaged as slides
- Stories: post 3x/day minimum — mix of behind the scenes, polls, reposts of your Reels

**YouTube Shorts** — upload same video again. No watermark. YouTube-optimized title (searchable keyword first).

**YouTube Long-form** — separate content. But you can build it from your short-form. Every 4-6 Shorts in the same series = one long-form compilation or expanded deep-dive.

**X/Twitter** — text threads only. Take the lesson from your video, write it as a 5-tweet thread. Link the YouTube video at the end. No cross-posting vertical video here — it performs terribly.

### Scheduling Automation

Use Buffer (free plan supports 3 channels) or Later for scheduling Reels and TikTok in advance. Batch-schedule the whole week on Sunday.

Build a new Python script: `content-pipeline/schedule_week.py`
- Input: folder of processed videos + generated captions
- Output: scheduled posts via Buffer API (or at minimum, a posting checklist with copy-pasted captions ready)

### Audio Strategy (TikTok/Reels)

Trending audio is one of the fastest ways to get pushed by the algorithm. But most creators use audio randomly. Do this instead:

**Every Monday:** pull the top 10 trending sounds in the "Creator/Education" category on TikTok and save them in a `trending-audio-log.md`. Use them within 48h of adding them — sounds have a short trending window.

Extend Content Researcher to add: trending audio monitoring. Use TikTok Creative Center's trending sounds API (or scrape the public Creative Center page) and Slack DM you the top 5 sounds Monday morning.

---

## LAYER 5 — GROWTH ACCELERATION TACTICS

### The First 90 Days (Volume Phase)

You don't have enough data yet to know what performs. For the first 90 days, the strategy is pure volume.
- 2 TikToks/day minimum
- Every format tested at least 3 times before judging it
- Track every video in a `content-log.csv`: date, platform, topic, hook, views, followers gained, saves

At 90 days, you'll have enough data to see what your audience responds to. Then you shift to quality over quantity on what's proven, and kill what isn't working.

### Engagement Farming (Ethical)

The algorithm rewards engagement. Manufacture it early:
- Reply to every comment within the first 30 minutes of posting (the post's "golden window")
- Ask a direct question in every caption ("which one would you try first?")
- Reply to comments with VIDEO REPLIES (TikTok stitch feature) — these create new content and show the original video to new audiences
- Do 1 TikTok LIVE per week — even for 20 minutes. Lives boost your account's overall reach.

### Collab Strategy

Collabs are the single fastest growth lever available. One collab with a creator twice your size can add 10% of their audience to yours in a week.

Target strategy:
- Find creators in adjacent niches (photographers, motion designers, graphic designers, content marketers) who have 2-5x your following
- Offer value first — comment on their videos consistently for 2 weeks before reaching out
- Pitch a video that makes THEIR audience look smart (not one that's just about you)
- Format: "We each make a video on [topic] from our perspective, link each other at end"

Build a `collab-tracker.md` — track 20 potential collab targets, their niche, their size, your outreach status.

### The Comment Section as Content

The best TikTok growth hack that barely anyone does consistently:

Go to the top 5 creators in your niche. Leave insightful, interesting, slightly controversial comments that invite responses. Not "great video!" but "I've tried this and the opposite worked for me — here's why..."

When your comment gets likes, it shows to their entire audience. Some percentage clicks your profile. This is free distribution from your competitors' audiences.

Spend 15 minutes per day on this. Track it. It compounds.

### Pinned Video Strategy

Your pinned videos are your first impression. Most people pin their most viewed videos. That's wrong.

Pin these three types:
1. **Who I am** — 30-60 second introduction video. Who you are, what you make, why follow you. Film this Week 1, pin it forever.
2. **Best tutorial** — your highest-save-rate tutorial (saves = people want to come back to this = they follow to save it)
3. **Most viral short** — social proof. Shows new visitors you've had success.

Update pin #3 as you grow. Never change pins #1 and #2 unless you're rebranding.

---

## LAYER 6 — ANALYTICS AND FEEDBACK SYSTEM

### Weekly Analytics Review (every Sunday, 30 min)

Pull from Social Media Analytics:
- Views this week vs last week (growth or decline)
- Top 3 performing videos (topic, hook, format)
- Worst 3 performing videos (same breakdown)
- Follower growth rate
- Save rate on Reels/TikTok (saves > likes as a quality signal)

Ask yourself three questions every week:
1. What worked? Double down on it immediately.
2. What flopped? Kill the format if it flops 3 times in a row.
3. What didn't I post that I should have? (trending moment you missed, collab opportunity, etc.)

### The Content Audit (monthly)

Every 30 days, run a full audit:
- Delete or archive any video under 500 views after 30+ days (on TikTok — low performers drag your account's algorithm score down)
- Identify your top 3 performing series/topics — plan 4 more in each next month
- Review comment sections for content ideas (the comments are a free research tool)
- Update your competitor tracking list — remove any creator who's stopped posting, add new rising creators

### The 90-Day Pivot Rule

If a content pillar or series hasn't broken through after 90 days and 20+ videos, you pivot. Not quit — pivot. Change the hook style, change the format, change the angle. The topic might be right but the execution wrong, or vice versa. Test one variable at a time.

---

## THE NEW TOOL TO BUILD

**"Content OS" — a single command-line tool that ties all of this together.**

`python content-os.py --mode=daily`

What it does:
1. Pulls today's trend brief from Content Researcher (cached, runs once daily)
2. Pulls this week's content calendar (a simple `content-calendar.json` you maintain)
3. Shows today's task: what to film, what to edit, what to upload
4. Outputs today's captions (pre-written by Claude based on topic)
5. Outputs today's hooks (3 options, pre-scored by Hook Optimizer)

`python content-os.py --mode=weekly`
1. Runs full competitor analysis via Creator Intel
2. Runs Social Media Analytics weekly report
3. Generates next week's content calendar based on what performed and what's trending
4. Outputs to Slack DM

This doesn't require new infrastructure — it's a wrapper around tools you already have. It saves 2-3 hours per week of context switching.

---

## THE 12-MONTH ROADMAP

**Month 1-2 (Foundation):**
- Film WHO I AM video, pin it
- Establish all 5 content pillars
- Post 2x/day TikTok minimum
- Run 90-day volume phase
- Set up weekly analytics review habit

**Month 3-4 (Data-Driven):**
- Review 90 days of data — kill what isn't working, double down on what is
- Identify 1-2 series to commit to for the year
- Start YouTube long-form (1 per week, built from your Shorts)
- First collab outreach (10 targets)

**Month 5-6 (Scaling):**
- Hit 10k TikTok followers target → unlock Live gifts, DM links in comments
- Start email list (free resource as lead magnet — e.g., "My full AI editing workflow PDF")
- Carousels on Instagram generating 5k+ saves per week

**Month 7-9 (Monetization):**
- 50k TikTok target → brand deal eligible
- YouTube 1k subscribers + 4k watch hours → monetization
- First product offer: could be a Notion template, preset pack, or course waitlist
- Analytical SaaS start driving sign-ups via content

**Month 10-12 (Authority):**
- You are the AI videographer creator. Nobody else occupies this exact space.
- Inbound brand deals in the $500-2k range per post
- Consistent 10k-50k views per average video
- Email list at 5k+ subscribers — a real owned audience

---

## THE ONE RULE

The system above only works if you use it. The biggest killer isn't bad content — it's inconsistency. Posting 2x/day for 2 weeks then going dark for a week is worse than posting 1x/day forever.

Build the habit first. Then optimize the content. Then scale what works.

The research system tells you what to make. The production system makes it fast. The distribution system gets it seen. The analytics system tells you what to keep doing. Run all four simultaneously, forever.
