"""
State machine for the pipeline. One video-in-progress per posting day.
State persists across restarts via state.json.
"""

import json
import os
from datetime import datetime
from config import STATE_FILE

# ─── Stage enum ───────────────────────────────────────────────────────────────
IDLE                     = 'IDLE'
NEWS_COLLECTED           = 'NEWS_COLLECTED'
SCRIPT_READY             = 'SCRIPT_READY'
AWAITING_SCRIPT_APPROVAL = 'AWAITING_SCRIPT_APPROVAL'
SCRIPT_APPROVED          = 'SCRIPT_APPROVED'
VOICEOVER_DONE           = 'VOICEOVER_DONE'
AVATAR_DONE              = 'AVATAR_DONE'
BROLL_DONE               = 'BROLL_DONE'
VIDEO_ASSEMBLED          = 'VIDEO_ASSEMBLED'
UPLOADED_PRIVATE         = 'UPLOADED_PRIVATE'
AWAITING_VIDEO_APPROVAL  = 'AWAITING_VIDEO_APPROVAL'
VIDEO_APPROVED           = 'VIDEO_APPROVED'
PUBLISHED                = 'PUBLISHED'
FAILED                   = 'FAILED'

TERMINAL_STAGES = {PUBLISHED, FAILED}
APPROVAL_STAGES = {AWAITING_SCRIPT_APPROVAL, AWAITING_VIDEO_APPROVAL}

# ─── Load / save ──────────────────────────────────────────────────────────────

def load_state():
    if not STATE_FILE.exists():
        return _blank_state()
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return _blank_state()


def save_state(updates: dict):
    state = load_state()
    state.update(updates)
    state['updated_at'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    return state


def reset_state():
    state = _blank_state()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    return state


def get_stage():
    return load_state().get('stage', IDLE)


def set_stage(stage: str):
    save_state({'stage': stage})


def is_in_approval_gate():
    return get_stage() in APPROVAL_STAGES


def is_idle_or_done():
    stage = get_stage()
    return stage in (IDLE, PUBLISHED, FAILED)


def record_feedback(feedback: str):
    state = load_state()
    history = state.get('feedback_history', [])
    history.append({'text': feedback, 'at': datetime.now().isoformat()})
    save_state({'feedback_history': history})


def _blank_state():
    return {
        'stage': IDLE,
        'date': None,
        'raw_stories': [],
        'script': None,
        'script_revision': 0,
        'voiceover_paths': {},    # {story_index: path}
        'hook_video_path': None,
        'outro_video_path': None,
        'broll_paths': {},        # {story_index: {video: path, screenshot: path}}
        'assembled_video_path': None,
        'youtube_video_id': None,
        'youtube_private_url': None,
        'video_revision': 0,
        'feedback_history': [],
        'slack_message_ts': None,
        'updated_at': None,
    }
