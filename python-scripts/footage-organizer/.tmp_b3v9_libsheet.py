import os, importlib.util, sqlite3
spec=importlib.util.spec_from_file_location('sheet','.tmp_b3v9_sheet.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
db=sqlite3.connect(r'D:/Sai/.footage-index.sqlite')
with open(r'D:/Sai/07_QUERY_PULLS/_horiz.txt') as f:
    paths=[l.strip() for l in f if l.strip()]
print('horiz clips:',len(paths))
items=[]
for p in paths:
    cid=os.path.basename(p).replace('.MP4','').replace('.mp4','')
    r=db.execute('select category from clips where path=?',(p,)).fetchone()
    cat=(r[0] if r else '?')[:8]
    jp=m.extract('D:/Sai/'+p,'lib_'+cid)
    items.append((jp, cid+' '+cat, p))
# batch into sheets of 16
B=16
for bi in range(0,len(items),B):
    chunk=items[bi:bi+B]
    m.sheet([(i[0],i[1]) for i in chunk], f'D:/Sai/07_QUERY_PULLS/_sheet_lib_{bi//B}.jpg', cols=4)
# save mapping
with open(r'D:/Sai/07_QUERY_PULLS/_libmap.txt','w') as f:
    for i in items: f.write(i[1].split()[0]+'\t'+i[2]+'\n')
print('sheets written:', (len(items)+B-1)//B)
