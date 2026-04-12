"""
Full pipeline test using mock APIs — no HeyGen, no ElevenLabs, no YouTube upload.
Costs: ~$0.01 (one Claude Sonnet call for the script) + Pexels/Reddit/NewsAPI (free).

What this tests end-to-end:
  - News collection (real API calls to Reddit + NewsAPI + YouTube)
  - Script writing (real Claude call — you'll see the actual script quality)
  - Slack approval loop (REAL — you'll get the actual Slack message with buttons)
  - Voiceover: replaced with FFmpeg-generated silence (no ElevenLabs cost)
  - Avatar clips: replaced with FFmpeg-generated placeholder videos (no HeyGen cost)
  - B-roll: real Pexels + Playwright screenshots
  - Video assembly: real FFmpeg — produces an actual playable .mp4
  - YouTube: skipped — opens the finished video file locally instead
  - Approval gate 2: sends local video link (not YouTube private)

Run: python test_pipeline.py
"""

import sys
import os
import time
import threading
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# ─── Mock environment ─────────────────────────────────────────────────────────
# Patch expensive APIs before anything else imports them
import unittest.mock as mock

# Patch ElevenLabs with FFmpeg-generated silence
def _mock_elevenlabs(text: str) -> bytes:
    duration = max(5, len(text.split()) // 3)
    tmp = Path('python-scripts/ai-shorts-channel/.tmp') / 'mock_silence.mp3'
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
        '-t', str(duration), '-c:a', 'mp3', str(tmp),
    ], capture_output=True)
    return tmp.read_bytes()

# Patch HeyGen with FFmpeg black video placeholder
def _mock_heygen_submit(text: str) -> str:
    return 'mock_video_id_' + text[:8].replace(' ', '_')

def _mock_heygen_poll(video_id: str) -> str:
    # Generate a placeholder black video with the text overlaid
    label = video_id.replace('mock_video_id_', '')
    tmp = Path('python-scripts/ai-shorts-channel/.tmp') / f'mock_avatar_{abs(hash(video_id))}.mp4'
    if not tmp.exists():
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'color=c=black:size=1080x1920:rate=30',
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '6',
            '-vf', f"drawtext=text='[AVATAR PLACEHOLDER]':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            '-c:v', 'libx264', '-c:a', 'aac',
            str(tmp),
        ], capture_output=True)
    return tmp.as_uri()   # Fake URL — we'll handle this in download

# Patch YouTube upload
def _mock_upload(video_path, script) -> tuple:
    print(f"\n[mock] YouTube upload SKIPPED — opening local video instead")
    # Open the video in the default player
    try:
        os.startfile(str(video_path))   # Windows
    except Exception:
        subprocess.run(['start', '', str(video_path)], shell=True)
    fake_id  = 'mock_video_id'
    fake_url = f"file:///{str(video_path).replace(chr(92), '/')}"
    return fake_id, fake_url

def _mock_make_public(video_id: str):
    print(f"[mock] YouTube make_public SKIPPED (no real upload in test mode)")

def _mock_delete_video(video_id: str):
    pass


# Apply patches
mock.patch('voiceover_gen._call_elevenlabs', _mock_elevenlabs).start()
mock.patch('avatar_gen._submit', _mock_heygen_submit).start()
mock.patch('avatar_gen._poll', _mock_heygen_poll).start()
mock.patch('publisher.upload_private', _mock_upload).start()
mock.patch('publisher.make_public', _mock_make_public).start()
mock.patch('publisher.delete_video', _mock_delete_video).start()

# Fix HeyGen download mock — just use the local file directly
original_generate_clip = None

def _mock_generate_clip(text: str, label: str) -> Path:
    from config import TMP_DIR
    import hashlib
    out_path = TMP_DIR / f'avatar_{label}_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp4'
    if not out_path.exists():
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', 'color=c=black:size=1080x1920:rate=30',
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '6',
            '-vf', f"drawtext=text='[{label.upper()} AVATAR]':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5",
            '-c:v', 'libx264', '-c:a', 'aac',
            str(out_path),
        ], capture_output=True)
    return out_path

mock.patch('avatar_gen._generate_clip', _mock_generate_clip).start()

# ─── Now import the real pipeline ─────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

import state_manager as sm
import slack_bot
from news_collector  import collect_news
from script_writer   import write_script, format_for_slack
from voiceover_gen   import generate_voiceovers
from avatar_gen      import generate_avatar_clips
from broll_collector import collect_broll
from video_assembler import assemble_video
from publisher       import upload_private, make_public
from config          import TMP_DIR, OUTPUT_DIR

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ─── Test run ─────────────────────────────────────────────────────────────────

