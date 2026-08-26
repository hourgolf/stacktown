"""Print the BENCH_ camera transforms so the capture path can use them."""
import json
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = {}
for a in eas.get_all_level_actors():
    n = a.get_actor_label()
    if not n.startswith('BENCH_'):
        continue
    l, r = a.get_actor_location(), a.get_actor_rotation()
    out[n] = dict(location=dict(x=l.x, y=l.y, z=l.z),
                  rotation=dict(pitch=r.pitch, yaw=r.yaw, roll=r.roll))
print('BENCHCAMS ' + json.dumps(out))
