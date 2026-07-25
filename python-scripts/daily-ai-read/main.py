"""Daily AI Read — researches one AI topic and emails Gray a 5-10 minute cited read.

Runs daily via .github/workflows/daily-ai-read.yml. Topic history lives in
topics-log.json so subjects never repeat; each issue is archived to archive/.
"""

import base64
import json
import os
import sys
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

DIR = Path(__file__).parent
LOG_PATH = DIR / "topics-log.json"
ARCHIVE_DIR = DIR / "archive"
TO_ADDRESS = "graydavis33@gmail.com"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You write "Daily AI Read", a daily research-backed email that teaches Gray Davis about AI.

WHO GRAY IS: a freelance videographer and content creator (brand: Graydient Media) who works in
marketing/social media, edits in Adobe Premiere and CapCut, posts on Instagram/TikTok/X/YouTube,
and is a beginner coder who builds automation tools with Claude Code. He is smart but new to AI
and programming concepts — explain everything in plain English, define every technical term the
moment you use it, and use concrete analogies.

CONTENT MIX (balance across issues using the covered-topics log; never repeat a covered topic):
- Roughly 3 of every 5 issues: an AI FUNDAMENTALS deep-dive — how the technology actually works,
  core concepts and terms he keeps encountering as he builds with AI tools.
- Roughly 1 of 5: AI NEWS — what genuinely happened in AI in the last ~10 days: major model or
  feature launches, significant published research from large labs and corporations, real
  industry shifts. Prefer this category on days when something big actually happened.
- Roughly 1 of 5: INDUSTRY USE — how people in Gray's industry and adjacent ones (video
  production, editing, marketing, social media, content creation, solo business owners) are
  actually using AI in their work today, with real documented examples.
Pick the specific topic yourself — choose what is most valuable and current, not generic filler.

RESEARCH RULES:
- Use web search several times before writing. Verify claims across sources.
- Every substantive claim must be backed by a cited source, linked inline where the claim is made.
- Prefer primary sources: official documentation, company announcements, published research,
  reputable tech press. Never invent statistics. If evidence is mixed or disputed, say so plainly.
- No hype. Straight talk about what is real, what is marketing, and what is still unknown.

LENGTH: 1,100-1,800 words (a 5-10 minute read).

OUTPUT FORMAT — follow exactly:
TITLE: <honest, curiosity-driving subject line, under 70 characters>
CATEGORY: <fundamentals | news | industry>
TOPIC: <short-kebab-slug-for-the-log>
===HTML===
<the full email body as HTML>

HTML SPEC: mobile-first single column, max-width 600px centered, inline CSS only, dark text
(#1a1a1a) on white, font-family -apple-system system stack, 17px body text with 1.6 line height.
Structure: a 1-2 sentence hook paragraph; a light-grey rounded "The 2-minute version" TL;DR box
with 3-5 bullet takeaways; the main explanation in scannable sections with bold h2 headers;
a "Why this matters for you" section connecting it to video/content/marketing work; a
"Try this today" box with one concrete 5-minute action; a numbered "Sources" list of links at
the end. Links underlined, color #1a56db. No images, no emojis."""


def load_log():
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text())
    return []


def generate_issue(log):
    client = anthropic.Anthropic()
    issue_num = len(log) + 1
    user_msg = (
        f"Today is {date.today().isoformat()}. Write issue #{issue_num}.\n\n"
        f"Covered topics so far (do not repeat any of these):\n"
        f"{json.dumps(log, indent=1) if log else '(none yet — this is the first issue)'}"
    )
    messages = [{"role": "user", "content": user_msg}]
    while True:
        with client.messages.stream(
            model=MODEL,
            max_tokens=24000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}],
            messages=messages,
        ) as stream:
            response = stream.get_final_message()
        if response.stop_reason != "pause_turn":
            break
        messages = [{"role": "user", "content": user_msg},
                    {"role": "assistant", "content": response.content}]
    text = "".join(b.text for b in response.content if b.type == "text")
    head, _, html = text.partition("===HTML===")
    meta = {}
    for line in head.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip().upper()] = val.strip()
    if not html.strip() or "TITLE" not in meta:
        raise RuntimeError(f"unexpected model output format:\n{text[:500]}")
    return issue_num, meta, html.strip()


def send_email(subject, html):
    raw = os.environ.get("GMAIL_SEND_TOKEN_JSON")
    if raw:
        creds = Credentials.from_authorized_user_info(json.loads(raw))
    else:
        creds = Credentials.from_authorized_user_file(DIR / "token.json")
    if not creds.valid:
        creds.refresh(Request())
    service = build("gmail", "v1", credentials=creds)
    msg = MIMEText(html, "html")
    msg["to"] = TO_ADDRESS
    msg["subject"] = subject
    body = {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    service.users().messages().send(userId="me", body=body).execute()


def main():
    log = load_log()
    issue_num, meta, html = generate_issue(log)
    title = meta["TITLE"]

    ARCHIVE_DIR.mkdir(exist_ok=True)
    archive_file = ARCHIVE_DIR / f"{date.today().isoformat()}-{meta.get('TOPIC', 'issue')}.html"
    archive_file.write_text(html)

    if "--no-email" not in sys.argv:
        send_email(f"Daily AI Read #{issue_num} — {title}", html)

    log.append({
        "date": date.today().isoformat(),
        "issue": issue_num,
        "title": title,
        "category": meta.get("CATEGORY", ""),
        "topic": meta.get("TOPIC", ""),
    })
    LOG_PATH.write_text(json.dumps(log, indent=1))
    print(f"Issue #{issue_num} [{meta.get('CATEGORY')}] {title} -> {archive_file.name}")


if __name__ == "__main__":
    main()
