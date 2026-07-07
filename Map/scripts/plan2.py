# -*- coding: utf-8 -*-
import json, collections, yaml
MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization'
D = json.load(open(f'{MAPD}/Map/map_data.json'))
RU = yaml.safe_load(open(f'{MAPD}/rules.yaml'))
Z = D['zones']
G = collections.defaultdict(set)
for a, b, _ in D['edges']:
    G[a].add(b); G[b].add(a)

SCORE = {int(k): v for k, v in RU['city_score'].items() if v}
RANK = RU['monster_difficulty']['type_rank']
def diff(n):
    r = RANK.get(Z[n]['monster'])
    return r if r else 5   # unrated mid
BORDER = set(json.load(open('/sessions/lucid-practical-feynman/mnt/outputs/border_zones.json')))

def by_level(l): return [n for n in Z if Z[n]['level'] == l]

split = {}
for l in range(1, 8):
    zs = sorted(by_level(l), key=lambda n: Z[n]['x'])
    half = len(zs)//2
    for i, n in enumerate(zs):
        split[n] = 'W' if i < half else 'E'
split['8-1'] = 'contested'

def reachable(side, week):
    allowed = {n for n in Z if Z[n]['open'] <= week and split.get(n)==side}
    starts = [n for n in allowed if n in BORDER]
    seen = set(starts); st = list(starts)
    while st:
        u = st.pop()
        for v in G[u]:
            if v in allowed and v not in seen:
                seen.add(v); st.append(v)
    return seen

plans = {}
for side in 'WE':
    plans[side] = {}
    for wk in range(1,7):
        pool = sorted(reachable(side, wk),
                      key=lambda n: (-SCORE[Z[n]['level']], diff(n), n))
        hs = pool[:10]
        sc = sum(SCORE[Z[n]['level']] for n in hs)
        hard = sum(1 for n in hs if diff(n)==7)
        plans[side][wk] = {'hold': hs, 'daily': sc, 'hard_holds': hard}

# capture workload per side over season: every zone ever entering a hold set + assume held transit minimal
for side in 'WE':
    caps = []
    prev = set()
    for wk in range(1,7):
        new = [n for n in plans[side][wk]['hold'] if n not in prev]
        caps += new
        prev |= set(new)
        plans[side][wk]['new_captures'] = sorted(new, key=lambda n:(-Z[n]['level'], n))
    hard = [n for n in caps if diff(n)==7]
    easy = [n for n in caps if diff(n)<=2]
    print(f'{side}: total captures {len(caps)}, hard(7) {len(hard)} {sorted(hard)}')
    print(f'   easy(1-2) {len(easy)}')
    plans[side]['season_captures'] = caps
    plans[side]['season_hard'] = len(hard)

for side in 'WE':
    print(f'--- {side} ---')
    for wk in range(1,7):
        p = plans[side][wk]
        ann = ['%s(%s%s)' % (n, Z[n]['monster'], diff(n)) for n in p['new_captures']]
        print(f'w{wk} daily={p["daily"]:6d} 新占: {", ".join(ann)}')

json.dump({'split': split, 'plans': plans},
          open('/sessions/lucid-practical-feynman/mnt/outputs/plan_result2.json','w'),
          ensure_ascii=False, indent=1)
