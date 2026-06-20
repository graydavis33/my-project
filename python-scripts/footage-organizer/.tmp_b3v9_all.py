import subprocess, os
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
PATHS=[l.strip() for l in open('.tmp_b3v9_paths.txt') if l.strip()]
os.makedirs('.tmp_b3v9/frames', exist_ok=True)
def ext(p):
    cid=os.path.basename(p).replace('.MP4','')
    out='.tmp_b3v9/frames/'+cid+'.jpg'
    if os.path.exists(out): return (out,cid)
    r=subprocess.run(['ffmpeg','-y','-ss','0.5','-i','D:/Sai/'+p,'-frames:v','1','-vf','scale=320:-1',out],capture_output=True,timeout=90)
    return (out if os.path.exists(out) else None, cid)
res=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    res=list(ex.map(ext, PATHS))
def sheet(items, outpath, cols=4, cell=320):
    valid=[(p,l) for p,l in items if p and os.path.exists(p)]
    if not valid: return 0
    rows=(len(valid)+cols-1)//cols
    cw,ch=cell, cell*9//16+22
    s=Image.new('RGB',(cols*cw,rows*ch),(20,20,20)); d=ImageDraw.Draw(s)
    try: font=ImageFont.truetype('arial.ttf',16)
    except: font=ImageFont.load_default()
    for i,(p,l) in enumerate(valid):
        im=Image.open(p).convert('RGB'); im.thumbnail((cw,cell*9//16))
        x=(i%cols)*cw; y=(i//cols)*ch
        s.paste(im,(x,y+20)); d.rectangle([x,y,x+cw,y+20],fill=(0,0,0))
        d.text((x+4,y+2),l,fill=(255,180,60),font=font)
    s.save(outpath,quality=85); return len(valid)
items=[(p,c) for p,c in res]
n1=sheet(items[:24], '.tmp_b3v9/sheetA.jpg')
n2=sheet(items[24:], '.tmp_b3v9/sheetB.jpg')
print('SHEETS_DONE', n1, n2)
