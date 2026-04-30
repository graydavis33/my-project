"""
Founders Series — Debrief Generator
Auto-research a founder + generate interview questions for Sai's Founders Series.

Usage:
    python debrief.py "Founder Name" "Company Name"

Workflow:
    1. Reads linkedin.txt from the founder's folder (you paste manually)
    2. Uses Claude with web search to research Crunchbase, news, podcasts
    3. Generates debrief.md + interview-questions.md in the folder
"""

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

GDRIVE_BASE = Path.home() / "Library/CloudStorage/GoogleDrive-graydavis33@gmail.com/My Drive/Founders Series"
FOUNDERS_DIR = GDRIVE_BASE / "founders"
TEMPLATES_DIR = GDRIVE_BASE / "_templates"

MODEL = "claude-sonnet-4-6"


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def find_or_create_folder(founder_name: str) -> Path:
    """Find an existing folder for the founder, or create a new one with this week's date."""
    slug = slugify(founder_name)
    if FOUNDERS_DIR.exists():
        for existing in FOUNDERS_DIR.iterdir():
            if existing.is_dir() and slug in existing.name:
                return existing
    today = dt.date.today()
    year, week, _ = today.isocalendar()
    folder_name = f"{year}-week{week:02d}-{slug}"
    new_folder = FOUNDERS_DIR / folder_name
    new_folder.mkdir(parents=True, exist_ok=True)
    return new_folder


def read_linkedin(folder: Path) -> str:
    """Read the manually-pasted LinkedIn profile text."""
    linkedin_file = folder / "linkedin.txt"
    if not linkedin_file.exists():
        print(f"\n⚠️  No linkedin.txt found in {folder}")
        print("Please paste the founder's LinkedIn profile text into:")
        print(f"  {linkedin_file}")
        print("Then re-run this script.\n")
        linkedin_file.touch()
        sys.exit(1)
    text = linkedin_file.read_text().strip()
    if not text:
        print(f"\n⚠️  linkedin.txt is empty: {linkedin_file}")
        print("Paste the LinkedIn profile text into it, then re-run.\n")
        sys.exit(1)
    return text


def build_research_prompt(founder: str, company: str, linkedin: str) -> str:
    return f"""You are a research assistant for "Founders Series" — a video interview series \
in the style of MTV Cribs meets School of Hard Knocks. The host (Sai) interviews founders \
and CEOs in their offices, blending an office tour with a deep career conversation.

Your job: research the founder below and produce TWO things:
1. A founder debrief (markdown)
2. A list of 15-20 tailored interview questions (markdown)

## FOUNDER
Name: {founder}
Company: {company}

## LINKEDIN PROFILE (provided manually)
{linkedin}

## RESEARCH STEPS
Use the web_search tool to gather:
- Company info: Crunchbase data (funding, team size, founded date, investors, HQ)
- Recent news: press, articles, interviews from the last 6-12 months
- Podcast appearances: any podcasts the founder has been on
- Notable wins: awards, viral moments, major customers, exits
- Notable failures or pivots: prior startups that failed, public setbacks
- Anything interesting or unique about this founder's story

Aim for 5-8 web searches total. Prioritize quality over quantity.

## OUTPUT FORMAT
Output EXACTLY two markdown sections, separated by the line "---DEBRIEF-END---":

### Section 1: Debrief
Use this template structure:

# Founder Debrief — {founder}

> Auto-generated on {dt.date.today().isoformat()} for Founders Series
> Company: **{company}**

## Quick Facts
- **Age:** (estimate from LinkedIn if not stated)
- **Hometown / Where from:**
- **College:**
- **Current Role:**
- **Years in industry:**

## Company Snapshot
- **Company:** {company}
- **Founded:**
- **Industry / Niche:**
- **Team size:**
- **Total funding raised:**
- **Latest round:**
- **Notable investors:**
- **HQ Location:**

## Career Path
(Bullets — high level only.)

## Notable Wins
(Press, awards, big customers.)

## Notable Failures / Lessons
(The "school of hard knocks" angle.)

## Recent News & Press
(Last 6-12 months. Include source + date + 1-line summary.)

## Talking Points (the good stuff)
(What's actually interesting about THIS founder. Story angles to dig into.)

## Things to Ask About
(Specific moments or claims worth asking the founder to elaborate on.)

## Red Flags / Avoid
(Sensitive topics, lawsuits, controversies — handle carefully.)

## Sources
(Bullet list of URLs used.)

---DEBRIEF-END---

### Section 2: Interview Questions

# Interview Questions — {founder}

> 15-20 questions in MTV Cribs meets School of Hard Knocks tone.
> Mix of standard backbone (origin, money, lessons) + custom questions \
based on this specific founder's story.

## Backbone Questions (always ask)
1. ...

## Custom Questions (founder-specific)
6. ...

## Office Tour Prompts ("Cribs"-style)
(Things to ask while walking through the office.)

## Wildcard / Closer
(One or two off-the-wall questions to end on.)

Begin research now."""


def generate_debrief(founder: str, company: str, linkedin: str) -> str:
    """Run Claude with web search to generate the debrief."""
    load_dotenv(Path.home() / "Desktop/my-project/python-scripts/founders-series/.env")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  No ANTHROPIC_API_KEY found in .env file.")
        print("Create python-scripts/founders-series/.env with:")
        print("  ANTHROPIC_API_KEY=your-key-here\n")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_research_prompt(founder, company, linkedin)

    print(f"\n🔍 Researching {founder} ({company})... this takes 1-2 minutes.\n")

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": prompt}],
    )

    while response.stop_reason == "pause_turn":
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.content},
            ],
        )

    full_text = ""
    for block in response.content:
        if block.type == "text":
            full_text += block.text

    return full_text


def split_output(full_text: str) -> tuple[str, str]:
    """Split Claude's output into debrief + questions."""
    sep = "---DEBRIEF-END---"
    if sep not in full_text:
        return full_text, ""
    parts = full_text.split(sep, 1)
    return parts[0].strip(), parts[1].strip()


def main():
    parser = argparse.ArgumentParser(description="Generate a founder debrief.")
    parser.add_argument("founder", help='Founder name, e.g., "Jane Doe"')
    parser.add_argument("company", help='Company name, e.g., "Acme Inc"')
    args = parser.parse_args()

    print(f"📁 Setting up folder for {args.founder}...")
    folder = find_or_create_folder(args.founder)
    print(f"   {folder}")

    linkedin = read_linkedin(folder)
    print(f"✅ Read LinkedIn ({len(linkedin)} chars)")

    full_text = generate_debrief(args.founder, args.company, linkedin)
    debrief, questions = split_output(full_text)

    debrief_file = folder / "debrief.md"
    questions_file = folder / "interview-questions.md"

    debrief_file.write_text(debrief)
    print(f"✅ Saved: {debrief_file}")

    if questions:
        questions_file.write_text(questions)
        print(f"✅ Saved: {questions_file}")
    else:
        print("⚠️  No question section found — check debrief.md for full output.")

    notes_file = folder / "notes.md"
    if not notes_file.exists():
        notes_file.write_text(
            f"# Notes — {args.founder}\n\n"
            "Use this file for day-of-shoot notes, post-shoot debriefs, "
            "memorable quotes, anything off-script.\n"
        )
        print(f"✅ Created: {notes_file}")

    print(f"\n🎉 Done! Open the folder:\n   {folder}\n")


if __name__ == "__main__":
    main()
