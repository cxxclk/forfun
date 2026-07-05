# -*- coding: utf-8 -*-
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.segmentation import watershed
from scipy import ndimage as ndi

BASE = '/sessions/lucid-practical-feynman/mnt/outputs'
MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization/Map'

TYPES = {
 '海龟':   ['1-2','1-9','1-16','2-3','2-10','2-17','3-6','3-13','4-2','4-7','4-12','5-3','5-8','6-2'],
 '章鱼':   ['1-3','1-10','1-17','2-4','2-11','2-18','3-7','3-14','4-3','4-8','4-13','5-4','5-9','6-3'],
 '绿石人': ['1-1','1-8','1-15','2-2','2-9','2-16','3-5','3-12','4-1','4-6','4-11','5-2','5-7','6-1'],
 '蜘蛛':   ['1-7','1-14','2-1','2-8','2-15','3-4','3-8','3-11','4-4','4-9','4-14','5-5','5-10','6-4'],
 '红刺机甲':['1-6','1-13','1-20','2-7','2-14','3-3','3-10'],
 '蓝白机甲':['1-4','1-11','2-5','2-12','3-1'],
 '棕爪机甲':['1-5','1-12','1-19','2-6','2-13','3-9'],
 '骑手兽': ['4-5','4-10','5-1','5-6','5-11'],
 '深蓝机甲':['1-18'],
 '深色重甲':['3-2','7-1','7-2','7-3'],
 '中央BOSS':['8-1'],
}
RANK = {'海龟':1,'绿石人':2,'蜘蛛':3,'蓝白机甲':4,
        '章鱼':7,'红刺机甲':7,'棕爪机甲':7}  # 1=最容易刷个人积分; 未列=未知
UNSURE = ['3-8','3-2','5-10','6-1','6-4','5-11','1-18','7-1','7-2','7-3','2-5','1-7']

zone_type = {}
for t, zs in TYPES.items():
    for z in zs:
        assert z not in zone_type, z
        zone_type[z] = t
assert len(zone_type) == 85, len(zone_type)

json.dump({'zone_type': zone_type,
           'type_rank': RANK,
           'unsure': UNSURE,
           'types': {t: sorted(zs) for t, zs in TYPES.items()}},
          open(f'{MAPD}/monster_types.json','w'), ensure_ascii=False, indent=1)

# also merge into map_data.json
D = json.load(open(f'{MAPD}/map_data.json'))
for n, z in D['zones'].items():
    z['monster'] = zone_type[n]
    z['difficulty'] = RANK.get(zone_type[n])
json.dump(D, open(f'{MAPD}/map_data.json','w'), ensure_ascii=False, indent=1)

# ---- contact sheet grouped by final type ----
im = Image.open(f'{MAPD}/Map.jpg').crop((10, 700, 1075, 1500)).convert('RGB')
arr = np.asarray(im).astype(float)
H, W = arr.shape[:2]
palette = [(239,243,179),(127,202,211),(138,216,170),(158,209,110),
           (234,247,222),(171,90,12),(130,18,12),(170,167,57),(196,120,30)]
dists = np.stack([np.linalg.norm(arr - np.array(c), axis=2) for c in palette])
fillmask = dists.min(axis=0) < 45
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
redtext = (r>140)&(g<100)&(b<100)&(r-np.maximum(g,b)>60)
blob = ndi.binary_closing(ndi.binary_opening((~fillmask)&(~redtext), iterations=1), iterations=2)
comp, ncomp = ndi.label(blob)
crops = {}
for n in names:
    zm = labels == idx[n]
    best, bestc = 0, None
    for ci in np.unique(comp[zm]):
        if ci == 0: continue
        c = ((comp==ci)&zm).sum()
        if c > best: best, bestc = c, ci
    if bestc and best > 120:
        ys, xs = np.where((comp==bestc)&zm)
        crops[n] = im.crop((max(0,xs.min()-3), max(0,ys.min()-3), min(W,xs.max()+3), min(H,ys.max()+3)))
    else:
        x, y = seeds[n]
        crops[n] = im.crop((max(0,x-30), max(0,y-30), min(W,x+30), min(H,y+30)))

try: fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
except: fnt = None
cell, cols = 80, 14
order_types = list(TYPES.keys())
rows = sum(1 + (len(TYPES[t])-1)//cols for t in order_types)
sheet = Image.new('RGB', (cols*cell, rows*cell + len(order_types)*22), (30,33,26))
d = ImageDraw.Draw(sheet)
yoff = 0
for t in order_types:
    zs = sorted(TYPES[t], key=lambda n:(int(n.split('-')[0]), int(n.split('-')[1])))
    rk = RANK.get(t)
    d.text((6, yoff+3), f'{t}  rank={rk if rk else "?"}', fill=(255,220,80), font=fnt)
    yoff += 22
    for i, n in enumerate(zs):
        x = (i%cols)*cell; y = yoff + (i//cols)*cell
        c = crops[n].copy(); c.thumbnail((cell-6, cell-22))
        sheet.paste(c, (x+3, y+2))
        col = (255,120,120) if n in UNSURE else (255,255,255)
        d.text((x+3, y+cell-17), n + ('?' if n in UNSURE else ''), fill=col, font=fnt)
    yoff += (1 + (len(zs)-1)//cols)*cell
sheet.save(f'{MAPD}/怪物分类表.png')
print('saved 怪物分类表.png, monster_types.json, map_data.json updated')
