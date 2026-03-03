"""
voice_analyzer.py
Analyzes Gray's sent emails to build a personal voice profile.
The profile is saved to voice_profile.txt and loaded by drafter.py
so every draft sounds like Gray wrote it himself.
"""

import os
import anthropic
from config import ANTHROPIC_API_KEY
from gmail_client import get_gmail_service, fetch_sent_emails

VOICE_PROFILE_PATH = os.path.join(os.path.dirname(__file__), "voice_profile.txt")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def build_voice_profile():
    """
    Fetch sent emails, analyze writing style with Claude,
    and save the profile to voice_profile.txt.
    """
    print("  Analyzing your sent emails to learn your writing style...")

    service = get_gmail_service()
    sent_emails = fetch_sent_emails(service, count=25)

    if not sent_emails:
        print("  No sent emails found. Using default tone.")
        return None

    print(f"  Found {len(sent_emails)} sent emails to analyze.")

    # Build a combined sample of sent emails for Claude to analyze
    samples = ""
    for i, email in enumerate(sent_emails[:20], 1):
        body = email["body"].strip()[:600]
        if body:
            samples += f"\n--- Email {i} (To: {email['to']}, Subject: {email['subject']}) ---\n{body}\n"

    prompt = f"""Analyze the following emails written by Gray Davis and create a detailed writing style profile.

Focus on:
- Tone (formal vs casual, warm vs direct)
- Sentence length and structure
- How he opens emails (does he use greetings? Which ones?)
- How he closes emails (sign-offs, phrases he uses)
- Vocabulary choices (simple vs complex words)
- Punctuation habits (exclamation points, ellipses, etc.)
- Any recurring phrases or expressions
- Overall personality that comes through

Write the profile as a set of clear instructions that an AI could follow to mimic his exact style.
Be specific with examples where possible.

Here are Gray's sent emails:
{samples}

Write the style profile now:"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    profile = response.content[0].text.strip()

    with open(VOICE_PROFILE_PATH, "w") as f:
        f.write(profile)

    print("  Voice profile saved.")
    return profile


def load_voice_profile():
    """Load the saved voice profile, or return None if it doesn't exist."""
    if os.path.exists(VOICE_PROFILE_PATH):
        with open(VOICE_PROFILE_PATH, "r") as f:
            return f.read()
    return None


def refresh_voice_profile():
    """Force a fresh analysis even if a profile already exists."""
    if os.path.exists(VOICE_PROFILE_PATH):
        os.remove(VOICE_PROFILE_PATH)
    return build_voice_profile()
