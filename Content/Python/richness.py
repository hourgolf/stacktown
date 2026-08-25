"""Is the city losing detail as it grows? Measure it, do not argue about it.

The F1 reader said the main city reads as a miniature but that later blocks
lost architectural detail and material richness. Three numbers per building,
all readable from the snapshot:

  ROLES     how many distinct material roles the elevation carries
  MATS      how many distinct material instances it actually uses
  PLANES    how many distinct depth planes its STREET elevation stands on -
            the thing that makes a facade read as built rather than printed,
            and the measure Stage 0 was tuned against
"""
import _path, snapshot, collections
import citygeom as G
from city import BLOCKS

snap = snapshot.take()
LOT = {}
for blk in BLOCKS:
    for l in blk['lots']:
        if l['kind'] in ('gen', 'av'):
            LOT[l['name']] = (blk['name'], l.get('style') or 'vernacular')

acc = {}
for a in snap['actors']:
    p = a['label'].split('_')
    if p[0] not in ('BLD2', 'ELEV', 'AV') or len(p) < 2:
        continue
    who = p[1] if p[0] != 'AV' else 'AV'
    if who not in LOT:
        continue
    d = acc.setdefault(who, dict(roles=set(), mats=set(), y=set(), n=0))
    for c in a['comps']:
        d['roles'].add(c['name'].split('_')[0])
        for m in c['mats']:
            if m:
                d['mats'].add(m)
        if c['aabb']:
            d['y'].add(round(c['aabb'][0][1]/8.0))     # 8 uu buckets
        d['n'] += 1

# Parts per METRE is unfair to a low building: a two-storey block over 13 m has
# half the elevation of a four-storey one and cannot carry the same count. The
# honest denominator is the AREA of the street elevation.
SPECS = {l['name']: l for b in BLOCKS for l in b['lots'] if l['kind'] == 'gen'}
rows = []
for who, d in acc.items():
    blk, style = LOT[who]
    sp = SPECS.get(who)
    area = 1.0
    if sp:
        h = (sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0)
             + sp.get('parapet', 0.0))
        area = (sp['width']/100.0) * (h/100.0)
    rows.append((blk, style, who, len(d['roles']), len(d['mats']), len(d['y']),
                 d['n'], d['n']/area))
rows.sort()
print('%-4s %-11s %-9s %5s %5s %6s %6s %8s'
      % ('blk', 'style', 'lot', 'ROLES', 'MATS', 'PLANES', 'parts', 'per m2'))
for r in rows:
    print('%-4s %-11s %-9s %5d %5d %6d %6d %8.2f' % r)
by = collections.defaultdict(list)
for r in rows:
    by[r[1]].append(r)
print()
for st in sorted(by):
    v = by[st]
    print('%-11s  n=%d  roles %.1f  mats %.1f  planes %.1f  parts %.0f  per m2 %.2f'
          % (st, len(v), sum(x[3] for x in v)/len(v), sum(x[4] for x in v)/len(v),
             sum(x[5] for x in v)/len(v), sum(x[6] for x in v)/len(v),
             sum(x[7] for x in v)/len(v)))