def run_test():
    sm.reset_state()
    today = datetime.now().strftime('%Y-%m-%d')
    sm.save_state({'date': today})

    print("\n" + "=" * 60)
    print("  AI Shorts Channel — TEST PIPELINE")
    print("  (mock APIs: HeyGen + ElevenLabs + YouTube skipped)")
    print("=" * 60 + "\n")

    # Step 1: Collect news
    print("[test] Collecting news...")
    stories = collect_news(force=True)
    print(f"[test] Got {len(stories)} stories\n")
    sm.save_state({'stage': sm.NEWS_COLLECTED, 'raw_stories': stories})

    # Step 2: Write script
    print("[test] Writing script with Claude...")
    script = write_script(stories)
    sm.save_state({'stage': sm.SCRIPT_READY, 'script': script})
    print(f"[test] Script: {script.get('youtube_title')}\n")

    # Step 3: Start Slack bot
    slack_bot.start_listener()
    time.sleep(2)

    # Step 4: Send script for review — REAL Slack message with buttons
    print("[test] Sending script to Slack...")
    approval_event = threading.Event()
    approval_result = {}

    def on_script(approved, feedback):
        approval_result['approved'] = approved
        approval_result['feedback'] = feedback
        approval_event.set()

    slack_bot.on_script_approval(on_script)
    slack_bot.send_script_review(format_for_slack(script))
    sm.set_stage(sm.AWAITING_SCRIPT_APPROVAL)

    print("[test] Waiting for your response in Slack... (60 second timeout in test mode)")
    approval_event.wait(timeout=300)  # 5 min timeout for test

    if not approval_result.get('approved'):
        feedback = approval_result.get('feedback')
        if feedback:
            print(f"[test] Feedback received: {feedback}")
            script = write_script(stories, feedback=feedback, revision=1)
            sm.save_state({'script': script, 'script_revision': 1})
            approval2 = threading.Event()

            def on_script2(approved, feedback2):
                approval_result['approved'] = approved
                approval2.set()

            slack_bot.on_script_approval(on_script2)
            slack_bot.send_script_review(format_for_slack(script))
            approval2.wait(timeout=300)

        if not approval_result.get('approved'):
            print("[test] Script not approved — test stopped")
            return

    print("\n[test] Script approved! Generating media (mocked)...")
    slack_bot.send_notification("Test mode: Script approved — generating media with mock APIs...")
    sm.set_stage(sm.SCRIPT_APPROVED)

    # Step 5: Generate all media in parallel (mocked)
    vo_paths = {}
    broll_paths = {}
    hook_path = outro_path = None

    def gen_vo():
        result = generate_voiceovers(script)
        vo_paths.update(result)

    def gen_avatar():
        nonlocal hook_path, outro_path
        hook_path, outro_path = generate_avatar_clips(script)

    def gen_broll():
        result = collect_broll(script)
        broll_paths.update(result)

    threads = [
        threading.Thread(target=gen_vo),
        threading.Thread(target=gen_avatar),
        threading.Thread(target=gen_broll),
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    print("[test] Media ready — assembling video...")
    sm.set_stage(sm.BROLL_DONE)

    # Step 6: Assemble the real video
    output = OUTPUT_DIR / f'test_{today}.mp4'
    broll_path_objs = {int(k): {kk: Path(vv) if vv else None for kk, vv in v.items()} for k, v in broll_paths.items()}
    vo_path_objs    = {int(k): Path(v) for k, v in vo_paths.items()}

    assemble_video(
        script=script,
        hook_path=hook_path,
        outro_path=outro_path,
        broll_paths=broll_path_objs,
        voiceover_paths=vo_path_objs,
        output_path=output,
    )
    sm.save_state({'stage': sm.VIDEO_ASSEMBLED, 'assembled_video_path': str(output)})

    # Step 7: Mock upload — opens video locally
    video_id, watch_url = upload_private(output, script)
    sm.save_state({'stage': sm.UPLOADED_PRIVATE, 'youtube_video_id': video_id, 'youtube_private_url': watch_url})

    # Step 8: Video review via Slack
    video_event = threading.Event()
    video_result = {}

    def on_video(approved, feedback):
        video_result['approved'] = approved
        video_result['feedback'] = feedback
        video_event.set()

    slack_bot.on_video_approval(on_video)
    slack_bot.send_video_review(
        f"file:///{str(output).replace(chr(92), '/')}",
        script.get('youtube_title', 'Test Short'),
    )
    slack_bot.send_notification(
        f"Test mode: Video assembled at:\n`{output}`\n"
        f"Open it in your video player to review, then approve or request changes above."
    )
    sm.set_stage(sm.AWAITING_VIDEO_APPROVAL)
    print(f"\n[test] Video assembled: {output}")
    print("[test] Waiting for video approval in Slack...")

    video_event.wait(timeout=300)

    if video_result.get('approved'):
        sm.set_stage(sm.PUBLISHED)
        slack_bot.send_notification(
            "Test complete! Pipeline ran end-to-end.\n\n"
            "Once you have HeyGen + ElevenLabs API keys set up, run `python main.py` for the real thing."
        )
        print("\n[test] TEST PASSED — full pipeline works end-to-end!")
    else:
        print(f"\n[test] Video feedback: {video_result.get('feedback')}")
        print("[test] In production, this would trigger a video rebuild.")
        slack_bot.send_notification("Test ended after video feedback. All systems working correctly.")

    print("\n" + "=" * 60)
    print("  Test complete. Check your Slack + the output file.")
    print(f"  Video: {output}")
    print("=" * 60)


if __name__ == '__main__':
    run_test()
    # Keep alive for Slack
    while True:
        time.sleep(5)
