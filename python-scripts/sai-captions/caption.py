#!/usr/bin/env python3
"""
Sai Captions — auto-caption a 1080x1920 vertical short to match
the Batch1 Vid 2 reference style (Montserrat SemiBold, white, upper-third,
soft drop shadow).

Usage:
    python caption.py /path/to/input.mp4
    python caption.py /path/to/input.mp4 --output /path/to/output.mp4
    python caption.py /path/to/input.mp4 --model small.en

Pipeline:
    1. Extract mono 16kHz wav from the video
    2. Transcribe with faster-whisper (word-level timestamps)
    3. Group words into 2-3 word "caption cards"
    4. Render each card as a transparent 1080x1920 PNG (PIL)
    5. Overlay the PNGs into the video at their timestamps (ffmpeg overlay filter)
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel
from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ─────────────────────────────────────────────────────────────
# Caption style (matches Batch1 Vid 2 final)
# ─────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
FONT_PATH = HERE / "fonts" / "Montserrat.ttf"
FONT_VARIATION = "SemiBold"   # variable-font axis name (weight 600)

VIDEO_W = 1080
VIDEO_H = 1920
FONT_SIZE = 72               # smaller than ref — Gray's v1.1 preference
LINE_SPACING = 14            # unused now (single-line only) but kept for future
# Words to keep capitalized — keyed by lowercase form, value is the canonical capitalization
PRESERVE_CASE = {
    "i": "I",
    "i'm": "I'm",
    "i've": "I've",
    "i'll": "I'll",
    "i'd": "I'd",
    "i'mma": "I'mma",
    "i'ma": "I'ma",
    "sai": "Sai",
    "sai's": "Sai's",
    "waddell": "Waddell",
    "waddell's": "Waddell's",
}
PUNCTUATION_STRIP = ".,!?;:\"()[]{}—–-…"
TEXT_COLOR = (255, 255, 255, 255)
SHADOW_COLOR = (0, 0, 0, 160)   # soft black @ ~63% alpha
SHADOW_OFFSET = (5, 6)       # x, y offset of shadow (angled down-right, Gray 2026-07-05)
SHADOW_BLUR = 6              # gaussian blur radius for shadow softness
TOP_MARGIN = 320             # y of TOP of first text line (matches ref upper-third)
SIDE_MARGIN = 60             # left/right safe area

# ─────────────────────────────────────────────────────────────
# Caption grouping rules
# ─────────────────────────────────────────────────────────────
MAX_WORDS_PER_CARD = 3
MAX_CARD_DURATION = 1.6      # seconds — don't hold a card longer than this
MIN_CARD_DURATION = 0.35     # don't flash a card shorter than this
PAUSE_BREAK_THRESHOLD = 0.45 # if gap between words > this, force a new card


def run(cmd, **kw):
    """Run a shell command, raise on failure."""
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def probe_video(video_path: Path):
    """Return (width, height, duration_sec, fps_str) using ffprobe."""
    out = run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]).stdout.strip().splitlines()
    w, h, fps, dur = int(out[0]), int(out[1]), out[2], float(out[3])
    return w, h, dur, fps


def extract_audio(video_path: Path, wav_path: Path):
    """Extract mono 16kHz wav for whisper."""
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video_path),
        "-ac", "1", "-ar", "16000", "-vn",
        str(wav_path),
    ])


def transcribe(wav_path: Path, model_size: str):
    """Run faster-whisper with word timestamps. Returns flat list of (word, start, end)."""
    print(f"  loading whisper model: {model_size} ...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print("  transcribing ...")
    segments, info = model.transcribe(
        str(wav_path),
        language="en",
        word_timestamps=True,
        vad_filter=True,
    )
    words = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            text = w.word.strip()
            if not text:
                continue
            words.append((text, w.start, w.end))
    return words


def group_words(words):
    """Pack words into caption cards (2-3 words each)."""
    cards = []
    current = []
    for word, start, end in words:
        if not current:
            current.append((word, start, end))
            continue
        gap = start - current[-1][2]
        words_so_far = len(current)
        card_dur = end - current[0][1]
        if (
            words_so_far >= MAX_WORDS_PER_CARD
            or card_dur > MAX_CARD_DURATION
            or gap > PAUSE_BREAK_THRESHOLD
        ):
            cards.append(current)
            current = [(word, start, end)]
        else:
            current.append((word, start, end))
    if current:
        cards.append(current)

    fixed = []
    for i, card in enumerate(cards):
        start = card[0][1]
        end = card[-1][2]
        if end - start < MIN_CARD_DURATION:
            end = start + MIN_CARD_DURATION
        if i + 1 < len(cards):
            next_start = cards[i + 1][0][1]
            if end > next_start:
                end = next_start
        fixed.append((card, start, end))
    return fixed


def clean_word(word: str) -> str:
    """Strip punctuation, lowercase everything except names / I-forms in PRESERVE_CASE."""
    cleaned = word.strip(PUNCTUATION_STRIP)
    canonical = PRESERVE_CASE.get(cleaned.lower())
    if canonical:
        return canonical
    return cleaned.lower()


def card_lines(card):
    """Return the card text as a single line (Gray's v1.1 preference)."""
    cleaned = [clean_word(w) for w, _, _ in card if clean_word(w)]
    return [" ".join(cleaned)] if cleaned else [""]


def render_card_png(lines, png_path: Path, font: ImageFont.FreeTypeFont):
    """Render one caption card as a transparent 1080x1920 PNG with drop shadow."""
    img = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))

    # Shadow layer (drawn first, blurred)
    shadow_layer = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    # Text layer (sharp white)
    text_layer = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    # Measure line heights
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = font.getbbox(line)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    y_cursor = TOP_MARGIN
    for line, lw, lh in zip(lines, line_widths, line_heights):
        x = (VIDEO_W - lw) // 2
        # Shadow
        shadow_draw.text(
            (x + SHADOW_OFFSET[0], y_cursor + SHADOW_OFFSET[1]),
            line, font=font, fill=SHADOW_COLOR,
        )
        # White text
        text_draw.text((x, y_cursor), line, font=font, fill=TEXT_COLOR)
        y_cursor += lh + LINE_SPACING

    # Blur the shadow, composite shadow then text
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    img.alpha_composite(shadow_layer)
    img.alpha_composite(text_layer)
    img.save(png_path, "PNG")


