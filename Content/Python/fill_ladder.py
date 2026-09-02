#!/usr/bin/env python3
"""SUBJECT: DENSITY BOARD (secondary). Sun-to-fill ratio, mechanism 2.

    python3 Content/Python/fill_ladder.py

The census found CITY_Sun dominant (+23.6) with CITY_Key (+8.1), CITY_Fill
(+2.2) and CITY_Sky (+0.7) supplying ~11 levels of largely directionless fill.
Our shadows measure LIFTED against B1 - 0.518 against 0.337 - so reducing the
fill should deepen them. Whether it also buys LOCAL CONTRAST, which is the
real deficit (grad_p90 12 against 92), is the question.

EXPOSURE IS HELD BY ISO, NOT BY THE LIGHTS. Compensating with the sun would
change the very ratio under test - a fill ladder wearing a brightness label,
which is the trap dof.py records from the DOF sweep. ISO is a CAMERA property,
so the lighting keeps exactly one variable.

THE BASELINE COMES FROM THE FILE, NOT FROM THIS RUN. The first attempt at this
ladder crashed partway with the fill at 0.5x and never restored; the next run
read that halved scene as its baseline and "restored" to it. Three lights and
the ISO were left at half. So: restore_baseline() reads the recorded pre-touch
state, writes it back, and READS BACK to assert - and it runs in a finally, so
a crash here cannot poison whatever runs next.
"""
import json
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
FILL = ('CITY_Key', 'CITY_Fill', 'CITY_Sky')
RUNGS = (1.0, 0.5, 0.25, 0.0)
B1 = {'grad_p90': 92, 'lift': 0.337, 'spread': 190}


def main():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], 'PIE active'
    n = len(json.loads(ue.tool(S, 'find_actors', {
        'name': 'SETB_', 'tag': '', 'collision_channels': []}))['returnValue'])
    assert n > 100, 'only %d buildings standing - no subject' % n
    base = AB.restore_baseline()          # start from a known-clean scene
    cam = json.load(open(os.path.join(OUT, 'ab_camera.json')))
    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    comps = {l: AB.light_comp(l, dict(AB.LIGHTS)[l]) for l in FILL}
    st, iso0 = AB._iso()
    print('SUBJECT: DENSITY BOARD (secondary), %d buildings' % n)
    print('fill baseline: %s' % {l: '%.3g' % base[l] for l in FILL})
    print('%-8s %8s %8s %10s %8s %8s' % ('fill x', 'ISO', 'mean', 'grad_p90',
                                         'lift', 'spread'))
    rows, ctrl = [], None
    try:
        for k in RUNGS:
            for l in FILL:
                ue.tool(OBJ, 'set_properties', {'instance': comps[l], 'values':
                        json.dumps({'intensity': base[l] * k})})
            iso = iso0
            def shoot(i):
                st['cameraISO'] = float(i)
                ue.tool(OBJ, 'set_properties', {'instance': AB._post(),
                        'values': json.dumps({'settings': st})})
                ue.declare_lens(float(st['depthOfFieldFstop']), float(i),
                                float(st['cameraShutterSpeed']))
                return AB.measure(AB._shoot(
                    'FILL2_x%s' % ('%g' % k).replace('.', 'p'), cam, ann))
            m = shoot(iso)
            if ctrl is None:
                ctrl = m['mean']
            for _ in range(4):
                if abs(m['mean'] - ctrl) <= 2.0:
                    break
                iso *= ctrl / max(1.0, m['mean'])
                m = shoot(iso)
            m['k'], m['iso'] = k, iso
            rows.append(m)
            print('%-8g %8.0f %8.2f %10d %8.3f %8d'
                  % (k, iso, m['mean'], m['grad_p90'], m['lift'], m['spread']))
    finally:
        AB.restore_baseline()
    print()
    print('B1 target: grad_p90 %d, lift %.3f, spread %d'
          % (B1['grad_p90'], B1['lift'], B1['spread']))
    json.dump({'subject': 'density board (secondary)', 'rows': rows, 'b1': B1},
              open(os.path.join(OUT, 'fill_ladder.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
