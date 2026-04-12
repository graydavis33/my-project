import os
from dotenv import load_dotenv

load_dotenv()

# ─── Slack ────────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_USER_ID   = os.getenv('SLACK_USER_ID')

# ─── APIs ─────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY    = os.getenv('ANTHROPIC_API_KEY')
HEYGEN_API_KEY       = os.getenv('HEYGEN_API_KEY')
HEYGEN_AVATAR_ID     = os.getenv('HEYGEN_AVATAR_ID')
ELEVENLABS_API_KEY   = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID  = os.getenv('ELEVENLABS_VOICE_ID')
PEXELS_API_KEY       = os.getenv('PEXELS_API_KEY')
NEWS_API_KEY         = os.getenv('NEWS_API_KEY')
YOUTUBE_API_KEY      = os.getenv('YOUTUBE_API_KEY')

# ─── Channel ──────────────────────────────────────────────────────────────────
CHANNEL_NAME = os.getenv('CHANNEL_NAME', 'Signal AI')

# ─── Pipeline ─────────────────────────────────────────────────────────────────
NUM_STORIES    = 3
POSTING_DAYS   = {'monday', 'wednesday', 'friday', 'sunday'}  # lowercase weekday names
MAX_SCRIPT_REVISIONS   = 3
MAX_VIDEO_REVISIONS    = 3

# Video timing (seconds) — script writer uses these word counts
HOOK_DURATION     = 5    # ~14 words at 170 wpm
STORY_DURATION    = 12   # ~34 words at 170 wpm
OUTRO_DURATION    = 4    # ~11 words at 170 wpm
VIDEO_TARGET_DURATION = HOOK_DURATION + (NUM_STORIES * STORY_DURATION) + OUTRO_DURATION  # ~45 sec

# Word targets for script writer (at 170 wpm / 2.8 wps)
HOOK_WORDS   = 14
STORY_WORDS  = 34
OUTRO_WORDS  = 11

# ─── Paths ────────────────────────────────────────────────────────────────────
import pathlib
BASE_DIR   = pathlib.Path(__file__).parent
TMP_DIR    = BASE_DIR / '.tmp'
OUTPUT_DIR = BASE_DIR / 'output'
ASSETS_DIR = BASE_DIR / 'assets'
MUSIC_DIR  = ASSETS_DIR / 'music'
FONTS_DIR  = ASSETS_DIR / 'fonts'
STATE_FILE = BASE_DIR / 'state.json'

# ─── YouTube ──────────────────────────────────────────────────────────────────
YT_OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
]
YT_TOKEN_FILE  = BASE_DIR / 'yt_token.json'
YT_SECRET_FILE = BASE_DIR / 'client_secret.json'

# ─── HeyGen ───────────────────────────────────────────────────────────────────
HEYGEN_API_BASE    = 'https://api.heygen.com'
HEYGEN_POLL_INTERVAL = 15  # seconds between status checks
HEYGEN_TIMEOUT     = 600   # max seconds to wait for video generation

# ─── ElevenLabs ───────────────────────────────────────────────────────────────
ELEVENLABS_API_BASE = 'https://api.elevenlabs.io/v1'
ELEVENLABS_MODEL    = 'eleven_multilingual_v2'

# ─── News sources ─────────────────────────────────────────────────────────────
NEWSAPI_SOURCES = 'techcrunch,wired,ars-technica,the-verge,reuters,bloomberg,bbc-technology'
REDDIT_SUBS     = ['artificial', 'MachineLearning', 'technology']
REDDIT_MIN_SCORE = 100  # Only posts with this many upvotes

# ─── Video ────────────────────────────────────────────────────────────────────
VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS    = 30
VIDEO_CRF    = 23      # FFmpeg quality (lower = better, larger file)
MUSIC_VOLUME = 0.12    # Background music volume relative to VO
