# multicam-mirror

Apply a [video-use](https://github.com/browser-use/video-use) EDL's A-cam cuts to a parallel B-cam, after auto-syncing the two takes via shared room audio.

## What it does

1. Extracts mono audio from both cameras
2. Computes the audio offset via scipy cross-correlation
3. For every cut range in the EDL, produces the same range on B-cam (offset-shifted)
4. ffmpeg-extracts those B-cam segments
5. Concats them into `final_b.mp4`

Output: a B-cam reel that's cut at the same moments as `final_a.mp4` (which video-use produced). Drop both onto a Premiere/Resolve timeline as parallel tracks for a multicam edit.

## Usage

```bash
python main.py <a_cam.mp4> <b_cam.mp4> <edl.json> [--out-dir DIR] [--window 30]
```

Defaults:
- `--out-dir ./multicam_out/`
- `--window 30` — seconds of audio used for sync correlation

## Install

```bash
cd python-scripts/multicam-mirror
pip install -r requirements.txt
```

Requires `ffmpeg` on PATH (already installed if `hyperframes doctor` is green).

## Limits (v1)

- **Single-A-cam EDLs only.** If video-use picks from multiple A-cam takes (multiple `source` IDs in the EDL), v1 errors out. v2 will accept a B-cam-per-A-cam mapping.
- **No grade / overlays / subtitles applied.** B-cam output is raw cuts — overlays and grade live on the A-cam reel.
- **Sync window defaults to first 30s.** If the cameras start more than 30s apart, increase `--window`.

## How it composes with video-use

```
A-cam.mp4 + B-cam.mp4
        |
        v
[video-use]  ← Claude Code drives this; produces edl.json + final_a.mp4 against A-cam
        |
        v (edl.json + b_cam.mp4)
[multicam-mirror]  ← this tool; produces final_b.mp4
        |
        v
final_a.mp4 + final_b.mp4 → Premiere/Resolve multicam timeline
```
