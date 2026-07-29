"""Daily AI Read — researches one AI topic and emails Gray a 5-10 minute cited read.

Runs daily via .github/workflows/daily-ai-read.yml. Topic history lives in
topics-log.json so subjects never repeat; each issue is archived to archive/.
"""

import base64
import json
import os
import re
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
and programming concepts — define every technical term the moment you use it, use concrete
analogies, and write at a 10th-grade reading level (short sentences, everyday words, no fluff).

CONTENT MIX (balance across issues using the covered-topics log; never repeat a covered topic):
- Roughly 2 of every 5 issues: an AI FUNDAMENTALS explainer — how the technology actually works,
  core concepts and terms he keeps encountering as he builds with AI tools.
- Roughly 2 of 5: REAL-WORLD USE — how real people and companies in Gray's world use AI today,
  with documented examples and specific tools/workflows. Rotate across: content creation
  (scripting, ideation, thumbnails, captions), video production and editing (auto-editing,
  color, audio cleanup, VFX, transcription), and analytics/growth (audience data, A/B testing,
  performance prediction, social media automation).
- Roughly 1 of 5: AI NEWS — what genuinely happened in AI in the last ~10 days: major model or
  feature launches, significant research from big labs and corporations, real industry shifts.
  Prefer this category on days when something big actually happened.
Pick the specific topic yourself — choose what is most valuable and current, not generic filler.
Even in fundamentals issues, include at least one real-world example from content creation,
production, or analytics.

RESEARCH RULES:
- Use web search several times before writing. Verify claims across sources.
- Every substantive claim must be backed by a cited source, linked inline where the claim is made.
- Prefer primary sources: official documentation, company announcements, published research,
  reputable tech press. Never invent statistics. If evidence is mixed or disputed, say so plainly.
- No hype. Straight talk about what is real, what is marketing, and what is still unknown.

LENGTH: 700-1,100 words for the article body (tight, zero filler — every paragraph teaches
something), plus the 10-question quiz described below.

OUTPUT FORMAT — follow exactly:
TITLE: <honest, curiosity-driving subject line, under 70 characters>
CATEGORY: <fundamentals | industry | news>
TOPIC: <short-kebab-slug-for-the-log>
===HTML===
<div ...>  <- the email body. Start IMMEDIATELY with the opening <div> tag. No markdown code
fences, no commentary, no notes, no text of any kind outside the HTML. Everything the reader
sees must be inside the designed page.

HTML SPEC — professional, clean, editorial look. Mobile-first single column, max-width 600px
centered, inline CSS only, font-family -apple-system system stack. Outer wrapper: white card
(#ffffff) with border-radius 12px, 1px solid #e5e7eb border, 32px padding, on a #f3f4f6 page
background, generous whitespace throughout. Text #111827, 16px, line-height 1.65.

Structure, in order:
1. Masthead: "DAILY AI READ" in 12px letter-spaced uppercase #6b7280, with "Issue #N · <date>"
   on the same line, thin bottom border.
2. Title as a 26px bold h1, then a 1-2 sentence hook paragraph in #4b5563.
3. "THE 2-MINUTE VERSION" box: #f9fafb background, 8px radius, 3-5 short bullet takeaways.
4. The article in scannable sections with 19px bold h2 headers and a thin divider above each.
5. "WHY THIS MATTERS FOR YOU" section tying it to video/content/marketing work with a concrete
   real-world scenario.
6. "TRY THIS TODAY" box (same style as the 2-minute box): one 5-minute action.
7. "TEST YOURSELF" section: exactly 10 numbered questions covering the article. Format each as
   its own block: the question in bold, then immediately below it an indented answer panel
   (#f9fafb background, 3px solid #d1d5db left border, 12px padding) beginning with
   "Answer:" in bold followed by the answer and a 1-2 sentence explanation of WHY, so the
   reader learns from checking themselves. Mix recall questions with applied "what would you
   do" questions.
8. "SOURCES" as a numbered list of links, 14px.
Links #1d4ed8, underlined. No images, no emojis."""


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
    # Keep strictly the HTML: drop markdown fences, stray notes, or citation text
    # the model may emit around it — only the first "<" through the last ">" survives.
    html = html.replace("```html", "").replace("```", "")
    start, end = html.find("<"), html.rfind(">")
    if start == -1 or end == -1 or "TITLE" not in meta:
        raise RuntimeError(f"unexpected model output format:\n{text[:500]}")
    return issue_num, meta, html[start:end + 1]


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
