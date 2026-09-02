#!/usr/bin/env python3
"""The lighting A/B: does SOURCE SIZE close the gap to B1?

    python3 Content/Python/lighting_ab.py            the source-size ladder
    python3 Content/Python/lighting_ab.py --dry      plan only, no editor

Docs/LIGHTING_STUDY.md measured our frame against the B1 reference and
inverted the obvious diagnosis: we are not too harsh, we are too FLAT. Local
contrast (gradient p90) is 12 against the reference's 92, our shadows are
LIFTED (p05/p50 0.500 vs 0.337), and our histogram is unimodal where B1 has a
whole second bright population.

The study's first-ranked mechanism is SOURCE SIZE, and it is first precisely
because it contradicts a decision this lane made deliberately and the owner
approved: board_light.py argues "softness comes from source SIZE relative to
subject... a studio window onto a 68 m board". That is correct optics working
as designed - and a large soft source is exactly how you erase local contrast.

THE CONFOUND THAT WOULD HAVE RUINED IT, solved here rather than discovered in
the frames. A rect light's brightness depends on its AREA. Halving width and
height quarters the emitting surface, so a naive size ladder is also a
brightness ladder - and this project has already been bitten by exactly that
shape: dof.py records a sweep that "changed the stop alone and produced a
brightness ladder wearing a depth-of-field label".

So each rung is EXPOSURE-MATCHED before it is judged: after resizing, the
intensity is solved by measurement until the frame's mean luma matches the
control's within a tolerance, and the achieved mean is recorded beside every
frame. A rung that could not be matched is reported as unmatched rather than
quietly compared.

ONE VARIABLE. Everything else is frozen: same framing, same board, same
species, same lens state (ue.tool refuses a capture whose lens is undeclared
and off the gate condition, so exposure cannot drift underneath the ladder).
"""
import base64
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import ue  # noqa: E402
import img  # noqa: E402
import wood_set as WS  # noqa: E402
import wood_board as wb  # noqa: E402

S, A, OBJ, APP = wb.S, wb.A, wb.OBJ, wb.APP
LEVEL, OUT = wb.LEVEL, wb.OUT

# width x height. The control is what board_light.py ships and what the owner
# approved; each rung halves the linear dimension, so the AREA quarters.
LADDER = [(4000.0, 2600.0), (2000.0, 1300.0), (1000.0, 650.0), (400.0, 260.0)]
MEAN_TOL = 2.0          # luma levels; tighter than the eye can see
MAX_SOLVE = 6           # intensity iterations per rung


def _key():
    got = json.loads(ue.tool(S, 'find_actors', {
        'name': 'LIGHT_BoardKey', 'tag': '',
        'collision_channels': []}))['returnValue']
    assert got, 'LIGHT_BoardKey missing - run board_light.py'
    comps = json.loads(ue.tool(A, 'get_components', {
        'actor': got[0]}))['returnValue']
    lc = [c for c in comps if 'RectLight' in c.get('refPath', '')]
    return lc[0] if lc else comps[-1]


def _set(comp, **kw):
    ue.tool(OBJ, 'set_properties', {'instance': comp,
                                    'values': json.dumps(kw)})


def _shoot(tag, cam, ann):
    ue.tool(APP, 'SetCameraTransform', {'transform': cam})
    time.sleep(9)
    r = json.loads(ue.tool(APP, 'CaptureViewport', {
        'captureTransform': cam, 'annotations': ann,
        'bShowUI': False}))['returnValue']
    p = os.path.join(OUT, '%s.png' % tag)
    open(p, 'wb').write(base64.b64decode(r['image']['data']))
    return p


