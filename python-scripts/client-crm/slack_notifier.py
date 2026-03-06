"""
slack_notifier.py
Sends weekly CRM reminder to Slack.
"""

from slack_sdk import WebClient
from config import SLACK_BOT_TOKEN, SLACK_USER_ID

_client = WebClient(token=SLACK_BOT_TOKEN)


def send_reminder(blocks: list):
    _client.chat_postMessage(
        channel=SLACK_USER_ID,
        blocks=blocks,
        text="📋 Weekly CRM Reminder",
    )
