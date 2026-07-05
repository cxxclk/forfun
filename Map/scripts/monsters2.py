import json, numpy as np
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
from scipy import ndimage as ndi

BASE = '/sessions/lucid-practical-feynman/mnt/outputs'
MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization/Map'
im = Image.open(f'{MAPD}/Map.jpg').crop((10, 700, 1075, 1500)).convert('RGB')
arr = np.asarray(im).astype(float)
H, W = arr.shape[:2]

palette = [(239,243,179),(127,202,211),(138,216,170),(158,209,110),
           (234,247,222),(171,90,12),(130,18,12),(170,167,57),(196,120,30)]
dists = np.stack([np.linalg.norm(arr - np.array(c), axis=2) for c in palette])
fillmask = dists.min(axis=0) < 45          # generous fill detection
passable = ndi.binary_erosion(dists.min(axis=0) < 32, iterations=1)

seeds = json.load(open(f'{BASE}/seeds.json'))
names = sorted(seeds.keys())
idx = {n: i+1 for i, n in enumerate(names)}
markers = np.zeros((H, W), dtype=np.int32)
for n, (x, y) in seeds.items():
    x = min(max(int(x),3),W-4); y = min(max(int(y),3),H-4)
    if not passable[y, x]:
        for r in range(1, 26):
            ys, xs = np.mgrid[max(0,y-r):min(H,y+r+1), max(0,x-r):min(W,x+r+1)]
            m = passable[ys, xs]
            if m.any(): y, x = int(ys[m][0]), int(xs[m][0]); break
    markers[y, x] = idx[n]
labels = watershed(np.where(passable,0,1).astype(np.uint8), markers)

r, g, b = arr[...,0], arr[...,1], arr[...,2]
redtext = (r > 140) & (g < 100) & (b < 100) & (r - np.maximum(g,b) > 60)
blob = (~fillmask) & (~redtext)
blob = ndi.binary_opening(blob, iterations=1)
blob = ndi.binary_closing(blob, iterations=2)   # merge sprite parts
comp, ncomp = ndi.label(blob)

# assign each sufficiently-big blob to zone(s) by overlap; a blob may cover several sprites
zone_pix = {}   # zone -> list of (count, comp_id)
for ci in range(1, ncomp+1):
    m = comp == ci
    if m.sum() < 250: continue
    zs, cnts = np.unique(labels[m], return_counts=True)
    for z, c in zip(zs, cnts):
        if z == 0 or c < 150: continue
        zone_pix.setdefault(names[z-1], []).append((int(c), ci))

sprite_mask = {}
for n, lst in zone_pix.items():
    lst.sort(reverse=True)
    ci = lst[0][1]
    m = (comp == ci) & (labels == idx[n])   # only this zone's part of the blob
    sprite_mask[n] = m
missing = [n for n in names if n not in sprite_mask]
print('missing:', missing)

# features: color histogram of sprite pixels (RGB 4x4x4) L2-normalized
feats, order = [], []
crops = {}
for n, m in sprite_mask.items():
    ys, xs = np.where(m)
    x0,x1,y0,y1 = xs.min(), xs.max(), ys.min(), ys.max()
    crops[n] = im.crop((max(0,x0-3), max(0,y0-3), min(W,x1+3), min(H,y1+3)))
    px = arr[m]
    hist, _ = np.histogramdd(px, bins=(4,4,4), range=((0,256),)*3)
    hist = hist.flatten(); hist = hist/ (np.linalg.norm(hist)+1e-9)
    feats.append(hist); order.append(n)
feats = np.array(feats)

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
Dm = cosine_distances(feats)
cl = AgglomerativeClustering(n_clusters=None, distance_threshold=0.22,
                             metric='precomputed', linkage='average').fit(Dm)
groups = {}
for n, c in zip(order, cl.labels_):
    groups.setdefault(int(c), []).append(n)
print('clusters:', len(groups))
for c, zs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f'type{c:02d} ({len(zs)}):', sorted(zs))

cell, cols = 78, 12
rows = sum(1 + (len(zs)-1)//cols for zs in groups.values())
sheet = Image.new('RGB', (cols*cell, rows*cell+len(groups)*18+40), (30,33,26))
d = ImageDraw.Draw(sheet)
yoff = 0
for c, zs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    d.text((4, yoff+2), f'type{c:02d}', fill=(255,220,80))
    yoff += 18
    for i, n in enumerate(sorted(zs)):
        x = (i % cols)*cell; y = yoff + (i//cols)*cell
        t = crops[n].copy(); t.thumbnail((cell-6, cell-22))
        sheet.paste(t, (x+3, y+2))
        d.text((x+3, y+cell-17), n, fill=(255,255,255))
    yoff += (1 + (len(zs)-1)//cols)*cell
d.text((4, yoff+4), 'missing: '+', '.join(missing), fill=(255,120,120))
sheet.save(f'{BASE}/monster_sheet2.png')
json.dump({'clusters': {f'type{k:02d}': sorted(v) for k,v in groups.items()}, 'missing': missing},
          open(f'{BASE}/clusters2.json','w'), indent=1)
print('done')
