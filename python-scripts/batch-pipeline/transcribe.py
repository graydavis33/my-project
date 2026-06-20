import json, subprocess, tempfile
from pathlib import Path
import config

def to_words(raw, shift):
    segs = []
    for s in raw.get("segments", []):
        ws = [{"start": round(float(w["start"])-shift, 3),
               "end": round(float(w["end"])-shift, 3),
               "word": w["word"].strip()} for w in s.get("words", [])]
        segs.append({"start": round(float(s["start"])-shift, 3),
                     "end": round(float(s["end"])-shift, 3), "words": ws})
    return {"segments": segs}

def transcribe(media, shift=0.0):
    if config.whisper_backend() == "openai":
        import whisper
        model = whisper.load_model("large-v3", device="cuda")
        raw = model.transcribe(str(media), language="en", word_timestamps=True)
    else:
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["mlx_whisper","--model","mlx-community/whisper-large-v3-mlx",
                "--word-timestamps","True","--language","en","--output-format","json",
                "--output-dir",td,str(media)], check=True)
            raw = json.loads(next(Path(td).glob("*.json")).read_text())
    return to_words(raw, shift)