def measure(path):
    """The five numbers the study fixed on, plus the mean the match needs."""
    im = img.load(path)
    px = im.px
    n = len(px)
    s = sorted(px)
    def pct(q): return s[min(n - 1, int(n * q))]
    g = []
    w = im.w
    for y in range(4, im.h - 4, 5):
        b = y * w
        for x in range(4, w - 4, 5):
            g.append(abs(px[b + x + 1] - px[b + x - 1])
                     + abs(px[b + w + x] - px[b - w + x]))
    g.sort()
    gm = len(g)
    h = [0] * 16
    for v in px:
        h[v >> 4] += 1
    return {'mean': sum(px) / float(n),
            'grad_p90': g[int(gm * .9)], 'grad_p99': g[int(gm * .99)],
            'lift': pct(.05) / max(1.0, float(pct(.50))),
            'spread': pct(.95) - pct(.05),
            'peak_pct': 100.0 * max(h) / n}


# B1's own numbers, the target to APPROACH - not a score to maximise. A frame
# that hit 92 and looked like a photocopy would have failed.
B1 = {'grad_p90': 92, 'grad_p99': 231, 'lift': 0.337, 'spread': 190,
      'peak_pct': 16.2}


# --- THE BASELINE FILE -----------------------------------------------------
#
# 2026-09-02: a fill ladder crashed partway (my own lens guard false-refusing
# on a float round-trip) with the fill already set to 0.5x, and never reached
# its restore. The NEXT run read that halved state as its baseline, laddered
# down from it, and faithfully "restored" to the contaminated values. Three
# lights and the post volume's ISO were left at half, and it was found only
# because the coordinator asked me to CONFIRM restoration rather than assert
# it.
#
# A RESTORE IS ONLY AS GOOD AS THE BASELINE IT CAPTURED, and an in-run capture
# is worthless the moment any earlier run died holding the scene. So the
# baseline lives in a FILE, written once from a known-clean scene, and every
# ladder restores from that file and reads back to prove it.
LIGHTS = (
    ('CITY_Sun', '/Script/Engine.DirectionalLight'),
    ('CITY_Key', '/Script/Engine.RectLight'),
    ('CITY_Fill', '/Script/Engine.RectLight'),
    ('CITY_StreetKey_A', '/Script/Engine.RectLight'),
    ('CITY_StreetKey_C', '/Script/Engine.RectLight'),
    ('CITY_Sky', '/Script/Engine.SkyLight'),
)
BASELINE = os.path.join(OUT, 'light_baseline.json')


def light_comp(label, cls):
    for a in json.loads(ue.tool(S, 'find_actors', {
            'name': label, 'tag': '', 'collision_channels': [],
            'actor_type': {'refPath': cls}}))['returnValue']:
        for c in json.loads(ue.tool(A, 'get_components', {
                'actor': a}))['returnValue']:
            if 'LightComponent' in c.get('refPath', ''):
                return c
    return None


def _post():
    return json.loads(ue.tool(S, 'find_actors', {
        'name': 'LOOK_Post', 'tag': '',
        'collision_channels': []}))['returnValue'][0]


def _iso():
    st = json.loads(json.loads(ue.tool(OBJ, 'get_properties', {
        'instance': _post(), 'properties': ['settings']}))['returnValue'])['settings']
    return st, float(st['cameraISO'])


def write_baseline(force=False):
    """Record the scene's pre-touch light state. Refuses to overwrite unless
    forced, because writing it from a dirty scene is how the poison spreads."""
    if os.path.exists(BASELINE) and not force:
        return json.load(open(BASELINE))
    out = {}
    for label, cls in LIGHTS:
        c = light_comp(label, cls)
        if c is None:
            continue
        out[label] = float(json.loads(json.loads(ue.tool(OBJ, 'get_properties', {
            'instance': c, 'properties': ['intensity']}))['returnValue']
            )['intensity'])
    out['_iso'] = _iso()[1]
    json.dump(out, open(BASELINE, 'w'), indent=1)
    return out