def render_all_cards(cards, work_dir: Path):
    """Render every card to a PNG. Returns list of (png_path, start, end)."""
    if not FONT_PATH.exists():
        sys.exit(f"Font not found: {FONT_PATH}")
    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    try:
        font.set_variation_by_name(FONT_VARIATION)
    except (AttributeError, OSError):
        pass
    out = []
    for i, (card, start, end) in enumerate(cards):
        lines = card_lines(card)
        png_path = work_dir / f"card_{i:03d}.png"
        render_card_png(lines, png_path, font)
        out.append((png_path, start, end))
    return out


def burn_captions(video_path: Path, card_pngs, output_path: Path, video_duration: float):
    """Burn the caption PNGs into the video as overlays at their timestamps."""
    # Build ffmpeg input list: video + every PNG
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video_path),
    ]
    for png_path, _, _ in card_pngs:
        cmd += ["-loop", "1", "-i", str(png_path)]

    # Build overlay filter chain
    # [0:v] is the base video.
    # [N:v] is the Nth PNG (1-indexed).
    parts = []
    prev_label = "0:v"
    for i, (_, start, end) in enumerate(card_pngs, start=1):
        next_label = f"v{i}"
        parts.append(
            f"[{prev_label}][{i}:v]overlay=x=0:y=0:enable='between(t,{start:.3f},{end:.3f})'[{next_label}]"
        )
        prev_label = next_label

    filter_complex = ";".join(parts) if parts else ""

    cmd += [
        "-filter_complex", filter_complex,
        "-map", f"[{prev_label}]",
        "-map", "0:a?",
        "-c:a", "copy",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-t", f"{video_duration:.3f}",
        str(output_path),
    ]
    run(cmd)


