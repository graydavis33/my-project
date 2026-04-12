"""
AI Shorts Channel — Main Orchestrator

Runs as a persistent process (Slack bot always on).
On posting days, runs the full pipeline with two human-in-the-loop gates:
  1. Script review via Slack
  2. Video review via Slack (private YouTube link)

Usage:
  python main.py            — start the bot and pipeline scheduler
  python main.py --dry-run  — collect news + generate script, send to Slack, stop before any paid API calls
  python main.py --reset    — clear current state and start fresh
  python main.py --resume   — resume pipeline from current state (useful after a crash)
"""

import sys
import time
import logging
import threading
from datetime import datetime
from pathlib import Path

import schedule

import state_manager as sm
import slack_bot
from news_collector  import collect_news
from script_writer   import write_script, format_for_slack
from voiceover_gen   import generate_voiceovers
from avatar_gen      import generate_avatar_clips
from broll_collector import collect_broll
from video_assembler import assemble_video
from publisher       import upload_private, make_public, delete_video
from config          import POSTING_DAYS, TMP_DIR, OUTPUT_DIR, MAX_SCRIPT_REVISIONS, MAX_VIDEO_REVISIONS

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'agent.log', encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

DRY_RUN = '--dry-run' in sys.argv


# ─── Pipeline stages ──────────────────────────────────────────────────────────

def run_pipeline():
    """Entry point for the daily pipeline. Called by scheduler on posting days."""
    state = sm.load_state()
    stage = state.get('stage', sm.IDLE)
    today = datetime.now().strftime('%Y-%m-%d')

    if stage == sm.PUBLISHED and state.get('date') == today:
        log.info("[pipeline] Already published today — nothing to do")
        return

    if stage not in (sm.IDLE, sm.FAILED) and state.get('date') != today:
        log.warning("[pipeline] Stale state from a previous day — resetting")
        sm.reset_state()
        stage = sm.IDLE

    if stage == sm.IDLE:
        sm.save_state({'date': today})
        _stage_collect_news()


def _stage_collect_news():
    log.info("[pipeline] Stage: Collect news")
    stories = collect_news()
    if not stories:
        _fail("No news stories collected")
        return
    sm.save_state({'stage': sm.NEWS_COLLECTED, 'raw_stories': stories})
    _stage_write_script()


def _stage_write_script(feedback: str = None):
    log.info("[pipeline] Stage: Write script")
    state   = sm.load_state()
    stories = state['raw_stories']
    rev     = state.get('script_revision', 0)

    if rev >= MAX_SCRIPT_REVISIONS:
        slack_bot.send_notification(
            f"Script has been revised {MAX_SCRIPT_REVISIONS} times. Reply `reset` to start fresh."
        )
        return

    try:
        script = write_script(stories, feedback=feedback, revision=rev)
    except Exception as e:
        _fail(f"Script writing failed: {e}")
        return

    sm.save_state({
        'stage':            sm.SCRIPT_READY,
        'script':           script,
        'script_revision':  rev + (1 if feedback else 0),
    })
    _stage_send_script_for_review(script)


def _stage_send_script_for_review(script: dict):
    log.info("[pipeline] Stage: Send script to Slack for review")
    formatted = format_for_slack(script)
    slack_bot.send_script_review(formatted)
    sm.set_stage(sm.AWAITING_SCRIPT_APPROVAL)

    # Register callback — will be triggered when Gray replies
    slack_bot.on_script_approval(_handle_script_response)
    log.info("[pipeline] Waiting for script approval...")


def _handle_script_response(approved: bool, feedback: str = None):
    """Called by Slack bot when Gray replies to script review."""
    if approved:
        log.info("[pipeline] Script approved!")
        sm.set_stage(sm.SCRIPT_APPROVED)
        if DRY_RUN:
            slack_bot.send_notification("Dry run complete — stopping before production API calls.")
            return
        slack_bot.on_script_approval(None)   # De-register
        threading.Thread(target=_stage_generate_media, daemon=True).start()
    else:
        log.info(f"[pipeline] Script feedback: {feedback}")
        sm.record_feedback(feedback)
        slack_bot.on_script_approval(None)
        _stage_write_script(feedback=feedback)


