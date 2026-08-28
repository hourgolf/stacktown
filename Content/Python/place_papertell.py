"""Stand the paper-tell study in Sandbox_Bench. Group C panels, Group A cars.

THE SANDBOX GUARD IS HONOURED, NOT ROUTED AROUND. study_place.py refuses to
build outside Sandbox_Bench and records why: workshop furniture once spawned
into a shipping level and ended up standing in a board capture. Stage2_Street
is gate evidence and is currently dressed as well, so putting a study wall in
it would be the same mistake with two reasons instead of one. If this refuses,
the fix is to open the sandbox, not to widen the guard.

GROUP A USES CARS, NOT PANELS, DELIBERATELY. The hypothesis is about an object
CLASS - "the vehicles carry the same material effect as the buildings" - so a
flat panel cannot test it. Only the BODY slot changes between the four; glass,
trim and tyres are held constant, which is what makes the body the variable.
"""
import json
import unreal

SANDBOX = 'Sandbox_Bench'
MATS = '/Game/Stacktown/Materials'
MESH = '/Game/Stacktown/Meshes'

lvl = unreal.get_editor_subsystem(
    unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
if SANDBOX not in lvl:
    raise SystemExit(
        'refusing to build the paper-tell study in %s\n'
        '    Open /Game/Maps/%s in the editor and run this again.' % (lvl, SANDBOX))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# clear of the bench stand at (-12000,-2640) and of study_place's own wall at
# (-20000,-2640): this takes its own ground so the two studies cannot shadow
# or occlude each other.
# z is the slab's CENTRE, so it is half the slab height - at 0 the panel
# sat half underground and the camera aimed into the floor.
C_AT = (-20000.0, -8000.0, 600.0)
A_AT = (-20000.0, -11000.0, 0.0)
STEP = 2600.0

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('STUDY_PT_'):
        eas.destroy_actor(a)

C = ['MI_pt_c0_t006', 'MI_pt_c1_t012', 'MI_pt_c2_t025', 'MI_pt_c3_t050']
A = ['MI_pt_a0_card', 'MI_pt_a1_resin', 'MI_pt_a2_diecast', 'MI_pt_a3_wire']
CAR = 'SM_Baked_Muscle'

def spawn(mesh, label, loc, yaw=0.0):
    sm = unreal.load_asset(mesh)
    if not sm:
        raise SystemExit('missing mesh %s' % mesh)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(*loc), unreal.Rotator(0, yaw, 0))
    a.set_actor_label(label)
    a.static_mesh_component.set_editor_property('static_mesh', sm)
    return a

placed = []
# --- Group C: the tiling sweep on the study panel mesh ---------------------
for i, m in enumerate(C):
    mi = unreal.load_asset('%s/%s' % (MATS, m))
    if not mi:
        raise SystemExit('missing panel material %s' % m)
    # A PLAIN SLAB, ONE SLOT. The first version used SM_MatStudy, which is
    # the EARLIER study's wall: nine slots including glass, interior and
    # frame, with window openings between the panels. Setting one material
    # across all nine turned its glazing into paper, and aiming at the mesh's
    # bounds centre put the camera on a window void - the capture measured
    # sky and blackness and produced a tidy, meaningless set of numbers.
    # A study needs a surface, not a building.
    a = spawn('/Engine/BasicShapes/Cube',
              'STUDY_PT_C%d_%s' % (i, m[9:]),
              (C_AT[0] + i*STEP, C_AT[1], C_AT[2]))
    # 2000 x 1200: at the FAR standoff the frame is 1640 x 919, so the
    # panel has to overfill it or the capture measures the backdrop.
    a.set_actor_scale3d(unreal.Vector(20.0, 0.4, 12.0))
    comp = a.static_mesh_component
    for s in range(max(1, comp.get_num_materials())):
        comp.set_material(s, mi)
    o, e = a.get_actor_bounds(False)
    placed.append(('C%d' % i, m, [o.x, o.y, o.z], [e.x, e.y, e.z]))

# --- Group A: the family swap on a car, BODY SLOT ONLY ---------------------
glass = unreal.load_asset('%s/MI_glass_b_2S' % MATS)
metal = unreal.load_asset('%s/MI_dark_metal' % MATS)
for i, m in enumerate(A):
    mi = unreal.load_asset('%s/%s' % (MATS, m))
    if not mi:
        raise SystemExit('missing family material %s' % m)
    a = spawn('%s/%s' % (MESH, CAR), 'STUDY_PT_A%d_%s' % (i, m[9:]),
              (A_AT[0] + i*STEP, A_AT[1], A_AT[2]), yaw=-20.0)
    comp = a.static_mesh_component
    # body / glass / trim / tyres - the slot order hero_veh.py established by
    # looking, because the donor meshes record nothing about which is which
    order = [mi, glass, metal, metal]
    for s in range(max(1, comp.get_num_materials())):
        comp.set_material(s, order[s] if s < len(order) else mi)
    o, e = a.get_actor_bounds(False)
    placed.append(('A%d' % i, m, [o.x, o.y, o.z], [e.x, e.y, e.z]))

les.save_current_level()
print('PTSTUDY ' + json.dumps(placed))
for tag, m, o, e in placed:
    print('  %-4s %-18s centre %8.0f %8.0f %7.0f   half %6.0f %6.0f %6.0f'
          % (tag, m, o[0], o[1], o[2], e[0], e[1], e[2]))
