#!/usr/bin/env python3
"""D16's A/B pairs on the dressed play board. Null-first, one variable.

    python3 Content/Python/wear_pairs.py --attention   pair 1: polish or dirt?

Subject: the 14 pinned parcels dressed by study_dress.py, at the first-boot
play framing in study_pose.json. Never the study wall - D16 is explicit that
pairs go on buildings at the show camera.

NULL FIRST. Frame 0 is every channel at 0, which must be indistinguishable
from the board before wear existed, because at Attention = 0 the splice is
EdgeWearLift * 1.0 exactly. If the null frame differs from the undressed
look, the wiring is wrong and no ladder above it means anything.

THE COMPANION MEASUREMENT IS READ WITHIN ONE FRAME, NOT ACROSS TWO. D16:
"sample a recess patch and an arris patch in the same frame. Attention must
RAISE the arris and leave the recess alone. If a recess darkens, the
mechanism is grime and the mechanism is wrong." Within-frame is also the only
drift-immune form available here - wear.py --settle measured 0.4-0.9 levels
between consecutive captures of an untouched scene, so any across-frame patch
comparison of that size would be reading the renderer, not the material.

TestCity is NEVER saved. CPD is restored to zeros in a finally block, and
study_dress.py --clear still has to run afterwards.
"""
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
import wood_board as wb  # noqa: E402
import testcity_pins as TP  # noqa: E402
import cpdmap          # noqa: E402

S, A, OBJ, APP = wb.S, wb.A, wb.OBJ, wb.APP
OUT = os.path.join(wb.OUT, 'wear')
PARCEL_CLASS = '/Game/Stacktown/Runtime/BP_Parcel.BP_Parcel_C'
POSE = json.load(open(os.path.join(HERE, 'study_pose.json')))
CAM = {'location': POSE['location'], 'rotation': POSE['rotation']}


def _pie_guard():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], \
        'PIE active'


def parcels():
    """Every dressed parcel component. Discovered, not assumed."""
    out = []
    for lot, p in sorted(TP.PINS.items()):
        label = 'TC_Bld_%s_%s_t%d' % (lot, p['rid'], p['tier'])
        hits = json.loads(ue.tool(S, 'find_actors', {
            'name': label, 'tag': '',
            'actor_type': {'refPath': PARCEL_CLASS},
            'collision_channels': []}))['returnValue']
        if len(hits) == 1:
            out.append((lot, {'refPath': hits[0]['refPath'] + '.Building'}))
    assert out, 'no dressed parcels found - run study_dress.py --dress first'
    return out


SLOTS = 8   # channels 0..6 are spoken for; the array must reach index 6


