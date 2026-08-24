"""Re-place props with a rule about WHAT each asset is, and a footprint test.

The water tank is 877 uu - 8.8 m - and is a ROOFTOP asset. It was dropped at
Y-160, mid-sidewalk, intersecting a facade, because props were placed at
arbitrary coordinates with no thought about what they are.

Two rules now:
  rooftop assets  -> on a roof deck, at that building's parapet height
  street assets   -> sidewalk band only, and rejected if their footprint
                     overlaps a building or another prop
"""
import unreal, sys
sys.path.insert(0,'/private/tmp/claude-501/-Users-ben-Documents-New-project/c7b8ef13-3903-46ab-bd2b-18279bb95fe6/scratchpad')
from lots import LOTS

AV = '/Game/AssetsvilleTown/Meshes'
F = '/Game/Stacktown/Materials'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def M(n): return unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(('SUR_prop', 'SUR_tree')):
        eas.destroy_actor(a)

SIDEWALK = (-400.0, -120.0)     # Y band that is actually pavement
BUILDING_FRONT = -60.0          # anything at Y > this is inside a building
placed = []

def footprint_free(x, y, r):
    if y > BUILDING_FRONT - r:
        return False
    for px, py, pr in placed:
        if ((x - px) ** 2 + (y - py) ** 2) ** 0.5 < (r + pr) * 0.9:
            return False
    return True

def put(folder, name, x, y, z, yaw, label, colour, native=False, radius=None):
    sm = unreal.EditorAssetLibrary.load_asset('%s/%s/%s.%s' % (AV, folder, name, name))
    if not sm:
        print('  missing', name); return False
    e = sm.get_bounds().box_extent
    # a tree CANOPY is meant to overhang the pavement; only its trunk collides,
    # so foliage passes an explicit trunk radius instead of its bounds
    r = radius if radius is not None else max(e.x, e.y)
    if z == 0.0 and not footprint_free(x, y, r):
        print('  REJECTED %-20s at X%.0f Y%.0f (r=%.0f) - overlap' % (name, x, y, r))
        return False
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('SUR_' + label)
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i, s in enumerate(sm.get_editor_property('static_materials')):
        c.set_material(i, s.material_interface if native else M(colour))
    if z == 0.0:
        placed.append((x, y, r))
    return True

# --- rooftop assets, on actual roofs: X and Z derived from the lot table -----
def roof_z(spec):
    if spec['kind']=='av': return spec['floors']*spec['fl_h']
    return spec['gf_h']+spec['floors']*spec['fl_h']+spec['parapet']
BY={l['name']:l for l in LOTS}
_n=BY['Narrow']; _m=BY['Mid']; _a=BY['AV']
put('StreetProps','SM_Water_Tank_01', _n['x0']+_n['width']*0.45, 380.0, roof_z(_n), -18,'roofTank','MI_concrete')
put('StreetProps','SM_airCondition_01', _m['x0']+_m['width']*0.32, 300.0, roof_z(_m), 24,'roofAC1','MI_frame_print')
put('StreetProps','SM_airCondition_02', _m['x0']+_m['width']*0.62, 420.0, roof_z(_m), -37,'roofAC2','MI_frame_print')
put('StreetProps','SM_AntennaBig_01',  _a['x0']+_a['width']*0.45, 400.0, roof_z(_a),  8,'roofAnt','MI_frame_print')

# --- street assets, sidewalk band, footprint-tested --------------------------
put('StreetProps', 'SM_Bicycle_01', 3050.0, -250.0, 0.0, 62, 'bike', 'MI_frame_print')
put('StreetProps', 'SM_barrel_1', 1830.0, -240.0, 0.0, 15, 'barrel', 'MI_frame_print')

# --- trees: native materials, alpha-cut foliage ------------------------------
for i, nm in enumerate(('SM_tree_01', 'SM_tree_03', 'SM_tree_01', 'SM_tree_03')):
    put('Nature', nm, 560.0 + i * 1120.0, -300.0, 0.0, -20 + i * 47,
        'tree%d' % i, '', native=True, radius=45.0)
print('props placed: %d street/roof items' % (len(placed)))
les.save_current_level()
