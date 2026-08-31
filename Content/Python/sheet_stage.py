"""Stage one baked catalogue mesh alone, and report its bounds and stamp.

Placed on the studio floor WEST of the board - clear of the city, in front of
the backdrop, and lit by the same sun and sky. Consistency across models is
what a contact sheet needs; the board's local rect lights do not reach here
and that is fine, because every model is judged under the same light.

    job:    {"asset": "/Game/Stacktown/Baked/SM_..."}
    writes: stacktown_sheet_info.json  {bounds, stamp}
"""
import os, json, tempfile
import unreal

JOB = os.path.join(tempfile.gettempdir(), 'stacktown_sheet_job.json')
OUT = os.path.join(tempfile.gettempdir(), 'stacktown_sheet_info.json')
AT = unreal.Vector(-12000.0, -2640.0, 0.0)
P = 'Stacktown.'
TAGS = ('Recipe', 'Tier', 'TierName', 'Width', 'Gate', 'GateRules', 'Parts',
        'Materials', 'Density', 'SpanX', 'SpanY', 'Stamped')

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('SHEET_'):
        eas.destroy_actor(a)

job = json.load(open(JOB))
path = job['asset']
sm = unreal.load_asset(path)
if not sm:
    raise SystemExit('sheet_stage: no asset at %s' % path)

a = eas.spawn_actor_from_class(unreal.StaticMeshActor, AT, unreal.Rotator(0, 0, 0))
a.set_actor_label('SHEET_' + path.rsplit('/', 1)[-1])
a.static_mesh_component.set_editor_property('static_mesh', sm)

org, ext = a.get_actor_bounds(False)
info = dict(
    bounds=[org.x - ext.x, org.y - ext.y, org.x + ext.x, org.y + ext.y],
    z0=org.z - ext.z, z1=org.z + ext.z,
    slots=len(sm.get_editor_property('static_materials')),
    tris=sm.get_num_triangles(0) if hasattr(sm, 'get_num_triangles') else 0,
    stamp={k: unreal.EditorAssetLibrary.get_metadata_tag(sm, P + k) for k in TAGS})
json.dump(info, open(OUT, 'w'))
print('  staged %s  %.0f x %.0f x %.0f  slots %d'
      % (path.rsplit('/', 1)[-1], ext.x*2, ext.y*2, ext.z*2, info['slots']))
