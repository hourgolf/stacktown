"""Run the city tick, in Python, against the REAL runtime assets.

The Blueprint graph is editor work and node authoring is not exposed. But the
graph is only one implementation of the tick - the DATA path is the thing worth
proving, and it can be exercised now: spawn real BP_Parcel actors, read the
real DA_Catalogue, and do exactly what ResolveMesh will do.

This also produces the first number against the budget in RUNTIME_SLICE.md:
a 500-parcel tick under 100 ms.
"""
import unreal, time
import _path  # noqa: F401

RT = '/Game/Stacktown/Runtime'
PAD = (6200.0, 1500.0)
N = 500

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cat = unreal.load_asset('%s/DA_Catalogue' % RT)
bp = unreal.load_asset('%s/BP_Parcel' % RT)
assert cat and bp, 'runtime assets missing'

ids = [str(x) for x in cat.get_editor_property('RecipeIds')]
tiers = list(cat.get_editor_property('Tiers'))
widths = list(cat.get_editor_property('Widths'))
meshes = list(cat.get_editor_property('Meshes'))
names = [str(x) for x in cat.get_editor_property('TierNames')]
print('catalogue: %d rows' % len(ids))

# the exact lookup ResolveMesh will do
LUT = {(ids[i], tiers[i], widths[i]): meshes[i] for i in range(len(ids))}


def resolve(actor):
    key = (str(actor.get_editor_property('RecipeId')),
           int(actor.get_editor_property('Tier')),
           float(actor.get_editor_property('WidthUU')))
    m = LUT.get(key)
    if not m:
        return False
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        c.set_editor_property('static_mesh', m)
        return True
    return False


for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('SIM_'):
        eas.destroy_actor(a)

t0 = time.time()
parcels = []
for i in range(N):
    x = PAD[0] + (i % 25)*900.0
    y = PAD[1] + (i // 25)*1700.0
    a = eas.spawn_actor_from_class(bp.generated_class(),
                                   unreal.Vector(x, y, 0.0), unreal.Rotator())
    a.set_actor_label('SIM_%03d' % i)
    a.set_editor_property('RecipeId', unreal.Name('cottage' if i % 2 else 'walkup'))
    a.set_editor_property('WidthUU', 820.0 if i % 2 else 1420.0)
    a.set_editor_property('Tier', 0)
    a.set_editor_property('Level', 0.0)
    resolve(a)
    parcels.append(a)
spawn_ms = (time.time() - t0)*1000.0
print('placed %d parcels in %.0f ms  (%.2f ms each)' % (N, spawn_ms, spawn_ms/N))

# --- the tick: advance Level, derive Tier, resolve ONLY when it changed -----
for step in range(1, 4):
    t0 = time.time()
    changed = 0
    for a in parcels:
        lvl = min(1.0, float(a.get_editor_property('Level')) + 0.34)
        a.set_editor_property('Level', lvl)
        want = int(round(lvl*2.0))
        if want != int(a.get_editor_property('Tier')):
            a.set_editor_property('Tier', want)
            resolve(a)
            changed += 1
    ms = (time.time() - t0)*1000.0
    print('tick %d: %d of %d parcels upgraded, %6.1f ms  (%.3f ms per parcel)'
          % (step, changed, N, ms, ms/N))

t0 = time.time()
for a in parcels:
    lvl = min(1.0, float(a.get_editor_property('Level')))
    a.set_editor_property('Level', lvl)
    want = int(round(lvl*2.0))
    if want != int(a.get_editor_property('Tier')):
        a.set_editor_property('Tier', want); resolve(a)
print('tick with nothing to do: %.1f ms' % ((time.time() - t0)*1000.0))
print('SIM_ actors left in the level: %d (run wipe_sim.py to clear)' % len(parcels))
