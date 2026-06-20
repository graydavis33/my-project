import subprocess, re, sys
paths=[l.strip() for l in open(r'D:/Sai/07_QUERY_PULLS/_cand.txt') if l.strip()]
horiz=[]
for i,p in enumerate(paths):
    full='D:/Sai/'+p
    try:
        o=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height:stream_tags=rotate:side_data=rotation',
            '-of','default=noprint_wrappers=1',full],capture_output=True,text=True,timeout=45).stdout
    except Exception:
        print('TIMEOUT',p,flush=True); continue
    rots=[int(x) for x in re.findall(r'rotat[a-z_]*[=:]\s*(-?\d+)',o)]
    if not any(abs(x) in (90,270) for x in rots):
        horiz.append(p)
    if i%50==0: print('...',i,'/',len(paths),'horiz',len(horiz),flush=True)
with open(r'D:/Sai/07_QUERY_PULLS/_horizFINAL.txt','w') as f:
    f.write('\n'.join(horiz)+'\n')
print('FINAL',len(horiz),flush=True)
