import os, shutil
# Find B-roll folder real name
parent='D:/Sai'
brfolder=None
for d in os.listdir(parent):
    if d.startswith('B-roll'): brfolder=os.path.join(parent,d)

DEST='D:/Sai/07_QUERY_PULLS/b3v9-broll'
SETS={
 'sai-working-system':[
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2152.MP4'),   # Sai at desk/laptop in office
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2214.MP4'),   # Sai working at desk on laptop
    ('lib','05_FOOTAGE_LIBRARY/screens-and-text/W02_Apr-20-26/C2150.MP4'),# Sai laptop Zoom team call
    ('br','C2724.MP4'),  # Sai desk + mic + laptop + whiteboard, team call
 ],
 'structure-workspace':[
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2156.MP4'),   # office interior desks
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2211.MP4'),   # modern office interior
    ('br','C2732.MP4'),  # subway info display screen (system/data viz)
 ],
 'creative-thinking':[
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2110.MP4'),   # Sai thinking on couch
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W03_Apr-27-May-3/C2353.MP4'),# Sai reading/holding device
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W03_Apr-27-May-3/C2349.MP4'),# Sai by window
    ('br','C2729.MP4'),  # hands scrolling phone (ideas/input)
 ],
 'founder-journey':[
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2206.MP4'),   # Central Park skyline
    ('lib','05_FOOTAGE_LIBRARY/candid-people/W02_Apr-20-26/C2208.MP4'),   # Central Park skyline
    ('br','C2726.MP4'),  # Sai standing kitchen
    ('br','C2746.MP4'),  # detail texture
 ],
}
copied=[]; missing=[]
for theme,items in SETS.items():
    d=os.path.join(DEST,theme); os.makedirs(d,exist_ok=True)
    for kind,p in items:
        src = (brfolder+'/'+p) if kind=='br' else ('D:/Sai/'+p)
        name = os.path.basename(p)
        dst = os.path.join(d,name)
        if not os.path.exists(src):
            missing.append((theme,p)); continue
        shutil.copy2(src,dst); copied.append((theme,name))
print('COPIED', len(copied))
for t,n in copied: print('  ',t,n)
if missing:
    print('MISSING')
    for t,p in missing: print('  ',t,p)