def _read_cpd(comp):
    r = json.loads(ue.tool(OBJ, 'get_properties', {
        'instance': comp, 'properties': ['CustomPrimitiveData']}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    return (r.get('CustomPrimitiveData') or {}).get('data')


def _grow(comp, slots=None):
    """Grow the CPD array to SLOTS, ONE ELEMENT AT A TIME, all zeros.

    The setter refuses a call that changes an array's size and its contents
    together - "elements changed alongside the size change; insertion points
    are ambiguous" - and a multi-step grow in one call lands silently short
    rather than erroring. So growth is its own phase, zeros only, and the
    values go in afterwards at a fixed size. Parcels start at 2 or 4 slots
    depending on what has touched them, so this is not a fixed number of
    steps.
    """
    slots = slots or SLOTS
    cur = _read_cpd(comp) or []
    while len(cur) < slots:
        ue.tool(OBJ, 'set_properties', {'instance': comp, 'values': json.dumps(
            {'CustomPrimitiveData': {'data': [0.0] * (len(cur) + 1)}})})
        got = _read_cpd(comp) or []
        assert len(got) > len(cur), 'CPD array refused to grow past %d' % len(cur)
        cur = got
    return cur


def set_cpd(comps, **kw):
    """Write the wear channels at the indices cpdmap declares.

    The array is 8 long and every non-wear slot is left at 0, because
    channels 1, 2 and 3 belong to B4's GlowLevel, GlowState and Selection -
    the collision the first wire walked into. Writing a short array would
    also silently drop channel 4 upward, so the length is explicit.

    The struct field is lowercase `data`. Capital `Data` writes nothing and
    reads back None; the assertion below is what caught that, and without it
    the ladder would have rendered three identical frames and looked like a
    finding about the material.
    """
    v = [0.0] * SLOTS
    for name, idx in cpdmap.WEAR:
        v[idx] = float(kw.get(name.lower(), 0.0))
    for lot, c in comps:
        _grow(c)
        ue.tool(OBJ, 'set_properties', {'instance': c, 'values': json.dumps(
            {'CustomPrimitiveData': {'data': v}})})
    back = json.loads(ue.tool(OBJ, 'get_properties', {
        'instance': comps[0][1],
        'properties': ['CustomPrimitiveData']}))['returnValue']
    if isinstance(back, str):
        back = json.loads(back)
    got = (back.get('CustomPrimitiveData') or {}).get('data')
    assert got is not None and len(got) >= SLOTS and \
        [round(x, 4) for x in got[:SLOTS]] == [round(x, 4) for x in v], \
        'CPD read-back disagrees: wanted %s got %s' % (v, got)
    return v


def shoot(tag):
    ue.tool(APP, 'SetCameraTransform', {'transform': CAM})
    time.sleep(10)
    r = json.loads(ue.tool(APP, 'CaptureViewport', {
        'captureTransform': CAM, 'annotations': [], 'bShowUI': False}))['returnValue']
    os.makedirs(OUT, exist_ok=True)
    import base64
    p = os.path.join(OUT, '%s.png' % tag)
    open(p, 'wb').write(base64.b64decode(r['image']['data']))
    return p


def attention():
    _pie_guard()
    comps = parcels()
    print('%d dressed parcels' % len(comps))
    frames = {}
    try:
        for label, att in (('null', 0.0), ('burnished', 1.0), ('unpolished', -1.0)):
            set_cpd(comps, attention=att)
            frames[label] = shoot('att_%s' % label)
            print('  Attention %+.1f -> %s' % (att, os.path.basename(frames[label])))
    finally:
        set_cpd(comps)
        print('  CPD restored to zeros')
    a = img.load(frames['null'])
    b = img.load(frames['burnished'])
    print('\nnull vs burnished, whole frame: %.4f levels' % img.mean_abs_diff(a, b))
    json.dump({k: v for k, v in frames.items()},
              open(os.path.join(OUT, 'attention_pair.json'), 'w'), indent=1)
    return frames


def age():
    """The Age ladder, with the mechanism proved BEFORE the ladder is read.

    Attention taught this the hard way: its four scalars were present,
    readable and correctly channelled, and the thing they drove was inert -
    so a ladder would have been four frames of renderer drift wearing a
    label. Here the extremes are shot first and required to beat the drift
    reference, and the ladder is only reported if they do.
    """
    _pie_guard()
    comps = parcels()
    print('%d dressed parcels' % len(comps))
    frames, drift = {}, None
    try:
        set_cpd(comps, age=0.0)
        a0 = shoot('age_000')
        a0b = shoot('age_000_repeat')          # the drift reference, same state
        drift = img.mean_abs_diff(img.load(a0), img.load(a0b))
        set_cpd(comps, age=1.0)
        a1 = shoot('age_100')
        sig = img.mean_abs_diff(img.load(a0b), img.load(a1))
        print('\n  drift, same state twice : %.4f' % drift)
        print('  Age 0 -> 1              : %.4f' % sig)
        if sig <= drift * 2.0:
            print('  MECHANISM DEAD OR TOO WEAK - not reporting a ladder on it.')
            return None
        print('  mechanism live (%.1fx drift). Shooting the ladder.\n' % (sig / drift))
        frames['0.00'], frames['1.00'] = a0, a1
        for v in (0.33, 0.66):
            set_cpd(comps, age=v)
            frames['%.2f' % v] = shoot('age_%03d' % int(v * 100))
            print('  Age %.2f -> %s' % (v, os.path.basename(frames['%.2f' % v])))
    finally:
        set_cpd(comps)
        print('  CPD restored to zeros')
    json.dump({'frames': frames, 'drift': drift},
              open(os.path.join(OUT, 'age_ladder.json'), 'w'), indent=1)
    return frames


if __name__ == '__main__':
    {'--attention': attention, '--age': age}[sys.argv[1] if len(sys.argv) > 1
                                             else '--age']()
