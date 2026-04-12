"""
Assembles the final 9:16 Short using FFmpeg subprocess calls.

Timeline:
  [0-5s]   HeyGen hook avatar (with its audio)
  [5-17s]  Story 1: B-roll + ElevenLabs VO + headline text overlay
  [17-29s] Story 2: B-roll + ElevenLabs VO + headline text overlay
  [29-41s] Story 3: B-roll + ElevenLabs VO + headline text overlay
  [41-45s] HeyGen outro avatar (with its audio)

Background music runs at low volume under all segments.
"""

import subprocess
import shutil
import json
from pathlib import Path
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_CRF,
    HOOK_DURATION, STORY_DURATION, OUTRO_DURATION,
    MUSIC_VOLUME, MUSIC_DIR, FONTS_DIR, TMP_DIR, CHANNEL_NAME,
)


def assemble_video(
    script: dict,
    hook_path: Path,
    outro_path: Path,
    broll_paths: dict,       # {0: {video: Path, screenshot: Path}, ...}
    voiceover_paths: dict,   # {0: Path, 1: Path, 2: Path}
    output_path: Path,
) -> Path:
    _check_ffmpeg()

    # Prep individual segments
    hook_prep  = _scale_video(hook_path,  TMP_DIR / 'hook_scaled.mp4',  HOOK_DURATION)
    outro_prep = _scale_video(outro_path, TMP_DIR / 'outro_scaled.mp4', OUTRO_DURATION)

    broll_preps = []
    for i, story in enumerate(script['stories']):
        broll_video = broll_paths.get(i, {}).get('video')
        if not broll_video or not broll_video.exists():
            broll_video = _generate_fallback_broll(i)
        prep = _prepare_broll_segment(broll_video, i, STORY_DURATION)
        broll_preps.append(prep)

    # Generate SRT caption file
    srt_path = _build_srt(script)

    # Final assembly
    music_file = _pick_music()
    _final_assembly(
        hook_prep, outro_prep, broll_preps,
        voiceover_paths, script, srt_path, music_file, output_path,
    )

    print(f"[video] Assembled: {output_path}")
    return output_path


# ─── Segment preparation ──────────────────────────────────────────────────────

def _scale_video(src: Path, dst: Path, duration: float) -> Path:
    """Scale and crop any video to 1080x1920, trim to duration."""
    if dst.exists():
        return dst
    cmd = [
        'ffmpeg', '-y',
        '-i', str(src),
        '-t', str(duration),
        '-vf', (
            f'scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,'
            f'crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}'
        ),
        '-r', str(VIDEO_FPS),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', str(VIDEO_CRF),
        '-an',   # Strip audio — will be mixed separately
        str(dst),
    ]
    _run(cmd, f"scale {src.name}")
    return dst


def _prepare_broll_segment(broll_video: Path, index: int, duration: float) -> Path:
    """Loop B-roll to fill the story duration, scaled to 1080x1920."""
    dst = TMP_DIR / f'broll{index}_ready.mp4'
    if dst.exists():
        return dst
    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1',    # Loop video indefinitely
        '-i', str(broll_video),
        '-t', str(duration),
        '-vf', (
            f'scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,'
            f'crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}'
        ),
        '-r', str(VIDEO_FPS),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', str(VIDEO_CRF),
        '-an',
        str(dst),
    ]
    _run(cmd, f"prepare broll {index}")
    return dst


def _generate_fallback_broll(index: int) -> Path:
    """Black fallback clip if Pexels had no results."""
    dst = TMP_DIR / f'broll{index}_fallback.mp4'
    if dst.exists():
        return dst
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=c=0x111111:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:rate={VIDEO_FPS}',
        '-t', str(STORY_DURATION),
        '-c:v', 'libx264', '-preset', 'fast',
        str(dst),
    ]
    _run(cmd, f"fallback broll {index}")
    return dst


# ─── SRT captions ─────────────────────────────────────────────────────────────

def _build_srt(script: dict) -> Path:
    """Write an SRT file with story title captions timed to each segment."""
    srt_path = TMP_DIR / 'captions.srt'
    lines = []
    idx = 1

    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    offset = float(HOOK_DURATION)
    for i, story in enumerate(script['stories']):
        start = offset + i * STORY_DURATION
        end   = start + STORY_DURATION - 0.5
        lines.append(f"{idx}")
        lines.append(f"{ts(start)} --> {ts(end)}")
        lines.append(story['title'].upper())
        lines.append("")
        idx += 1

    srt_path.write_text("\n".join(lines), encoding='utf-8')
    return srt_path


# ─── Final assembly ───────────────────────────────────────────────────────────

