import json, numpy as np
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
from scipy import ndimage as ndi

BASE = '/sessions/lucid-practical-feynman/mnt/outputs'
im = Image.open('/sessions/lucid-practical-feynman/mnt/Path Optimization/Map/Map.jpg')
crop = im.crop((10, 700, 1075, 1500)).convert('RGB')
arr = np.asarray(crop).astype(float)
H, W = arr.shape[:2]

# flat fill palette of zones
palette = [
    (239,243,179), (127,202,211), (138,216,170), (158,209,110),
    (234,247,222), (171,90,12), (130,18,12), (170,167,57),
    (196,120,30),  # lighter orange variant (level 6/7 ring)
]
dists = np.stack([np.linalg.norm(arr - np.array(c), axis=2) for c in palette])
mind = dists.min(axis=0)
passable = mind < 32
# dilate barrier by 1px (erode passable) to seal jpeg-blended border pixels
passable = ndi.binary_erosion(passable, iterations=1)

cost = np.where(passable, 0, 1).astype(np.uint8)

seeds = json.load(open(f'{BASE}/seeds.json'))
names = sorted(seeds.keys())
idx = {n: i+1 for i, n in enumerate(names)}
markers = np.zeros((H, W), dtype=np.int32)
bad = []
for n, (x, y) in seeds.items():
    x = min(max(int(x), 3), W-4); y = min(max(int(y), 3), H-4)
    if not passable[y, x]:
        # find nearest passable pixel within 25px
        found = False
        for r in range(1, 26):
            ys, xs = np.mgrid[max(0,y-r):min(H,y+r+1), max(0,x-r):min(W,x+r+1)]
            m = passable[ys, xs]
            if m.any():
                yy, xx = ys[m][0], xs[m][0]
                x, y = int(xx), int(yy); found = True; break
        if not found: bad.append(n)
    markers[y, x] = idx[n]
print('seeds with no passable pixel nearby:', bad)

labels = watershed(cost, markers)

adj = {}
for axis in (0, 1):
    a = labels[:-1, :] if axis == 0 else labels[:, :-1]
    b = labels[1:, :] if axis == 0 else labels[:, 1:]
    diff = a != b
    pairs, counts = np.unique(
        np.stack([np.minimum(a[diff], b[diff]), np.maximum(a[diff], b[diff])]), axis=1, return_counts=True)
    for (p, q), c in zip(pairs.T, counts):
        adj[(int(p), int(q))] = adj.get((int(p), int(q)), 0) + int(c)

MIN_BORDER = 15
edges = [(names[p-1], names[q-1], c) for (p, q), c in sorted(adj.items()) if c >= MIN_BORDER]

zones = {}
cy, cx = np.mgrid[0:H, 0:W]
for n, i in idx.items():
    mask = labels == i
    area = int(mask.sum())
    zones[n] = {'level': int(n.split('-')[0]),
                'x': round(float(cx[mask].mean()), 1) if area else seeds[n][0],
                'y': round(float(cy[mask].mean()), 1) if area else seeds[n][1],
                'area': area, 'neighbors': []}
for a, b, c in edges:
    zones[a]['neighbors'].append(b)
    zones[b]['neighbors'].append(a)

json.dump({'width': W, 'height': H,
           'edges': [[a, b, c] for a, b, c in edges], 'zones': zones},
          open(f'{BASE}/map_data_raw.json', 'w'), indent=1)

deg = sorted(((len(z['neighbors']), n) for n, z in zones.items()))
print('zones:', len(zones), 'edges:', len(edges))
print('low degree:', deg[:8])
print('high degree:', deg[-8:])
print('small regions:', [(n, z['area']) for n, z in zones.items() if z['area'] < 800])

# connectivity check
import collections
g = collections.defaultdict(set)
for a, b, c in edges: g[a].add(b); g[b].add(a)
seen = set(); stack = ['8-1']
while stack:
    u = stack.pop()
    if u in seen: continue
    seen.add(u); stack.extend(g[u])
print('connected from 8-1:', len(seen), 'of', len(zones))

# colored segmentation preview + edge overlay
rng = np.random.default_rng(1)
cols = rng.integers(40, 255, (len(names)+1, 3))
seg = cols[labels].astype(np.uint8)
Image.blend(crop, Image.fromarray(seg), 0.55).save(f'{BASE}/seg_preview.png')

ov = crop.copy(); d = ImageDraw.Draw(ov)
for a, b, c in edges:
    za, zb = zones[a], zones[b]
    d.line([za['x'], za['y'], zb['x'], zb['y']], fill=(255, 0, 0), width=2)
for n, z in zones.items():
    d.ellipse([z['x']-4, z['y']-4, z['x']+4, z['y']+4], fill=(255,255,0), outline=(0,0,0))
ov.save(f'{BASE}/adjacency_overlay.png')
print('done')
