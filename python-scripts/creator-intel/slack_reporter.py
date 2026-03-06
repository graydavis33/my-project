"""
slack_reporter.py
Formats and sends the weekly creator intelligence report to Slack.
"""

from datetime import datetime
from slack_sdk import WebClient
from config import SLACK_BOT_TOKEN, SLACK_USER_ID

_client = WebClient(token=SLACK_BOT_TOKEN)


def send_report(report_text: str, creator_count: int, video_count: int):
    """Send the intelligence report as a Slack DM."""
    today = datetime.now().strftime("%B %-d, %Y")
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🧠 Creator Intel Report — {today}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"_Analyzed {video_count} videos from {creator_count} creators_",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": report_text},
        },
    ]

    _client.chat_postMessage(
        channel=SLACK_USER_ID,
        blocks=blocks,
        text=f"🧠 Creator Intel Report — {today}",
    )
