#!/usr/bin/env python
"""Full end-to-end orchestrator for batch video processing.

Usage:
    python orchestrate.py --batch 3 --video 13

Workflow:
    1. Find A-cam and B-cam sources in 01_ORGANIZED/Batch_NN/Vid_MM/
    2. Extract audio → sync via cross-correlation
    3. Create synced angle files (re-encoded, frame-locked, same duration)
    4. Extract lav audio (whichever cam has it) → clean → transcribe
    5. Auto-select proposed ranges
    6. Build config JSON
    7. Run cut → captions → verify → package
    8. Report final package location
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config, sync, audio_clean, transcribe, select, cut, captions, verify, package, review
import render as render_mod


def _extract_audio(video_path: Path, out_wav: Path, sr: int = 48000) -> None:
    """Extract mono audio from video to WAV."""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ac", "1", "-ar", str(sr),
        "-acodec", "pcm_s16le",
        str(out_wav)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extract failed: {result.stderr}")
    print(f"  ✓ extracted audio: {out_wav.name}")


def _mux_audio_to_video(video_path: Path, audio_path: Path, out_video: Path) -> None:
    """Mux (replace) audio track in video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_video)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mux failed: {result.stderr}")
    print(f"  ✓ muxed: {out_video.name}")


def _extract_trim(video_path: Path, trim_in: float, trim_out: float, out_video: Path,
                  codec_args: list) -> None:
    """Extract a trimmed segment, re-encoding with codec_args."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(trim_in),
        "-i", str(video_path),
        "-t", str(trim_out - trim_in),
        "-r", "24000/1001",  # lock FPS
    ] + codec_args + [str(out_video)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg trim failed: {result.stderr}")
    print(f"  ✓ trimmed: {out_video.name}")


def _detect_lav_cam(a_wav: Path, b_wav: Path) -> str:
    """Simple heuristic: LAV audio is cleaner (higher RMS in mid freqs, lower low freq).
    For now, just return 'B' (B-cam typically has the lav).
    TODO: implement proper spectral analysis.
    """
    return "B"


def _read_title(vid_folder: Path, vid_n: int) -> str:
    """Read the title from the Vid folder's _INFO.txt first line, else 'Video {M}'."""
    info = vid_folder / "_INFO.txt"
    if info.exists():
        for line in info.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                return line
    return f"Video {vid_n}"


def _words_for_range(words: list, seg_in: float, seg_out: float) -> str:
    """Join the transcript words whose start falls within [seg_in, seg_out)."""
    return " ".join(
        w["word"] for w in words
        if seg_in <= w["start"] < seg_out
    ).strip()


def _looks_like_question(text: str) -> bool:
    return text.strip().endswith("?")


def _build_segments_json(batch_n: int, vid_n: int, title: str, offset: float,
                         dominance: float, a_rel: str, b_rel: str,
                         seeded_ranges: list, words: list,
                         transcript_segs: list) -> dict:
    """Assemble the SEGMENTS.json dict from seeded ranges + B-cam words.

    seeded_ranges: [(seg_in, seg_out, next_word_start, hard_cap), ...] from select.select
    words:         flat B-cam word list [{"word","start","end"}, ...]
    transcript_segs: [{"start","end","text"}, ...] full B-cam segment list for reference
    Pure logic — no ffmpeg/whisper. Matches the shared schema exactly.
    """
    segments = []
    for i, r in enumerate(seeded_ranges):
        seg_in, seg_out = float(r[0]), float(r[1])
        text = _words_for_range(words, seg_in, seg_out)
        tag = ""
        if i == 0 and _looks_like_question(text):
            tag = "HOOK — your question"
        segments.append({"in": seg_in, "out": seg_out, "text": text, "tag": tag, "tail": None})

    return {
        "batch_n": batch_n,
        "vid_n": vid_n,
        "title": title,
        "offset": offset,
        "offset_dominance": dominance,
        "a_src": a_rel,
        "b_src": b_rel,
        "fps": "24000/1001",
        "segments": segments,
        "dropped": [],
        "transcript": transcript_segs,
    }


