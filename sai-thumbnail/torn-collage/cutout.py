import sys
from rembg import remove, new_session
from PIL import Image

src = sys.argv[1]
out = sys.argv[2]

session = new_session("u2net_human_seg")
img = Image.open(src).convert("RGBA")
res = remove(img, session=session)

# drop floating fragments — keep only the largest connected blob (the person)
import numpy as np
from scipy import ndimage
alpha = np.array(res.split()[-1])
mask = alpha > 12
labeled, n = ndimage.label(mask)
if n > 1:
    sizes = ndimage.sum(mask, labeled, range(1, n + 1))
    largest = int(np.argmax(sizes)) + 1
    keep = labeled == largest
    res.putalpha(Image.fromarray(np.where(keep, alpha, 0).astype("uint8")))

# crop to the non-transparent bounding box
bbox = res.getbbox()
if bbox:
    res = res.crop(bbox)
res.save(out)
print("wrote", out, res.size)
