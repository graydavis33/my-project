"""
Automated setup for the AI Shorts Channel.

Run this AFTER filling in .env with your API keys.
It will: install dependencies, install Playwright, verify FFmpeg,
run YouTube OAuth, validate all API connections, and set up
Windows Task Scheduler for Mon/Wed/Fri/Sun at 6am.

Usage:
  python setup.py           — full setup
  python setup.py --check   — just verify all APIs are working
"""

import os
import sys
import json
import subprocess
import shutil
import textwrap
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# ─── Step tracking ────────────────────────────────────────────────────────────
_steps_done   = []
_steps_failed = []


def step(name: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            print(f"\n{'─'*55}")
            print(f"  {name}")
            print(f"{'─'*55}")
            try:
                result = fn(*args, **kwargs)
                _steps_done.append(name)
                print(f"  OK")
                return result
            except Exception as e:
                _steps_failed.append((name, str(e)))
                print(f"  FAILED: {e}")
                return None
        return wrapper
    return decorator


# ─── Setup steps ──────────────────────────────────────────────────────────────

@step("1. Check Python version")
def check_python():
    if sys.version_info < (3, 9):
        raise EnvironmentError(f"Python 3.9+ required (you have {sys.version})")
    print(f"  Python {sys.version.split()[0]}")


@step("2. Load .env file")
def load_env():
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        # Copy from example
        example = BASE_DIR / '.env.example'
        if example.exists():
            import shutil
            shutil.copy(example, env_file)
        raise FileNotFoundError(
            f".env not found.\n"
            f"  Created from .env.example at: {env_file}\n"
            f"  Fill in your API keys, then re-run setup.py"
        )
    from dotenv import load_dotenv
    load_dotenv(env_file)
    _check_required_keys()


def _check_required_keys():
    required = {
        'ANTHROPIC_API_KEY':   'Anthropic (claude.ai/api)',
        'SLACK_BOT_TOKEN':     'Slack (copy from email-agent .env)',
        'SLACK_APP_TOKEN':     'Slack (copy from email-agent .env)',
        'SLACK_USER_ID':       'Slack (copy from email-agent .env)',
        'HEYGEN_API_KEY':      'HeyGen (heygen.com → Settings → API)',
        'HEYGEN_AVATAR_ID':    'HeyGen (heygen.com → Avatars → copy ID)',
        'ELEVENLABS_API_KEY':  'ElevenLabs (elevenlabs.io → Profile → API Keys)',
        'ELEVENLABS_VOICE_ID': 'ElevenLabs (elevenlabs.io → Voices → copy ID)',
        'PEXELS_API_KEY':      'Pexels (pexels.com/api — free)',
        'NEWS_API_KEY':        'NewsAPI (newsapi.org — free)',
        'YOUTUBE_API_KEY':     'Google Cloud Console → YouTube Data API v3',
    }
    missing = [(k, src) for k, src in required.items() if not os.getenv(k)]
    if missing:
        lines = "\n".join(f"    {k:<28} → {src}" for k, src in missing)
        raise ValueError(f"Missing keys in .env:\n{lines}")
    print(f"  All {len(required)} keys present")


@step("3. Install Python dependencies")
def install_deps():
    req = BASE_DIR / 'requirements.txt'
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', str(req), '-q'],
        check=True,
    )
    print(f"  All packages installed")


