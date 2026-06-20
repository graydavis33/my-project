import subprocess, re
from concurrent.futures import ThreadPoolExecutor
paths=[l.strip() for l in open(r'D:/Sai/07_QUERY_PULLS/_cand.txt') if l.strip()]
def chk(p):
    try:
        o=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
          '-show_entries','stream=tags=rotate:side_data=rotation',
          '-of','default=noprint_wrappers=1','D:/Sai/'+p],
          capture_output=True,text=True,timeout=40).stdout
    except Exception:
        return (p,None)
    rots=[int(x) for x in re.findall(r'rotat[a-z_]*[=:]\s*(-?\d+)',o)]
    return (p, not any(abs(x) in (90,270) for x in rots))
horiz=[]; errs=[]
with ThreadPoolExecutor(max_workers=8) as ex:
    for p,ok in ex.map(chk,paths):
        if ok is None: errs.append(p)
        elif ok: horiz.append(p)
open(r'D:/Sai/07_QUERY_PULLS/_horizFINAL.txt','w').write('\n'.join(horiz)+'\n')
print('HORIZ',len(horiz),'ERR',len(errs),'TOTAL',len(paths))
