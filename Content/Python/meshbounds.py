"""Measure every donor mesh's LOCAL bounds once, and write them where the
offline tools can read them.

WHY THIS IS THE KEYSTONE. Three separate things are blind to donor geometry
because a donor's true extent is not in the recorded part list - the generator
records a piece as an asset path, a location and a scale, and nothing about
the shape at the other end of that path:

  1. the offline GATE-05 sweep, which reproduces a PASSING known answer but
     reports 0.0 uu on a model the editor gate refuses at 1162 uu;
  2. preview.py's as_snapshot, which drops kind=='mesh' outright - and that
     one is LIVE and STAMPS, so it can certify a mesh the editor gate refuses;
  3. catalogue_audit's spans, which inherit the same blindness.

A donor's PIVOT is the thing that actually bites. SM_drainPipe_ending spans
local z -59.8..0 - the shoe hangs entirely BELOW its origin - so placing it by
its origin buried it, and a piece whose pivot sits far from its geometry can
throw a model a whole parcel width off without a single box moving. avkit
records each piece's SIZE but never where that size sits relative to the
pivot, which is exactly the missing number.

Output goes to Tools/measure/ and NOT to Content/ - Content holds .py only.
"""
import unreal
import _path  # noqa: F401
import avkit
import json
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())))),
    'x')  # placeholder, replaced below
PROJ = os.path.abspath(unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_dir()))
OUT = os.path.join(PROJ, 'Tools', 'measure', 'meshbounds.json')

eal = unreal.EditorAssetLibrary

# every donor the generator can place, from the one vocabulary that owns them
CATALOGUE = {}
for src in ('PIECES', 'HERO'):
    for key, row in getattr(avkit, src, {}).items():
        CATALOGUE[key] = (row[0], row[1] if len(row) > 1 else None, src)

# ubkit draws from a folder rather than a dict, and the generator places its
# flowerbed parts - so a table built only from avkit misses a whole donor pack
# and reports 0.0 uu on models that use them. Any FOLDER a kit module points
# at is swept whole; that way adding a piece to a kit cannot silently reopen
# the blind spot.
FOLDERS = []
for _mod in ('ubkit',):
    try:
        _m = __import__(_mod)
    except Exception:
        continue
    for _n in dir(_m):
        _v = getattr(_m, _n)
        if isinstance(_v, str) and _v.startswith('/Game/') and _v.endswith('/'):
            FOLDERS.append(_v)
for _f in sorted(set(FOLDERS)):
    for _a in eal.list_assets(_f, recursive=True, include_folder=False):
        _path = _a.split('.')[0]
        if _path.rsplit('/', 1)[-1].startswith('SM_'):
            CATALOGUE.setdefault(_path.rsplit('/', 1)[-1], (_path, None, 'folder'))

table = {}
missing = []
for key, (path, declared, src) in sorted(CATALOGUE.items()):
    sm = eal.load_asset(path)
    if not sm:
        missing.append('%s -> %s' % (key, path))
        continue
    bb = sm.get_bounding_box()          # LOCAL space, pivot at the origin
    lo, hi = bb.min, bb.max
    ext = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    # the number avkit never recorded: how far the geometry sits from the pivot
    table[key] = {
        'asset': path, 'src': src,
        'lo': [round(lo.x, 2), round(lo.y, 2), round(lo.z, 2)],
        'hi': [round(hi.x, 2), round(hi.y, 2), round(hi.z, 2)],
        'ext': [round(v, 2) for v in ext],
        'declared': list(declared) if declared else None,
    }

# SELF-CHECK against a fact recorded independently in avkit.downpipe's own
# docstring, from the bug that cost a shoe buried underground. If the table
# cannot reproduce a bound somebody already measured by hand, it is not a
# measurement, it is a guess with a filename.
chk = table.get('drainpipe_end')
ok = False
if chk:
    ok = (abs(chk['lo'][2] - (-59.8)) < 1.5 and abs(chk['hi'][2]) < 1.5)
    print('SELFCHECK drainpipe_end local z %.1f..%.1f  expected -59.8..0  %s'
          % (chk['lo'][2], chk['hi'][2], 'AGREES' if ok else 'DISAGREES'))
else:
    print('SELFCHECK drainpipe_end MISSING from the table')

# where declared size and measured extent disagree, avkit is stale
drift = []
for k, v in table.items():
    d = v.get('declared')
    if not d or len(d) != 3:
        continue
    if max(abs(a - b) for a, b in zip(d, v['ext'])) > 2.0:
        drift.append((k, d, v['ext']))

json.dump({'note': 'local-space bounds, pivot at origin; uu',
           'selfcheck_drainpipe_end': ok, 'meshes': table},
          open(OUT, 'w'), indent=1, sort_keys=True)
print('BOUNDS measured %d donors -> %s' % (len(table), OUT))
if missing:
    print('BOUNDS MISSING %d: %s' % (len(missing), '; '.join(missing[:5])))
if drift:
    print('BOUNDS avkit size DRIFT on %d:' % len(drift))
    for k, d, e in drift[:8]:
        print('BOUNDS    %-16s declared %s  measured %s' % (k, d, e))
