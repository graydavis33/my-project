"""
slack_bot.py
Handles all Slack interactions:
  - Sending draft notifications with Send / Edit / Skip buttons
  - Listening for button clicks via Socket Mode
  - Triggering Gmail send when user approves a draft
"""

import json
import threading
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_USER_ID

web_client = WebClient(token=SLACK_BOT_TOKEN)

# Stores pending drafts in memory: { action_id -> { email, draft, send_callback } }
pending_drafts = {}


def send_draft_notification(email, draft, send_callback):
    """
    Send a Slack DM to Gray with the draft and action buttons.
    send_callback(draft_text) is called when the user hits Send.
    """
    action_id = email["id"]
    pending_drafts[action_id] = {
        "email": email,
        "draft": draft,
        "send_callback": send_callback,
    }

    sender_name = email["from"].split("<")[0].strip() or email["from"]

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📬 Email needs a reply"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*From:*\n{email['from']}"},
                {"type": "mrkdwn", "text": f"*Subject:*\n{email['subject']}"},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Original message:*\n{email['body'][:400]}…"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Suggested reply:*\n```{draft}```"},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ Send"},
                    "style": "primary",
                    "action_id": f"send_{action_id}",
                    "value": action_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✏️ Edit & Send"},
                    "action_id": f"edit_{action_id}",
                    "value": action_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "❌ Skip"},
                    "style": "danger",
                    "action_id": f"skip_{action_id}",
                    "value": action_id,
                },
            ],
        },
    ]

    web_client.chat_postMessage(channel=SLACK_USER_ID, blocks=blocks, text="New email draft ready")


def handle_action(client: SocketModeClient, req: SocketModeRequest):
    """Process button clicks from Slack."""
    if req.type != "interactive":
        return

    client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

    payload = req.payload
    action = payload["actions"][0]
    action_id_full = action["action_id"]
    email_id = action["value"]
    channel = payload["channel"]["id"]
    message_ts = payload["message"]["ts"]

    if email_id not in pending_drafts:
        web_client.chat_postMessage(channel=channel, text="⚠️ This draft has already been handled.")
        return

    entry = pending_drafts.pop(email_id)

    if action_id_full.startswith("send_"):
        entry["send_callback"](entry["draft"])
        web_client.chat_update(
            channel=channel,
            ts=message_ts,
            text=f"✅ Reply sent to *{entry['email']['from']}*.",
            blocks=[],
        )

    elif action_id_full.startswith("edit_"):
        # Open a Slack modal for editing
        trigger_id = payload["trigger_id"]
        web_client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": f"submit_edit_{email_id}",
                "title": {"type": "plain_text", "text": "Edit your reply"},
                "submit": {"type": "plain_text", "text": "Send"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "private_metadata": json.dumps({
                    "email_id": email_id,
                    "channel": channel,
                    "message_ts": message_ts,
                    "email": entry["email"],
                    "send_callback_key": email_id,
                }),
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "reply_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "reply_text",
                            "multiline": True,
                            "initial_value": entry["draft"],
                        },
                        "label": {"type": "plain_text", "text": "Your reply"},
                    }
                ],
            },
        )
        # Re-add to pending so modal submit can find it
        pending_drafts[email_id] = entry

    elif action_id_full.startswith("skip_"):
        web_client.chat_update(
            channel=channel,
            ts=message_ts,
            text=f"❌ Skipped email from *{entry['email']['from']}*.",
            blocks=[],
        )


def handle_view_submission(client: SocketModeClient, req: SocketModeRequest):
    """Handle the Edit modal when user submits edited text."""
    if req.type != "interactive":
        return

    payload = req.payload
    if payload.get("type") != "view_submission":
        return

    client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

    callback_id = payload["view"]["callback_id"]
    if not callback_id.startswith("submit_edit_"):
        return

    metadata = json.loads(payload["view"]["private_metadata"])
    email_id = metadata["email_id"]
    channel = metadata["channel"]
    message_ts = metadata["message_ts"]

    edited_text = (
        payload["view"]["state"]["values"]["reply_block"]["reply_text"]["value"]
    )

    if email_id in pending_drafts:
        entry = pending_drafts.pop(email_id)
        entry["send_callback"](edited_text)
        web_client.chat_update(
            channel=channel,
            ts=message_ts,
            text=f"✅ Edited reply sent to *{entry['email']['from']}*.",
            blocks=[],
        )


def start_listener():
    """Start the Slack Socket Mode listener in a background thread."""
    socket_client = SocketModeClient(app_token=SLACK_APP_TOKEN, web_client=web_client)

    socket_client.socket_mode_request_listeners.append(handle_action)
    socket_client.socket_mode_request_listeners.append(handle_view_submission)

    def run():
        socket_client.connect()
        # Keep thread alive
        import time
        while True:
            time.sleep(1)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return socket_client
