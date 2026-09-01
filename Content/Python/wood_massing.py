#!/usr/bin/env python3
"""Build DIRECTION B's carved masses LIVE, in timber, and photograph them.

    python3 Content/Python/wood_massing.py

THE POINT. Every timber frame so far has been a FLAGSHIP building re-skinned
in wood, which the owner correctly rejected: "you are just building flagship
building with only one material (wood) whereas the doctrine states you should
be building new simpler forms." B1 is windowless carved masses. This builds
those - genbuild with `massing_only`, which suppresses the glazing family at
the emission primitives and removes 59-74% of a model's parts.

NO BAKE. genbuild's LIVE path spawns real components into the open level, so
the masses can be seen without a bake and without the bake policy's triggers.
Driven from LOCAL python calling MCP from OUTSIDE the editor - the only safe
direction; an MCP call from inside a rung script waits on its own thread.

STAGED INSIDE CITY_Room and removed afterwards, removal VERIFIED by search. The
level is asserted before every mutating step and TestCity is never saved.
"""
import json
import os
import sys
import time
import base64
import contextlib
import io

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import genbuild  # noqa: E402
import preview  # noqa: E402
import ue  # noqa: E402

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
APP = 'EditorToolset.EditorAppToolset'
LEVEL = '/Game/Maps/TestCity'
MATD = '/Game/Stacktown/Materials'
PROJECT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(PROJECT, 'Saved', 'DirectionB')

# one species per mass, spanning the height range as before
SUBJECTS = [
    ('maple',  'vernacular8', 0, 820.0),
    ('oak',    'modern8',     5, 1640.0),
    ('cherry', 'modern3',     3, 1230.0),
    ('walnut', 'tower',       6, 1230.0),
]
# INSIDE CITY_Room. This staged at y=60000, which is OUTSIDE the room
# entirely (x +/-37536, y +/-34116), so these subjects were photographed
# against a black void - AGENTS.md founding failure 5, and measurably:
# the frames this produced ran 42-58%% of pixels crushed to black. That
# is what the owner was looking at when they said "I can't see anything".
# 20000 puts the row on the lit floor where the board already stands.
BASE_Y = 20000.0
SPACING = 3200.0


def assert_level():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s - refusing' % lvl
    return lvl


def main():
    print('level:', assert_level())
    made = []
    genbuild.live()
    try:
        x = 0.0
        for sp, rid, tier, w in SUBJECTS:
            with contextlib.redirect_stdout(io.StringIO()):
                spec, _rec = preview.collect(rid, tier, w)
            spec = dict(spec)
            spec['massing_only'] = True
            spec['name'] = 'MASS_%s' % sp
            spec['wall'] = 'MI_wood_%s' % sp        # role -> timber
            spec['roofmat'] = 'MI_wood_%s' % sp
            spec['trim'] = 'MI_wood_%s' % sp
            t0 = time.time()
            with contextlib.redirect_stdout(io.StringIO()):
                genbuild.build(spec, origin=(x, BASE_Y, 0.0), yaw=0.0)
            print('%-8s %-14s t%d  %4d parts suppressed, built in %.0fs'
                  % (sp, rid, tier, len(genbuild.MASSING_SKIPPED), time.time() - t0))
            made.append('MASS_%s' % sp)
            x += SPACING
    finally:
        genbuild.live(False)

    # bind every component of every mass to its timber
    for sp, _r, _t, _w in SUBJECTS:
        acts = json.loads(ue.tool(S, 'find_actors', {
            'name': 'MASS_%s' % sp, 'tag': '', 'collision_channels': []}))['returnValue']
        mi = '%s/MI_wood_%s.MI_wood_%s' % (MATD, sp, sp)
        n = 0
        for a in acts:
            comps = json.loads(ue.tool(A, 'get_components', {'actor': a}))['returnValue']
            for c in comps:
                if 'StaticMeshComponent' in c.get('refPath', '') or \
                        c.get('refPath', '').rsplit('.', 1)[-1].startswith(
                            ('Wall_', 'Band_', 'Tile_', 'Roof_', 'Accent_',
                             'Rail_', 'Brick_', 'Timber_', 'Ground_')):
                    ue.tool(OBJ, 'set_properties', {'instance': c, 'values': json.dumps(
                        {'overrideMaterials': [{'refPath': mi}]})})
                    n += 1
        print('%-8s %4d components bound to timber' % (sp, n))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    span = SPACING * (len(SUBJECTS) - 1)
    for tag, cam in (
        ('DIRECTIONB_massing_blockhero',
         {'location': {'x': span / 2.0, 'y': BASE_Y - 11000.0, 'z': 2800.0},
          'rotation': {'pitch': -10.0, 'yaw': 90.0, 'roll': 0.0},
          'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}),
        ('DIRECTIONB_massing_playerzoom',
         {'location': {'x': SPACING * 1.0, 'y': BASE_Y - 2600.0, 'z': 700.0},
          'rotation': {'pitch': -4.0, 'yaw': 90.0, 'roll': 0.0},
          'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}})):
        ue.tool(APP, 'SetCameraTransform', {'transform': cam})
        time.sleep(10)
        for i in range(3):
            r = json.loads(ue.tool(APP, 'CaptureViewport', {
                'captureTransform': cam, 'annotations': ann,
                'bShowUI': False}))['returnValue']
            open(os.path.join(OUT, '%s_%d.png' % (tag, i)), 'wb').write(
                base64.b64decode(r['image']['data']))
            time.sleep(1.6)
        print('captured', tag)

    assert_level()
    for nm in made:
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': nm, 'tag': '', 'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})
    left = json.loads(ue.tool(S, 'find_actors', {
        'name': 'MASS_', 'tag': '', 'collision_channels': []}))['returnValue']
    print('\nMASS_ actors left:', len(left))
    assert not left, 'cleanup incomplete'
    print('level clean; %s NOT saved' % LEVEL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
