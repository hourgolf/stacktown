"""Stage one baked mesh ON THE MODEL BOARD - the hero position.

sheet_stage.py parks a model at (-12000, -2640), far off the board, which is
fine for a neutral catalogue shot but useless for judging the stage lighting:
LIGHT_Key sits at (-2430,-2970) aimed yaw 45, i.e. at the board at (550,-100),
so a model at -12000 is behind the light, outside the beam and outside the
barn doors. Turning the key on changed a sheet-stage frame by -0.5 of a mean.

This puts the model where the lights are actually pointed, and on the board's
TOP surface (z = 0, per stagegeo) rather than the room floor.

  reads:  stacktown_board_job.json  {asset}
  writes: stacktown_board_info.json {bounds, z0, z1}
"""
import unreal
import _path  # noqa: F401
import stagegeo
import json
import os
import tempfile

SANDBOX = 'Sandbox_Bench'
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if SANDBOX not in eus.get_editor_world().get_path_name():
    raise SystemExit('sandbox only')

TMP = tempfile.gettempdir()
job = json.load(open(os.path.join(TMP, 'stacktown_board_job.json')))
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('BOARD_'):
        eas.destroy_actor(a)

if job.get('clear'):
    print('boardstage: cleared')
else:
    sm = eal.load_asset(job['asset'])
    if not sm:
        raise SystemExit('missing %s' % job['asset'])
    bb = sm.get_bounding_box()
    # centre the model's FOOTPRINT on the board, base on the board's top
    at = unreal.Vector(550.0 - (bb.min.x + bb.max.x) / 2.0,
                       -100.0 - (bb.min.y + bb.max.y) / 2.0,
                       stagegeo.BOARD_TOP_Z)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, at,
                                   unreal.Rotator(0, 0, 0))
    a.set_actor_label('BOARD_%s' % job['asset'].split('/')[-1])
    a.static_mesh_component.set_editor_property('static_mesh', sm)
    o, e = a.get_actor_bounds(False)
    info = dict(bounds=[o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y],
                z0=o.z - e.z, z1=o.z + e.z)
    json.dump(info, open(os.path.join(TMP, 'stacktown_board_info.json'), 'w'))
    print('boardstage: %s at (%.0f,%.0f,%.0f)  z %.0f..%.0f'
          % (a.get_actor_label(), at.x, at.y, at.z, info['z0'], info['z1']))
