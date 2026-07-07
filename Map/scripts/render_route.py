# -*- coding: utf-8 -*-
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.segmentation import watershed
from scipy import ndimage as ndi

BASE = '/sessions/lucid-practical-feynman/mnt/outputs'
MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization'
im = Image.open(f'{MAPD}/Map/Map.jpg').crop((10, 700, 1075, 1500)).convert('RGB')
arr = np.asarray(im).astype(float)
H, W = arr.shape[:2]
D = json.load(open(f'{MAPD}/Map/map_data.json'))
Z = D['zones']

palette = [(239,243,179),(127,202,211),(138,216,170),(158,209,110),
           (234,247,222),(171,90,12),(130,18,12),(170,167,57),(196,120,30)]
dists = np.stack([np.linalg.norm(arr - np.array(c), axis=2) for c in palette])
passable = ndi.binary_erosion(dists.min(axis=0) < 32, iterations=1)
seeds = json.load(open(f'{BASE}/seeds.json'))
names = sorted(seeds.keys())
idx = {n: i+1 for i, n in enumerate(names)}
markers = np.zeros((H, W), dtype=np.int32)
for n,(x,y) in seeds.items():
    x=min(max(int(x),3),W-4); y=min(max(int(y),3),H-4)
    if not passable[y,x]:
        for r in range(1,26):
            ys,xs = np.mgrid[max(0,y-r):min(H,y+r+1), max(0,x-r):min(W,x+r+1)]
            m = passable[ys,xs]
            if m.any(): y,x = int(ys[m][0]), int(xs[m][0]); break
    markers[y,x] = idx[n]
labels = watershed(np.where(passable,0,1).astype(np.uint8), markers)

PHASES = [
    ('W1', (80,170,255),  ['1-15','2-1']),
    ('W2', (120,220,255),  ['2-8','2-16']),
    ('W3', (40,220,140),  ['4-12','4-7']),
    ('W4', (255,215,0),   ['5-8']),
    ('W5', (255,130,30),  ['6-1','6-4','6-2','6-3','5-9']),
    ('W6', (235,40,40),   ['7-3','7-2','7-1']),
    ('终', (180,40,220),  ['8-1']),
]
alpha = 0.55
out = arr.copy()
for _, col, zs in PHASES:
    for n in zs:
        m = labels == idx[n]
        out[m] = out[m]*(1-alpha) + np.array(col)*alpha
img = Image.fromarray(out.astype(np.uint8))
d = ImageDraw.Draw(img)
F = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
try: f16 = ImageFont.truetype(F, 17); f13 = ImageFont.truetype(F, 13)
except:
    F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    f16 = ImageFont.truetype(F, 17); f13 = ImageFont.truetype(F, 13)

ARROWS = [
    ('1-15','2-8'),('2-8','2-16'),('2-16','4-12'),('4-12','5-8'),
    ('5-8','6-1'),('5-8','6-4'),('6-1','6-3'),
    ('2-1','4-7'),('4-7','6-2'),('6-2','5-9'),
    ('5-8','7-3'),('7-3','7-2'),('6-2','7-1'),('7-3','8-1'),
]
def arrow(a, b, col=(255,255,255)):
    ax,ay,bx,by = Z[a]['x'],Z[a]['y'],Z[b]['x'],Z[b]['y']
    d.line([ax,ay,bx,by], fill=col, width=4)
    import math
    ang = math.atan2(by-ay, bx-ax)
    for s in (-0.5, 0.5):
        d.line([bx,by, bx-16*math.cos(ang+s), by-16*math.sin(ang+s)], fill=col, width=4)
for a,b in ARROWS: arrow(a,b)

legend = '  '.join(f'{ph}' for ph,_,_ in PHASES)
d.rectangle([0,0,W,26], fill=(20,22,16))
x = 8
for ph, col, zs in PHASES:
    t = f'{ph}: {"、".join(zs)}'
    d.text((x, 4), t, fill=col, font=f13)
    x += d.textlength(t, font=f13) + 16
img.save(f'{BASE}/r_route.png')
print('route map saved')
