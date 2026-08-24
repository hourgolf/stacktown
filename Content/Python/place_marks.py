"""Create BLD_Marks and one component per fabrication mark (MCP side).

Components are made with PrimitiveTools.add_cube because that is the path that
works in this project; the mesh, material and transform are retargeted
afterwards by place_marks_ue.py. The actor sits at the origin unrotated, so
local transforms are world transforms and the table stays readable.
"""
import ue, json

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'

marks = json.load(open('marks_table.json'))

r = ue.tool(S, 'add_to_scene_from_class',
            {'actor_type': {'refPath': '/Script/Engine.Actor'},
             'name': 'BLD_Marks',
             'xform': {'location': {'x': 0, 'y': 0, 'z': 0}}})
actor = json.loads(r)['returnValue']
ue.tool(A, 'set_label', {'actor': actor, 'label': 'BLD_Marks'})

n = 0
for m in marks:
    res = ue.tool(P, 'add_cube', {
        'actor': actor, 'name': m['name'],
        'dimensions': {'x': 10.0, 'y': 10.0, 'z': 10.0},
        'local_transform': {'location': {'x': m['loc'][0],
                                         'y': m['loc'][1],
                                         'z': m['loc'][2]}}})
    if 'ERROR' in res:
        print('  FAIL', m['name'], res[:90])
    else:
        n += 1
print('created BLD_Marks with %d of %d components' % (n, len(marks)))
