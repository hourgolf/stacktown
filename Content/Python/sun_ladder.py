#!/usr/bin/env python3
"""SUBJECT: THE DENSITY BOARD (secondary). Play-board run pending dressing.

WHY NOT THE PLAY BOARD, which the owner chose as primary: its fourteen parcels
carry staticMesh = NONE in the EDITOR world, because the from-scratch design
assigns meshes at RUNTIME (ResolveMesh at BeginPlay). Buildings exist only in
PIE, and the capture bridge photographs the editor world - so the play board
is, correctly, an empty board to every frame this study can take. A dressing
script is being built to place the pinned identities editor-side; this ladder
re-runs on the play framing the moment it lands.

The mechanism transfers even though the ratios will not: CITY_Sun dominates
BOTH boards (+23.6 density, and the largest contributor near the origin too).
What will NOT transfer is "sun-to-fill", because the fill is a different set
of lights on each board.

An earlier version of this file ran against cam_city.py's pose and returned a
flat null across 40x of source angle. That pose is from an older era of this
map and frames bare ground: the null was measured on a frame with nothing in
it to cast a shadow, and it has been withdrawn rather than reported.

The sun's source-angle ladder — the lighting study's first mechanism on the
real instrument.

    python3 Content/Python/sun_ladder.py

WHY THE SUN AND WHY THIS PROPERTY. The census (Docs/LIGHTING_STUDY.md) found
CITY_Sun dominates BOTH boards - +28.4 luma levels on the play board against
CITY_Key's +6.4 - despite carrying an intensity of 430 where the rect lights
carry 2e7. Directional lights do not attenuate with distance, so intensity
numbers do not rank these lights.

A directional light's shadow SOFTNESS is its angular diameter,
`lightSourceAngle` - the true analogue of the rect light's source size that
the original study aimed at and never reached. Ours is at the physical sun's
0.5357 degrees.

THE DEFICIT IS LOCAL CONTRAST: gradient p90 measures 12 against the B1
reference's 92, and shadows are lifted (0.500 vs 0.337). A SMALLER angle
hardens every shadow edge on the light doing most of the work.

THE LADDER BRACKETS BOTH WAYS on purpose - 2.0 degrees is softer than the real
sun, 0.05 is far harder. A ladder that only goes the way you expect cannot
show you that the effect runs the other way, and this study has already been
wrong about a direction once.

A-B-A THROUGHOUT: a fresh control before and after every rung, because the
first census was contaminated by a scene still converging and reported three
lights as negative contributors - impossible for an additive light, and the
tell that the baseline was moving underneath the measurement.
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
import lighting_ab as AB  # noqa: E402
import wood_board as wb  # noqa: E402

S, A, OBJ, APP = wb.S, wb.A, wb.OBJ, wb.APP
OUT = wb.OUT
LADDER = [2.0, 0.5357, 0.20, 0.05]        # control is 0.5357, the real sun
B1 = {'grad_p90': 92, 'lift': 0.337, 'spread': 190}


def subject_cam():
    """The density board's oblique - the same transform wood_set captured it
    with, read from disk rather than re-derived, so the ladder and the board
    cannot disagree about where the camera stood."""
    f = os.path.join(OUT, 'ab_camera.json')
    assert os.path.exists(f), 'no ab_camera.json - run wood_set.py --keep'
    return json.load(open(f))


def sun():
    for a in json.loads(ue.tool(S, 'find_actors', {
            'name': 'CITY_Sun', 'tag': '', 'collision_channels': [],
            'actor_type': {'refPath': '/Script/Engine.DirectionalLight'}}
            ))['returnValue']:
        for c in json.loads(ue.tool(A, 'get_components', {
                'actor': a}))['returnValue']:
            if 'LightComponent' in c.get('refPath', ''):
                return c
    raise SystemExit('CITY_Sun not found')


def main():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], \
        'PIE active - refusing'
    c = sun()
    was = json.loads(json.loads(ue.tool(OBJ, 'get_properties', {
        'instance': c, 'properties': ['lightSourceAngle']}))['returnValue']
        )['lightSourceAngle']
    cam = subject_cam()
    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    n = len(json.loads(ue.tool(S, 'find_actors', {
        'name': 'SETB_', 'tag': '', 'collision_channels': []}))['returnValue'])
    assert n > 100, ('only %d buildings standing - this ladder measures shadow '
                     'behaviour and needs a subject that casts them. The last '
                     'run of this file returned a null on an empty frame.' % n)
    print('SUBJECT: DENSITY BOARD (secondary), %d buildings.' % n)
    print('sun lightSourceAngle was %.4f deg' % was)
    print('%-9s %8s %10s %8s %8s   %s'
          % ('angle', 'mean', 'grad_p90', 'lift', 'spread', 'vs B1 grad 92'))
    rows = []
    for ang in LADDER:
        ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                json.dumps({'lightSourceAngle': float(ang)})})
        tag = 'SUN_ang%s' % ('%g' % ang).replace('.', 'p')
        m = AB.measure(AB._shoot(tag, cam, ann))
        m['angle'] = ang
        rows.append(m)
        print('%-9.4f %8.2f %10d %8.3f %8d   %+d'
              % (ang, m['mean'], m['grad_p90'], m['lift'], m['spread'],
                 m['grad_p90'] - B1['grad_p90']))
    ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
            json.dumps({'lightSourceAngle': float(was)})})
    back = json.loads(json.loads(ue.tool(OBJ, 'get_properties', {
        'instance': c, 'properties': ['lightSourceAngle']}))['returnValue']
        )['lightSourceAngle']
    assert abs(back - was) < 1e-4, 'sun angle NOT restored (%.4f)' % back
    print('sun restored to %.4f deg' % back)
    json.dump({'subject': 'density board (secondary)', 'rows': rows, 'b1': B1, 'was': was},
              open(os.path.join(OUT, 'sun_ladder.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
