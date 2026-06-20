import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont
FRAMES = 'D:/Sai/07_QUERY_PULLS/_frames'
os.makedirs(FRAMES, exist_ok=True)

def extract(clip, name):
    out = os.path.join(FRAMES, name + '.jpg')
    subprocess.run(['ffmpeg','-y','-ss','1','-i',clip,'-frames:v','1','-vf','scale=320:-1',out],
                   capture_output=True, timeout=60)
    return out if os.path.exists(out) else None

def sheet(items, outpath, cols=4, cell=320):
    # items = list of (jpgpath, label)
    valid=[(p,l) for p,l in items if p and os.path.exists(p)]
    if not valid: 
        print('no frames'); return
    rows=(len(valid)+cols-1)//cols
    cw, ch = cell, cell*9//16 + 22
    sheet=Image.new('RGB',(cols*cw, rows*ch),(20,20,20))
    d=ImageDraw.Draw(sheet)
    try: font=ImageFont.truetype('arial.ttf',16)
    except: font=ImageFont.load_default()
    for i,(p,l) in enumerate(valid):
        im=Image.open(p).convert('RGB')
        im.thumbnail((cw, cell*9//16))
        x=(i%cols)*cw; y=(i//cols)*ch
        sheet.paste(im,(x,y+20))
        d.rectangle([x,y,x+cw,y+20],fill=(0,0,0))
        d.text((x+4,y+2),l,fill=(255,180,60),font=font)
    sheet.save(outpath, quality=85)
    print('wrote', outpath, len(valid),'cells')

if __name__=='__main__':
    pass