def _final_assembly(
    hook_prep, outro_prep, broll_preps,
    voiceover_paths, script, srt_path, music_file, output_path: Path,
):
    """
    One FFmpeg pass: concat video segments, burn captions, mix audio (VO + music).
    Hook and outro use HeyGen audio. Stories use ElevenLabs VO + background music.
    """

    # Build concat list for video segments (no audio)
    concat_txt = TMP_DIR / 'concat.txt'
    segments = [hook_prep] + broll_preps + [outro_prep]
    concat_txt.write_text(
        "\n".join(f"file '{str(s.resolve()).replace(chr(92), chr(47))}'" for s in segments)
    )

    # Step 1: Concat video-only track
    concat_vid = TMP_DIR / 'concat_video.mp4'
    _run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', str(concat_txt),
        '-c:v', 'copy',
        str(concat_vid),
    ], "concat video")

    # Step 2: Build full audio track
    # hook audio + story VOs + outro audio
    hook_audio  = TMP_DIR / 'hook_audio.aac'
    outro_audio = TMP_DIR / 'outro_audio.aac'
    _extract_audio(hook_prep,  hook_audio,  HOOK_DURATION)
    _extract_audio(outro_prep, outro_audio, OUTRO_DURATION)

    # Concat audio: hook + story1 + story2 + story3 + outro
    audio_concat_txt = TMP_DIR / 'audio_concat.txt'
    audio_files = [hook_audio]
    for i in range(len(script['stories'])):
        vo = voiceover_paths.get(i)
        if vo and vo.exists():
            audio_files.append(vo)
        else:
            # Silence fallback
            silence = TMP_DIR / f'silence_{i}.aac'
            if not silence.exists():
                _run([
                    'ffmpeg', '-y',
                    '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo',
                    '-t', str(STORY_DURATION), '-c:a', 'aac',
                    str(silence),
                ], f"silence {i}")
            audio_files.append(silence)
    audio_files.append(outro_audio)

    audio_concat_txt.write_text(
        "\n".join(f"file '{str(a.resolve()).replace(chr(92), chr(47))}'" for a in audio_files)
    )
    vo_track = TMP_DIR / 'vo_track.aac'
    _run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', str(audio_concat_txt),
        '-c:a', 'aac', '-ar', '44100',
        str(vo_track),
    ], "concat audio")

    # Step 3: Final mix — concat_vid + caption burn + VO + music
    font_path = _find_font()
    srt_escaped = str(srt_path.resolve()).replace('\\', '/').replace(':', r'\:')

    filter_complex = (
        f"[0:v]subtitles='{srt_escaped}':force_style='FontName={font_path},"
        f"FontSize=52,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"BackColour=&H80000000,Outline=2,Shadow=1,Alignment=2,"
        f"MarginV=120'[burnt]"
    )

    if music_file and music_file.exists():
        music_vol = MUSIC_VOLUME
        # Get total video duration to loop music
        total_dur = HOOK_DURATION + len(script['stories']) * STORY_DURATION + OUTRO_DURATION
        _run([
            'ffmpeg', '-y',
            '-i', str(concat_vid),
            '-i', str(vo_track),
            '-stream_loop', '-1', '-i', str(music_file),
            '-filter_complex',
            f"{filter_complex};"
            f"[2:a]volume={music_vol},atrim=0:{total_dur}[music];"
            f"[1:a][music]amix=inputs=2:duration=first[aout]",
            '-map', '[burnt]', '-map', '[aout]',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', str(VIDEO_CRF),
            '-c:a', 'aac', '-ar', '44100', '-b:a', '192k',
            '-shortest',
            str(output_path),
        ], "final assembly")
    else:
        _run([
            'ffmpeg', '-y',
            '-i', str(concat_vid),
            '-i', str(vo_track),
            '-filter_complex', f"{filter_complex}",
            '-map', '[burnt]', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', str(VIDEO_CRF),
            '-c:a', 'aac', '-ar', '44100', '-b:a', '192k',
            '-shortest',
            str(output_path),
        ], "final assembly (no music)")


def _extract_audio(video: Path, out: Path, duration: float):
    if out.exists():
        return
    _run([
        'ffmpeg', '-y',
        '-i', str(video),
        '-t', str(duration),
        '-vn', '-c:a', 'aac', '-ar', '44100',
        str(out),
    ], f"extract audio {video.name}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_ffmpeg():
    if not shutil.which('ffmpeg'):
        raise EnvironmentError(
            "ffmpeg not found in PATH.\n"
            "Install: https://ffmpeg.org/download.html or run setup.py"
        )


def _pick_music() -> Path | None:
    music_files = list(MUSIC_DIR.glob('*.mp3')) + list(MUSIC_DIR.glob('*.m4a'))
    return music_files[0] if music_files else None


def _find_font() -> str:
    for f in FONTS_DIR.glob('*.ttf'):
        return str(f.resolve()).replace('\\', '/')
    # Fallback to system font on Windows
    system_font = Path('C:/Windows/Fonts/arial.ttf')
    if system_font.exists():
        return str(system_font).replace('\\', '/')
    return 'Arial'


def _run(cmd: list[str], label: str):
    print(f"[ffmpeg] {label}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg '{label}' failed:\n{result.stderr[-800:]}")
