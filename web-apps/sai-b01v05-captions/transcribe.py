"""Transcribe source.aac -> words.json (word-level timestamps)."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import whisper

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

HERE = Path(__file__).parent
WAV = HERE / "source.wav"
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(HERE/"source.aac"),
                "-ac","1","-ar","16000","-c:a","pcm_s16le",str(WAV)], check=True)

model = whisper.load_model("large-v3", device="cuda")
result = model.transcribe(str(WAV), word_timestamps=True, language="en", fp16=True, verbose=False)
words = []
for seg in result["segments"]:
    for w in seg.get("words", []):
        words.append({"word": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])})
(HERE/"words.json").write_text(json.dumps(words, indent=2), encoding="utf-8")
print(f"{len(words)} words")
print(result["text"].strip())
