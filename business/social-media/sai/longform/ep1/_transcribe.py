import os, glob, mlx_whisper, datetime
BASE = os.path.expanduser("~/Desktop/my-project/business/social-media/sai/longform/ep1")
AUD = os.path.join(BASE, "_audio")
OUT = os.path.join(BASE, "_transcripts")
os.makedirs(OUT, exist_ok=True)
MODEL = "mlx-community/whisper-large-v3-mlx"
files = sorted(glob.glob(os.path.join(AUD, "*.mp3")))
def ts(s):
    return str(datetime.timedelta(seconds=int(s)))
for i, f in enumerate(files, 1):
    name = os.path.splitext(os.path.basename(f))[0]
    outp = os.path.join(OUT, name + ".md")
    if os.path.exists(outp):
        print(f"[{i}/{len(files)}] skip {name}", flush=True)
        continue
    print(f"[{i}/{len(files)}] transcribing {name} ...", flush=True)
    r = mlx_whisper.transcribe(f, path_or_hf_repo=MODEL, language="en")
    lines = [f"# {name}\n"]
    for seg in r["segments"]:
        lines.append(f"[{ts(seg['start'])}] {seg['text'].strip()}")
    with open(outp, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"[{i}/{len(files)}] done -> {name}", flush=True)
print("ALL DONE", flush=True)