def restore_baseline(verbose=True):
    """Put every light and the ISO back to the FILE's values, then READ BACK
    and assert. Call it in a finally: a ladder that dies mid-rung must not
    leave the scene for the next run to mistake for normal."""
    assert os.path.exists(BASELINE), (
        'no %s - write it from a known-clean scene before any ladder runs'
        % BASELINE)
    want = json.load(open(BASELINE))
    bad = []
    for label, cls in LIGHTS:
        if label not in want:
            continue
        c = light_comp(label, cls)
        if c is None:
            continue
        ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                json.dumps({'intensity': want[label]})})
        got = float(json.loads(json.loads(ue.tool(OBJ, 'get_properties', {
            'instance': c, 'properties': ['intensity']}))['returnValue']
            )['intensity'])
        if abs(got - want[label]) > max(1e-6, 1e-3 * abs(want[label])):
            bad.append('%s wanted %g got %g' % (label, want[label], got))
    st, _cur = _iso()
    st['cameraISO'] = float(want['_iso'])
    ue.tool(OBJ, 'set_properties', {'instance': _post(),
                                    'values': json.dumps({'settings': st})})
    _st2, got_iso = _iso()
    if abs(got_iso - want['_iso']) > 0.5:
        bad.append('ISO wanted %g got %g' % (want['_iso'], got_iso))
    ue.declare_lens()
    assert not bad, 'RESTORE FAILED: %s' % '; '.join(bad)
    if verbose:
        print('baseline restored and read back: %d lights + ISO %g'
              % (len(want) - 1, want['_iso']))
    return want


def main():
    if '--dry' in sys.argv:
        print('source-size ladder, exposure-matched:')
        for w, h in LADDER:
            print('  %6.0f x %-6.0f  area %.2fx the control'
                  % (w, h, (w * h) / (LADDER[0][0] * LADDER[0][1])))
        print('\ntarget (B1): %s' % B1)
        return 0

    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], \
        'PIE is active - refusing to shoot a study over someone else\'s session'
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %r' % lvl
    standing = len(json.loads(ue.tool(S, 'find_actors', {
        'name': 'SETB_', 'tag': '', 'collision_channels': []}))['returnValue'])
    assert standing > 100, (
        'only %d SETB_ actors standing - the study shoots the 12x9 board, '
        'which is the view the game is played from. Run wood_set.py --keep '
        'first.' % standing)

    comp = _key()
    base = json.loads(ue.tool(OBJ, 'get_properties', {
        'instance': comp, 'properties': ['intensity']}))['returnValue']
    inten = float(json.loads(base)['intensity'])
    print('control intensity %.1f, %d buildings standing' % (inten, standing))

    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    cam = json.load(open(os.path.join(OUT, 'ab_camera.json'))) \
        if os.path.exists(os.path.join(OUT, 'ab_camera.json')) else None
    assert cam, ('no ab_camera.json - wood_set writes the oblique transform '
                 'there so the ladder shoots the same frame it does')

    rows, control_mean = [], None
    for i, (w, h) in enumerate(LADDER):
        tag = 'LIGHT_src%04dx%04d' % (w, h)
        _set(comp, sourceWidth=w, sourceHeight=h)
        # EXPOSURE MATCH: area changed, so brightness did. Solve intensity
        # until the frame mean matches the control, or say it did not.
        cur, matched = inten, False
        for _try in range(MAX_SOLVE):
            _set(comp, intensity=cur)
            p = _shoot(tag, cam, ann)
            m = measure(p)
            if control_mean is None:
                control_mean = m['mean']
                matched = True
                break
            if abs(m['mean'] - control_mean) <= MEAN_TOL:
                matched = True
                break
            cur *= control_mean / max(1.0, m['mean'])
        m['intensity'] = cur
        m['matched'] = matched
        m['size'] = '%.0fx%.0f' % (w, h)
        rows.append(m)
        print('%-14s mean %6.1f %s  grad_p90 %3d  lift %.3f  spread %3d'
              % (m['size'], m['mean'], 'OK ' if matched else 'UNMATCHED',
                 m['grad_p90'], m['lift'], m['spread']))

    _set(comp, sourceWidth=LADDER[0][0], sourceHeight=LADDER[0][1],
         intensity=inten)
    print('key restored to the approved control')
    json.dump({'rows': rows, 'b1': B1},
              open(os.path.join(OUT, 'lighting_ab.json'), 'w'), indent=1)
    print('wrote lighting_ab.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
