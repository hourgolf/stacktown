#!/usr/bin/env python3
"""WHAT LIFTING D11 SECTION 3 WOULD LOOK LIKE. Five treatments, one block.

    python3 Content/Python/carve_compare.py

D11 section 3 locks the carving scope: "No recessed openings. No carved window
bays. Setbacks, a plinth, and a scored line where a stage steps; all
information from silhouette and tone." The owner has allowed a LITTLE lifting
of that lock on condition of seeing it first. This is the seeing.

NOTHING IS LIFTED BY RUNNING THIS. genbuild's `carve` key defaults to None,
which emits the locked single box - genbuild_identity confirms 10 models
unchanged. These five assets exist to be photographed side by side and then
mostly thrown away.

ONE VARIABLE. Same footprint, same height, same species, same seed, same
light, same frame. Only the treatment moves, so a difference in the frame is
a difference in carving and not in anything else. A single stage, so even the
locked scored line is absent and the comparison is not muddied by it.

THE PART COUNT IS THE ARGUMENT AGAINST EACH ONE and is printed beside it.
BETA_TWIN seam 3 makes fewer parts per m2 the direction itself, so a treatment
that reads beautifully at four times the parts is not free, and the owner
should be choosing with that number in view rather than after it.
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import genbuild  # noqa: E402
import ue  # noqa: E402
import wood_board as wb  # noqa: E402

RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
OUT_ASSET = '/Game/Stacktown/BakedWood'
TMP = tempfile.gettempdir()
S, A, OBJ, MIT = wb.S, wb.A, wb.OBJ, wb.MIT
APP, MATD, LEVEL, OUT = wb.APP, wb.MATD, wb.LEVEL, wb.OUT

# the locked treatment first, then the four candidates, cheapest first
MODES = [(None, 'locked'), ('base', 'base'), ('band', 'band'),
         ('courses', 'courses'), ('flutes', 'flutes')]
GEOM = dict(width=900.0, depth=820.0, height=2400.0,
            stages=[(1.0, 0.0)], cap=0.0)
SPECIES = 'oak'          # never rotated, so the normal was never crossed
GAP = 420.0


def main():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s - refusing' % lvl
    assert json.loads(ue.tool(S, 'find_actors', {
        'name': 'LIGHT_BoardKey', 'tag': '',
        'collision_channels': []}))['returnValue'], 'run board_light.py first'

    print('%-10s %6s %8s  %s' % ('treatment', 'parts', 'vs locked', 'asset'))
    counts = {}
    for mode, tag in MODES:
        spec = dict(GEOM, style='mass', name='Carve%s' % tag, seed=4242,
                    plinth=24.0, hand_tolerance=False, carve=mode,
                    wall='MI_wood_%s' % SPECIES,
                    roofmat='MI_wood_%s' % SPECIES,
                    trim='MI_wood_%s' % SPECIES)
        genbuild.record()
        with contextlib.redirect_stdout(io.StringIO()):
            genbuild.build(spec)
        rec = genbuild.drain()
        counts[tag] = len([r for r in rec if r['kind'] == 'box'])
        json.dump({'boxes': rec, 'out': '%s/SM_Carve_%s' % (OUT_ASSET, tag),
                   'wall': spec['wall'], 'roofmat': spec['roofmat'],
                   'trim': spec['trim'], 'panel_overrides': {},
                   'chamfer': 14.0},
                  open(os.path.join(TMP, 'stacktown_fastbake_job.json'), 'w'))
        r = subprocess.run([RUNG, 'fastbake.py'], capture_output=True,
                           text=True, cwd=HERE)
        ok = 'FASTBAKED' in r.stdout and 'success: True' in r.stdout
        print('%-10s %6d %7s%%  %s' % (tag, counts[tag],
              '%+.0f' % (100.0 * (counts[tag] / float(counts['locked']) - 1.0)),
              'baked' if ok else 'FAILED: %s' % r.stdout[-120:]))
        if not ok:
            return 1

    for stale in ('CARVE_',):
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': stale, 'tag': '',
                'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})

    span = len(MODES) * GEOM['width'] + (len(MODES) - 1) * GAP
    ox = wb.BASE_X + 3400.0 - span / 2.0
    oy = wb.BASE_Y + 2440.0
    cache = {}
    for i, (mode, tag) in enumerate(MODES):
        label = 'CARVE_%s' % tag
        r = json.loads(ue.tool(S, 'add_to_scene_from_asset', {
            'asset_path': '%s/SM_Carve_%s' % (OUT_ASSET, tag), 'name': label,
            'xform': {'location': {'x': ox + i * (GEOM['width'] + GAP),
                                   'y': oy, 'z': 0.0},
                      'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                      'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}))['returnValue']
        ue.tool(A, 'set_label', {'actor': r, 'label': label})
        mi = wb.mi_for(SPECIES, 0, cache)
        for c in json.loads(ue.tool(A, 'get_components', {
                'actor': r}))['returnValue']:
            if 'StaticMeshComponent' in c.get('refPath', ''):
                ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                        json.dumps({'overrideMaterials': [mi]})})
    print('\n%d treatments standing, left to right: %s'
          % (len(MODES), ', '.join(t for _, t in MODES)))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    cx = ox + span / 2.0
    import wood_set as WS
    shots = (
        ('CARVE_row', WS.look_at(cx, oy + GEOM['depth'] / 2.0, 1250.0,
                                 9000.0, -8.0, 74.0)),
        ('CARVE_close', WS.look_at(ox + GEOM['width'] * 1.6,
                                   oy + GEOM['depth'] / 2.0, 1150.0,
                                   4200.0, -6.0, 62.0)))
    for tag, cam in shots:
        ue.tool(APP, 'SetCameraTransform', {'transform': cam})
        time.sleep(9)
        got = json.loads(ue.tool(APP, 'CaptureViewport', {
            'captureTransform': cam, 'annotations': ann,
            'bShowUI': False}))['returnValue']
        import base64
        open(os.path.join(OUT, '%s.png' % tag), 'wb').write(
            base64.b64decode(got['image']['data']))
        print('captured', tag)

    if '--keep' not in sys.argv:
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': 'CARVE_', 'tag': '',
                'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})
        print('cleaned; %s NOT saved' % LEVEL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
