# Sai Content — Filming & Footage Organization System

**Purpose:** One canonical folder structure for everything Gray films, edits, and delivers for Sai. Cross-machine (Windows + Mac), integrates with [[Footage Organizer]] Python tool + Obsidian planning vault.

**Prepared:** 2026-04-14 (for first day filming 2026-04-15)
**Lives at (pick one and stick with it):**
- Windows: `G:/Sai/` (external SSD)
- Mac: `/Volumes/Sai/` (same SSD, different mount path)
- Or on a synced cloud folder if you prefer (Dropbox / iCloud) — but NVMe SSD is faster for editing

**Alternative names for the root:** `Sai/` · `Trendify-Content/` · `Karra-Media/` — pick whatever's shortest for you.

---

## TL;DR

```
Sai/
├── 00_TEMPLATES/        Reusable project templates, LUTs, title cards
├── 01_RAW_INCOMING/     Fresh card dumps, organized by date
├── 02_ORGANIZED/        After Footage Organizer runs (auto-sorted by content)
├── 03_PROJECTS/         Active edits (episodes/, shorts/, linkedin/)
├── 04_DELIVERED/        Final published files (backed up)
├── 05_ARCHIVE/          Old projects, retired content
├── 06_BROLL_LIBRARY/    Reusable B-roll pulled from past shoots
└── 07_ASSETS/           Brand assets, fonts, logos, music library
```

**The flow, every shoot day:**
```
Card → 01_RAW_INCOMING/2026-MM-DD/ → [Footage Organizer runs]
    → 02_ORGANIZED/2026-MM-DD/{interview, broll, meeting, ...}
    → [You pick clips for today's short] → 03_PROJECTS/shorts/DayN_.../selects/
    → [Edit in Premiere] → 03_PROJECTS/shorts/DayN_.../exports/{TT, IG, YT}/
    → [Publish] → 04_DELIVERED/shorts/ (backup)
    → [Optional] → 06_BROLL_LIBRARY/{category}/ (stash reusable clips)
```

---

## 1. Full Folder Structure

