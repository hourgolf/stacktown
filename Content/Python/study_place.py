"""Stand the study wall on the studio floor and report its bounds."""
import json
import unreal
# WELL clear of the bench stand at (-12000, -2640): at a 5,972 uu standoff the
# building stood between the camera and panels 4 and 5, so their samples were
# measuring a dark facade. A study that photographs something else is not a
# study.
AT = unreal.Vector(-20000.0, -2640.0, 0.0)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('STUDY_'):
        eas.destroy_actor(a)
sm = unreal.load_asset('/Game/Stacktown/Baked/SM_MatStudy')
if not sm:
    raise SystemExit('no study mesh')
# MEASURED: LIGHT_Sun is pitch -52, yaw 45, so light travels toward +X/+Y and
# down. A face is lit when its normal opposes that - which is the -Y face, the
# panel's ORIGINAL orientation. Yawing the wall 180 to "fix the lighting" put
# the study on the shadow side; the panels only ever looked dark because a
# vertical wall under a 52-degree sun takes 43% of the light a floor does.
a = eas.spawn_actor_from_class(unreal.StaticMeshActor, AT, unreal.Rotator(0, 0, 0))
a.set_actor_label('STUDY_Wall')
a.static_mesh_component.set_editor_property('static_mesh', sm)
org, ext = a.get_actor_bounds(False)
print('STUDYBOUNDS ' + json.dumps(dict(
    o=[org.x, org.y, org.z], e=[ext.x, ext.y, ext.z])))
les.save_current_level()
