"""Capture and measure the paper-tell study. JUDGE MODE, two standoffs.

JUDGE, NOT SHOW. This asks how a surface reads, so it runs with depth of
field off. Grain under f/2 bokeh measures the bokeh. The lens doctrine's own
line: judge is the internal instrument, and weak surface can never hide
behind optics.

TWO STANDOFFS, because "player zoom" and "the closer they looked" are not the
same distance and the cold read named both:
    3189 uu - ONE FACADE FILLING THE FRAME, the gate's own definition of
              player zoom (frame is 0.514 x distance at 28.84 deg, so this is
              a 1640-wide facade exactly filling it)
     800 uu - inspection range, where the reader said it got easier to spot

Every panel is photographed alone, centred, at both. The numbers are a mean,
an sd and an anisotropy ratio; none of those settle a look, which is why the
frames are written out to be looked at.
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ue, cap2, img, live, lensrig

E = 'EditorToolset.EditorAppToolset'
FAR, NEAR = 3189.0, 800.0


def actors():
    """The study's own actors, from the editor, with their bounds."""
    import subprocess, tempfile
    src = ('import unreal, json\n'
           'eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n'
           'out = []\n'
           'for a in eas.get_all_level_actors():\n'
           '    L = a.get_actor_label()\n'
           '    if not L.startswith("STUDY_PT_"):\n'
           '        continue\n'
           '    o, e = a.get_actor_bounds(False)\n'
           '    out.append([L, [o.x,o.y,o.z], [e.x,e.y,e.z]])\n'
           'print("PTACT " + json.dumps(sorted(out)))\n')
    f = os.path.join(tempfile.gettempdir(), '_ptact.py')
    open(f, 'w').write(src)
    r = subprocess.run(['python3', os.path.join(HERE, 'uepy.py'), f],
                       capture_output=True, text=True)
    line = next((l for l in r.stdout.splitlines() if 'PTACT' in l), None)
    if not line:
        raise SystemExit('no STUDY_PT_ actors found - run place_papertell.py '
                         'in Sandbox_Bench first\n' + r.stdout[-400:])
    return json.loads(line.split('PTACT', 1)[1].strip())


def shoot(label, centre, dist, out):
    """Camera on -Y at `dist`, aimed at the panel centre. -Y is the LIT face:
    study_place.py measured LIGHT_Sun at pitch -52 yaw 45, so light travels
    toward +X/+Y and a -Y normal is the one that opposes it. Yawing a study
    to 'fix the lighting' once put it on the shadow side."""
    loc = {'x': centre[0], 'y': centre[1] - dist, 'z': centre[2]}
    rot = {'pitch': 0.0, 'yaw': 90.0, 'roll': 0.0}
    cap2.set_fov()
    for _ in range(6):
        ue.tool(E, 'SetCameraTransform', {'transform': {
            'location': loc, 'rotation': rot, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
        g = json.loads(ue.tool(E, 'GetCameraTransform', {}))['returnValue']['location']
        if all(abs(g[k] - loc[k]) < 2 for k in 'xyz'):
            break
    cap2.VIEWS['_pt'] = (loc, rot)
    for _ in range(12):
        cap2.capture(out, '_pt', fov=False)
    im = img.load(out)
    x0, x1 = int(im.w*0.35), int(im.w*0.65)
    y0, y1 = int(im.h*0.35), int(im.h*0.65)
    dx, dy, ratio = img.anisotropy(im, x0, y0, x1, y1)
    s = live.stats(out)
    return dict(mean=s['mean'], sd=s['sd'], dx=dx, dy=dy, ratio=ratio)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else '.'
    r = lensrig.apply('judge')
    assert r['readback']['depth_of_field_fstop'] == 4.0, 'lens is not judge'
    print('lens: judge, grain %s\n' % r['grain'])
    rows = {}
    print('%-26s %6s %7s %7s %7s %6s' % ('panel', 'dist', 'mean', 'sd', 'detail', 'aniso'))
    for label, o, e in actors():
        for tag, d in (('far', FAR), ('near', NEAR)):
            p = os.path.join(outdir, 'PT_%s_%s.png' % (label[9:], tag))
            m = shoot(label, o, d, p)
            rows['%s/%s' % (label, tag)] = m
            print('%-26s %6.0f %7.2f %7.2f %7.3f %6.2f'
                  % (label[9:], d, m['mean'], m['sd'],
                     (m['dx']+m['dy'])/2.0, m['ratio']))
    json.dump(rows, open(os.path.join(outdir, 'papertell.json'), 'w'),
              indent=1, sort_keys=True)
    print('\nDETAIL is the mean high-pass residual - how much surface texture '
          'survives at that distance.\nNo number here settles a look. Open the frames.')


if __name__ == '__main__':
    main()
