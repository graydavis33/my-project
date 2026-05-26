"""Transcribe Sai's batch-script voice memos using local Whisper (medium model).

Runs in this folder, writes part1-transcript.md and part2-transcript.md.
"""
import whisper, time
from pathlib import Path

MODEL = "medium"
HERE = Path(__file__).parent

print(f"Loading Whisper {MODEL} model (first run downloads ~1.5GB)...")
t0 = time.time()
model = whisper.load_model(MODEL)
print(f"  Loaded in {time.time()-t0:.1f}s")

for fname in ["part1.mp3", "part2.mp3"]:
    src = HERE / fname
    if not src.exists():
        print(f"SKIP — {src} not found")
        continue
    base = src.stem
    out = HERE / f"{base}-transcript.md"
    print(f"\nTranscribing {fname}...")
    t1 = time.time()
    result = model.transcribe(str(src), verbose=False)
    dur_audio = result["segments"][-1]["end"] if result["segments"] else 0
    elapsed = time.time() - t1
    print(f"  Audio: {dur_audio/60:.1f} min | Wall: {elapsed/60:.1f} min | Ratio: {elapsed/dur_audio:.2f}x realtime")

    with open(out, "w") as f:
        f.write(f"# Voice Memo Transcript — {base}\n\n")
        f.write(f"*Source: /Volumes/Footage/Sai/06_ASSETS/Voice Memos/{fname.replace('part1.mp3','Part 1 of batch scripts.m4a').replace('part2.mp3','Part 2 of batch script.m4a')}*\n")
        f.write(f"*Duration: {dur_audio:.0f}s ({dur_audio/60:.1f} min)*\n")
        f.write(f"*Model: Whisper {MODEL}*\n")
        f.write(f"*Transcribed: 2026-05-26*\n\n---\n\n")
        f.write("## Full Transcript\n\n")
        f.write(result["text"].strip() + "\n\n---\n\n")
        f.write("## Timestamped Segments\n\n")
        for seg in result["segments"]:
            mm = int(seg["start"] // 60); ss = int(seg["start"] % 60)
            f.write(f"**[{mm:02d}:{ss:02d}]** {seg['text'].strip()}\n\n")
    print(f"  Saved {out.name} ({len(result['text'])} chars, {len(result['segments'])} segments)")

print("\nDONE")
