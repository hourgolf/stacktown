"""Place the donor props into the works yard, from the SAME layout zones.py built.

The rule this project uses for donor geometry, unchanged: their SHAPES, our
MATERIALS, their textures never shipped. Every material slot on every donor
mesh is rebound below - if a slot were missed the donor's own texture would
render, and a checker grid or a photographic steel would break the handmade
card look in one frame. MISSING is printed rather than skipped, because a
silently unbound slot is exactly the failure that would survive review.

Runs through rung.sh (needs `unreal` directly to spawn StaticMeshActors). The
layout comes from zonelayout.yard_layout, so the fence panels land on the
plinths zones.py built for them and nothing stands on the apron.
"""
import _path  # noqa: F401
import math
import unreal
from city import BLOCKS
from zonelayout import yard_layout

D = '/Game/Deko_MatrixDemo/City/Meshes'
F = '/Game/Stacktown/Materials'

# role -> (mesh, our material). Measured sizes in deko_probe.py.
ROLE = {
    'container_long':  ('SM_ShippingContainer_A01_N1', 'MI_card_ochre'),
    'container_short': ('SM_ShippingContainer_B01_N1', 'MI_card_rose'),
    'scaffold':        ('SM_Scaffolding_A01_N1',       'MI_dark_metal'),
    'ladder':          ('SM_Ladder_A01_N1',            'MI_dark_metal'),
    'lumber_stack':    ('SM_LumberStack_A01_N1',       'MI_wood'),
    'lumber_pile':     ('SM_LumberPile_B01_N1',        'MI_wood'),
    'pallet':          ('SM_WoodenPallet_B01_N1',      'MI_wood'),
    'plywood':         ('SM_PlywoodBoards_A01_N1',     'MI_wood'),
}
# the second long container reads better as a different painted box
ALT = {'container_long': ('SM_ShippingContainer_C01_N1', 'MI_card_sage')}

# Slot-name overrides, applied before the role's material. Empty now that the
# donor fence is gone; kept because it is the hook a donor mesh with a mixed
# slot set needs, and re-adding it later should not mean re-deriving it.
BY_SLOT = {}

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

_mat, _mesh = {}, {}
def M(n):
    if n not in _mat:
        _mat[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    return _mat[n]
def SM(n):
    if n not in _mesh:
        _mesh[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (D, n, n))
    return _mesh[n]

blk = next(b for b in BLOCKS for l in b['lots'] if l.get('kind') == 'vacant')
spec = next(l for l in blk['lots'] if l.get('kind') == 'vacant')
LO = yard_layout(spec)
ox, oy, oz = blk['origin']
name = spec['name']

gone = 0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('PROP_%s_' % name):
        eas.destroy_actor(a); gone += 1
print('removed %d old yard props' % gone)

made, bound, unbound, missing = 0, 0, 0, []
def put(role, lx, ly, lz, lyaw, tag, alt=False):
    """Block-local in, world out - through the SAME rotation citygeom uses.

    The first version added origin + local without rotating the offset and
    claimed the actor rotation made it yaw-safe. It did not: the rotation
    only turns the mesh, not the translation, so on a yaw-180 block every
    prop would land mirrored outside its lot. Block H is yaw 0 today, which
    is the only reason it looked right."""
    global made, bound, unbound
    mesh, mat = ALT[role] if (alt and role in ALT) else ROLE[role]
    sm = SM(mesh)
    if not sm:
        missing.append(mesh); return
    yr = math.radians(blk['yaw'])
    c_, s_ = math.cos(yr), math.sin(yr)
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(ox + lx*c_ - ly*s_, oy + lx*s_ + ly*c_, oz + lz),
        unreal.Rotator(0.0, 0.0, blk['yaw'] + lyaw))   # (roll, pitch, yaw)
    a.set_actor_label('PROP_%s_%s' % (name, tag))
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    slots = sm.get_editor_property('static_materials')
    for i in range(len(slots)):
        # a slot may be overridden by name - the chain-link wire is its own
        # slot and takes the masked card while the frame takes metal
        ours = M(BY_SLOT.get(str(slots[i].material_slot_name), mat))
        if ours:
            c.set_material(i, ours); bound += 1
        else:
            unbound += 1
    made += 1

# The fence is OURS now - zones.py builds it from the same layout runs. The
# donor chain-link is gone because its mask texture carries graffiti tags as
# well as wire, and the parking sign went with it: a car park sign standing in
# the middle of a private yard was a street asset in the wrong place.
seen = {}
for role, lx, ly, lz, lyaw in LO['props']:
    seen[role] = seen.get(role, 0) + 1
    put(role, lx, ly, 20.0 + lz, lyaw, '%s%d' % (role, seen[role]),
        alt=(role == 'container_long' and seen[role] == 2))

if missing:
    print('MISSING MESHES: %s' % ', '.join(sorted(set(missing))))
if unbound:
    print('UNBOUND SLOTS: %d - a donor texture would render' % unbound)
print('yard: placed %d donor props, %d material slots bound to ours' % (made, bound))
les.save_current_level()
