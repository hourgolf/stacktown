#!/usr/bin/env python3
"""Render every stamped catalogue mesh from three angles into one HTML sheet.

    python3 contact_sheet.py [recipe ...] [--width=1230]

WHAT THIS IS AND IS NOT. Part count is a floor, not a standard - it catches
BARE, not BAD. Every mesh in the catalogue clears DETAIL_MIN by four to nine
times, so the gate is currently saying nothing about quality. This sheet is
what answers that, and it answers it the only way quality can be answered:
a person looks at it.

So this is a TRIAGE TOOL, not evidence. cap2 says so in its own docstring and
AGENTS.md forbids submitting an automated capture as gate evidence. Nothing
here decides anything; it puts thirty models in front of you in one pass
instead of one at a time, which is the difference between reviewing at scale
and micromanaging.

The REAR view is not decoration. The F1 reader's finding was that houses and
walk-ups had nothing on their sides or backs, and a sheet that only showed
the front would have agreed the catalogue was fine.
"""
import os, sys, json, base64, subprocess, tempfile, math, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401
import recipes

ROOT = os.path.dirname(os.path.dirname(HERE))
RUNG = os.path.join(ROOT, 'Tools', 'rung.sh')
SHOT = os.environ.get('STACKTOWN_SHOTS') or tempfile.mkdtemp(prefix='sheet_')
TMP = tempfile.gettempdir()
OUT = '/Game/Stacktown/Baked'

sys.path.insert(0, os.path.join(ROOT, 'Tools', 'measure'))
SCRATCH = os.environ.get('STACKTOWN_SCRATCH', '')
if SCRATCH:
    sys.path.insert(0, SCRATCH)
import ue, cap2, framing            # noqa: E402  (need the paths above first)

# bearing = the compass yaw the camera LOOKS ALONG. The model faces -Y, so a
# camera south of it looking north is bearing 90.
VIEWS = [('three-quarter', 55.0, -22.0),
         ('elevation',     90.0, -10.0),
         ('rear',         250.0, -22.0)]


def rung(script):
    r = subprocess.run([RUNG, script], capture_output=True, text=True, cwd=HERE)
    if 'success: True' not in r.stdout:
        raise SystemExit('%s failed\n%s' % (script, r.stdout[-600:] or r.stderr[-600:]))
    return r.stdout


def land(loc, rot):
    for _ in range(4):
        ue.tool('EditorToolset.EditorAppToolset', 'SetCameraTransform',
                {'transform': {'location': loc, 'rotation': rot,
                               'scale': {'x': 1, 'y': 1, 'z': 1}}})
        g = json.loads(ue.tool('EditorToolset.EditorAppToolset',
                               'GetCameraTransform', {}))['returnValue']['location']
        if all(abs(g[k] - loc[k]) < 2 for k in 'xyz'):
            return True
    return False


def shoot(asset, info):
    """Three captures of the staged model. Returns [(name, png path)]."""
    rect = info['bounds']
    z1 = max(info['z1'], 200.0)
    out = []
    cap2.set_fov()
    for name, bearing, pitch in VIEWS:
        loc, rot = framing.frame(rect, bearing, pitch=pitch, z0=info['z0'],
                                 z1=z1, margin=1.22)
        if not land(loc, rot):
            print('    %s: camera did not land' % name)
            continue
        p = os.path.join(SHOT, '%s_%s.png' % (asset, name))
        cap2.VIEWS[name] = (loc, rot)
        for _ in range(12):
            cap2.capture(p, name)
        # NO CROP. The inherited `-c 1542 2313 --cropOffset 0 244` takes the
        # TOP 1542 rows of a 2244-row capture, which is fine for a board shot
        # where the subject sits high and silently beheads a tall building -
        # t3 came back with its ground floor cut off. Downscale the whole
        # frame instead; the framing solver has already composed it.
        sub = os.path.join(SHOT, '%s_%s_s.png' % (asset, name))
        subprocess.run(['sips', '-Z', '520', p, '--out', sub],
                       capture_output=True)
        out.append((name, sub))
    return out