@step("4. Install Playwright browser")
def install_playwright():
    result = subprocess.run(
        [sys.executable, '-m', 'playwright', 'install', 'chromium', '--with-deps'],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise EnvironmentError(result.stderr[-400:])
    print(f"  Chromium installed")


@step("5. Check FFmpeg")
def check_ffmpeg():
    if shutil.which('ffmpeg'):
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        version = result.stdout.split('\n')[0]
        print(f"  {version}")
        return

    # Offer to download on Windows
    print("  FFmpeg not found. Attempting to download...")
    _download_ffmpeg_windows()


def _download_ffmpeg_windows():
    import urllib.request, zipfile, io

    ffmpeg_url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
    install_dir = Path.home() / 'ffmpeg'
    bin_dir = install_dir / 'bin'

    print(f"  Downloading FFmpeg to {install_dir} ...")
    with urllib.request.urlopen(ffmpeg_url, timeout=120) as resp:
        data = resp.read()

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.namelist():
            if member.endswith(('.exe',)) and '/bin/' in member:
                filename = Path(member).name
                with z.open(member) as src:
                    (bin_dir).mkdir(parents=True, exist_ok=True)
                    (bin_dir / filename).write_bytes(src.read())

    # Add to user PATH permanently via setx
    current_path = os.environ.get('PATH', '')
    if str(bin_dir) not in current_path:
        subprocess.run(['setx', 'PATH', f"{current_path};{bin_dir}"], check=True)
        print(f"  Added {bin_dir} to PATH. Restart your terminal for it to take effect.")
    else:
        print(f"  FFmpeg already in PATH at {bin_dir}")


@step("6. Create asset directories")
def create_assets():
    dirs = [
        BASE_DIR / '.tmp',
        BASE_DIR / 'output',
        BASE_DIR / 'assets' / 'music',
        BASE_DIR / 'assets' / 'fonts',
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"  Created: .tmp/, output/, assets/music/, assets/fonts/")
    print(f"  ACTION NEEDED: Add 1-2 royalty-free MP3 tracks to assets/music/")
    print(f"    → YouTube Audio Library: https://studio.youtube.com/channel/UC.../music")
    print(f"    → Pixabay Music (free):  https://pixabay.com/music/")


@step("7. Validate API connections")
def validate_apis():
    import requests as req
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')

    errors = []

    # Anthropic
    try:
        import anthropic
        c = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        c.messages.create(model='claude-haiku-4-5-20251001', max_tokens=10, messages=[{'role':'user','content':'hi'}])
        print("  Anthropic:   OK")
    except Exception as e:
        errors.append(f"Anthropic: {e}")

    # HeyGen — just verify key works by listing avatars
    try:
        r = req.get('https://api.heygen.com/v2/avatars',
                    headers={'X-Api-Key': os.getenv('HEYGEN_API_KEY')}, timeout=10)
        if r.status_code == 200:
            count = len(r.json().get('data', {}).get('avatars', []))
            print(f"  HeyGen:      OK ({count} avatars available)")
        else:
            errors.append(f"HeyGen: {r.status_code} {r.text[:100]}")
    except Exception as e:
        errors.append(f"HeyGen: {e}")

    # ElevenLabs — verify voice exists
    try:
        voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        r = req.get(f'https://api.elevenlabs.io/v1/voices/{voice_id}',
                    headers={'xi-api-key': os.getenv('ELEVENLABS_API_KEY')}, timeout=10)
        if r.status_code == 200:
            name = r.json().get('name', 'unknown')
            print(f"  ElevenLabs:  OK (voice: {name})")
        else:
            errors.append(f"ElevenLabs: {r.status_code} {r.text[:100]}")
    except Exception as e:
        errors.append(f"ElevenLabs: {e}")

    # Pexels
    try:
        r = req.get('https://api.pexels.com/videos/search',
                    headers={'Authorization': os.getenv('PEXELS_API_KEY')},
                    params={'query': 'technology', 'per_page': 1}, timeout=10)
        if r.status_code == 200:
            print(f"  Pexels:      OK")
        else:
            errors.append(f"Pexels: {r.status_code}")
    except Exception as e:
        errors.append(f"Pexels: {e}")

    # NewsAPI
    try:
        r = req.get('https://newsapi.org/v2/everything',
                    params={'q': 'AI', 'pageSize': 1, 'apiKey': os.getenv('NEWS_API_KEY')}, timeout=10)
        if r.status_code == 200:
            print(f"  NewsAPI:     OK")
        else:
            errors.append(f"NewsAPI: {r.status_code} {r.json().get('message','')}")
    except Exception as e:
        errors.append(f"NewsAPI: {e}")

    # Slack
    try:
        from slack_sdk import WebClient
        w = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        info = w.auth_test()
        print(f"  Slack:       OK (bot: {info['bot_id']})")
    except Exception as e:
        errors.append(f"Slack: {e}")

    if errors:
        raise ValueError("API validation failures:\n" + "\n".join(f"    {e}" for e in errors))


@step("8. YouTube OAuth (opens browser)")
def youtube_oauth():
    secret_file = BASE_DIR / 'client_secret.json'
    token_file  = BASE_DIR / 'yt_token.json'

    if token_file.exists():
        print("  yt_token.json already exists — checking if valid...")
        try:
            from publisher import get_youtube
            get_youtube()
            print("  YouTube OAuth: valid and working")
            return
        except Exception:
            print("  Token invalid — re-authenticating...")
            token_file.unlink()

    if not secret_file.exists():
        raise FileNotFoundError(
            f"client_secret.json not found.\n"
            f"  Steps:\n"
            f"  1. Go to: https://console.cloud.google.com\n"
            f"  2. Project: social-media-analytics-488803\n"
            f"  3. APIs & Services → Credentials → Create OAuth 2.0 Client ID\n"
            f"  4. Application type: Desktop App\n"
            f"  5. Download JSON → save as: {secret_file}\n"
            f"  Then re-run: python setup.py"
        )

    from publisher import get_youtube
    get_youtube()
    print("  YouTube OAuth complete — yt_token.json saved")


@step("9. Set up Windows Task Scheduler")
def setup_scheduler():
    python_exe = sys.executable
    script_path = BASE_DIR / 'main.py'
    working_dir = str(BASE_DIR)

    # Run at 6am on Mon, Wed, Fri, Sun
    days_map = {
        'Monday':    'MON',
        'Wednesday': 'WED',
        'Friday':    'FRI',
        'Sunday':    'SUN',
    }

    task_name = 'AIShortsChannel'

    # Delete existing task if present
    subprocess.run(
        ['schtasks', '/delete', '/tn', task_name, '/f'],
        capture_output=True,
    )

    # Create new task — runs at 6am daily, but main.py checks posting day internally
    result = subprocess.run([
        'schtasks', '/create',
        '/tn',  task_name,
        '/tr',  f'"{python_exe}" "{script_path}"',
        '/sc',  'DAILY',
        '/st',  '06:00',
        '/sd',  datetime.now().strftime('%m/%d/%Y'),
        '/ru',  os.environ.get('USERNAME', 'SYSTEM'),
        '/f',   # Force overwrite
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  Task '{task_name}' created — runs at 6am daily")
        print(f"  (main.py checks posting days Mon/Wed/Fri/Sun automatically)")
    else:
        raise EnvironmentError(f"schtasks failed: {result.stderr or result.stdout}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 55)
    print("  AI Shorts Channel — Setup")
    print("=" * 55)

    check_only = '--check' in sys.argv

    if check_only:
        load_env()
        validate_apis()
    else:
        check_python()
        load_env()
        install_deps()
        install_playwright()
        check_ffmpeg()
        create_assets()
        validate_apis()
        youtube_oauth()
        setup_scheduler()

    print("\n" + "=" * 55)
    if _steps_failed:
        print(f"  Setup complete with {len(_steps_failed)} issue(s):")
        for name, err in _steps_failed:
            print(f"    FAILED  {name}")
            print(f"            {err[:120]}")
        print("\n  Fix the above issues and re-run: python setup.py")
    else:
        print(f"  All {len(_steps_done)} steps passed!")
        print()
        print("  Next steps:")
        print("  1. Add 1-2 royalty-free MP3s to assets/music/")
        print("  2. Run a test: python main.py --dry-run")
        print("  3. Check Slack — you should get a script within ~30 seconds")
        print("  4. When ready for live posting: python main.py")

    print("=" * 55 + "\n")


if __name__ == '__main__':
    main()
