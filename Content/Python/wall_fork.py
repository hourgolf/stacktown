#!/usr/bin/env python3
"""Fork M_StudioWall so the backdrop can go down at night.

    python3 Content/Python/wall_fork.py --fork
    python3 Content/Python/wall_fork.py --verify

WHY A FORK AND NOT AN INSTANCE OVERRIDE. M_StudioWall's referencers are
Sandbox_Bench (flagship) and our MI_studio_wall_city, so the MASTER is shared
and the owner's separation ruling puts it out of this lane. The instance IS
ours - TestCity is its only referencer - but that does not help: an instance
can only override parameters its master exposes, and an instance override is
a STATIC value. Reading MPC_WoodCity.NightAmount has to happen inside the
material GRAPH, and that graph is the flagship's too. There is no version of
this that stays inside the instance.

WHY THE WALL HAS TO DIM AT ALL. M_StudioWall is MSM_UNLIT by construction
(mk_studioroom.py:45) so the cyclorama ignores every light in the level and
contributes provably zero GI to the board. Excellent by day; at night it means
dimming the rig leaves a dark board in front of a FULLY BRIGHT backdrop, and
the brightest thing in frame becomes the thing nobody is looking at.

    emissive' = emissive x lerp(1.0, NightWallDim, NightAmount)

At NightAmount 0 the lerp returns 1.0 exactly and the fork renders identically
to the original - inert by construction, which is what makes the re-parent
safe to do before the night numbers are settled.

NightWallDim 0.12: the backdrop falls FURTHER than the key light's 0.10 is
generous to, because a cyclorama at night should read as depth rather than as
a lit surface. This is the number most likely to move after the first frame.
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
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
APP = 'EditorToolset.EditorAppToolset'
SHARED_WALL = '%s/M_StudioWall' % WM.MATD
FORK_WALL = '%s/M_WoodStudioWall' % WM.MATD
INSTANCE = '%s/MI_studio_wall_city.MI_studio_wall_city' % WM.MATD
MPC = '%s/MPC_WoodCity.MPC_WoodCity' % WM.MATD
NIGHT_WALL_DIM = 0.12
LEDGER = os.path.join(WM.wb.OUT, 'wall_fork_ledger.json')


def _pie():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], 'PIE active'


def _count(path):
    return len(json.loads(ue.tool(M, 'get_expressions', {
        'material_or_function': {'refPath': path}}))['returnValue'])


def fork():
    _pie()
    WM.assert_not_shared(FORK_WALL + '.M_WoodStudioWall')   # must not raise
    before = _count(SHARED_WALL + '.M_StudioWall')
    if not json.loads(ue.tool(AT, 'exists', {'path': FORK_WALL}))['returnValue']:
        ok = json.loads(ue.tool(AT, 'duplicate', {
            'path': SHARED_WALL, 'new_path': FORK_WALL}))['returnValue']
        assert ok, 'duplicate refused'
        print('duplicated ->', FORK_WALL)
    F = {'refPath': FORK_WALL + '.M_WoodStudioWall'}
    pre = FORK_WALL + '.M_WoodStudioWall:MaterialExpression'
    r = json.loads(ue.tool(M, 'get_property_input', {
        'material': F, 'material_property': 'MP_EmissiveColor'}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    e = r.get('expression') if isinstance(r, dict) else None
    driver = e.get('refPath') if isinstance(e, dict) else None
    assert driver, 'fork emissive has no driver'

    def addx(cls, x, y):
        return json.loads(ue.tool(M, 'add_expression', {
            'material_or_function': F,
            'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
            'x': x, 'y': y}))['returnValue']

    def setp(n, v):
        ue.tool('editor_toolset.toolsets.object.ObjectTools', 'set_properties',
                {'instance': n, 'values': json.dumps(v)})

    one = addx('Constant', -900, 400); setp(one, {'R': 1.0})
    dim = addx('Constant', -900, 460); setp(dim, {'R': NIGHT_WALL_DIM})
    night = addx('CollectionParameter', -900, 520)
    setp(night, {'Collection': MPC, 'ParameterName': 'NightAmount'})
    lrp = addx('LinearInterpolate', -750, 460)
    mul = addx('Multiply', -600, 420)
    for a, ao, b, bi in ((one, '', lrp, 'A'), (dim, '', lrp, 'B'),
                         (night, '', lrp, 'Alpha'),
                         ({'refPath': driver}, '', mul, 'A'), (lrp, '', mul, 'B')):
        ue.tool(M, 'connect_expressions', {'from_expression': a, 'from_output_name': ao,
                                           'to_expression': b, 'to_input_name': bi})
    ue.tool(M, 'connect_to_output', {'expression': mul, 'output_name': '',
                                     'material_property': 'MP_EmissiveColor'})
    ue.tool(M, 'recompile', {'material_or_function': F})
    ue.tool(MIT, 'set_parent', {'instance': {'refPath': INSTANCE}, 'parent': F})
    added = [{'role': r_, 'refPath': n['refPath']} for r_, n in
             (('One', one), ('NightWallDim', dim), ('NightAmount', night),
              ('lerp', lrp), ('emissive*dim', mul))]
    json.dump({'added': added, 'emissive_driver': driver}, open(LEDGER, 'w'), indent=1)
    after = _count(SHARED_WALL + '.M_StudioWall')
    print('shared M_StudioWall expressions: %d -> %d  %s'
          % (before, after, 'UNCHANGED' if before == after else 'CHANGED - INVESTIGATE'))
    verify()


def verify():
    rows = []
    n_shared = _count(SHARED_WALL + '.M_StudioWall')
    rows.append(('M_StudioWall expressions (flagship)', n_shared == 3, n_shared))
    n_fork = _count(FORK_WALL + '.M_WoodStudioWall')
    rows.append(('M_WoodStudioWall expressions', n_fork == 8, n_fork))
    p = json.loads(ue.tool('editor_toolset.toolsets.object.ObjectTools', 'get_properties',
                           {'instance': {'refPath': INSTANCE},
                            'properties': ['Parent']}))['returnValue']
    if isinstance(p, str):
        p = json.loads(p)
    par = p.get('Parent')
    par = par.get('refPath') if isinstance(par, dict) else par
    rows.append(('MI_studio_wall_city parent', 'M_WoodStudioWall' in (par or ''),
                 (par or '?').split('/')[-1]))
    print('%-42s %-6s %s' % ('check', 'pass', 'value'))
    for l, ok, v in rows:
        print('%-42s %-6s %s' % (l, 'YES' if ok else 'NO', v))
    print('\n%s' % ('ALL PASS' if all(r[1] for r in rows) else 'FAILURES'))
    return all(r[1] for r in rows)


if __name__ == '__main__':
    {'--fork': fork, '--verify': verify}[sys.argv[1] if len(sys.argv) > 1 else '--fork']()
