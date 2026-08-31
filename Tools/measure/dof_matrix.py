import sys, math, json
sys.path.insert(0, '.')
import ue, cap2, live, dof, framing, shot
import citygeom as G

# f/2 at 1/240 everywhere except 'off', which is the gate condition f/4 at
# 1/60. Measured: exposure holds within 0.6 across five stops when shutter
# pays for aperture, so what changes along a row is depth of field alone.
COLS = [('off', None, 36.0, 4.0, 60.0),
        ('s150', 150.0, 150.0, 2.0, 240.0),
        ('s400', 400.0, 400.0, 2.0, 240.0),
        ('s1000', 1000.0, 1000.0, 2.0, 240.0)]

SUBJECTS = [('street', shot.lot_rect('Bijou'), 'N', 460.0, 1.02, -26.0),
            ('block', (7480.0, -8810.0, 10760.0, -7990.0), 'N', 760.0, 1.10, -30.0),
            ('board', G.board_rect(), None, 2600.0, 1.06, -32.0)]

out = {}
for name, rect, side, z1, margin, pitch in SUBJECTS:
    if side is None:
        loc, rot = framing.frame(rect, 132.0, pitch=pitch, z1=z1, margin=margin)
    else:
        loc, rot = framing.from_street(rect, side, pitch=pitch, z1=z1, margin=margin)
    tgt = ((rect[0]+rect[2])/2.0, (rect[1]+rect[3])/2.0, z1/2.0)
    dist = math.dist((loc['x'], loc['y'], loc['z']), tgt)
    cap2.set_fov()
    ue.tool('EditorToolset.EditorAppToolset', 'SetCameraTransform',
            {'transform': {'location': loc, 'rotation': rot,
                           'scale': {'x': 1, 'y': 1, 'z': 1}}})
    got = json.loads(ue.tool('EditorToolset.EditorAppToolset',
                             'GetCameraTransform', {}))['returnValue']['location']
    assert abs(got['x']-loc['x']) < 2 and abs(got['y']-loc['y']) < 2
    cap2.VIEWS[name] = (loc, rot)
    for tag, _sw, sensor, f, sh in COLS:
        if tag == 'off':
            dof.reset()
        else:
            dof.set_dof(f, dist, sensor=sensor, shutter=sh)
        fn = '%s_%s.png' % (name, tag)
        for _ in range(12):
            cap2.capture(fn, name)
        s = live.stats(fn)
        out['%s_%s' % (name, tag)] = dict(mean=round(s['mean'], 1),
                                          dist=round(dist), sensor=sensor)
        print('%-6s %-6s focus %6.0f uu  sensor %-6.0f mean %6.1f'
              % (name, tag, dist, sensor, s['mean']))
dof.reset()
json.dump(out, open('matrix.json', 'w'), indent=1)
print('matrix complete')
