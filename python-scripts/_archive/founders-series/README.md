# Founders Series — Debrief Generator

Auto-research a founder before you film them for Sai's Founders Series.

**What it does:** You paste a LinkedIn profile, run one command, and 1-2 minutes later you have a clean debrief markdown + 15-20 tailored interview questions saved on Google Drive.

---

## Folder Structure

Everything lives on Google Drive at:
```
My Drive/Founders Series/
├── _templates/           ← reusable templates (debrief, filming SOP)
└── founders/
    ├── 2026-week18-jane-doe/
    │   ├── linkedin.txt          ← you paste this manually
    │   ├── debrief.md            ← auto-generated
    │   ├── interview-questions.md ← auto-generated
    │   └── notes.md              ← your day-of notes
    └── ...
```

---

## First-Time Setup (only do this once)

Open Terminal and run:

```bash
cd ~/Desktop/my-project/python-scripts/founders-series
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

That's it. The Anthropic API key is already configured in `.env`.

---

## Running a Debrief — Step by Step

### Step 1: Get the founder's LinkedIn

1. Open the founder's LinkedIn profile in your browser
2. Select all the text on the page (Cmd+A, Cmd+C)
3. Decide their name + company name (e.g., "Jane Doe", "Acme Inc")

### Step 2: Run the script the first time

```bash
cd ~/Desktop/my-project/python-scripts/founders-series
source venv/bin/activate
python debrief.py "Jane Doe" "Acme Inc"
```

The script will create the founder's folder on Google Drive and tell you it needs the LinkedIn text.

### Step 3: Paste the LinkedIn text

The script will print a path like:
```
~/Library/CloudStorage/GoogleDrive-graydavis33@gmail.com/My Drive/Founders Series/founders/2026-week18-jane-doe/linkedin.txt
```

Open that file (it'll be on Google Drive — easiest is Finder → Google Drive → Founders Series → founders → [the new folder]) and paste the LinkedIn text into it. Save.

### Step 4: Run the script again

```bash
python debrief.py "Jane Doe" "Acme Inc"
```

This time it'll do the research (1-2 minutes) and save:
- `debrief.md` — full background research on the founder
- `interview-questions.md` — 15-20 tailored questions
- `notes.md` — empty file for your day-of notes

That's it. Open the folder, read the debrief, edit the questions if you want.

---

## What Gets Researched Automatically

- **Company info:** Crunchbase data, funding rounds, team size, investors, HQ
- **Recent news:** press, articles, interviews from the last 6-12 months
- **Podcast appearances:** any podcasts the founder has been on
- **Notable wins:** awards, viral moments, big customers
- **Notable failures:** prior startups, public setbacks, lessons learned
- **Story angles:** what's actually interesting about THIS founder

---

## Cost per Founder

About **$0.20-$0.50** per debrief (~5-8 web searches + Claude Sonnet 4.6).
At one founder per week, that's roughly $20/year. Cheap.

---

## Templates

Reusable templates live in `_templates/` on Google Drive:
- `debrief-template.md` — blank debrief structure (auto-filled by the script)
- `filming-sop.md` — Standard Operating Procedure for shoot day

Read `filming-sop.md` once before your next shoot. It's your day-of checklist.

---

## Troubleshooting

**"No ANTHROPIC_API_KEY found"** — the `.env` file is missing. Copy it from `~/Desktop/my-project/python-scripts/sai-linkedin/.env` (same key works).

**"linkedin.txt is empty"** — paste the LinkedIn profile text into the file and save before re-running.

**Script errors out mid-research** — re-run it. It's idempotent (won't double-create folders).

---

## Workflow at Scale

Once you're filming a new founder every week, the workflow is:

1. **Monday:** Pick the founder. Get their LinkedIn URL.
2. **Run the script.** Paste LinkedIn → run script. 2 minutes.
3. **Tuesday:** Read the debrief. Edit questions if needed.
4. **Wednesday/Thursday:** Film using the filming SOP as your day-of checklist.
5. **Friday:** Drop notes into `notes.md` while it's fresh.

That's the system.
