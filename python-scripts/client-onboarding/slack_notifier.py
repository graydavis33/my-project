"""
slack_notifier.py
Sends a Slack DM notification when a new client is onboarded.
"""

from slack_sdk import WebClient
from config import SLACK_BOT_TOKEN, SLACK_USER_ID

_client = WebClient(token=SLACK_BOT_TOKEN)


def notify_new_client(details: dict):
    """Send a Slack DM with new client summary."""
    company_str = f" ({details['company']})" if details.get('company') else ""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🎉 New Client Onboarded!"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Client:*\n{details['client_name']}{company_str}"},
                {"type": "mrkdwn", "text": f"*Email:*\n{details['client_email']}"},
                {"type": "mrkdwn", "text": f"*Project:*\n{details['project_type']}"},
                {"type": "mrkdwn", "text": f"*Budget:*\n${details['budget']}"},
                {"type": "mrkdwn", "text": f"*Timeline:*\n{details['timeline']}"},
                {"type": "mrkdwn", "text": f"*Scope:*\n{details['scope']}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_Contract + brief emailed. Logged to Google Sheet._",
            },
        },
    ]
    _client.chat_postMessage(
        channel=SLACK_USER_ID,
        blocks=blocks,
        text=f"New client onboarded: {details['client_name']}",
    )
