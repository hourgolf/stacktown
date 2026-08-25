"""One-off census of what the level actually contains, so labels.py is written
from the level rather than from memory. Guessing prefixes is what made
check_clear.py report 0 intersections while asking the wrong question."""
import unreal, collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def stem(n):
    out = []
    for ch in n:
        if ch.isdigit():
            break
        out.append(ch)
    return ''.join(out)

byp = collections.defaultdict(lambda: dict(n=0, cls=set(), ex=None, comps=0))
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    p = stem(lbl)
    d = byp[p]
    d['n'] += 1
    d['cls'].add(type(a).__name__)
    if d['ex'] is None:
        d['ex'] = lbl
        try:
            d['comps'] = len(a.get_components_by_class(unreal.StaticMeshComponent))
        except Exception:
            d['comps'] = -1
for p, d in sorted(byp.items(), key=lambda t: -t[1]['n']):
    print('%5d  %-22s %-34s smc=%-4s %s'
          % (d['n'], p, ','.join(sorted(d['cls']))[:34], d['comps'], d['ex']))
print('TOTAL ACTORS %d  DISTINCT PREFIXES %d' % (sum(d['n'] for d in byp.values()), len(byp)))
