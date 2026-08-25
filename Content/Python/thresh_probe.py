"""Measure the distributions a threshold would be drawn from, before choosing
one. A rule with an invented number either never fires or fires on correct
data; either way it teaches nothing."""
import _path, snapshot, labels, citygeom as G, collections
s = snapshot.take()

print('--- practical light pitch (defect was pitch 90 = aimed at the ceiling) ---')
p = [a['rot'][0] for a in s['actors']
     if a['family'] == 'LIGHT' and 'Practical' in a['label'] or
        (a['family'] == 'LIGHT' and a['label'][:6] == 'LIGHT2')]
if p:
    print('  n=%d  min %.1f  max %.1f  |pitch|>60: %d'
          % (len(p), min(p), max(p), sum(1 for v in p if abs(v) > 60)))
print('  all LIGHT actors by class:',
      dict(collections.Counter(a['cls'] for a in s['actors'] if a['family'] == 'LIGHT')))

print('--- tree crown overhang into a carriageway ---')
roads = G.road_rects()
ov = []
for a, c in snapshot.mesh_actors(s, labels.is_tree):
    r = snapshot.rect_of(c)
    if not r: continue
    worst = 0.0
    for rd in roads:
        i = G.intersect(rd, r)
        if i:
            worst = max(worst, min(i[2]-i[0], i[3]-i[1]))
    if worst: ov.append((worst, a['label']))
ov.sort(reverse=True)
print('  trees %d   overhanging road %d' % (len(snapshot.mesh_actors(s, labels.is_tree)), len(ov)))
for w, l in ov[:6]: print('    %7.1f uu  %s' % (w, l))

print('--- zone planting vs its own zone lot ---')
zl = {n + '/' + sp['name']: r for n, sp, r in G.lots(('plaza', 'green', 'park', 'vacant'))}
out = []
for a, c in snapshot.mesh_actors(s, labels.is_planting):
    if not a['label'].startswith('SUR_zone_'): continue
    zone = a['label'].split('_')[2]
    r = snapshot.rect_of(c)
    key = next((k for k in zl if k.endswith('/' + zone)), None)
    if not key or not r: continue
    out.append((G.overhang(zl[key], r), a['label'], c['mesh']))
out.sort(reverse=True)
print('  zone planting %d' % len(out))
for o, l, m in out[:8]: print('    overhang %7.1f uu  %-24s %s' % (o, l, m))

print('--- tree crown size, for context ---')
sz = collections.defaultdict(list)
for a, c in snapshot.mesh_actors(s, labels.is_planting):
    r = snapshot.rect_of(c)
    if r: sz[c['mesh']].append(max(r[2]-r[0], r[3]-r[1]))
for m in sorted(sz):
    v = sz[m]; print('    %-14s n=%-3d crown %.0f..%.0f uu' % (m, len(v), min(v), max(v)))
