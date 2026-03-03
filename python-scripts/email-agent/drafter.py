"""
drafter.py
Uses Claude AI to write a draft reply for emails that need a response.
Tone is based on Gray's actual writing style, learned from his sent emails.
Falls back to a friendly/professional blend if no voice profile exists yet.
"""

import anthropic
from config import ANTHROPIC_API_KEY
from voice_analyzer import load_voice_profile

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

DEFAULT_STYLE = """Write in a tone that is friendly and warm, but professional and concise.
Conversational — not stiff or corporate. Genuine — sounds like a real person, not a robot.
Keep replies focused and on-topic."""


def get_system_prompt():
    """Build the system prompt using Gray's voice profile if available."""
    voice_profile = load_voice_profile()

    if voice_profile:
        style_instructions = f"""You have analyzed Gray's past emails and learned his exact writing style.
Here is his voice profile — follow it precisely:

{voice_profile}"""
    else:
        style_instructions = DEFAULT_STYLE

    return f"""You are writing email replies on behalf of Gray Davis, a social media marketer
who works with small businesses, agencies, and content creators in the videography/video editing space.

{style_instructions}

Rules:
- Do NOT include a subject line
- Do NOT include "Dear [name]" — start directly with the reply content
- Sign off naturally in Gray's style followed by "Gray"
- Keep replies focused and on-topic
- If you're unsure about specific details (pricing, dates, etc.), leave a [placeholder] so Gray can fill it in"""


def write_draft(email):
    """
    Write a draft reply for the given email.
    Returns the draft body as a string.
    """
    system_prompt = get_system_prompt()

    user_message = f"""Write a reply to this email on behalf of Gray Davis.

Original email:
From: {email['from']}
Subject: {email['subject']}

{email['body'][:3000]}

Write only the reply body. No subject line. Start directly with the response."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text.strip()