def b64(p):
    return base64.b64encode(open(p, 'rb').read()).decode('ascii')


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(recipes.RECIPES)
    only_w = next((float(a.split('=')[1]) for a in sys.argv[1:]
                   if a.startswith('--width=')), None)
    rows = []
    for rid in want:
      for w in recipes.widths(rid):
        if only_w is not None and abs(w - only_w) > 1.0:
            continue
        for t in range(recipes.tier_count(rid)):
            asset = recipes.asset_name(rid, t, w)
            json.dump({'asset': '%s/%s' % (OUT, asset)},
                      open(os.path.join(TMP, 'stacktown_sheet_job.json'), 'w'))
            info_path = os.path.join(TMP, 'stacktown_sheet_info.json')
            if os.path.exists(info_path):
                os.remove(info_path)
            so = rung('sheet_stage.py')
            for ln in so.splitlines():
                if ln.startswith('[Info]   staged'):
                    print(ln[7:])
            info = json.load(open(info_path))
            rows.append((asset, info, shoot(asset, info)))
    rung('sheet_clear.py')
    write_html(rows)


def write_html(rows):
    st = lambda s, k: (s.get(k) or '-')
    cells = []
    for asset, info, shots in rows:
        s = info['stamp']
        imgs = ''.join(
            '<figure><img alt="%s %s" src="data:image/png;base64,%s">'
            '<figcaption>%s</figcaption></figure>' % (asset, n, b64(p), n)
            for n, p in shots)
        gate = st(s, 'Gate')
        cells.append(
            '<section class="model">'
            '<header><h2>%s</h2><span class="pill %s">%s</span></header>'
            '<p class="meta">%s &middot; tier %s &middot; %s uu wide &middot; '
            '%s parts &middot; %s materials &middot; %s/m&sup2; &middot; '
            '%d slots &middot; stamped %s</p>'
            '<div class="shots">%s</div></section>'
            % (asset, gate.lower(), gate, st(s, 'Recipe'), st(s, 'Tier'),
               st(s, 'Width'), st(s, 'Parts'), st(s, 'Materials'),
               st(s, 'Density'), info['slots'], st(s, 'Stamped'), imgs))

    html = HTML % dict(
        when=datetime.date.today().isoformat(),
        n=len(rows),
        views=' &middot; '.join(v[0] for v in VIEWS),
        body='\n'.join(cells))
    out = os.path.join(SHOT, 'contact_sheet.html')
    open(out, 'w').write(html)
    print('\ncontact sheet: %d models, %d captures -> %s'
          % (len(rows), sum(len(s) for _a, _i, s in rows), out))


HTML = '''<title>Catalogue Contact Sheet</title>
<style>
:root{--bg:#f6f4f0;--card:#fff;--ink:#22201c;--dim:#6f6a61;--line:#e0dbd2;
      --pass:#2f6b46;--passbg:#e4efe7;--fail:#8c3222;--failbg:#f6e4e0;}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#171614;--card:#201e1b;--ink:#ece8e1;--dim:#9d968a;--line:#332f2a;
  --pass:#7fc39a;--passbg:#1d3327;--fail:#e0917f;--failbg:#331f1a;}}
:root[data-theme="dark"]{--bg:#171614;--card:#201e1b;--ink:#ece8e1;--dim:#9d968a;
  --line:#332f2a;--pass:#7fc39a;--passbg:#1d3327;--fail:#e0917f;--failbg:#331f1a;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 ui-sans-serif,-apple-system,"Helvetica Neue",sans-serif;
  padding:32px 24px 64px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:1.5rem;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--dim);margin:0 0 28px;font-size:.9rem}
.model{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px 18px;margin-bottom:18px}
header{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{font-size:1rem;margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.pill{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;
  padding:2px 8px;border-radius:99px;font-weight:600}
.pill.pass{color:var(--pass);background:var(--passbg)}
.pill.fail{color:var(--fail);background:var(--failbg)}
.meta{color:var(--dim);font-size:.82rem;margin:6px 0 14px;
  font-variant-numeric:tabular-nums}
.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:12px}
figure{margin:0}
img{width:100%%;height:auto;display:block;border-radius:6px;
  border:1px solid var(--line);background:var(--bg)}
figcaption{color:var(--dim);font-size:.74rem;margin-top:5px;
  letter-spacing:.04em;text-transform:uppercase}
</style>
<div class="wrap">
<h1>Catalogue contact sheet</h1>
<p class="sub">%(n)d stamped models &middot; %(views)s &middot; %(when)s &middot;
a triage tool for review, not gate evidence</p>
%(body)s
</div>'''


if __name__ == '__main__':
    main()
