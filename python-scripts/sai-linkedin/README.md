# sai-linkedin — Reel-to-LinkedIn Post Pipeline

Turns a `video-use` AI Edit folder into a paste-ready LinkedIn post draft for Sai.

## What It Does

Reads the `master.srt` transcript that `video-use` already produced for the daily short, then asks Claude (Sonnet 4.6) to:

1. Summarize the reel into LinkedIn key points
2. Write a paste-ready LinkedIn caption in Sai's founder voice (800–1300 chars, scroll-stopping hook, no fluff)
3. Extract the post's core theme
4. Suggest 5 visual concepts to look for in the footage library

Outputs land in `<input_folder>/linkedin/`.

## Usage

```bash
cd python-scripts/sai-linkedin
source venv/bin/activate
python main.py "/Volumes/Footage/Sai/AI Edits/2026-04-28"
```

## Output

```
linkedin/
├── caption.txt       # Paste-ready LinkedIn post copy
├── theme.txt         # One-sentence theme
├── key_points.txt    # Bullet summary
└── visual_ideas.txt  # Concepts to look for in the footage library
```

## Posting Workflow (Manual for Now)

1. Run this script after the daily reel is rendered
2. Open `caption.txt` — copy the post text
3. Read `visual_ideas.txt` — find a matching photo/screenshot in the footage library
4. (Optional) polish the photo in Photoshop / an AI upscaler
5. Open LinkedIn, paste caption, attach photo, post

Time per post: ~5 minutes once the reel is rendered.

## Stack

- Python 3
- `anthropic` SDK with prompt caching on the system prompt
- Reads `master.srt` directly (no transcription cost — `video-use` already did it)

## Cost

~$0.005 per run (one Sonnet call, ~700 tokens in / 500 tokens out).

## Future (Not Built Yet)

- **Tier 2:** Auto-pick the matching photo from a Vision-tagged footage library
- **Tier 3:** Auto-post via LinkedIn API (blocked on Marketing Developer Platform approval, 5–14 business days)