```
Sai/
│
├── 00_TEMPLATES/
│   ├── premiere-project-template-LONGFORM.prproj      4K horizontal (Episode)
│   ├── premiere-project-template-SHORT.prproj         1080p vertical
│   ├── luts/                                          .cube color presets
│   │   ├── sai-interview-base.cube
│   │   └── nyc-street-warm.cube
│   ├── title-cards/                                   Intro/outro AE templates
│   ├── thumbnail-template.psd                         YouTube thumbnail PSD base
│   ├── lower-thirds/                                  Team/speaker title overlays
│   ├── sfx/                                           Go-to sound effects you reuse
│   └── music-license-tracker.md                       Which Artlist/Musicbed tracks you've used
│
├── 01_RAW_INCOMING/
│   └── YYYY-MM-DD/                                    One folder per shoot day
│       ├── a7IV_main/                                 Main camera card dump
│       ├── a7IV_b/                                    Second camera (if used)
│       ├── iphone/                                    iPhone shots, screen recordings
│       ├── audio/                                     External audio (Rode, lavs)
│       └── _NOTES.md                                  Day notes: what you shot, who's in it, issues
│
├── 02_ORGANIZED/
│   └── YYYY-MM-DD/                                    Footage Organizer output
│       ├── interview/                                 Talking head (Sai/Srikar direct-to-camera)
│       ├── broll_office/                              Office interior B-roll
│       ├── broll_nyc/                                 NYC street, skyline, walking
│       ├── meeting/                                   Real meetings, team moments
│       ├── screen_recording/                          Laptop/dashboard screen captures
│       ├── duo/                                       Shots with both brothers in frame
│       └── misc/                                      Anything that didn't auto-classify
│
├── 03_PROJECTS/
│   ├── episodes/                                      Long-form weekly show
│   │   └── E01_2026-04-15_Second-Agency-Before-22/    EP number_date_slug
│   │       ├── premiere/                              .prproj files + backup versions
│   │       │   ├── E01-v1.prproj
│   │       │   └── E01-v1 Auto-Save/
│   │       ├── selects/                               Chosen clips pulled from 02_ORGANIZED
│   │       ├── audio/                                 Music, VO, sound design
│   │       ├── graphics/                              Thumbnails, lower thirds, overlays
│   │       ├── exports/
│   │       │   ├── draft/                             Rough cuts for Sai review
│   │       │   │   └── E01-draft-v1.mp4
│   │       │   └── final/                             Shipped version
│   │       │       └── E01-final.mp4
│   │       ├── thumbnail/
│   │       │   ├── thumbnail.psd
│   │       │   └── thumbnail.jpg
│   │       └── _NOTES.md                              Script, shot list, Sai feedback, publish date
│   │
│   ├── shorts/                                        Daily short-form
│   │   └── Day001_2026-04-15_day1-of-building-trendify/
│   │       ├── premiere/
│   │       │   └── Day001.prproj
│   │       ├── selects/
│   │       ├── exports/
│   │       │   ├── TT/                                TikTok cut (15-30s, 1080x1920)
│   │       │   │   └── Day001-TT-final.mp4
│   │       │   ├── IG/                                Instagram Reels cut (30-60s, 1080x1920)
│   │       │   │   └── Day001-IG-final.mp4
│   │       │   └── YT/                                YouTube Shorts cut (60-90s, 1080x1920)
│   │       │       └── Day001-YT-final.mp4
│   │       └── _NOTES.md                              Hook used, format (1–9), post status
│   │
│   └── linkedin/                                      Daily LinkedIn images
│       └── 2026-04-15_linkedin/
│           ├── source.txt                             Sai's original post text
│           ├── reference/                             Any reference images / inspo
│           ├── working/                               Figma / Photoshop files
│           │   └── post-v2.psd
│           └── delivered.jpg                          What Sai posted
│
├── 04_DELIVERED/                                      BACKUP of everything published
│   ├── episodes/
│   │   └── E01_2026-04-22_Second-Agency-Before-22.mp4
│   ├── shorts/
│   │   ├── 2026-04-15_Day001_TT.mp4
│   │   ├── 2026-04-15_Day001_IG.mp4
│   │   └── 2026-04-15_Day001_YT.mp4
│   ├── linkedin/
│   │   └── 2026-04-15_linkedin.jpg
│   └── _DELIVERY_LOG.md                               Central log: what shipped when, which platforms, early metrics
│
├── 05_ARCHIVE/                                        Retired / old content
│   └── (move stuff here after ~3 months if not actively referenced)
│
├── 06_BROLL_LIBRARY/                                  Reusable B-roll across episodes
│   ├── nyc_skyline/
│   ├── nyc_street/
│   ├── office_interiors/
│   ├── sai_portraits/
│   ├── srikar_portraits/
│   ├── duo_shots/                                     Both brothers
│   ├── meetings/
│   ├── screen_recordings_trendify/                    Dashboards, client ads
│   ├── hands_typing/
│   └── _BROLL_INDEX.md                                Searchable list: what's in library
│
└── 07_ASSETS/
    ├── trendify_brand/                                Logos, colors, fonts (once Sai shares kit)
    ├── sai_brand/                                     If separate personal brand identity exists
    ├── fonts/
    ├── music/
    │   ├── artlist_downloads/
    │   └── musicbed_downloads/
    └── sfx_library/
```

---

## 2. Naming Conventions

Consistency = searchability. Lock these from Day 1.

### Dates
Always `YYYY-MM-DD` format. Sorts correctly alphabetically. Never `MM-DD-YYYY` or `4/15/26`.

### Day Counter (for the "Day X of Building Trendify" series)
`Day001`, `Day002`, …, `Day365`. Three digits. Sorts correctly.

