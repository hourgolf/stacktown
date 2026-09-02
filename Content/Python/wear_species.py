#!/usr/bin/env python3
"""The Age ladder for the owner's eye: walnut lightening beside oak darkening.

    python3 Content/Python/wear_species.py --ladder

HONEST LABEL, because the frames do not show what a first glance suggests.
This drives Age PER SPECIES from the material instance, not per building.
The per-building path - Custom Primitive Data - is BLOCKED: the component
property is the editor-set DEFAULTS array, while the shader reads the runtime
values only a SetCustomPrimitiveDataFloat call writes. So every walnut in
frame ages together and every oak ages together. That is a real property of
the material and worth judging; it is not the game behaviour, and the
difference is not cosmetic.

WHY THE CPD FLAG IS FLIPPED OFF TO DO THIS. A ScalarParameter with
bUseCustomPrimitiveData set IGNORES the instance override entirely - it reads
the primitive. Driving Age from an MI with the flag on measures nothing, and
this lane already reported one finding from exactly that non-test. The flag
goes off for the shoot and is restored in a finally block.

Subject: SE0 walnut (x=3180) and SW3 oak (x=-613), both at y=-1130, in one
frame. One species runs backwards under UV and the other does not, and a
single shared "age toward honey" curve would have been wrong for one of the
seven - D16's argument, shown rather than asserted.
"""
import base64
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path            # noqa: F401,E402
import ue               # noqa: E402
import img              # noqa: E402
import wear as W        # noqa: E402
import wear_age as WA   # noqa: E402

MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
APP = 'EditorToolset.EditorAppToolset'
OUT = os.path.join(W.OUT, 'species')
# Pulled back from the first attempt, which framed both species and showed
# neither: at y=-4300 the two buildings filled the edges and the forms were
# unreadable. The pair has to let the owner SEE the blocks, not just sample
# their colour.
CAM = {'location': {'x': 1283.0, 'y': -7400.0, 'z': 2100.0},
       'rotation': {'pitch': -13.0, 'yaw': 90.0, 'roll': 0.0}}


def mi(s):
    return {'refPath': '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s' % (s, s)}


def shoot(tag):
    ue.tool(APP, 'SetCameraTransform', {'transform': CAM})
    time.sleep(10)
    r = json.loads(ue.tool(APP, 'CaptureViewport', {
        'captureTransform': CAM, 'annotations': [],
        'bShowUI': False}))['returnValue']
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, '%s.png' % tag)
    open(p, 'wb').write(base64.b64decode(r['image']['data']))
    return p


def ladder():
    W._pie_guard()
    age = W.find_param('Age')
    frames = {}
    try:
        W._setp(age, {'bUseCustomPrimitiveData': False})
        W.recompile()
        assert W._props(age, ['bUseCustomPrimitiveData']
                        ).get('bUseCustomPrimitiveData') is False
        for v in (0.0, 0.5, 1.0):
            for s in WA.TINTS:
                ue.tool(MIT, 'set_scalar_parameter',
                        {'instance': mi(s), 'name': 'Age', 'value': v})
            frames['%.1f' % v] = shoot('age_%02d' % int(v * 10))
            print('  Age %.1f -> %s' % (v, os.path.basename(frames['%.1f' % v])))
    finally:
        for s in WA.TINTS:
            try:
                ue.tool(MIT, 'set_parameter_override',
                        {'instance': mi(s), 'name': 'Age', 'override': False})
            except Exception:
                pass
        W._setp(age, {'bUseCustomPrimitiveData': True})
        W.recompile()
        r = W._props(age, ['bUseCustomPrimitiveData', 'PrimitiveDataIndex'])
        assert r.get('bUseCustomPrimitiveData') is True and \
            r.get('PrimitiveDataIndex') == 0, 'Age flag NOT restored: %s' % r
        print('  Age restored: cpd on, channel 0')
    a, b = img.load(frames['0.0']), img.load(frames['1.0'])
    print('\n  whole frame, Age 0 -> 1: %.2f levels' % img.mean_abs_diff(a, b))
    json.dump(frames, open(os.path.join(OUT, 'ladder.json'), 'w'), indent=1)
    return frames


if __name__ == '__main__':
    ladder()
