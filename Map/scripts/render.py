import json, numpy as np, collections
from PIL import Image, ImageDraw, ImageFont
from skimage.segmentation import watershed
from scipy import ndimage as ndi

BASE = '/sessions/lucid-practical-feynman/mnt/outputs'
MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization/Map'
im = Image.open(f'{MAPD}/Map.jpg').crop((10, 700, 1075, 1500)).convert('RGB')
arr = np.asarray(im).astype(float)
H, W = arr.shape[:2]

D = json.load(open(f'{MAPD}/map_data.json'))
Z = D['zones']
R = json.load(open(f'{BASE}/plan_result.json'))
split, plans = R['split'], R['plans']

# rebuild segmentation labels (same as segment2)
palette = [(239,243,179),(127,202,211),(138,216,170),(158,209,110),
           (234,247,222),(171,90,12),(130,18,12),(170,167,57),(196,120,30)]
dists = np.stack([np.linalg.norm(arr - np.array(c), axis=2) for c in palette])
passable = ndi.binary_erosion(dists.min(axis=0) < 32, iterations=1)
cost = np.where(passable, 0, 1).astype(np.uint8)
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
labels = watershed(cost, markers)

def tint(zone_colors, alpha=0.45):
    """zone_colors: dict name->rgb; returns PIL image"""
    out = arr.copy()
    for n, c in zone_colors.items():
        m = labels == idx[n]
        out[m] = out[m]*(1-alpha) + np.array(c)*alpha
    return Image.fromarray(out.astype(np.uint8))

try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
except Exception:
    font = small = None

CW, CE = (40, 90, 220), (220, 40, 40)
CC = (255, 215, 0)

# 1) partition map
zc = {}
for n in Z:
    if n == '8-1': zc[n] = CC
    elif split.get(n) == 'W': zc[n] = CW
    elif split.get(n) == 'E': zc[n] = CE
img1 = tint(zc, 0.40)
d = ImageDraw.Draw(img1)
for n in ['7-3', '8-1']:
    z = Z[n]; d.ellipse([z['x']-16, z['y']-16, z['x']+16, z['y']+16], outline=(255,255,0), width=4)
d.text((10, 8), 'BLUE = West    RED = East    YELLOW RING = decisive (7-3, 8-1)', fill=(255,255,255), font=small,
       stroke_width=2, stroke_fill=(0,0,0))
img1.save(f'{BASE}/r_partition.png')

# 2) weekly hold maps (negotiated)
for wk in range(1, 7):
    zc = {}
    for n in plans['W'][str(wk)]['hold']: zc[n] = CW
    for n in plans['E'][str(wk)]['hold']: zc[n] = CE
    img = tint(zc, 0.55)
    d = ImageDraw.Draw(img)
    dw = plans['W'][str(wk)]['daily']; de = plans['E'][str(wk)]['daily']
    d.text((10, 8), f'Week {wk}: hold sets  |  W daily {dw}  E daily {de}', fill=(255,255,255), font=small,
           stroke_width=2, stroke_fill=(0,0,0))
    img.save(f'{BASE}/r_week{wk}.png')

# 3) lockdown map (all-out)
lock = R['lock7']
zc = {n: (150, 30, 200) for n in lock}
zc['8-1'] = CC
img = tint(zc, 0.55)
d = ImageDraw.Draw(img)
d.text((10, 8), 'ALL-OUT: 9-city lockdown = monopoly on all L7 + 8-1', fill=(255,255,255), font=small,
       stroke_width=2, stroke_fill=(0,0,0))
img.save(f'{BASE}/r_lockdown.png')

# 4) key contested cities map (week4-5 battleground)
zc = {n: (255,140,0) for n in ['5-8','5-9']}
for n in ['6-1','6-2','6-3','6-4']: zc[n] = (150,30,200)
for n in ['7-1','7-2','7-3']: zc[n] = (200,0,0)
zc['8-1'] = CC
img = tint(zc, 0.55)
d = ImageDraw.Draw(img)
d.text((10, 8), 'Battleground: ORANGE 5-8/5-9 (gate)  PURPLE L6  RED L7', fill=(255,255,255), font=small,
       stroke_width=2, stroke_fill=(0,0,0))
img.save(f'{BASE}/r_battleground.png')
print('rendered')