### Episode Numbers
`E01`, `E02`, …, `E99`. Two digits. If you get past 99 episodes, upgrade to `E001`.

### Folder Name Pattern
`<Counter>_<Date>_<slug>/`
- ✅ `Day001_2026-04-15_day1-of-building-trendify/`
- ✅ `E01_2026-04-15_second-agency-before-22/`

### File Name Pattern (Final Deliverables)
`<Project>_<Platform>_<version>.<ext>`
- ✅ `Day001_TT_final.mp4`
- ✅ `Day001_IG_final.mp4`
- ✅ `E01_final.mp4`
- ✅ `2026-04-15_linkedin.jpg`

### Raw Footage Files — DON'T rename
Leave raw files with their camera-assigned names (e.g., `C0047.MP4`). Renaming breaks Premiere relink if you ever need to reimport. Just dump them into dated folders as-is.

### Slug Rules (for folder names)
- Lowercase
- Hyphens, not spaces
- Max 40 characters
- Descriptive, not cryptic
- ✅ `hot-take-on-creator-agencies`
- ❌ `HotTakeOnCreatorAgencies`
- ❌ `htoca`

### Platform Codes
- `TT` = TikTok
- `IG` = Instagram Reels
- `YT` = YouTube Shorts (or longform on the main episode files)
- `LI` = LinkedIn
- `FB` = Facebook (if applicable)

---

## 3. Daily Workflow (Every Shoot Day)

**End of shoot day, after returning from location:**

```
┌──────────────────────────────────────────────────────────┐
│ STEP 1 — Dump cards (10 min)                             │
│ Copy a7IV_main, a7IV_b, iphone cards into:              │
│ 01_RAW_INCOMING/2026-04-15/{camera_name}/                │
│ Create _NOTES.md with 3 lines about the day              │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 2 — Run Footage Organizer (auto, ~5-15 min)        │
│ python python-scripts/footage-organizer/main.py          │
│   G:/Sai/01_RAW_INCOMING/2026-04-15/                     │
│ Output dumps into G:/Sai/02_ORGANIZED/2026-04-15/        │
│ [Future v2: hand-symbol tags override content analysis]  │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 3 — Back up raw (overnight)                         │
│ Rclone / cloud sync or secondary SSD:                    │
│ 01_RAW_INCOMING/ → cold backup                           │
│ Only delete card after backup confirmed                  │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 4 — Pick today's short, start project (5 min setup) │
│ Create: 03_PROJECTS/shorts/Day001_2026-04-15_<slug>/    │
│ Copy relevant clips from 02_ORGANIZED into selects/     │
│ Duplicate SHORT template .prproj into premiere/         │
│ Open Premiere, start editing                             │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 5 — Edit + export (90 min target)                   │
│ Edit once, export 3x from same timeline:                 │
│ - TT/ (15-30s, 1080x1920)                               │
│ - IG/ (30-60s, 1080x1920)                               │
│ - YT/ (60-90s, 1080x1920)                               │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 6 — Publish + log (10 min)                          │
│ Post to each platform (manual or via scheduler)          │
│ Copy final files → 04_DELIVERED/shorts/                 │
│ Append entry to 04_DELIVERED/_DELIVERY_LOG.md            │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 7 — Stash reusable B-roll (5 min)                   │
│ Any great B-roll worth keeping? Copy into                │
│ 06_BROLL_LIBRARY/{category}/                             │
│ Update 06_BROLL_LIBRARY/_BROLL_INDEX.md                  │
└──────────────────────────────────────────────────────────┘
```

**Total time from shoot end to post published:** 90-120 min target, 60 min once you're in flow.

---

## 4. Weekly Workflow (Episode Ship Day)

**The long-form episode ships Tuesday of Week 2, then weekly. Plan:**

