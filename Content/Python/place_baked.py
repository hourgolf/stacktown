"""Place the baked statics - safe to batch, unlike their skeletal originals."""
import unreal
F='/Game/Stacktown/Materials'; M='/Game/Stacktown/Meshes'
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_m={}
def mat(n):
    if n not in _m: _m[n]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))
    return _m[n]
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(('SKT_','BAKED_')): eas.destroy_actor(a)
# Baking skeletal -> static keeps the slot COUNT and drops the slot NAMES: the
# baked vehicles carry 'Material_0', 'None', 'None'. So the roles are read from
# the SOURCE skeletal mesh and applied POSITIONALLY, which is the documented way
# to handle these.
#
# Every slot used to get the body colour. That is why a rebuild turned the cars
# into single-colour lumps with no glazing, no trim and no second panel - and
# why build_block.py step 9 existed to undo it, pointing at a script
# (fix6_vehmats2.py) that is not in this repository.
_V = '/Game/AssetsvilleTown/Meshes/Vehicles/'
SOURCE = {'SM_Baked_Sedan':   _V + 'SK_veh_Sedan_01',
          'SM_Baked_Pickup':  _V + 'SK_veh_Pickup_01',
          'SM_Baked_Police':  _V + 'SK_veh_PoliceCarSedan_01',
          'SM_Baked_Truck':   _V + 'SK_veh_CargoTruckOld',
          'SM_Baked_Van':     _V + 'SK_veh_Van_01',
          'SM_Baked_Muscle':  _V + 'SK_veh_Muscle_01',
          'SM_Baked_Sport':   _V + 'SK_veh_SportClassic_01',
          'SM_Baked_Offroad': _V + 'SK_veh_Offroad_01',
          'SM_Baked_Veg':     _V + 'SK_veh_VegetableTruck'}
SECOND = 'MI_paint_cream'      # customMat_02 is a second painted panel, not an interior


def source_roles(mesh):
    """Slot names of the skeletal original, in order."""
    p = SOURCE.get(mesh)
    if not p: return []
    sk = unreal.EditorAssetLibrary.load_asset('%s.%s' % (p, p.rsplit('/', 1)[-1]))
    if not sk: return []
    return [str(m.material_slot_name) for m in sk.get_editor_property('materials')]


def role_material(slot, body):
    s = slot.lower()
    if 'glass' in s:        return 'MI_glass_b'
    if 'colorpalette' in s: return 'MI_frame_print'    # bumpers, lights, wheels atlas
    if s.endswith('_01') or s.startswith('carpaint1'): return body
    return SECOND


def put(mesh,x,y,yaw,label,colour):
    sm=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(M,mesh,mesh))
    if not sm: print('  missing',mesh); return
    a=eas.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,0.0),
                                 unreal.Rotator(0,0,yaw))
    a.set_actor_label('BAKED_'+label)
    c=a.static_mesh_component
    c.set_editor_property('static_mesh',sm)
    slots=source_roles(mesh)
    n=len(sm.get_editor_property('static_materials'))
    if len(slots)!=n:
        print('  %s: source has %d slots, baked has %d - falling back to body colour'
              %(mesh,len(slots),n))
        slots=[]
    for i in range(n):
        c.set_material(i, mat(role_material(slots[i], colour) if slots else colour))
    if slots:
        print('  %-10s %-18s %s'%(label,mesh,[role_material(sl,colour) for sl in slots]))
# Vehicles on EVERY street's kerbs, from the city table.
#
# The old version hardcoded four cars at fixed X on block A's kerb, so streets
# 2 and 3 had none. Nine vehicle types are baked now rather than four; parking
# is spaced with jitter and gaps, because a kerb filled end to end at a regular
# pitch reads as a car park, not a street.
import random, math
import _path
from city import STREETS, AVENUES, BOARD_E

FLEET = (('SM_Baked_Sedan', 'MI_card_rose'), ('SM_Baked_Pickup', 'MI_card_sage'),
         ('SM_Baked_Police', 'MI_paint_cream'), ('SM_Baked_Truck', 'MI_card_ochre'),
         ('SM_Baked_Van', 'MI_paint_cream'), ('SM_Baked_Muscle', 'MI_card_rose'),
         ('SM_Baked_Sport', 'MI_card_ochre'), ('SM_Baked_Offroad', 'MI_card_sage'),
         ('SM_Baked_Veg', 'MI_card_lift'))
X0, X1 = -300.0, BOARD_E     # the board grew east for the avenue

# A junction is keep-clear. The street parking lanes run the whole width of the
# board, so before this they ran straight through the avenue and out the far
# side: cars stood in the middle of the intersection, on the crossing bars, and
# one ended up on the avenue pavement with LAMP_a1E_52 through it. Exclude the
# avenue corridor plus half a car length at each end, so nothing overhangs the
# crossing either.
CAR_HALF = 270.0
JUNCTIONS = [(x_w - CAR_HALF, x_e + CAR_HALF) for x_w, x_e, _w in AVENUES]
def clear_of_junction(x):
    return all(not (a <= x <= b) for a, b in JUNCTIONS)
rnd = random.Random(6161)
n = 0
fi = rnd.randrange(len(FLEET))
for si, (y_far, y_near, walk) in enumerate(STREETS, 1):
    k_far, k_near = y_far + walk, y_near - walk
    # THE LONG AXIS IS LOCAL X. Measured off static_mesh.get_bounding_box():
    # SM_Baked_Sedan is 540 x 252, not 252 x 540. The earlier yaw of +/-90 came
    # from reading get_actor_bounds, which includes the actor ROOT at the origin
    # and therefore reports nonsense extents - the trap HANDOFF.md section 5
    # records twice over. Every car was parked broadside across the road, which
    # is what "randomly laid out" looked like. Yaw 0 and 180 lay them ALONG the
    # kerb, facing opposite ways on opposite sides, as parked cars do.
    if k_near - k_far < 320.0:      # too narrow to park both sides
        sides = ((k_near - 150.0, 180.0),)
    else:
        sides = ((k_far + 150.0, 0.0), (k_near - 150.0, 180.0))
    for sy, base_yaw in sides:
        x = X0 + 700.0 + rnd.uniform(0, 500)
        while x < X1 - 500.0:
            if rnd.random() < 0.72 and clear_of_junction(x):
                mesh, col = FLEET[fi % len(FLEET)]; fi += 1
                # tight tolerances: a parked car is within a few cm of the
                # kerb line and a couple of degrees of parallel
                put(mesh, x, sy + rnd.uniform(-12, 12),
                    base_yaw + rnd.uniform(-2.5, 2.5), 'veh%d' % n, col)
                n += 1
            x += 760.0 + rnd.uniform(-120, 420)
print('placed %d baked statics'%n)
les.save_current_level()
