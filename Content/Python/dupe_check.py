"""Are there two of anything that should be one?

DRESS-06 catches coincident DRESSING actors, which is how three silently-failed
wipes were found. It does not look at generated building families, and a
whole-level sweep that does not wipe first will double them just as quietly.
"""
import unreal, collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
seen = collections.Counter()
for a in eas.get_all_level_actors():
    seen[a.get_actor_label()] += 1
dupes = {k: v for k, v in seen.items() if v > 1}
print('actors %d   labels %d   DUPLICATED LABELS %d'
      % (sum(seen.values()), len(seen), len(dupes)))
byfam = collections.Counter(k.split('_')[0] for k in dupes)
for f, n in byfam.most_common(8):
    ex = next(k for k in dupes if k.startswith(f + '_') or k == f)
    print('  %-10s %4d duplicated labels, e.g. %s x%d' % (f, n, ex, dupes[ex]))