| Day | Action |
|---|---|
| Mon–Fri | Shoot Episode footage alongside shorts (see Week 1 plan in strategy doc) |
| Fri | Create `03_PROJECTS/episodes/E0X_date_slug/`, pull selects from the week's `02_ORGANIZED` folders |
| Fri–Sat | Edit rough cut in Premiere |
| Sat | Export draft to `exports/draft/`, send link to Sai |
| Sun | Incorporate Sai's feedback, finalize cut |
| Mon | Final export → `exports/final/`, thumbnail finalized |
| Tue | Publish to YouTube, copy to `04_DELIVERED/episodes/`, log in `_DELIVERY_LOG.md` |

---

## 5. Integration with Your Existing Tools

### Footage Organizer (`python-scripts/footage-organizer/`)
- **Input:** dump raw card footage into `01_RAW_INCOMING/YYYY-MM-DD/`
- **Run:** `python main.py G:/Sai/01_RAW_INCOMING/YYYY-MM-DD/`
- **Output:** organized clips land in `02_ORGANIZED/YYYY-MM-DD/` with content-based subfolders
- **v2 upgrade path** (per `python-scripts/footage-organizer/FUTURE_IDEAS.md`): hand-symbol tagging on last frame of each clip → more accurate categorization, cheaper (1 Vision call vs 4)

### Obsidian Vault (`Documents/Obsidian/Graydient Media/Content/Sai Karra/`)
- **Vault holds:** ideas, scripts, format plans, debrief notes, episode outlines
- **Drive holds:** actual footage, edits, exports
- **Cross-link them:** in each Premiere project folder's `_NOTES.md`, reference the Obsidian note: `See [[Inside Trendify E01]] in Obsidian`
- **Promoted video ideas in Obsidian** (e.g., `Content/Graydient Media/Editing Tips/30 Best Shortcuts for Premiere Pro.md`) → when you actually film one, the corresponding shoot day's `03_PROJECTS/.../` folder is where the files live

### Hook Optimizer (`python-scripts/hook-optimizer/`)
- Run BEFORE posting: `python main.py "day 1 of building trendify"`
- Generates title/hook/thumbnail variants
- Copy the chosen variants into the project's `_NOTES.md` for the record

### Social Media Analytics (`python-scripts/social-media-analytics/`)
- Weekly run, pulls performance data on Sai's accounts → Google Sheet
- Feeds into end-of-week iteration decisions

### Content Pipeline (`python-scripts/content-pipeline/`)
- Already has `--transcribe-only` mode (added 2026-04-14)
- Feed interview/monologue footage in → get transcript back → use in script drafting + captions

### Analytical (`web-apps/analytical/`)
- Deploy for Sai once accounts are set up safely (per `Social Media SaaS Vision`)
- Dashboard view of performance across platforms

---

## 6. Backup Strategy

**The 3-2-1 rule:** 3 copies of everything, 2 different media, 1 off-site.

| Tier | What | Where | Retention |
|---|---|---|---|
| **Primary** | Active projects + raw | `G:/Sai/` NVMe SSD (external) | Forever / until archived |
| **Secondary** | Same folder mirror | Second SSD / NAS / Time Machine | Always in sync |
| **Off-site** | Raw + delivered finals | Cloud (Backblaze, Wasabi, iCloud, Dropbox) | Forever |
| **Hot** | Most recent deliverables | Dropbox / Google Drive | 90 days |

**Specific recommendations:**
- **Raw footage:** Backblaze B2 is cheap ($6/TB/month). Set up a watch folder that uploads new `01_RAW_INCOMING/` files automatically.
- **Delivered finals:** Dropbox or Google Drive — 1TB is plenty, always accessible from any device
- **Premiere project files (.prproj):** iCloud or Dropbox for cross-machine work

**DON'T** rely on Creative Cloud alone to sync project files — it's slow + unreliable with big media libraries.