def render_caption_layer(card_pngs, output_path: Path, video_duration: float, fps: str):
    """Render the captions alone on a transparent base -> ProRes 4444 alpha .mov."""
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black@0.0:s={VIDEO_W}x{VIDEO_H}:r={fps}:d={video_duration:.3f},format=rgba",
    ]
    for png_path, _, _ in card_pngs:
        cmd += ["-loop", "1", "-i", str(png_path)]

    parts = []
    prev_label = "0:v"
    for i, (_, start, end) in enumerate(card_pngs, start=1):
        next_label = f"v{i}"
        parts.append(
            f"[{prev_label}][{i}:v]overlay=x=0:y=0:format=auto:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{next_label}]"
        )
        prev_label = next_label

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", f"[{prev_label}]",
        "-c:v", "prores_ks", "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le",
        "-t", f"{video_duration:.3f}",
        str(output_path),
    ]
    run(cmd)


def default_output_path(input_path: Path) -> Path:
    """`batch 1 vid 6 no captions.mp4` -> `batch 1 vid 6 captioned.mp4`"""
    stem = input_path.stem
    lower = stem.lower()
    if "no captions" in lower:
        idx = lower.find("no captions")
        new_stem = stem[:idx] + "captioned" + stem[idx + len("no captions"):]
    else:
        new_stem = f"{stem} captioned"
    return input_path.with_name(f"{new_stem}{input_path.suffix}")


def main():
    parser = argparse.ArgumentParser(description="Auto-caption a vertical short in Sai's style.")
    parser.add_argument("input", type=Path, help="Path to the input MP4 (no captions).")
    parser.add_argument("--output", type=Path, default=None, help="Output MP4 path.")
    parser.add_argument("--model", default="small.en", help="Whisper model (tiny.en, base.en, small.en, medium.en).")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temp wav + PNGs for debugging.")
    parser.add_argument("--layer", action="store_true",
                        help="Output a captions-only transparent ProRes 4444 .mov (separate layer for Premiere) instead of burning into the video.")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Input file not found: {args.input}")

    if args.layer:
        output_path = args.output or args.input.with_name(f"{args.input.stem} - captions layer.mov")
    else:
        output_path = args.output or default_output_path(args.input)
    print(f"INPUT : {args.input}")
    print(f"OUTPUT: {output_path}")

    work_dir = Path(tempfile.mkdtemp(prefix="sai-captions-"))
    print(f"  workdir: {work_dir}")
    wav_path = work_dir / "audio.wav"

    try:
        print("[1/5] probing video ...")
        w, h, dur, fps = probe_video(args.input)
        print(f"  {w}x{h}, {dur:.2f}s, {fps} fps")

        print("[2/5] extracting audio ...")
        extract_audio(args.input, wav_path)

        print("[3/5] transcribing ...")
        words = transcribe(wav_path, args.model)
        if not words:
            sys.exit("No words detected — check the audio.")
        print(f"  {len(words)} words")

        print("[4/5] grouping + rendering caption PNGs ...")
        cards = group_words(words)
        print(f"  {len(cards)} cards")
        card_pngs = render_all_cards(cards, work_dir)

        if args.layer:
            print("[5/5] rendering transparent caption layer (ProRes 4444) ...")
            render_caption_layer(card_pngs, output_path, dur, fps)
        else:
            print("[5/5] burning PNG overlays into video ...")
            burn_captions(args.input, card_pngs, output_path, dur)

        print(f"\nDONE -> {output_path}")
    except subprocess.CalledProcessError as e:
        print("\nffmpeg failed:")
        print(e.stderr)
        sys.exit(1)
    finally:
        if args.keep_temp:
            print(f"  temp files kept at: {work_dir}")
        else:
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
