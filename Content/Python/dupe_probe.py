"""Which actors are duplicated, and does Elm really have unbound materials?"""
import unreal
from collections import Counter, defaultdict
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
labels = Counter()
byl = defaultdict(list)
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    labels[l] += 1
    byl[l].append(a)
dupes = {k: v for k, v in labels.items() if v > 1}
print('duplicate labels: %d' % len(dupes))
for k in sorted(dupes)[:8]:
    locs = ['(%.0f,%.0f,%.0f)' % (a.get_actor_location().x,
                                  a.get_actor_location().y,
                                  a.get_actor_location().z) for a in byl[k]]
    print('   %-22s x%d  at %s' % (k, dupes[k], ' '.join(locs)))
print()
for a in byl.get('BLD2_Elm_H', []):
    bad = 0
    tot = 0
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        tot += 1
        m = c.get_material(0)
        if not m or m.get_name() == 'WorldGridMaterial':
            bad += 1
    l = a.get_actor_location()
    print('BLD2_Elm_H at (%.0f,%.0f,%.0f): %d of %d comps unbound'
          % (l.x, l.y, l.z, bad, tot))
