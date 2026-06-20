import subprocess, os
from concurrent.futures import ThreadPoolExecutor
PATHS = """05_FOOTAGE_LIBRARY/candid-people/W03_Apr-27-May-3/C2345.MP4
05_FOOTAGE_LIBRARY/candid-people/W03_Apr-27-May-3/C2349.MP4
05_FOOTAGE_LIBRARY/candid-people/W03_Apr-27-May-3/C2353.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2110.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2132.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2152.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2156.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2206.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2207.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2208.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2211.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2214.MP4
05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2219.MP4
05_FOOTAGE_LIBRARY/screens-and-text/W02_Apr-20-26/C2150.MP4
05_FOOTAGE_LIBRARY/walk-and-talk/W02_Apr-20-26/C2148.MP4
05_FOOTAGE_LIBRARY/walk-and-talk/W02_Apr-20-26/C2149.MP4
05_FOOTAGE_LIBRARY/interview-solo/W03_Apr-27-May-3/C2360.MP4
05_FOOTAGE_LIBRARY/interview-solo/W03_Apr-27-May-3/C2361.MP4
05_FOOTAGE_LIBRARY/interview-solo/W03_Apr-27-May-3/C2362.MP4
05_FOOTAGE_LIBRARY/misc/W03_Apr-27-May-3/C2358.MP4
05_FOOTAGE_LIBRARY/misc/W02_Apr-20-26/C2147.MP4
05_FOOTAGE_LIBRARY/misc/W02_Apr-20-26/C2151.MP4
05_FOOTAGE_LIBRARY/misc/W02_Apr-20-26/C2154.MP4
05_FOOTAGE_LIBRARY/misc/W02_Apr-20-26/C2155.MP4
05_FOOTAGE_LIBRARY/misc/W03_Apr-27-May-3/C2364.MP4
05_FOOTAGE_LIBRARY/misc/W03_Apr-27-May-3/C2363.MP4
05_FOOTAGE_LIBRARY/establishing-interior/W02_Apr-20-26/C2143.MP4
05_FOOTAGE_LIBRARY/establishing-interior/W02_Apr-20-26/C2142.MP4
05_FOOTAGE_LIBRARY/establishing-interior/W03_Apr-27-May-3/C2347.MP4
05_FOOTAGE_LIBRARY/establishing-interior/old-broll/C1106.MP4
05_FOOTAGE_LIBRARY/insert-hands/old-broll/C1074.MP4
05_FOOTAGE_LIBRARY/interview-solo/old-broll/C1079.MP4
05_FOOTAGE_LIBRARY/interview-solo/old-broll/C1085.MP4
05_FOOTAGE_LIBRARY/interview-solo/old-broll/C1080.MP4
05_FOOTAGE_LIBRARY/interview-solo/old-broll/C1078.MP4
05_FOOTAGE_LIBRARY/interview-solo/old-broll/C1084.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1081.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1082.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1112.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1108.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1075.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1109.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1111.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1077.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1076.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1110.MP4
05_FOOTAGE_LIBRARY/misc/old-broll/C1107.MP4
05_FOOTAGE_LIBRARY/candid-people/old-broll/C1083.MP4""".strip().split('\n')
os.makedirs('.tmp_b3v9/frames', exist_ok=True)
def ext(p):
    cid=os.path.basename(p).replace('.MP4','')
    out='.tmp_b3v9/frames/'+cid+'.jpg'
    subprocess.run(['ffmpeg','-y','-ss','1','-i','D:/Sai/'+p,'-frames:v','1','-vf','scale=320:-1',out],capture_output=True,timeout=60)
    return out if os.path.exists(out) else None
with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(ext, PATHS))
print('FRAMES_DONE', len([f for f in os.listdir('.tmp_b3v9/frames') if f.endswith('.jpg')]))
