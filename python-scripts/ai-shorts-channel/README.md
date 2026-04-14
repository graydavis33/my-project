# AI Shorts Channel

## What It Does
- Fully automated YouTube Shorts pipeline for daily AI news (channel: Signal AI)
- Collects top AI stories from NewsAPI + Reddit (r/artificial, r/MachineLearning, r/technology)
- Claude writes a ~45-second script (hook + 3 stories + outro) with target word counts tuned to 170 wpm
- Generates ElevenLabs voiceover, HeyGen avatar clips (hook + outro), and Pexels B-roll in parallel
- Assembles 1080x1920 vertical video with MoviePy, uploads as private to YouTube
- Two human-in-the-loop Slack gates: script review, then video review (with private YouTube link)
- On approval, flips video to public. Runs on posting days only: Mon, Wed, Fri, Sun at 6am
- Full state machine — crash-safe via `state.json`, resumable with `--resume`

## Key Files
- `main.py` — orchestrator, scheduler, state machine, Slack approval handlers
- `news_collector.py` — pulls stories from NewsAPI + Reddit
- `script_writer.py` — Claude script generation + Slack formatting
- `voiceover_gen.py` — ElevenLabs TTS for hook/stories/outro
- `avatar_gen.py` — HeyGen talking-head clips for hook and outro
- `broll_collector.py` — Pexels stock footage per story
- `video_assembler.py` — MoviePy stitches avatar + B-roll + VO + music into vertical short
- `publisher.py` — YouTube private upload, make-public, delete-draft
- `slack_bot.py` — Socket Mode listener, script/video review DMs, approval callbacks
- `state_manager.py` — `state.json` read/write, stage transitions
- `config.py` — all env loading, paths, word targets, video dimensions
- `setup.py` — installs deps, creates folders
- `copy_slack_env.py` — copies Slack tokens from email-agent's `.env`
- `test_pipeline.py` — pipeline smoke test
- `run.bat` — Windows launcher

## Stack
Python, Claude (Anthropic SDK), Slack (socket mode via slack-sdk), ElevenLabs TTS, HeyGen avatar API, Pexels API, NewsAPI, Reddit JSON, YouTube Data API v3 (OAuth), MoviePy, FFmpeg, Playwright, `schedule`

## Run
```bash
cd python-scripts/ai-shorts-channel && python main.py
```
Flags: `--dry-run` (stop before paid APIs), `--resume` (recover from crash), `--reset` (wipe state)

## Env Vars (.env)
`SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_USER_ID`, `ANTHROPIC_API_KEY`, `HEYGEN_API_KEY`, `HEYGEN_AVATAR_ID`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `PEXELS_API_KEY`, `NEWS_API_KEY`, `YOUTUBE_API_KEY`, `CHANNEL_NAME` (defaults to `Signal AI`)

Plus `client_secret.json` in the project folder for YouTube OAuth upload.

## Status
Code complete, awaiting accounts + .env setup. Needs HeyGen, ElevenLabs, Pexels, NewsAPI keys plus YouTube OAuth `client_secret.json`.

## Notes
- Posting days hardcoded in `config.py`: Mon/Wed/Fri/Sun. Scheduler runs daily at 6am but skips off-days
- Script and video each capped at 3 revisions (`MAX_SCRIPT_REVISIONS`, `MAX_VIDEO_REVISIONS`) — reply `reset` in Slack to start over
- Video target: ~45s (5s hook + 3x12s stories + 4s outro) at 1080x1920, 30fps
- Crash-safe — `state.json` tracks current stage, `--resume` picks up where it left off
- After publish, `.tmp/` gets cleaned of `.mp4/.mp3/.aac/.png/.srt` intermediates
- Reuses Slack tokens from email-agent — run `python copy_slack_env.py` to pull them over
- Paid per-run: ElevenLabs + HeyGen + Claude + possibly Pexels. Use `--dry-run` to test without spending on media gen
