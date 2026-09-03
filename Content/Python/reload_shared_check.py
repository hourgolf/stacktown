#!/usr/bin/env python3
"""Guard and verification for reload_shared.py. Run from outside the editor.

    python3 Content/Python/reload_shared_check.py --before
    ./Tools/rung.sh reload_shared.py
    python3 Content/Python/reload_shared_check.py --after

--before REFUSES the reload unless the in-memory master is already equivalent
to disk. If it has drifted from 195 expressions or its original drivers, the
in-memory copy holds something real and discarding it would destroy work.

--after proves the flag is gone AND that nothing was written: is_dirty False,
195 expressions, both drivers intact. The on-disk check is a separate
`git status` - the point of the whole exercise is that the .uasset must not
change, and only git can say that.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path            # noqa: F401,E402
import ue               # noqa: E402
import woodmaster as WM  # noqa: E402

M = 'editor_toolset.toolsets.material.MaterialTools'
AT = 'editor_toolset.toolsets.asset.AssetTools'
APP = 'EditorToolset.EditorAppToolset'
ASSET = WM.SHARED.split('.')[0]
EXPECT = 195
DRIVERS = {'MP_BaseColor': 'MaterialExpressionLinearInterpolate_3'}


def state():
    n = len(json.loads(ue.tool(M, 'get_expressions', {
        'material_or_function': {'refPath': WM.SHARED}}))['returnValue'])
    dirty = json.loads(ue.tool(AT, 'is_dirty',
                               {'asset_path': ASSET}))['returnValue']
    drv = {}
    for prop in DRIVERS:
        r = json.loads(ue.tool(M, 'get_property_input', {
            'material': {'refPath': WM.SHARED},
            'material_property': prop}))['returnValue']
        if isinstance(r, str):
            r = json.loads(r)
        e = r.get('expression') if isinstance(r, dict) else None
        rp = e.get('refPath') if isinstance(e, dict) else e
        drv[prop] = (rp or 'NONE').rsplit(':', 1)[-1]
    return n, dirty, drv


def report(tag):
    n, dirty, drv = state()
    print('%-8s expressions %-5s dirty %-6s %s'
          % (tag, n, dirty, ' '.join('%s<-%s' % (k, v) for k, v in drv.items())))
    return n, dirty, drv


def before():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], \
        'PIE active - refusing'
    n, dirty, drv = report('BEFORE')
    bad = []
    if n != EXPECT:
        bad.append('%d expressions, expected %d' % (n, EXPECT))
    for k, want in DRIVERS.items():
        if drv.get(k) != want:
            bad.append('%s <- %s, expected %s' % (k, drv.get(k), want))
    if bad:
        print('\nREFUSING THE RELOAD:')
        for b in bad:
            print('  ', b)
        print('The in-memory copy is NOT equivalent to disk. Discarding it '
              'would destroy real work. Investigate before clearing the flag.')
        return False
    if not dirty:
        print('\nAlready clean - no reload needed.')
        return False
    print('\nEquivalent to disk and dirty. Safe to reload.')
    return True


def after():
    n, dirty, drv = report('AFTER')
    ok = (n == EXPECT and dirty is False
          and all(drv.get(k) == v for k, v in DRIVERS.items()))
    print('\n%s' % ('CLEAR - flag gone, content intact.' if ok
                    else 'NOT CLEAR - investigate.'))
    print('Now confirm nothing was WRITTEN:')
    print('  git status --short Content/Stacktown/Materials/'
          'M_StacktownMaster.uasset     # must print nothing')
    return ok


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else '--before'
    ok = {'--before': before, '--after': after}[cmd]()
    raise SystemExit(0 if ok else 1)