def prep(batch_n: int, vid_n: int):
    """PREP phase: sync + transcribe B-cam + seed segments + build trim-review.

    Writes Cut/SEGMENTS.json (editable by Gray) and a HyperFrames trim-review comp.
    Gray reviews/edits, then --render does the rest.
    """
    lib = config.library_root()
    vid_folder = lib / f"01_ORGANIZED/Batch_{batch_n:02d}/Vid_{vid_n:02d}"
    a_cam_folder = vid_folder / "A-cam"
    b_cam_folder = vid_folder / "B-cam"

    a_videos = list(a_cam_folder.glob("*.MP4"))
    b_videos = list(b_cam_folder.glob("*.MP4"))
    if not a_videos or not b_videos:
        raise RuntimeError(f"No A-cam or B-cam video found in {vid_folder}")
    a_video, b_video = a_videos[0], b_videos[0]

    title = _read_title(vid_folder, vid_n)
    print(f"\n{'='*60}")
    print(f"PREP — BATCH {batch_n} VIDEO {vid_n} — {title}")
    print(f"{'='*60}")

    # --- Working dir + sync wavs ---
    cut_dir = vid_folder / "Cut"
    cut_dir.mkdir(exist_ok=True)
    print(f"\n[1/6] CUT DIR: {cut_dir}")

    print(f"\n[2/6] EXTRACT 8kHz SYNC AUDIO")
    a_wav = cut_dir / "a_sync_8k.wav"
    b_wav = cut_dir / "b_sync_8k.wav"
    _extract_audio(a_video, a_wav, sr=8000)
    _extract_audio(b_video, b_wav, sr=8000)

    # --- Verify offset ---
    print(f"\n[3/6] VERIFY OFFSET")
    vo = sync.verify_offset(a_wav, b_wav)
    offset, dominance = vo["offset"], vo["dominance"]
    print(f"  offset (tB - tA): {offset:+.4f}s   dominance: {dominance:.2f}")
    if dominance < 3:
        print(f"  ⚠ LOW-CONFIDENCE SYNC (dominance {dominance:.2f} < 3) — verify by eye")

    # --- Transcribe B-cam (carries the question hook + approved audio) ---
    print(f"\n[4/6] TRANSCRIBE B-CAM (word-level)")
    words_data = transcribe.transcribe(b_video)
    (cut_dir / "Bcam_words.json").write_text(json.dumps(words_data, indent=2), encoding="utf-8")
    all_words = [w for seg in words_data["segments"] for w in seg.get("words", [])]
    transcript_segs = [
        {"start": s["start"], "end": s["end"],
         "text": " ".join(w["word"] for w in s.get("words", [])).strip()}
        for s in words_data["segments"]
    ]
    print(f"  ✓ {len(all_words)} words, {len(transcript_segs)} segments")

    # --- Seed proposed segments from select.py (B-cam words + B-cam audio) ---
    print(f"\n[5/6] SEED PROPOSED SEGMENTS")
    sr_audio, audio_data = wavfile.read(str(b_wav))
    if audio_data.dtype == np.int16:
        audio_norm = audio_data.astype(np.float32) / 32768.0
    else:
        audio_norm = audio_data.astype(np.float32)
    seeded_ranges = select.select(all_words, audio_norm, sr_audio)
    print(f"  ✓ seeded {len(seeded_ranges)} segments")

    seg_json = _build_segments_json(
        batch_n, vid_n, title, offset, dominance,
        a_video.relative_to(lib).as_posix(),
        b_video.relative_to(lib).as_posix(),
        seeded_ranges, all_words, transcript_segs,
    )
    seg_path = cut_dir / "SEGMENTS.json"
    seg_path.write_text(json.dumps(seg_json, indent=2), encoding="utf-8")
    print(f"  ✓ wrote {seg_path}")

    # --- Build 720p proxy + HyperFrames trim-review ---
    print(f"\n[6/6] BUILD PROXY + TRIM-REVIEW")
    repo_root = Path(config.__file__).resolve().parents[2]
    proj = repo_root / "web-apps" / "hyperframes" / f"sai-b{batch_n}v{vid_n:02d}-trim-review"
    proj.mkdir(parents=True, exist_ok=True)
    review.make_proxy(b_video, proj / "bcam.mp4")
    review.build_review(
        [{"in": s["in"], "out": s["out"], "text": s["text"],
          "tag": s["tag"], "tail": s["tail"]} for s in seg_json["segments"]],
        "bcam.mp4", proj,
    )

    print(f"\n{'='*60}")
    print(f"PREP DONE")
    print(f"{'='*60}")
    print(f"1. Review the trim:  cd \"{proj}\"  &&  npx hyperframes preview")
    print(f"2. Edit segments:    {seg_path}")
    print(f"3. Render:           python orchestrate.py --batch {batch_n} --video {vid_n} --render")
    print(f"{'='*60}\n")


