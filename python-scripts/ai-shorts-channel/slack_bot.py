"""
Slack Socket Mode bot for the ai-shorts pipeline.
Listens for Gray's DM replies to advance or revise the pipeline.

Two approval gates:
  1. Script review — Gray replies "approve" or gives feedback
  2. Video review  — Gray replies "approve" or gives feedback

Runs in a persistent background thread alongside main.py.
"""

import time
import threading
import logging
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_USER_ID

log = logging.getLogger(__name__)
_web = WebClient(token=SLACK_BOT_TOKEN)

# Callback registered by main.py — called when Gray approves/rejects
_on_script_response: callable = None
_on_video_response:  callable = None


# ─── Public: register callbacks ───────────────────────────────────────────────

def on_script_approval(callback: callable):
    """callback(approved: bool, feedback: str | None)"""
    global _on_script_response
    _on_script_response = callback


def on_video_approval(callback: callable):
    """callback(approved: bool, feedback: str | None)"""
    global _on_video_response
    _on_video_response = callback


# ─── Sending messages ─────────────────────────────────────────────────────────

def send_message(text: str, blocks: list = None):
    """Send a DM to Gray."""
    _web.chat_postMessage(
        channel=SLACK_USER_ID,
        text=text,
        blocks=blocks,
    )


def send_script_review(script_text: str):
    """Send script for Gray's review with clear instructions."""
    send_message(
        text="Script ready for review — reply `approve` or give feedback",
        blocks=[
            {
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': script_text},
            },
        ],
    )


def send_video_review(private_url: str, youtube_title: str):
    """Send private YouTube link for Gray's review."""
    send_message(
        text=f"Video ready for review — reply `approve` to publish, or describe what to fix",
        blocks=[
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': (
                        f"*Video ready to review:*\n"
                        f"*{youtube_title}*\n\n"
                        f"<{private_url}|Watch private preview on YouTube>\n\n"
                        f"Reply `approve` to publish, or describe what to change."
                    ),
                },
            },
        ],
    )


def send_notification(text: str):
    """Send a simple status notification."""
    send_message(text)


# ─── Socket Mode listener ─────────────────────────────────────────────────────

def _handle_event(client: SocketModeClient, req: SocketModeRequest):
    client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

    if req.type != 'events_api':
        return

    event = req.payload.get('event', {})
    if event.get('type') != 'message':
        return
    if event.get('subtype'):
        return  # Ignore bot messages, edits, etc.
    if event.get('user') != SLACK_USER_ID:
        return  # Only care about Gray's messages
    if event.get('channel_type') not in ('im', 'mpim'):
        return  # Only DMs

    text = (event.get('text') or '').strip()
    if not text:
        return

    approved = text.lower() in ('approve', 'approved', 'yes', 'ok', '✅', 'looks good')
    feedback = None if approved else text

    log.info(f"[slack] Gray replied: '{text[:80]}' | approved={approved}")

    # Route to the correct callback in a non-blocking thread
    if _on_script_response:
        threading.Thread(
            target=_on_script_response,
            args=(approved, feedback),
            daemon=True,
        ).start()
        return

    if _on_video_response:
        threading.Thread(
            target=_on_video_response,
            args=(approved, feedback),
            daemon=True,
        ).start()


def start_listener():
    """Start the Slack Socket Mode listener in a persistent background thread."""
    def run():
        while True:
            try:
                socket_client = SocketModeClient(
                    app_token=SLACK_APP_TOKEN,
                    web_client=_web,
                )
                socket_client.socket_mode_request_listeners.append(_handle_event)
                socket_client.connect()
                log.info("[slack] Socket Mode connected")
                while socket_client.is_connected():
                    time.sleep(30)
                log.warning("[slack] Socket Mode disconnected — reconnecting in 10s...")
            except Exception as e:
                log.error(f"[slack] Listener error: {e} — reconnecting in 10s...")
            time.sleep(10)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    log.info("[slack] Listener thread started")
