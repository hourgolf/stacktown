"""Place the dormant road-segment pool in TestCity - STANDALONE.

The beta lane wrote build_road_pool() inside mk_testcity_builds.py, but
that file runs build() unconditionally at import (its own long-standing
convention), so importing it to reach one function would rebuild the
whole city. This is the same function body, alone, with its own guards.
RUN THROUGH rung.sh with PIE off and TestCity loaded; it mutates the
level (ten StaticMeshActors at the parcel pool's graveyard) and does NOT
save - the TestCity save is the owner's word, made separately.

Read-back prints label, mesh and material per actor; a material=None
line is the one uncertainty the lane named (override_materials as a
Python property) and must be checked before trusting the pool.
"""
import unreal

ROAD_POOL_SIZE = 10
_POOL_GRAVEYARD = unreal.Vector(0.0, 0.0, -50000.0)
_ROAD_CUBE = '/Engine/BasicShapes/Cube.Cube'
_ROAD_MATERIAL = '/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey'


def build_road_pool():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les.is_in_play_in_editor():
        raise SystemExit('ABORT: PIE is running')
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    lvl = ues.get_editor_world().get_path_name()
    if 'TestCity' not in lvl:
        raise SystemExit('ABORT: TestCity is not the loaded level (%s)' % lvl)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith('POOL_ROAD_'):
            eas.destroy_actor(a)
    cube = unreal.load_asset(_ROAD_CUBE)
    mat = unreal.load_asset(_ROAD_MATERIAL)
    if cube is None or mat is None:
        raise SystemExit('ABORT: cube=%s material=%s' % (cube, mat))
    readback = []
    for i in range(ROAD_POOL_SIZE):
        a = eas.spawn_actor_from_object(cube, _POOL_GRAVEYARD, unreal.Rotator(0.0, 0.0, 0.0))
        label = 'POOL_ROAD_%02d' % i
        a.set_actor_label(label)
        a.set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)
        mesh_path = mat_path = None
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_material(0, mat)
            sm = c.get_editor_property('static_mesh')
            mesh_path = sm.get_path_name() if sm else None
            m0 = c.get_material(0)
            mat_path = m0.get_path_name() if m0 else None
        readback.append((label, mesh_path, mat_path, a.get_class().get_name()))
    for label, mesh_path, mat_path, cls in readback:
        print('%s  %s  mesh=%s  material=%s' % (label, cls, mesh_path, mat_path))
    print('road pool: %d dormant POOL_ROAD_NN actors staged at the graveyard, hidden, '
          'non-colliding; TestCity is DIRTY and unsaved - the save is the owner\'s word' % len(readback))
    return readback


build_road_pool()