**Retention policy:**
- `01_RAW_INCOMING/YYYY-MM-DD/` → keep 30 days locally, then move to `05_ARCHIVE/` or cloud cold storage
- `03_PROJECTS/` → keep active ones on SSD, move to archive 60 days after ship
- `04_DELIVERED/` → keep forever (it's small)
- `06_BROLL_LIBRARY/` → grows forever — this is a long-term asset

---

## 7. The `_NOTES.md` File Convention

Every project folder has one. Kept lightweight. Sample:

```markdown
# Day 014 — "21 and running our biggest ad week ever"
Date filmed: 2026-04-28
Posted: 2026-04-28 | TT: [link] | IG: [link] | YT: [link]
Format: Format 3 (21 and…)

## Hook used
"21 and this is the biggest ad week we've ever had — $67K spent in 5 days."

## Notes
- Sai's energy was best in the office window shot, ep. 1
- Screen recording of the dashboard made the reveal work

## Metrics after 24h
TT: 12,340 views | IG: 3,410 views | YT: 810 views
```

This lets you scroll back in 3 months and remember WHY something worked.

---

## 8. The `_DELIVERY_LOG.md` File (Master Log)

One row per deliverable. At `04_DELIVERED/_DELIVERY_LOG.md`:

```markdown
| Date | Type | Project | Platform | Link | Day 7 Views |
|---|---|---|---|---|---|
| 2026-04-15 | Short | Day001 | TikTok | [link] | 8,210 |
| 2026-04-15 | Short | Day001 | Reels | [link] | 4,100 |
| 2026-04-15 | Short | Day001 | YT | [link] | 210 |
| 2026-04-15 | LinkedIn | 2026-04-15_linkedin | LI | [link] | — |
| 2026-04-16 | Short | Day002 | TikTok | [link] | 11,400 |
...
```

At end of each week, pull this into the end-of-week recap. This is the raw data that feeds your Week 2 iteration decision.

---

## 9. Cross-Machine Setup (Windows + Mac)

You work on Windows AND Mac. Paths differ. Handle it:

### Option A: External SSD (recommended)
- Samsung T7 Shield or SanDisk Extreme (USB-C, 2TB+)
- Format: **exFAT** (Windows + Mac both read/write; no individual file-size limit)
- On Windows it mounts as `G:/` (or whatever letter)
- On Mac it mounts as `/Volumes/Sai/`
- **The folder structure inside is identical regardless of OS**

### Option B: Cloud-synced folder
- Dropbox or iCloud — put `Sai/` inside
- Pros: automatic sync
- Cons: slower editing (SSD is faster), uses cloud bandwidth constantly
- Only do this if your edits are small-file (no 4K raw)

### Option C: Hybrid
- SSD for active `03_PROJECTS/` and `01_RAW_INCOMING/`
- Cloud for `04_DELIVERED/`, `06_BROLL_LIBRARY/`, `07_ASSETS/`

**My rec: Option A (external SSD).** Cross-machine, fast, reliable, cheap once you have one.

### Premiere Project File Handling
Premiere pins media paths absolutely. Opening a `.prproj` on a different machine with a different drive letter CAN cause "offline media" warnings. Fix:
- **Use "Project Manager"** (Premiere) to consolidate media relative to project folder before moving
- Or use the "Find Missing Media" dialog on first open

---

## 10. What to Do On Day 1 (Tomorrow)

Pre-shoot setup (do this tonight or before morning debrief):
- [ ] Create `G:/Sai/` (or wherever) with the full folder structure above
- [ ] Copy your Premiere templates (longform + short) into `00_TEMPLATES/`
- [ ] Copy any existing LUTs, fonts, SFX you use into the right subfolders of `00_TEMPLATES/` and `07_ASSETS/`
- [ ] Create `04_DELIVERED/_DELIVERY_LOG.md` with the header row above
- [ ] Create `06_BROLL_LIBRARY/_BROLL_INDEX.md` with a 2-line header
- [ ] Verify external SSD is exFAT formatted, both machines can read/write it

Day 1 first shoot:
- [ ] Create `01_RAW_INCOMING/2026-04-15/` folders for each camera
- [ ] Create `03_PROJECTS/shorts/Day001_2026-04-15_day1-of-building-trendify/`
- [ ] Film Format 4 short per Week 1 plan
- [ ] Run the daily workflow above
- [ ] Test: did Footage Organizer run successfully on the day's footage?

---

## 11. Script Helper: Folder Structure Creator

Drop this into a `.sh` (Mac) or `.ps1` (Windows) for one-time setup:

### Mac / WSL / Git Bash version (`create-sai-structure.sh`):
```bash
#!/bin/bash
ROOT="${1:-./Sai}"

mkdir -p "$ROOT"/{00_TEMPLATES/{luts,title-cards,lower-thirds,sfx},01_RAW_INCOMING,02_ORGANIZED,03_PROJECTS/{episodes,shorts,linkedin},04_DELIVERED/{episodes,shorts,linkedin},05_ARCHIVE,06_BROLL_LIBRARY/{nyc_skyline,nyc_street,office_interiors,sai_portraits,srikar_portraits,duo_shots,meetings,screen_recordings_trendify,hands_typing},07_ASSETS/{trendify_brand,sai_brand,fonts,music/{artlist_downloads,musicbed_downloads},sfx_library}}

# Seed empty log/index files
cat > "$ROOT/04_DELIVERED/_DELIVERY_LOG.md" <<'EOF'
# Sai Content — Delivery Log

| Date | Type | Project | Platform | Link | Day 7 Views |
|---|---|---|---|---|---|
EOF

cat > "$ROOT/06_BROLL_LIBRARY/_BROLL_INDEX.md" <<'EOF'
# B-Roll Library Index

Searchable list of reusable shots.
EOF

echo "Structure created at: $ROOT"
```

Run with: `bash create-sai-structure.sh /g/Sai` (adjust path as needed)

---

## 12. Gotchas + Pro Tips

- **Never edit in `01_RAW_INCOMING/`.** That's your source of truth. Always copy/link into a project folder.
- **Check storage weekly.** 4K footage grows fast (1 min 4K 60fps ≈ 1GB). Archive aggressively.
- **If a project folder crosses 100GB and you ship it,** compress to ZIP after moving to `05_ARCHIVE/`.
- **Version your exports.** `Day001-TT-v1.mp4`, `Day001-TT-v2.mp4`, `Day001-TT-final.mp4`. Never overwrite.
- **Date-rename if you forget slug.** Rename `Day001_2026-04-15_untitled/` to `Day001_2026-04-15_day1-of-building-trendify/` as soon as you know the slug. Past-you will thank present-you.
- **Hands-off the name of raw files.** If you rename them, Premiere relink breaks. Only rename exports.
- **One project folder = one shipping day's output.** Don't mix Day 1's short and Day 2's short in the same folder.

---

## 13. Relationship to Other Files in This Repo

- **Strategy plan:** `plans/2026-04-15-sai-debrief-content-strategy.md` — what content we're shooting
- **Research dossier:** `plans/2026-04-15-sai-debrief-research-deepdive.md` — why we're shooting what we're shooting
- **This doc:** `plans/2026-04-15-sai-footage-organization-system.md` — how we file what we shot
- **Footage Organizer:** `python-scripts/footage-organizer/` — the tool that pre-sorts raw footage
- **Footage Organizer v2 plan:** `python-scripts/footage-organizer/FUTURE_IDEAS.md` — hand-symbol tagging upgrade
- **Obsidian planning vault:** `~/Documents/Obsidian/Graydient Media/Content/Sai Karra/` — where ideas + scripts live

---

_Revise after Week 1 actual usage — the structure will need small adjustments once you feel the friction points in real shoots. Update in `plans/` OR promote to `workflows/sai-filming-workflow.md` once stabilized._
