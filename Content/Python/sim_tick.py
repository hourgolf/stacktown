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
from city import BOARD_N

RT = '/Game/Stacktown/Runtime'
# north of the CURRENT board top - the old literal (6200, 1500) predated the
# northward growth and sat the grid across street 0
PAD = (6200.0, BOARD_N + 700.0)
N = 500
TIER_MAX = 5                     # vernacular t0..t5

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
misses = 0
for i in range(N):
    x = PAD[0] + (i % 25)*900.0
    y = PAD[1] + (i // 25)*1700.0
    a = eas.spawn_actor_from_class(bp.generated_class(),
                                   unreal.Vector(x, y, 0.0), unreal.Rotator())
    a.set_actor_label('SIM_%03d' % i)
    # keyed to what the catalogue actually holds. The first run of this
    # benchmark was keyed cottage/walkup AFTER those rows were retired: every
    # resolve() missed, the miss was unchecked, and the recorded "first
    # number" timed 500 parcels that never received a mesh.
    a.set_editor_property('RecipeId', unreal.Name('vernacular'))
    a.set_editor_property('WidthUU', 1230.0)
    a.set_editor_property('Tier', 0)
    a.set_editor_property('Level', 0.0)
    if not resolve(a):
        misses += 1
    parcels.append(a)
spawn_ms = (time.time() - t0)*1000.0
print('placed %d parcels in %.0f ms  (%.2f ms each)' % (N, spawn_ms, spawn_ms/N))
if misses:
    raise SystemExit('%d of %d parcels FAILED to resolve a mesh - the '
                     'benchmark is meaningless, not slow. Check DA_Catalogue '
                     'against the parcel keys.' % (misses, N))
print('all %d parcels resolved a mesh' % N)

# --- the tick: advance Level, derive Tier, resolve ONLY when it changed -----
for step in range(1, 4):
    t0 = time.time()
    changed = 0
    for a in parcels:
        lvl = min(1.0, float(a.get_editor_property('Level')) + 0.34)
        a.set_editor_property('Level', lvl)
        want = int(round(lvl*TIER_MAX))
        if want != int(a.get_editor_property('Tier')):
            a.set_editor_property('Tier', want)
            if not resolve(a):
                raise SystemExit('tier %d failed to resolve mid-tick' % want)
            changed += 1
    ms = (time.time() - t0)*1000.0
    print('tick %d: %d of %d parcels upgraded, %6.1f ms  (%.3f ms per parcel)'
          % (step, changed, N, ms, ms/N))

t0 = time.time()
for a in parcels:
    lvl = min(1.0, float(a.get_editor_property('Level')))
    a.set_editor_property('Level', lvl)
    want = int(round(lvl*TIER_MAX))
    if want != int(a.get_editor_property('Tier')):
        a.set_editor_property('Tier', want)
        if not resolve(a):
            raise SystemExit('tier %d failed to resolve' % want)
print('tick with nothing to do: %.1f ms' % ((time.time() - t0)*1000.0))
print('SIM_ actors left in the level: %d (run wipe_sim.py to clear)' % len(parcels))