def _stage_generate_media():
    """Generate voiceover, avatar clips, and B-roll (can run in parallel)."""
    state  = sm.load_state()
    script = state['script']

    log.info("[pipeline] Stage: Generate media assets")
    slack_bot.send_notification("Script approved — generating voiceover and avatar clips...")

    errors = []

    # Voiceover and B-roll can run concurrently; avatar is separate
    vo_paths = {}
    broll_paths = {}
    hook_path = outro_path = None

    def gen_voiceover():
        try:
            result = generate_voiceovers(script)
            vo_paths.update(result)
            sm.save_state({'voiceover_paths': {k: str(v) for k, v in result.items()}})
        except Exception as e:
            errors.append(f"Voiceover: {e}")

    def gen_avatar():
        nonlocal hook_path, outro_path
        try:
            hook_path, outro_path = generate_avatar_clips(script)
            sm.save_state({
                'hook_video_path':  str(hook_path),
                'outro_video_path': str(outro_path),
            })
        except Exception as e:
            errors.append(f"Avatar: {e}")

    def gen_broll():
        try:
            result = collect_broll(script)
            broll_paths.update(result)
            sm.save_state({'broll_paths': {
                str(k): {kk: str(vv) if vv else None for kk, vv in v.items()}
                for k, v in result.items()
            }})
        except Exception as e:
            errors.append(f"B-roll: {e}")

    threads = [
        threading.Thread(target=gen_voiceover, daemon=True),
        threading.Thread(target=gen_avatar,    daemon=True),
        threading.Thread(target=gen_broll,     daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        _fail(f"Media generation errors: {'; '.join(errors)}")
        return

    sm.set_stage(sm.BROLL_DONE)
    _stage_assemble_video(script, hook_path, outro_path, broll_paths, vo_paths)


def _stage_assemble_video(script, hook_path, outro_path, broll_paths, vo_paths):
    log.info("[pipeline] Stage: Assemble video")
    today  = datetime.now().strftime('%Y-%m-%d')
    rev    = sm.load_state().get('video_revision', 0)
    output = OUTPUT_DIR / f'short_{today}_v{rev}.mp4'

    try:
        # Convert saved string paths back to Path objects
        broll_path_objs = {
            int(k): {kk: Path(vv) if vv else None for kk, vv in v.items()}
            for k, v in broll_paths.items()
        }
        vo_path_objs = {int(k): Path(v) for k, v in vo_paths.items()}

        assemble_video(
            script=script,
            hook_path=hook_path,
            outro_path=outro_path,
            broll_paths=broll_path_objs,
            voiceover_paths=vo_path_objs,
            output_path=output,
        )
    except Exception as e:
        _fail(f"Video assembly failed: {e}")
        return

    sm.save_state({'stage': sm.VIDEO_ASSEMBLED, 'assembled_video_path': str(output)})
    _stage_upload_private(script, output)


def _stage_upload_private(script: dict, video_path: Path):
    log.info("[pipeline] Stage: Upload as private")
    try:
        video_id, watch_url = upload_private(video_path, script)
    except Exception as e:
        _fail(f"YouTube upload failed: {e}")
        return

    sm.save_state({
        'stage':                sm.UPLOADED_PRIVATE,
        'youtube_video_id':     video_id,
        'youtube_private_url':  watch_url,
    })
    _stage_send_video_for_review(script, video_id, watch_url)


def _stage_send_video_for_review(script: dict, video_id: str, watch_url: str):
    log.info("[pipeline] Stage: Send video for review")
    slack_bot.send_video_review(watch_url, script.get('youtube_title', 'AI Short'))
    sm.set_stage(sm.AWAITING_VIDEO_APPROVAL)
    slack_bot.on_video_approval(_handle_video_response)
    log.info("[pipeline] Waiting for video approval...")


def _handle_video_response(approved: bool, feedback: str = None):
    """Called by Slack bot when Gray replies to video review."""
    if approved:
        log.info("[pipeline] Video approved — publishing!")
        sm.set_stage(sm.VIDEO_APPROVED)
        slack_bot.on_video_approval(None)
        threading.Thread(target=_stage_publish, daemon=True).start()
    else:
        log.info(f"[pipeline] Video feedback: {feedback}")
        sm.record_feedback(feedback)
        slack_bot.on_video_approval(None)
        threading.Thread(target=lambda: _handle_video_feedback(feedback), daemon=True).start()


def _handle_video_feedback(feedback: str):
    """Interpret feedback and rebuild the video or re-do from script."""
    state    = sm.load_state()
    video_id = state.get('youtube_video_id')
    rev      = state.get('video_revision', 0)
    script   = state.get('script')

    if rev >= MAX_VIDEO_REVISIONS:
        slack_bot.send_notification(
            f"Video revised {MAX_VIDEO_REVISIONS} times. Reply `reset` to start over from scratch."
        )
        return

    sm.save_state({'video_revision': rev + 1})

    # Delete old private draft
    if video_id:
        try:
            delete_video(video_id)
        except Exception:
            pass

    feedback_lower = feedback.lower()

    if any(w in feedback_lower for w in ('script', 'story', 'rewrite', 'redo script')):
        slack_bot.send_notification("Got it — rewriting the script with your feedback...")
        _stage_write_script(feedback=feedback)
    else:
        slack_bot.send_notification("Got it — rebuilding the video with your feedback...")
        # Clear B-roll cache so it re-fetches with different keywords if needed
        broll_paths = {}
        vo_paths = {int(k): Path(v) for k, v in state.get('voiceover_paths', {}).items()}
        hook_path  = Path(state['hook_video_path'])  if state.get('hook_video_path')  else None
        outro_path = Path(state['outro_video_path']) if state.get('outro_video_path') else None
        _stage_assemble_video(script, hook_path, outro_path, broll_paths, vo_paths)


def _stage_publish():
    log.info("[pipeline] Stage: Publish")
    state    = sm.load_state()
    video_id = state.get('youtube_video_id')
    try:
        make_public(video_id)
    except Exception as e:
        _fail(f"Publish failed: {e}")
        return

    sm.set_stage(sm.PUBLISHED)
    url = f"https://www.youtube.com/watch?v={video_id}"
    slack_bot.send_notification(f"Published! {url}\n\nSee you next posting day.")
    log.info(f"[pipeline] Published: {url}")
    _cleanup_tmp()


def _fail(reason: str):
    log.error(f"[pipeline] FAILED: {reason}")
    sm.set_stage(sm.FAILED)
    slack_bot.send_notification(f"Pipeline failed: {reason}\n\nRun `python main.py --resume` or `--reset` to recover.")


def _cleanup_tmp():
    """Remove intermediate files after a successful publish."""
    for f in TMP_DIR.glob('*'):
        if f.is_file() and f.suffix in ('.mp4', '.mp3', '.aac', '.png', '.srt'):
            try:
                f.unlink()
            except Exception:
                pass
    log.info("[pipeline] .tmp cleaned up")


# ─── Scheduler ────────────────────────────────────────────────────────────────

def _is_posting_day() -> bool:
    return datetime.now().strftime('%A').lower() in POSTING_DAYS


def scheduled_run():
    if _is_posting_day():
        log.info("[scheduler] Posting day — starting pipeline")
        threading.Thread(target=run_pipeline, daemon=True).start()
    else:
        log.info(f"[scheduler] Not a posting day ({datetime.now().strftime('%A')})")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    if '--reset' in sys.argv:
        sm.reset_state()
        log.info("State reset. Run without --reset to start fresh.")
        return

    log.info("=" * 60)
    log.info("AI Shorts Channel — Starting")
    log.info(f"Posting days: Mon, Wed, Fri, Sun | Dry run: {DRY_RUN}")
    log.info("=" * 60)

    # Start Slack bot (always on, listens for replies at any stage)
    slack_bot.start_listener()
    time.sleep(2)   # Let Socket Mode connect

    if '--resume' in sys.argv:
        log.info("Resuming from current state...")
        stage = sm.get_stage()
        log.info(f"Current stage: {stage}")
        if stage == sm.AWAITING_SCRIPT_APPROVAL:
            state  = sm.load_state()
            script = state.get('script')
            if script:
                slack_bot.on_script_approval(_handle_script_response)
                formatted = format_for_slack(script)
                slack_bot.send_script_review(formatted)
        elif stage == sm.AWAITING_VIDEO_APPROVAL:
            state    = sm.load_state()
            video_id = state.get('youtube_video_id')
            url      = state.get('youtube_private_url')
            script   = state.get('script', {})
            if url:
                slack_bot.on_video_approval(_handle_video_response)
                slack_bot.send_video_review(url, script.get('youtube_title', 'AI Short'))
        else:
            threading.Thread(target=run_pipeline, daemon=True).start()

    elif DRY_RUN:
        log.info("Dry run — starting pipeline now")
        threading.Thread(target=run_pipeline, daemon=True).start()

    else:
        # Run immediately if it's a posting day
        if _is_posting_day():
            log.info("Posting day — running now")
            threading.Thread(target=run_pipeline, daemon=True).start()

        # Then schedule at 6am daily
        schedule.every().day.at('06:00').do(scheduled_run)
        log.info("Scheduler set for 6am daily. Ctrl+C to stop.")

    # Keep alive
    while True:
        try:
            schedule.run_pending()
        except Exception:
            log.exception("Scheduler error")
        time.sleep(30)


if __name__ == '__main__':
    main()
