import subprocess, os, sys, shutil
sys.stdout.reconfigure(encoding="utf-8")

SAI = "D:/Sai"
EP2 = next(os.path.join(SAI,x) for x in os.listdir(SAI)
           if x.lower().startswith("b-roll") and "17" in x)
PULL = "D:/Sai/07_QUERY_PULLS/b3v4-broll"
FRAMES = "D:/Sai/07_QUERY_PULLS/_b3v4_frames"

def probe(f):
    out = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height:stream_tags=rotate:side_data=rotation",
        "-of","default=noprint_wrappers=1", f], capture_output=True, text=True)
    vals = {}
    for l in out.stdout.strip().splitlines():
        if "=" in l:
            k,v = l.split("=",1); vals[k]=v
    w,h = vals.get("width"), vals.get("height")
    rot = vals.get("rotate") or vals.get("rotation") or ""
    disp_vert = (rot in ("90","-90","270")) or (h and w and int(h)>int(w))
    return w,h,rot,disp_vert

def db():
    import sqlite3
    return sqlite3.connect(r"D:/Sai/.footage-index.sqlite")

def cmd_probe_ep2():
    files = sorted([os.path.join(EP2,x) for x in os.listdir(EP2) if x.upper().endswith(".MP4")])
    print("EP2 folder:", EP2)
    print("found", len(files))
    for f in files:
        w,h,rot,dv = probe(f)
        print(os.path.basename(f), f"{w}x{h}", "rot=["+rot+"]", "VERTICAL" if dv else "HORIZONTAL")

def cmd_lib_horiz():
    # candidate categories, report horizontal-only with full path + duration
    cats = ("establishing-exterior","establishing-interior","interview-solo",
            "candid-people","insert-hands","insert-detail","walk-and-talk",
            "misc","insert-product","reaction-listening","action-sport-fitness")
    c = db()
    rows = c.execute(
        "select path,category,filmed_date,duration_s,width,height from clips "
        "where category in ({}) order by category,filmed_date".format(
            ",".join("?"*len(cats))), cats).fetchall()
    horiz = []
    for path,cat,fd,dur,w,h in rows:
        full = os.path.join(SAI, path)
        if not os.path.exists(full):
            continue
        ww,hh,rot,dv = probe(full)
        if not dv:
            horiz.append((path,cat,fd,dur,ww,hh))
    print("HORIZONTAL library clips:", len(horiz))
    for path,cat,fd,dur,w,h in horiz:
        print(f"{cat}\t{fd}\t{dur}\t{w}x{h}\t{path}")

def cmd_frames(spec_file):
    # spec_file: lines of "label\tfullpath"
    os.makedirs(FRAMES, exist_ok=True)
    with open(spec_file, encoding="utf-8") as fh:
        for line in fh:
            line=line.strip()
            if not line: continue
            label, full = line.split("\t",1)
            out = os.path.join(FRAMES, label+".jpg")
            subprocess.run(["ffmpeg","-y","-ss","2","-i",full,"-frames:v","1",
                "-vf","scale=480:-1", out],capture_output=True)
            print("frame:", label, os.path.exists(out))

def cmd_sheet(prefix):
    from PIL import Image, ImageDraw, ImageFont
    import glob, math
    frames = sorted(glob.glob(os.path.join(FRAMES, prefix+"*.jpg")))
    if not frames:
        frames = sorted(glob.glob(os.path.join(FRAMES,"*.jpg")))
    cell, pad, cols = 360, 8, 4
    rows = math.ceil(len(frames)/cols)
    label_h = 22
    sheet = Image.new("RGB",(cols*(cell+pad)+pad, rows*(cell+label_h+pad)+pad),"black")
    d = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("arial.ttf",15)
    except: font = ImageFont.load_default()
    for i,f in enumerate(frames):
        im = Image.open(f); im.thumbnail((cell,cell))
        x = pad+(i%cols)*(cell+pad)
        y = pad+(i//cols)*(cell+label_h+pad)
        d.text((x,y), os.path.basename(f)[:-4], fill="white", font=font)
        sheet.paste(im,(x,y+label_h))
    out = f"D:/Sai/07_QUERY_PULLS/_b3v4_sheet_{prefix}.jpg"
    sheet.save(out); print(out, len(frames),"frames")

def cmd_copy(spec_file):
    # spec_file lines: beatfolder\tfullsrc
    with open(spec_file, encoding="utf-8") as fh:
        for line in fh:
            line=line.strip()
            if not line: continue
            beat, src = line.split("\t",1)
            dest_dir = os.path.join(PULL, beat)
            os.makedirs(dest_dir, exist_ok=True)
            w,h,rot,dv = probe(src)
            if dv:
                print("SKIP VERTICAL:", src); continue
            shutil.copy2(src, dest_dir)
            print("copied", beat, os.path.basename(src))

def cmd_verify():
    for beat in sorted(os.listdir(PULL)):
        bd = os.path.join(PULL,beat)
        if not os.path.isdir(bd): continue
        vids=[]; bad=[]
        for x in os.listdir(bd):
            full=os.path.join(bd,x)
            if x.lower().endswith((".mp4",".mov")):
                w,h,rot,dv=probe(full)
                vids.append(x);
                if dv: bad.append(x+" VERTICAL!")
            else:
                bad.append(x+" NOT-VIDEO!")
        print(f"{beat}: {len(vids)} videos", ("PROBLEMS: "+", ".join(bad)) if bad else "all horizontal videos OK")

def cmd_cleanup():
    import glob
    if os.path.isdir(FRAMES): shutil.rmtree(FRAMES)
    for s in glob.glob("D:/Sai/07_QUERY_PULLS/_b3v4_sheet_*.jpg"):
        os.remove(s)
    print("cleaned scratch")

if __name__ == "__main__":
    globals()["cmd_"+sys.argv[1]](*sys.argv[2:])
