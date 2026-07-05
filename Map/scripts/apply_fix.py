# -*- coding: utf-8 -*-
import json

MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization/Map'

TYPES = {
 '暴食':   ['1-2','1-9','1-16','2-3','2-10','2-17','3-6','3-13','4-2','4-7','4-12','5-3','5-8','6-2'],
 '章鱼':   ['1-3','1-10','1-17','2-4','2-11','2-18','3-7','3-14','4-3','4-8','4-13','5-4','5-9','6-3'],
 '巨魔':   ['1-1','1-8','1-15','2-2','2-9','2-16','3-5','3-12','4-1','4-6','4-11','5-2','5-7','6-1'],
 '看守者': ['1-7','1-14','2-1','2-8','2-15','3-4','3-11','4-4','4-9','4-14','5-5','5-10','6-4'],
 '烈焰':   ['1-6','1-13','1-20','2-7','2-14','3-3','3-10','7-3'],
 '风暴':   ['1-4','1-11','2-5','2-12','3-1','3-8','7-1','1-18'],
 '棕爪机甲':['1-5','1-12','1-19','2-6','2-13','3-9','7-2'],
 '骑手兽': ['4-5','4-10','5-1','5-6','5-11'],
 '混沌':   ['8-1'],
 '待定':   ['3-2'],
}
RANK = {'暴食':1,'巨魔':2,'看守者':3,'风暴':4,'章鱼':7,'烈焰':7,'棕爪机甲':7}

zone_type = {}
for t, zs in TYPES.items():
    for z in zs:
        assert z not in zone_type, z
        zone_type[z] = t
assert len(zone_type) == 85, len(zone_type)

json.dump({'zone_type': zone_type, 'type_rank': RANK,
           'unsure': ['3-2'],
           'types': {t: sorted(zs) for t, zs in TYPES.items()}},
          open(f'{MAPD}/monster_types.json','w'), ensure_ascii=False, indent=1)

D = json.load(open(f'{MAPD}/map_data.json'))
for n, z in D['zones'].items():
    z['monster'] = zone_type[n]
    z['difficulty'] = RANK.get(zone_type[n])
json.dump(D, open(f'{MAPD}/map_data.json','w'), ensure_ascii=False, indent=1)
print('updated monster_types.json + map_data.json')
