import unreal
from collections import Counter
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
c = Counter(a.get_actor_label() for a in eas.get_all_level_actors())
d = {k: v for k, v in c.items() if v > 1}
print('DUPES %d labels, %d actors total' % (len(d), sum(c.values())))
