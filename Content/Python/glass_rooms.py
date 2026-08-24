"""Shallow rooms behind the glazing, via the MCP bridge.

A back wall alone still reads flat. A floor and ceiling give the recess a
direction for light to fall off along, which is what makes a window read as
having a space behind it rather than a painted panel.
"""
import ue, json

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
F = '/Game/Stacktown/Materials'

BAYS = [(60.0, 300.0), (420.0, 660.0), (780.0, 1020.0)]
GF_H, FL_H, BAND_COURSE, RECESS, DEPTH = 420.0, 360.0, 44.0, 25.0, 46.0

acts = json.loads(ue.tool(S, 'find_actors',
                          {'name': '', 'tag': '', 'collision_channels': []}))['returnValue']
byname = {}
for a in acts:
    ref = a if isinstance(a, dict) else {'refPath': a}
    lbl = json.loads(ue.tool(A, 'get_label', {'actor': ref}))['returnValue']
    byname[lbl] = ref


def box(actor, name, x0, x1, y0, y1, z0, z1, mat):
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': abs(x1 - x0), 'y': abs(y1 - y0), 'z': abs(z1 - z0)},
        'local_transform': {'location': {'x': (x0 + x1) / 2.0,
                                         'y': (y0 + y1) / 2.0,
                                         'z': (z0 + z1) / 2.0}}})
    comps = json.loads(ue.tool(A, 'get_components', {'actor': actor}))['returnValue']
    for c in comps:
        if c['refPath'].split('.')[-1] == name:
            ue.tool(O, 'set_properties', {'instance': c, 'values': json.dumps(
                {'OverrideMaterials': [{'refPath': '%s/%s.%s' % (F, mat, mat)}]})})
            return True
    return False


added = 0
for n in range(1, 5):
    ref = byname.get('BLD_Floor_%d' % n)
    if not ref:
        continue
    z0 = GF_H + (n - 1) * FL_H
    wz0, wz1 = z0 + BAND_COURSE, z0 + FL_H - 55
    for i, (bx0, bx1) in enumerate(BAYS):
        added += box(ref, 'RoomFloor%d' % i, bx0 + 2, bx1 - 2,
                     RECESS + 3, RECESS + DEPTH, wz0, wz0 + 3, 'MI_frame_print')
        added += box(ref, 'RoomCeil%d' % i, bx0 + 2, bx1 - 2,
                     RECESS + 3, RECESS + DEPTH, wz1 - 3, wz1, 'MI_interior')
        added += box(ref, 'RoomSideL%d' % i, bx0 + 2, bx0 + 5,
                     RECESS + 3, RECESS + DEPTH, wz0, wz1, 'MI_interior')
        added += box(ref, 'RoomSideR%d' % i, bx1 - 5, bx1 - 2,
                     RECESS + 3, RECESS + DEPTH, wz0, wz1, 'MI_interior')
print('added %d room surfaces' % added)
