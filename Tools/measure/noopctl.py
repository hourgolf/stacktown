"""The control for the OFFSET half's no-op proof. Before and after, compared.

WHY THIS RUNS FIRST AND ALONE. The combined graph item carries two
verification standards: the PaperOffset/PaperRotate parameters must prove a
byte-identical no-op at (0,0), while the octave layer is a look change BY
DESIGN and proves itself on the study wall instead. Those cannot share a
capture. Once the octave layer lands, "did anything change?" has the answer
"yes, deliberately", and the no-op claim can never be made again. So the
control is taken before ANY edit, the offset params go in, the control is
retaken, and only then does the octave work start.

"BYTE-IDENTICAL" IS NOT AVAILABLE AND SAYING SO MATTERS. TAA jitters every
frame, so two captures of an unchanged scene already differ - settle.py
measured that floor at 3.65-3.86 and works to 4.3. The honest claim is
therefore "indistinguishable from an unchanged scene at today's measured
noise floor", and the floor is measured NOW rather than inherited, because it
was established under a different lens mode and a different level.

Three orientations, because the paper chain is triplanar and a no-op on the
facade proves nothing about the flank or the ground.
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ue, cap2, img, live, lensrig

E = 'EditorToolset.EditorAppToolset'

VIEWS = {
    # normal -Y: the control that was always fine
    'facade': ({'x': 5946.0, 'y': -22610.0, 'z': 700.0},
               {'pitch': 0.0, 'yaw': 90.0, 'roll': 0.0}),
    # normal -X: the case triplanar.py existed to fix
    'flank':  ({'x': 2400.0, 'y': -21700.0, 'z': 700.0},
               {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}),
    # normal +Z: degenerate under the old projection and never measured
    'ground': ({'x': 5000.0, 'y': -22750.0, 'z': 520.0},
               {'pitch': -90.0, 'yaw': 0.0, 'roll': 0.0}),
}


def settled(tag, out, eps=0.35, tries=40):
    """Capture until two consecutive frames agree, not a fixed count.

    A fixed 14 captures was not enough and produced a confident wrong answer:
    a material edit invalidates Lumen's surface cache, and settle.py already
    measured 47.5 mean-abs-diff between two captures of an IDENTICAL scene
    taken across such an edit. Comparing a settled BEFORE against an
    unsettled AFTER measures the recompile, not the change - and it fails in
    the direction that looks like a real finding, which is the worst way for
    a measurement to be wrong.
    """
    prev = None; quiet = 0
    for i in range(tries):
        im = shoot(tag, out, reps=3)
        if prev is not None:
            d = img.mean_abs_diff(prev, im)
            quiet = quiet + 1 if d < eps else 0
            if quiet >= 2:
                return im, i + 1, d
        prev = im
    raise SystemExit('%s never settled in %d captures' % (tag, tries))


def shoot(tag, out, reps=14):
    loc, rot = VIEWS[tag]
    cap2.set_fov()
    for _ in range(6):
        ue.tool(E, 'SetCameraTransform', {'transform': {
            'location': loc, 'rotation': rot, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
        g = json.loads(ue.tool(E, 'GetCameraTransform', {}))['returnValue']['location']
        if all(abs(g[k] - loc[k]) < 2 for k in 'xyz'):
            break
    cap2.VIEWS['_n'] = (loc, rot)
    for _ in range(reps):
        cap2.capture(out, '_n', fov=False)
    return img.load(out)


def measure(im):
    x0, x1 = int(im.w*0.30), int(im.w*0.70)
    y0, y1 = int(im.h*0.30), int(im.h*0.70)
    dx, dy, r = img.anisotropy(im, x0, y0, x1, y1)
    return dict(mean=round(img.mean(im.px), 4), detail=round((dx+dy)/2.0, 4),
                aniso=round(r, 4))


def run(phase, outdir):
    lensrig.apply('judge')
    rec = {}
    for tag in VIEWS:
        p = os.path.join(outdir, 'NOOP_%s_%s.png' % (tag, phase))
        im, n, d = settled(tag, p)
        m = measure(im); m['settled_after'] = n; m['settle_delta'] = round(d, 4)
        if phase == 'before':
            # today's floor, per framing: a second capture of the SAME
            # unchanged scene. Anything at or under this is indistinguishable
            # from having changed nothing.
            p2 = os.path.join(outdir, 'NOOP_%s_floor.png' % tag)
            im2, _, _ = settled(tag, p2)
            m['floor'] = round(max(img.mean_abs_diff(im, im2), 0.30), 4)
        rec[tag] = m
        print('  %-7s mean %8.3f  detail %7.4f  aniso %6.3f  settled@%-2d%s'
              % (tag, m['mean'], m['detail'], m['aniso'], m['settled_after'],
                 '  floor %.3f' % m['floor'] if 'floor' in m else ''))
    f = os.path.join(outdir, 'noop_%s.json' % phase)
    json.dump(rec, open(f, 'w'), indent=1, sort_keys=True)
    return rec


def compare(outdir):
    b = json.load(open(os.path.join(outdir, 'noop_before.json')))
    a = json.load(open(os.path.join(outdir, 'noop_after.json')))
    ok = True
    print('%-8s %10s %10s %8s %8s' % ('view', 'diff', 'floor', 'd-mean', 'verdict'))
    for tag in sorted(b):
        im_b = img.load(os.path.join(outdir, 'NOOP_%s_before.png' % tag))
        im_a = img.load(os.path.join(outdir, 'NOOP_%s_after.png' % tag))
        d = img.mean_abs_diff(im_b, im_a)
        dm = abs(a[tag]['mean'] - b[tag]['mean'])
        good = d <= b[tag]['floor']
        ok = ok and good
        print('%-8s %10.4f %10.4f %8.4f %8s'
              % (tag, d, b[tag]['floor'], dm, 'PASS' if good else 'FAIL'))
    print('\nNO-OP %s' % ('PROVEN at today\'s measured floor' if ok
                          else 'NOT PROVEN - the offset params changed the render'))
    return ok


if __name__ == '__main__':
    what = sys.argv[1]
    out = sys.argv[2]
    if what == 'compare':
        raise SystemExit(0 if compare(out) else 1)
    run(what, out)