def orchestrate(batch_n: int, vid_n: int):
    """Run the full pipeline on a single video."""
    lib = config.library_root()
    vid_folder = lib / f"01_ORGANIZED/Batch_{batch_n:02d}/Vid_{vid_n:02d}"
    a_cam_folder = vid_folder / "A-cam"
    b_cam_folder = vid_folder / "B-cam"

    # Find video files
    a_videos = list(a_cam_folder.glob("*.MP4"))
    b_videos = list(b_cam_folder.glob("*.MP4"))
    if not a_videos or not b_videos:
        raise RuntimeError(f"No A-cam or B-cam video found in {vid_folder}")

    a_video = a_videos[0]
    b_video = b_videos[0]
    print(f"\n{'='*60}")
    print(f"BATCH {batch_n} VIDEO {vid_n} — {a_video.stem}")
    print(f"{'='*60}")

    # --- Create working directory ---
    work_dir = vid_folder / "Synced"
    work_dir.mkdir(exist_ok=True)
    print(f"\n[1/7] WORK DIR: {work_dir}")

    # --- Extract audio for sync ---
    print(f"\n[2/7] EXTRACT AUDIO FOR SYNC")
    a_wav_tmp = work_dir / "a_audio.wav"
    b_wav_tmp = work_dir / "b_audio.wav"
    _extract_audio(a_video, a_wav_tmp)
    _extract_audio(b_video, b_wav_tmp)

    # --- Sync via cross-correlation ---
    print(f"\n[3/7] SYNC AUDIO")
    offset = sync.compute_offset(a_wav_tmp, b_wav_tmp)
    print(f"  offset: {offset:+.4f}s (B's time = A's time + offset)")
    residual_check = min(abs(offset - round(offset, 2)) * 1000, 0.5)  # Shouldn't be way off
    print(f"  residual: {residual_check:.1f}ms")

    # --- Determine sync trim points (find overlap region) ---
    # If B starts 5s after A, we trim A from 5s onward and B from 0 onward
    if offset >= 0:
        # B started after A; trim A's head
        trim_a_in, trim_b_in = offset, 0.0
    else:
        # A started after B; trim B's head
        trim_a_in, trim_b_in = 0.0, -offset

    # Get video duration (use the shorter one as the limit)
    probe_a = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(a_video)],
        capture_output=True, text=True
    ).stdout.strip()
    probe_b = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(b_video)],
        capture_output=True, text=True
    ).stdout.strip()

    dur_a = float(probe_a) - trim_a_in
    dur_b = float(probe_b) - trim_b_in
    sync_duration = min(dur_a, dur_b)

    trim_a_out = trim_a_in + sync_duration
    trim_b_out = trim_b_in + sync_duration

    print(f"  trim A: {trim_a_in:.2f}–{trim_a_out:.2f}s")
    print(f"  trim B: {trim_b_in:.2f}–{trim_b_out:.2f}s")

    # --- Create synced angle videos ---
    print(f"\n[4/7] CREATE SYNCED ANGLE VIDEOS")
    synced_a = work_dir / f"B{batch_n}_V{vid_n:02d}_A-cam_SYNCED.mov"
    synced_b = work_dir / f"B{batch_n}_V{vid_n:02d}_B-cam_SYNCED.mov"
    _extract_trim(a_video, trim_a_in, trim_a_out, synced_a, config.PRORES422)
    _extract_trim(b_video, trim_b_in, trim_b_out, synced_b, config.PRORES422)

    # --- Extract and clean lav audio ---
    print(f"\n[5/7] EXTRACT & CLEAN LAV AUDIO")
    lav_cam = _detect_lav_cam(a_wav_tmp, b_wav_tmp)
    print(f"  detected LAV on {lav_cam}-cam")

    lav_video = b_video if lav_cam == "B" else a_video
    lav_offset = trim_b_in if lav_cam == "B" else trim_a_in

    lav_wav_raw = work_dir / "lav_raw.wav"
    _extract_audio(lav_video, lav_wav_raw)

    # Trim to sync region
    sr, lav_data = wavfile.read(str(lav_wav_raw))
    if lav_data.ndim > 1:
        lav_data = lav_data.mean(axis=1)
    i_start = max(0, int(lav_offset * sr))
    i_end = min(len(lav_data), int((lav_offset + sync_duration) * sr))
    lav_data_trimmed = lav_data[i_start:i_end].astype(np.int16)

    lav_wav_trimmed = work_dir / "lav_trimmed.wav"
    print(f"  writing trimmed audio: {i_start//sr:.2f}–{i_end//sr:.2f}s ({len(lav_data_trimmed)} samples)")
    wavfile.write(str(lav_wav_trimmed), sr, lav_data_trimmed)

    if not lav_wav_trimmed.exists():
        raise RuntimeError(f"Failed to create {lav_wav_trimmed}")
    print(f"  ✓ trimmed LAV audio: {lav_wav_trimmed.name}")

    # Clean
    lav_wav_clean = audio_clean.clean(lav_wav_trimmed)
    print(f"  ✓ cleaned LAV audio")

    # --- Transcribe ---
    print(f"\n[6/7] TRANSCRIBE")
    words_json_path = work_dir / "words.json"
    words_data = transcribe.transcribe(lav_wav_clean)
    words_json_path.write_text(json.dumps(words_data, indent=2))
    # Flatten words for select.py
    all_words = [w for seg in words_data["segments"] for w in seg.get("words", [])]
    print(f"  ✓ {len(all_words)} words transcribed")

    # --- Auto-select ranges ---
    print(f"\n[7/7] AUTO-SELECT RANGES")
    sr_audio, audio_data = wavfile.read(str(lav_wav_clean))
    # Normalize audio to float [-1, 1]
    if audio_data.dtype == np.int16:
        audio_norm = audio_data.astype(np.float32) / 32768.0
    else:
        audio_norm = audio_data.astype(np.float32)
    proposed_ranges = select.select(all_words, audio_norm, sr_audio)
    total_duration = sum(r[1] - r[0] for r in proposed_ranges)
    print(f"  ✓ proposed {len(proposed_ranges)} segments, {total_duration:.1f}s total")

    # --- Build config JSON ---
    config_dict = {
        "batch_n": batch_n,
        "vid_n": vid_n,
        "title": f"Video {vid_n}",  # TODO: read from _INFO.txt
        "synced_a": str(synced_a.relative_to(lib)),
        "synced_b": str(synced_b.relative_to(lib)),
        "lav_wav": str(lav_wav_clean.relative_to(lib)),
        "words_json": str(words_json_path.relative_to(lib)),
        "lav": lav_cam,
        "ranges": proposed_ranges,
    }

    config_json = work_dir / "config.json"
    config_json.write_text(json.dumps(config_dict, indent=2))
    print(f"\n✓ Config saved: {config_json}")

    # Done. Output files are ready for manual editing in Premiere.
    print(f"\n{'='*60}")
    print(f"DONE — Materials ready for editing:")
    print(f"{'='*60}")
    print(f"Synced A-cam:    {synced_a}")
    print(f"Synced B-cam:    {synced_b}")
    print(f"Cleaned audio:   {lav_wav_clean}")
    print(f"Auto-selected ranges: {len(proposed_ranges)} segments, {total_duration:.1f}s")
    print(f"Range details:   {config_json}")
    print(f"\nImport the synced MOVs into Premiere on a multicam timeline.")
    print(f"Use the cleaned audio as your lav track.")
    print(f"Cut to the ranges in config.json for editorial guidance.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser("Batch video pipeline: --prep, then (Gray edits), then --render")
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--video", type=int, required=True)
    p.add_argument("--prep", action="store_true", help="PREP phase: sync, transcribe, seed segments, build trim-review")
    p.add_argument("--render", action="store_true", help="RENDER phase (built by the render task)")
    args = p.parse_args()

    if args.prep:
        prep(args.batch, args.video)
    elif args.render:
        render_mod.render(args.batch, args.video)
    else:
        print("Human-in-the-loop pipeline. Run --prep first, edit Cut/SEGMENTS.json, then --render.")
