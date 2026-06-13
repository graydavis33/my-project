import os, glob, re, subprocess, datetime, mlx_whisper

SRC = "/Users/graydavis28/batch 3"
BASE = os.path.expanduser("~/Desktop/my-project/business/social-media/sai/longform/ep2")
AUD = os.path.join(BASE, "_audio")
OUT = os.path.join(BASE, "_transcripts")
os.makedirs(AUD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
MODEL = "mlx-community/whisper-large-v3-mlx"

def ts(s):
    return str(datetime.timedelta(seconds=int(s)))

def folder_date(folder):
    m = re.match(r"(\d{2})[:\-](\d{2})[:\-](\d{2})", folder)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None

def clip_date(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags=creation_time",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True).stdout.strip()
    if len(out) >= 10 and out[4] == "-":
        y, mo, da = out[:10].split("-")
        return f"{mo}-{da}-{y[2:]}"
    return "restweek"

# Gather every clip across the dropped folders, named <date>_<clip> to match Ep 1
clips = []
for folder in sorted(os.listdir(SRC)):
    fpath = os.path.join(SRC, folder)
    if not os.path.isdir(fpath):
        continue
    fd = folder_date(folder)
    mp4s = sorted(glob.glob(os.path.join(fpath, "*.MP4")) + glob.glob(os.path.join(fpath, "*.mp4")))
    for mp4 in mp4s:
        clipname = os.path.splitext(os.path.basename(mp4))[0]
        date = fd or clip_date(mp4)
        clips.append((f"{date}_{clipname}", mp4))

print(f"Found {len(clips)} clips across {SRC}", flush=True)

# Step 1 — extract 16kHz mono mp3 (fast, audio only)
for i, (name, mp4) in enumerate(clips, 1):
    mp3 = os.path.join(AUD, name + ".mp3")
    if os.path.exists(mp3):
        continue
    print(f"[extract {i}/{len(clips)}] {name}", flush=True)
    subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vn", "-ac", "1", "-ar", "16000", mp3],
                   capture_output=True)

# Step 2 — transcribe each with mlx-whisper, timestamped markdown
for i, (name, mp4) in enumerate(clips, 1):
    mp3 = os.path.join(AUD, name + ".mp3")
    outp = os.path.join(OUT, name + ".md")
    if os.path.exists(outp):
        print(f"[{i}/{len(clips)}] skip {name}", flush=True)
        continue
    print(f"[{i}/{len(clips)}] transcribing {name} ...", flush=True)
    r = mlx_whisper.transcribe(mp3, path_or_hf_repo=MODEL, language="en")
    lines = [f"# {name}\n"]
    for seg in r["segments"]:
        lines.append(f"[{ts(seg['start'])}] {seg['text'].strip()}")
    with open(outp, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"[{i}/{len(clips)}] done -> {name}", flush=True)

print("ALL DONE", flush=True)
