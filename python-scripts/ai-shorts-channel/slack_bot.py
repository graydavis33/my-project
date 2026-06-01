"""
Slack Socket Mode bot for the ai-shorts pipeline.
Uses interactive buttons (same pattern as email-agent) so it works with the
existing Slack app configuration — no Slack app changes required.

Two approval gates:
  1. Script review — Approve / Request Changes (opens modal for feedback text)
  2. Video review  — Approve & Publish / Request Changes (same modal pattern)
"""

import json
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

# Callbacks registered by main.py
_on_script_response: callable = None
_on_video_response:  callable = None

# Action ID prefixes
_ACT_SCRIPT_APPROVE  = 'shorts_script_approve'
_ACT_SCRIPT_FEEDBACK = 'shorts_script_feedback'
_ACT_VIDEO_APPROVE   = 'shorts_video_approve'
_ACT_VIDEO_FEEDBACK  = 'shorts_video_feedback'
_VIEW_SCRIPT         = 'shorts_script_modal'
_VIEW_VIDEO          = 'shorts_video_modal'


# ─── Callback registration ────────────────────────────────────────────────────

def on_script_approval(callback):
    """callback(approved: bool, feedback: str | None)"""
    global _on_script_response
    _on_script_response = callback


def on_video_approval(callback):
    """callback(approved: bool, feedback: str | None)"""
    global _on_video_response
    _on_video_response = callback


# ─── Sending messages ─────────────────────────────────────────────────────────

def send_script_review(script_text: str):
    """Send script to Gray's DM with Approve / Request Changes buttons."""
    _web.chat_postMessage(
        channel=SLACK_USER_ID,
        text="Script ready — approve or request changes",
        blocks=[
            {
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': script_text},
            },
            {'type': 'divider'},
            {
                'type': 'actions',
                'elements': [
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': '✅  Approve Script'},
                        'style': 'primary',
                        'action_id': _ACT_SCRIPT_APPROVE,
                    },
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': '✏️  Request Changes'},
                        'action_id': _ACT_SCRIPT_FEEDBACK,
                    },
                ],
            },
        ],
    )


def send_video_review(private_url: str, youtube_title: str):
    """Send private YouTube link to Gray's DM with Approve / Request Changes buttons."""
    _web.chat_postMessage(
        channel=SLACK_USER_ID,
        text="Video ready — approve to publish or request changes",
        blocks=[
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': (
                        f"*Video ready for review:*\n"
                        f"*{youtube_title}*\n\n"
                        f"<{private_url}|Watch private preview on YouTube>\n\n"
                        f"_Watch the full video, then approve or describe what to change._"
                    ),
                },
            },
            {'type': 'divider'},
            {
                'type': 'actions',
                'elements': [
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': '🚀  Approve & Publish'},
                        'style': 'primary',
                        'action_id': _ACT_VIDEO_APPROVE,
                    },
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': '✏️  Request Changes'},
                        'action_id': _ACT_VIDEO_FEEDBACK,
                    },
                ],
            },
        ],
    )


def send_notification(text: str):
    _web.chat_postMessage(channel=SLACK_USER_ID, text=text)


# ─── Socket Mode event handlers ───────────────────────────────────────────────

def _handle_interactive(client: SocketModeClient, req: SocketModeRequest):
    if req.type != 'interactive':
        return

    client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

    payload = req.payload

    # ── Button clicks ──────────────────────────────────────────────────────────
    if payload.get('type') == 'block_actions':
        action     = payload['actions'][0]
        action_id  = action['action_id']
        trigger_id = payload.get('trigger_id')
        channel    = payload.get('channel', {}).get('id', SLACK_USER_ID)
        msg_ts     = payload.get('message', {}).get('ts')

        if action_id == _ACT_SCRIPT_APPROVE:
            _update_message(channel, msg_ts, "✅ Script approved — generating media assets...")
            _fire(_on_script_response, approved=True, feedback=None)

        elif action_id == _ACT_SCRIPT_FEEDBACK:
            _open_feedback_modal(trigger_id, _VIEW_SCRIPT, "Script feedback",
                                 "What would you like to change?", channel, msg_ts)

        elif action_id == _ACT_VIDEO_APPROVE:
            _update_message(channel, msg_ts, "🚀 Video approved — publishing to YouTube...")
            _fire(_on_video_response, approved=True, feedback=None)

        elif action_id == _ACT_VIDEO_FEEDBACK:
            _open_feedback_modal(trigger_id, _VIEW_VIDEO, "Video feedback",
                                 "What would you like to change? (e.g. 'swap story 2', 'too slow', 'redo script')",
                                 channel, msg_ts)

    # ── Modal submissions ──────────────────────────────────────────────────────
    elif payload.get('type') == 'view_submission':
        callback_id = payload['view']['callback_id']
        feedback    = (
            payload['view']['state']['values']
            ['feedback_block']['feedback_input']['value'] or ''
        ).strip()
        metadata = json.loads(payload['view'].get('private_metadata', '{}'))
        channel  = metadata.get('channel', SLACK_USER_ID)
        msg_ts   = metadata.get('msg_ts')

        if callback_id == _VIEW_SCRIPT:
            _update_message(channel, msg_ts, f"✏️ Script feedback received: _{feedback}_\nRevising...")
            _fire(_on_script_response, approved=False, feedback=feedback)

        elif callback_id == _VIEW_VIDEO:
            _update_message(channel, msg_ts, f"✏️ Video feedback received: _{feedback}_\nRebuilding...")
            _fire(_on_video_response, approved=False, feedback=feedback)


def _open_feedback_modal(trigger_id, callback_id, title, placeholder, channel, msg_ts):
    _web.views_open(
        trigger_id=trigger_id,
        view={
            'type': 'modal',
            'callback_id': callback_id,
            'title':  {'type': 'plain_text', 'text': title},
            'submit': {'type': 'plain_text', 'text': 'Send'},
            'close':  {'type': 'plain_text', 'text': 'Cancel'},
            'private_metadata': json.dumps({'channel': channel, 'msg_ts': msg_ts}),
            'blocks': [{
                'type': 'input',
                'block_id': 'feedback_block',
                'element': {
                    'type': 'plain_text_input',
                    'action_id': 'feedback_input',
                    'multiline': True,
                    'placeholder': {'type': 'plain_text', 'text': placeholder},
                },
                'label': {'type': 'plain_text', 'text': 'Your feedback'},
            }],
        },
    )


def _update_message(channel: str, ts: str, text: str):
    try:
        _web.chat_update(channel=channel, ts=ts, text=text, blocks=[])
    except Exception:
        _web.chat_postMessage(channel=SLACK_USER_ID, text=text)


def _fire(callback, approved: bool, feedback: str):
    if callback:
        threading.Thread(target=callback, args=(approved, feedback), daemon=True).start()
    else:
        log.warning("[slack] No callback registered for this response")


# ─── Listener ─────────────────────────────────────────────────────────────────

def start_listener():
    def run():
        while True:
            try:
                socket_client = SocketModeClient(app_token=SLACK_APP_TOKEN, web_client=_web)
                socket_client.socket_mode_request_listeners.append(_handle_interactive)
                socket_client.connect()
                log.info("[slack] Socket Mode connected")
                while socket_client.is_connected():
                    time.sleep(30)
                log.warning("[slack] Disconnected — reconnecting in 10s...")
            except Exception as e:
                log.error(f"[slack] Error: {e} — reconnecting in 10s...")
            time.sleep(10)

    threading.Thread(target=run, daemon=True).start()
    log.info("[slack] Listener thread started")
