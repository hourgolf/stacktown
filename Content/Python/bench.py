"""The BENCHMARK STAND: one catalogue model, permanently placed, with cameras.

    ./Tools/rung.sh bench.py                 the current benchmark model
    ./Tools/rung.sh bench.py <asset name>    any baked mesh

Until now every catalogue model was staged, captured and destroyed inside the
contact-sheet run, so there was nothing in the level to look at - the owner
asked where the model actually was, and the honest answer was "nowhere, for
about four seconds at a time".

The stand is WEST of the board on the studio floor: clear of the city, in
front of the backdrop, lit by the same sun and sky. Three CineCameraActors are
solved onto it rather than remembered, the way cameras.py derives the block
cameras - a camera should not be a remembered number.

    BENCH_Hero     three-quarter, the money shot
    BENCH_Street   low and close, what a pedestrian sees
    BENCH_Roof     high, for the roof garden and the penthouse
"""
import sys, math
import unreal

SANDBOX = 'Sandbox_Bench'


def _require_sandbox():
    """Refuse to build workshop furniture in the shipping level.

    This used to spawn into Stage2_Block, which is how the benchmark
    building ended up standing on the studio floor in a board capture.
    The project guard allows the sandbox map now; this makes sure the
    benchmark stand can only ever land there.
    """
    lvl = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
    if SANDBOX not in lvl:
        raise SystemExit(
            'refusing to build the benchmark stand in %s\n'
            '    Open /Game/Maps/%s and run this again.' % (lvl, SANDBOX))


_require_sandbox()
import _path  # noqa: F401

# DERIVED, not remembered. (-12000, -2640) was a spot on the Stage2 studio
# floor, and carried into the sandbox it put the model past the west end of
# the backdrop - on the ground, but outside the room. A benchmark stand
# belongs in the middle of whatever display board the level actually has.
def _stand_spot():
    eas_ = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    best = None
    for a in eas_.get_all_level_actors():
        n = a.get_actor_label()
        if n in ('STAGE_ModelBoard', 'STAGE_Ground') and (best is None or
                                                          n.endswith('Board')):
            o, e = a.get_actor_bounds(False)
            best = (n, unreal.Vector(o.x, o.y, o.z + e.z))
    if best:
        print('  standing on %s' % best[0])
        return best[1]
    print('  no stage found - standing at the origin')
    return unreal.Vector(0.0, 0.0, 0.0)
BAKED = '/Game/Stacktown/Baked'
DEFAULT = 'SM_Bld_vernacular_t5_w1230'
FOCAL = 70.0
SENSOR_W = 36.0

asset = (sys.argv[1] if len(sys.argv) > 1 else None) or DEFAULT
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(('BENCH_', 'STAND_')):
        eas.destroy_actor(a)

sm = unreal.load_asset('%s/%s' % (BAKED, asset))
if not sm:
    raise SystemExit('bench: no baked mesh named %s' % asset)

AT = _stand_spot()
stand = eas.spawn_actor_from_class(unreal.StaticMeshActor, AT,
                                   unreal.Rotator(0, 0, 0))
stand.set_actor_label('STAND_%s' % asset)
stand.static_mesh_component.set_editor_property('static_mesh', sm)

org, ext = stand.get_actor_bounds(False)
cx, cy, cz = org.x, org.y, org.z
half = max(ext.x, ext.y)
top = org.z + ext.z

HFOV = 2.0 * math.degrees(math.atan(SENSOR_W / (2.0 * FOCAL)))


def look(name, bearing, pitch, aim_z, fit, margin):
    """Solve a standoff that CONTAINS the model, then aim at aim_z.

    The first version sized the standoff from the FOOTPRINT and ignored
    height, so a 1976 uu penthouse tier came back cropped: it solved for a
    615 uu subject and the building is three times that tall. The capture is
    2802 x 2244, so the vertical field is narrower than the horizontal and
    height is usually the binding constraint, not width.
    """
    vfov = 2.0 * math.degrees(math.atan(
        math.tan(math.radians(HFOV/2.0)) * (2244.0/2802.0)))
    d_w = (fit * margin) / math.tan(math.radians(HFOV / 2.0))
    d_h = (ext.z * margin) / math.tan(math.radians(vfov / 2.0))
    dist = max(d_w, d_h)
    r = math.radians(bearing)
    lx = cx - dist * math.cos(r)
    ly = cy - dist * math.sin(r)
    lz = aim_z + dist * math.tan(math.radians(-pitch))
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == name:
            eas.destroy_actor(a)
    cam = eas.spawn_actor_from_class(unreal.CineCameraActor,
                                     unreal.Vector(lx, ly, lz),
                                     unreal.Rotator(0.0, pitch, bearing))
    cam.set_actor_label(name)
    try:
        cc = cam.get_cine_camera_component()
        cc.set_editor_property('current_focal_length', FOCAL)
        f = cc.get_editor_property('focus_settings')
        f.set_editor_property('manual_focus_distance', dist)
        cc.set_editor_property('focus_settings', f)
    except Exception as e:
        print('  (focus not set: %s)' % str(e)[:60])
    print('  %-14s bearing %3.0f  pitch %4.0f  standoff %6.0f  at (%.0f, %.0f, %.0f)'
          % (name, bearing, pitch, dist, lx, ly, lz))


print('bench: %s  %.0f x %.0f x %.0f' % (asset, ext.x*2, ext.y*2, ext.z*2))
look('BENCH_Hero',   55.0, -20.0, cz + ext.z*0.15, max(half, ext.z*0.62), 1.30)
look('BENCH_Street', 78.0,  -6.0, cz - ext.z*0.30, half*0.72, 1.15)
look('BENCH_Roof',   62.0, -42.0, top - ext.z*0.18, half*0.80, 1.20)
les.save_current_level()
print('stand at (%.0f, %.0f) - pilot a BENCH_ camera to watch it' % (AT.x, AT.y))
