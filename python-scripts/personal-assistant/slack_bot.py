"""
slack_bot.py
Handles all Slack I/O for the Personal Assistant:
  - Socket Mode listener for incoming DMs (Gray messages from phone or desktop)
  - send_message() helper for all outbound messages
"""

import logging
import threading
import time

from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_USER_ID

log = logging.getLogger(__name__)

web_client = WebClient(token=SLACK_BOT_TOKEN)


def send_message(text: str, channel: str = None):
    """Send a plain-text DM to Gray (or any channel if specified)."""
    target = channel or SLACK_USER_ID
    try:
        web_client.chat_postMessage(channel=target, text=text)
    except Exception as e:
        log.error(f"Failed to send Slack message: {e}")


def _handle_message(client: SocketModeClient, req: SocketModeRequest):
    """Handle incoming DM messages from Gray."""
    if req.type != "events_api":
        return

    # Acknowledge receipt immediately (Slack requires this within 3 seconds)
    client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

    event = req.payload.get("event", {})

    # Only handle direct messages (im channel type)
    if event.get("type") != "message":
        return

    # Ignore bot messages (including our own replies)
    if event.get("bot_id") or event.get("subtype"):
        return

    # Only respond to messages from Gray
    if event.get("user") != SLACK_USER_ID:
        return

    text = event.get("text", "").strip()
    channel = event.get("channel")

    if not text:
        return

    log.info(f"Received Slack message: '{text[:80]}'")

    # Acknowledge immediately so Gray knows we got it
    send_message("Got it, thinking...", channel=channel)

    # Process in a background thread so we don't block the Socket Mode listener
    def process():
        try:
            from dispatcher import handle_message
            reply = handle_message(text)
            send_message(reply, channel=channel)
        except Exception as e:
            log.exception("Error handling message")
            send_message(f"Something went wrong: {e}", channel=channel)

    threading.Thread(target=process, daemon=True).start()


def start_listener():
    """Start the Slack Socket Mode listener in a background thread with auto-reconnect."""

    def run():
        while True:
            try:
                socket_client = SocketModeClient(
                    app_token=SLACK_APP_TOKEN,
                    web_client=web_client,
                )
                socket_client.socket_mode_request_listeners.append(_handle_message)
                socket_client.connect()
                log.info("Slack Socket Mode connected.")
                # Keep alive — reconnect if connection drops
                while socket_client.is_connected():
                    time.sleep(30)
                log.warning("Slack Socket Mode disconnected. Reconnecting in 10s...")
            except Exception as e:
                log.error(f"Slack listener error: {e}. Reconnecting in 10s...")
            time.sleep(10)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
