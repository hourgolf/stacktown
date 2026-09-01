#!/usr/bin/env python3
"""A SOFT KEY over direction B's board. Owner-approved 2026-09-01.

    python3 Content/Python/board_light.py          add / update
    python3 Content/Python/board_light.py --off    remove

WHY. The board has been lit by the CITY's directional sun: one hard,
distant source. A photographed model is lit by a LARGE NEAR source - a window
or a softbox - which is why its shadows have soft edges and its streets are
filled with warm bounce rather than sky. Hard sun on clean geometry reads as a
render whatever the material does, and the owner's verdict on the last board
was exactly that.

ATTENUATION IS THE WHOLE SAFETY ARGUMENT. mk_studioroom's own note records
fill lights that reached the board from 13,691 uu against a 30,000 attenuation
- caught by arithmetic, not by eye. This board sits at (21000, 20000) and the
CITY is at the origin, ~29,000 uu away, so the radius is held at 11,000: large
enough to wrap the 6,800 uu board, far short of the city. The number is
checked below rather than asserted.

LIGHT_ PREFIX, deliberately. Any script that wipes actors excludes LOOK_ by
rule; the lighting family is LIGHT_ and this joins it so a future sweep treats
it like every other light rather than as an unknown.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import ue  # noqa: E402

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
LEVEL = '/Game/Maps/TestCity'
BX, BY = 21000.0, 20000.0
BW, BD = 6800.0, 4880.0
RADIUS = 11000.0
CITY = (0.0, 0.0)


def main():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s' % lvl
    existing = json.loads(ue.tool(S, 'find_actors', {
        'name': 'LIGHT_BoardKey', 'tag': '',
        'collision_channels': []}))['returnValue']
    for a in existing:
        ue.tool(S, 'remove_from_scene', {'actor': a})
    if '--off' in sys.argv:
        print('removed %d; board key off' % len(existing))
        return 0

    cx, cy = BX + BW / 2.0, BY + BD / 2.0
    # CHECK THE ATTENUATION REACHES THE BOARD AND NOT THE CITY, before placing
    d_city = math.hypot(cx - CITY[0], cy - CITY[1])
    reach = math.hypot(BW, BD) / 2.0
    print('key to board corner %.0f uu, to city %.0f uu, radius %.0f'
          % (reach, d_city, RADIUS))
    assert reach < RADIUS < d_city, (
        'radius %.0f must cover the board (%.0f) and fall short of the city '
        '(%.0f)' % (RADIUS, reach, d_city))

    r = json.loads(ue.tool(S, 'add_to_scene_from_class', {
        'actor_type': {'refPath': '/Script/Engine.RectLight'},
        'name': 'LIGHT_BoardKey',
        'xform': {'location': {'x': cx - 2600.0, 'y': cy - 3400.0,
                               'z': 5200.0},
                  'rotation': {'pitch': -52.0, 'yaw': 58.0, 'roll': 0.0}}}
        ))['returnValue']
    ue.tool(A, 'set_label', {'actor': r, 'label': 'LIGHT_BoardKey'})
    comps = json.loads(ue.tool(A, 'get_components', {'actor': r}))['returnValue']
    lc = [c for c in comps if 'RectLight' in c.get('refPath', '')]
    tgt = lc[0] if lc else comps[-1]
    # A BIG SOURCE IS THE POINT. Softness comes from source SIZE relative to
    # subject, not from an intensity curve - a 4 m x 2.6 m rectangle at this
    # distance is a studio window onto a 68 m board.
    want = {'sourceWidth': 4000.0, 'sourceHeight': 2600.0,
            'intensity': 26.0, 'attenuationRadius': RADIUS,
            'lightColor': {'r': 255, 'g': 244, 'b': 226, 'a': 255},
            'castShadows': True}
    # NOT sourceSoftRadius - that lives on point/spot lights and a rect light
    # refuses it. A rect light's softness IS its source rectangle, which is
    # the physically honest version anyway: a window is soft because it is
    # big, not because a radius says so.
    ue.tool(OBJ, 'set_properties', {'instance': tgt,
                                    'values': json.dumps(want)})
    back = ue.tool(OBJ, 'get_properties', {
        'instance': tgt,
        'properties': ['sourceWidth', 'sourceHeight', 'attenuationRadius',
                       'intensity']})
    print('soft key placed; read back: %s' % back[:170])
    return 0


if __name__ == '__main__':
    sys.exit(main())
