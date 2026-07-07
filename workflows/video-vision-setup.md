# Video Vision — Claude Watches Videos (claude-video-vision plugin)

**Created:** 2026-07-05 (Mac session)
**Purpose:** Give Claude Code real video understanding — it extracts frames with ffmpeg and looks at them, plus transcribes the audio, so it knows what a video looks AND sounds like. Works on local files (MP4, MOV, WebM, AVI, MKV) and YouTube URLs.

> Not an official Anthropic feature (that's still an open feature request). This is the community plugin `jordanrendric/claude-video-vision` (864 stars, MIT license). Code was security-reviewed 2026-07-05 before install: everything runs locally; the only network traffic is the one-time Whisper model download from HuggingFace.

---

## How it works (plain English)

1. You mention a video file or YouTube link in any Claude Code session.
2. The plugin's skill kicks in: Claude gets metadata, runs a structural analysis (scene changes, silence, motion), and transcribes the audio — all on your machine.
3. Claude then pulls out frames at smart moments and literally looks at them as images.
4. You can ask follow-ups ("what's on screen at 0:42?", "does the hook match the caption?") and it drills into specific seconds.

No API keys. No uploads. Transcription runs fully offline.

---

## Mac status: DONE (2026-07-05)

- Plugin installed at user scope (`claude plugin list` shows it enabled)
- whisper.cpp installed via Homebrew (`whisper-cli`)
- Config written to `~/.claude-video-vision/config.json` (backend: local, engine: cpp)
- ffmpeg / Node / yt-dlp were already present

**First use note:** the first transcription auto-downloads the Whisper model (~150MB, one time). Restart Claude Code (reload the VS Code window) before first use so the plugin's tools load.

**Try it:** open a session and say
`Watch /path/to/some-short.mp4 and tell me if the hook matches the visual`

---

## Windows status: DONE (2026-07-06)

- Plugin v1.2.0 installed at user scope (`claude plugin list` shows it enabled)
- Config written to `C:\Users\Gray Davis\.claude-video-vision\config.json` (python engine, large-v3 — GPU)
- Prereqs verified: node v24.14.0, ffmpeg 8.1, python whisper 20250625
- Whisper large-v3 model already cached (transcriber uses it), so no first-use download
- Note: `whisper --help` crashes with a cp1252 UnicodeEncodeError on this machine — cosmetic (help text contains a CJK char); actual transcription runs fine. If the plugin ever chokes parsing whisper output, set `PYTHONIOENCODING=utf-8` as a user env var.

### Windows-only extra steps (the Mac instructions weren't enough)

Two gotchas surfaced; both fixed, documented for reinstalls:

1. **`--strict-mcp-config` ignores plugin-bundled MCP servers** (same issue as the Sandcastles install, 2026-06-02). The plugin's skills + agent load fine, but its MCP tools (`video_info`, `video_watch`, …) never appear because the VS Code extension only reads `~/.claude.json`. Fix: register the server directly in `~/.claude.json` → `mcpServers` (backup taken first: `~/.claude.json.bak-2026-07-06`).
2. **`npx -y claude-video-vision@latest` was broken on this machine** — corrupted npx cache (`ajv-formats` installed without its `ajv` peer dep → `Cannot find module 'ajv'`). Fix: cleared the bad `_npx` cache entry and installed globally instead: `npm install -g claude-video-vision` (v1.3.2). MCP entry uses the global install directly:
   ```json
   "claude-video-vision": {
     "command": "node",
     "args": ["C:/Users/Gray Davis/AppData/Roaming/npm/node_modules/claude-video-vision/dist/index.js"]
   }
   ```
   MCP initialize handshake verified working by hand. Upgrades are now deliberate: `npm update -g claude-video-vision` (Windows does NOT auto-track `@latest` like the Mac's npx does).
- After the config change: reload the VS Code window again so the MCP server connects. `/mcp` should show **9** servers on Windows now.

## Windows setup steps (for reference / reinstall)

Run these in a terminal on the Windows machine:

**1. Check prerequisites** (all three should already exist from the batch pipeline):

```
node --version     (need 20+)
ffmpeg -version
whisper --help     (the GPU Whisper used by transcriber)
```

If `whisper` isn't on PATH, either activate the venv that has it, or `pip install openai-whisper`.

**2. Install the plugin** (same two commands as Mac):

```
claude plugin marketplace add jordanrendric/claude-video-vision
claude plugin install claude-video-vision@claude-video-vision
```

**3. Create the config file** at `C:\Users\Gray Davis\.claude-video-vision\config.json`:

```json
{
  "backend": "local",
  "whisper_engine": "python",
  "whisper_model": "large-v3",
  "frame_mode": "images",
  "frame_format": "jpeg",
  "frame_resolution": 512,
  "default_fps": "auto",
  "max_frames": 100,
  "enable_index": true
}
```

Difference vs Mac: Windows uses `"whisper_engine": "python"` + `"whisper_model": "large-v3"` because the RTX 5070 GPU Whisper is already installed there and is faster. (Mac uses `"cpp"` + `"auto"` = whisper.cpp.)

**4. Restart Claude Code** (reload VS Code window). Done.

---

## What this unlocks for the Sai workflow

- Review a delivered short before sending: "watch this and check the captions sync"
- Study reference videos: paste a YouTube URL, get format/hook/pacing breakdown
- Smarter b-roll checks: Claude can confirm what a clip actually shows, not just its filename
- Training the shorts auto-editor: Claude can compare its cut vs Gray's final visually

## Troubleshooting

- Plugin tools missing in a session → reload the VS Code window (plugins load at session start).
- **MCP tools still missing after a reload → start a NEW conversation.** A resumed conversation keeps the MCP server set it started with; window reloads refresh skills but NOT MCP servers. (Cost us two reloads on install day before figuring this out. End-to-end verified working via a fresh headless session: `video_info` returned real metadata.)
- CLI sessions show the server twice (`plugin:claude-video-vision:...` npx + user-scope `claude-video-vision` node) — harmless duplicate; the VS Code extension only loads the user-scope one because of `--strict-mcp-config`.
- Slow first transcription → it's downloading the Whisper model; one-time only.
- Very long videos → it analyzes structure first and samples frames, so it won't flood the session; drill in with follow-up questions instead of asking for everything at once.
- Config changes → edit `~/.claude-video-vision/config.json` (Mac) or the path in step 3 (Windows), or just ask Claude to change a setting (it has a `video_configure` tool).
