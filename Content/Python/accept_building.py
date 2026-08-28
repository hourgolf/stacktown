"""Stand the STANDARD ACCEPTANCE BUILDING on clear ground.

WHY A DEDICATED COPY. Acceptance now happens on a building, and the gate's
player-zoom definition is one facade filling the frame - 3189 uu for a 1640
wide building at 28.84 deg. Every building in the sandbox sits in a street
with a facing row 1500 uu away, so that standoff always lands inside, or
behind, the opposite row: the first attempt photographed the BACK of
ST_S_1_vernacular3 at 818 uu and reported it as a player-zoom frame. Clear
ground removes the failure mode instead of working around it per shot.

WHY THIS BUILDING. Mid-tier vernacular, per the survey design: piers, bands,
reveals and quoins, which is what the studio-director skill ranks first -
"a model reads as physical because light catches real edges". A curtain-wall
modern is mostly glass and would judge the glazing, not the card. It is also
1640 wide, so the far standoff is exactly the gate's own 3189 rather than a
number chosen to suit.

FACING -Y, WHICH IS THE LIT FACE. LIGHT_Sun is pitch -52 yaw 45, so light
travels toward +X/+Y and a -Y normal opposes it. study_place.py records a
whole study once yawed 180 "to fix the lighting" and put itself in shadow.
"""
import unreal

SRC = 'ST_N_6_vernacular5_t4'
AT = unreal.Vector(-20000.0, -30000.0, -128.0)
LABEL = 'ACCEPT_Vernacular'


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = ues.get_editor_world()

    src = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        try:
            if a.get_actor_label() == SRC:
                src = a; break
        except Exception:
            pass
    if not src:
        raise SystemExit('source building %s not found' % SRC)
    comp = src.static_mesh_component
    mesh = comp.get_editor_property('static_mesh')
    mats = [comp.get_material(i) for i in range(comp.get_num_materials())]
    rot = src.get_actor_rotation()

    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith(LABEL):
            eas.destroy_actor(a)
    b = eas.spawn_actor_from_class(unreal.StaticMeshActor, AT, rot)
    b.set_actor_label(LABEL)
    c = b.static_mesh_component
    c.set_editor_property('static_mesh', mesh)
    for i, m in enumerate(mats):
        if m:
            c.set_material(i, m)
    les.save_current_level()

    o, e = b.get_actor_bounds(False)
    face_y = o.y - e.y
    width = e.x * 2.0
    far = width / 0.5143
    print('ACCEPT %s' % LABEL)
    print('  mesh        %s' % mesh.get_name())
    print('  centre      %.0f %.0f %.0f' % (o.x, o.y, o.z))
    print('  size        %.0f wide  %.0f tall' % (width, e.z * 2.0))
    print('  front face  y = %.0f  (the -Y, lit face)' % face_y)
    print('  far standoff %.0f uu  -> camera y = %.0f' % (far, face_y - far))
    print('  near standoff 800 uu -> camera y = %.0f' % (face_y - 800.0))
    # clearance: nothing may sit between the camera and the face
    lo_y, hi_y = face_y - far - 200.0, face_y
    blockers = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        try:
            L = a.get_actor_label()
        except Exception:
            continue
        if L == LABEL or L.startswith('LIGHT') or L.startswith('LOOK'):
            continue
        ao, ae = a.get_actor_bounds(False)
        if ao.z + ae.z < -300:      # the floor plane
            continue
        if (ao.y - ae.y) > hi_y or (ao.y + ae.y) < lo_y:
            continue
        if abs(ao.x - o.x) > (ae.x + e.x):
            continue
        blockers.append(L)
    print('  CLEARANCE   %s' % ('CLEAR' if not blockers else 'BLOCKED BY %s' % blockers))


if __name__ == '__main__':
    main()
