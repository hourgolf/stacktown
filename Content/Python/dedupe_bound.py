"""Remove duplicate actors, keeping the one whose materials are BOUND.

dedupe.py keeps whichever copy `get_all_level_actors` happens to return
first. Here that was the good one - but only by luck: the duplicated blocks F
and G each carry one fully-bound copy and one with every single component on
WorldGridMaterial (137 of 137 on BLD2_Elm_H). Keeping the wrong one would
silently strip a whole block's materials and pass NAME-03 while doing it.

So the choice is made on evidence: for each label, keep the copy with the
fewest unbound slots, and report what was actually removed.
"""
import unreal
from collections import defaultdict

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
alls = eas.get_all_level_actors()
assert alls, 'enumerated zero actors'

byl = defaultdict(list)
for a in alls:
    byl[a.get_actor_label()].append(a)


def unbound(a):
    n = 0
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_material(0)
        if not m or m.get_name() in ('WorldGridMaterial', 'DefaultMaterial'):
            n += 1
    return n


killed, kept_bad = 0, 0
for label, group in sorted(byl.items()):
    if len(group) < 2:
        continue
    scored = sorted(((unbound(a), i, a) for i, a in enumerate(group)),
                    key=lambda t: (t[0], t[1]))
    keep = scored[0]
    print('  %-22s x%d  keeping the copy with %d unbound (worst had %d)'
          % (label, len(group), keep[0], scored[-1][0]))
    if keep[0] > 0:
        kept_bad += 1
    for _n, _i, a in scored[1:]:
        eas.destroy_actor(a)
        killed += 1

print('removed %d duplicate actors' % killed)
if kept_bad:
    print('WARNING: %d labels had NO fully-bound copy - re-run step_roles'
          % kept_bad)
les.save_current_level()
