#!/usr/bin/env python3
"""Prove the generator still emits EXACTLY what it emitted before.

    python3 genbuild_identity.py            check against the frozen manifest
    python3 genbuild_identity.py --freeze   re-freeze (only with a reason)

WHY THIS IS A TOOL AND NOT A HABIT. Every generator change this project makes
is supposed to be additive: a new spec key with a behaviour-preserving default,
so nothing already built moves. That claim is cheap to make and was, until now,
checked by hand - five separate times in one session while the estate office
went in, each time by dumping genbuild's sink and diffing it in a scratch
file. A check run by hand is a check that stops being run.

WHAT IT COVERS. The five city houses from city.py, which are live in the hero
block and are the ones an office fit-out could most easily have moved, plus one
model from each catalogue family so the commercial generators are not left
unwatched. Everything runs through genbuild's SINK - no editor, no bake, no
actors - so this is fast enough to run before every commit that touches
generation.

WHAT IT STORES. A hash per model, not the records themselves: the manifest
stays small enough to read in a diff, and a changed hash is the whole signal.
Counts ride along so a failure says HOW it differs before you go looking.

A TRAP THIS TOOL WILL WALK INTO, WRITTEN DOWN BECAUSE IT COST AN HOUR.
On this machine `sys.pycache_prefix` is `~/Library/Caches/com.apple.python`,
so Python writes bytecode OUTSIDE the repository - deleting
`Content/Python/__pycache__` clears NOTHING. And cache invalidation is
source mtime+size, both of which can survive an edit: changing `22` to `21`
and changing it back leaves the size identical, and if both edits land in the
same second the mtime matches too. Python then serves the stale bytecode and
this tool reports a regression that is not in the file.

The tell is that `exec(open(path).read())` and `import` disagree. When they
do, the file is not the problem:

    rm -rf "$(python3 -c 'import sys,importlib.util as u; print(u.cache_from_source("'"$PWD"'/Content/Python/recipes.py"))' | xargs dirname)"

or simply clear `~/Library/Caches/com.apple.python/<abs path to repo>`.

FREEZING IS A DECISION. --freeze rewrites the baseline, which is exactly what
an unnoticed regression would want you to do. Do it only when output SHOULD
have changed, and say so in the commit message.
"""
import hashlib
import io
import json
import os
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401,E402
import genbuild  # noqa: E402
import recipes  # noqa: E402

MANIFEST = os.path.join(HERE, 'genbuild_identity.json')

# one model per commercial family, so a change inside a shared helper cannot
# hide behind "the houses are fine"
CATALOGUE = [('vernacular', 3, 1230.0), ('modern8', 2, 2050.0),
             ('deco4', 2, 1640.0), ('contemporary6', 3, 2460.0),
             ('office', 0, 2050.0)]


def _digest(records):
    """A stable hash of a sink dump. Floats are rounded before hashing: the
    generator is arithmetic, and an unrounded float would make this tool
    report a regression for a change in the last bit that nothing can see."""
    def clean(v):
        if isinstance(v, float):
            return round(v, 4)
        if isinstance(v, list):
            return [clean(x) for x in v]
        if isinstance(v, dict):
            return {k: clean(v[k]) for k in sorted(v)}
        return v
    blob = json.dumps([clean(r) for r in records], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def sample():
    """{name: {boxes, actors, sha}} for everything we watch."""
    from city import BLOCKS
    import preview
    out = {}
    for blk in BLOCKS:
        for spec in blk['lots']:
            if spec.get('style') != 'house':
                continue
            genbuild.record()
            with contextlib.redirect_stdout(io.StringIO()):
                genbuild.build_house(
                    dict(spec, floors=spec.get('floors', 0),
                         gf_h=spec.get('gf_h', 300.0),
                         fl_h=spec.get('fl_h', 280.0),
                         bays=spec.get('bays', 3),
                         depth=spec.get('depth', 700.0)),
                    origin=blk['origin'], yaw=blk['yaw'])
            rec = genbuild.drain()
            out['house:' + spec['name']] = _row(rec)
    for rid, tier, w in CATALOGUE:
        if rid not in recipes.RECIPES:
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            _spec, rec = preview.collect(rid, tier, w)
        out['catalogue:%s_t%d_w%d' % (rid, tier, int(w))] = _row(rec)
    return out


def _row(rec):
    return {'actors': sum(1 for r in rec if r.get('kind') == 'actor'),
            'boxes': sum(1 for r in rec if r.get('kind') == 'box'),
            'sha': _digest(rec)}


def main():
    cur = sample()
    if '--freeze' in sys.argv or not os.path.exists(MANIFEST):
        json.dump(cur, open(MANIFEST, 'w'), indent=1, sort_keys=True)
        print('FROZE %d model(s) -> %s' % (len(cur), os.path.basename(MANIFEST)))
        for k in sorted(cur):
            print('  %-40s %4d boxes  %s' % (k, cur[k]['boxes'], cur[k]['sha']))
        return 0
    old = json.load(open(MANIFEST))
    bad = []
    for k in sorted(set(old) | set(cur)):
        a, b = old.get(k), cur.get(k)
        if a is None:
            print('  NEW      %-40s %4d boxes' % (k, b['boxes']))
            continue
        if b is None:
            bad.append('%s: GONE from the sample' % k)
            continue
        if a['sha'] != b['sha']:
            bad.append('%s: boxes %d -> %d, sha %s -> %s'
                       % (k, a['boxes'], b['boxes'], a['sha'], b['sha']))
    if bad:
        print('GENERATOR OUTPUT MOVED - %d model(s):' % len(bad))
        for line in bad:
            print('  ' + line)
        print('If this was intended, re-freeze with --freeze and say why in '
              'the commit message.')
        return 1
    print('generator identity: %d model(s) unchanged' % len(old))
    return 0


if __name__ == '__main__':
    sys.exit(main())
