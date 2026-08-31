"""What parts-per-square-metre do the ACCEPTED open lots actually carry?

The threshold for DETAIL-02 has to come from work already judged good, not
from a number that sounds right. Green, Greens and Square were reviewed and
kept; Yard is the one that was bare. So measure all four and read the answer.
"""
import _path  # noqa: F401
import snapshot
import citygeom as G

snap = snapshot.take()
lots = {sp['name']: (sp, r) for _n, sp, r in
        G.lots(('plaza', 'green', 'park', 'vacant'))}

for nm in sorted(lots):
    sp, r = lots[nm]
    area = (sp['width']/100.0) * (sp['depth']/100.0)
    zone_parts, dress = 0, 0
    for a in snap['actors']:
        lbl = a['label']
        if lbl == 'ZONE_%s' % nm:
            zone_parts += len(a['comps'])
        elif lbl.startswith(('SUR_', 'PROP_', 'BAKED_')) and a['comps']:
            x, y = a['loc'][0], a['loc'][1]
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                dress += len(a['comps'])
    tot = zone_parts + dress
    print('%-8s %-7s %6.0f m2   zone %3d + dressing %3d = %3d   %.3f parts/m2'
          % (nm, sp['kind'], area, zone_parts, dress, tot, tot/area))
