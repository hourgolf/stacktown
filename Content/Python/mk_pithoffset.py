#!/usr/bin/env python3
"""Push the end-grain PITH off centre, per block.

    python3 Content/Python/mk_pithoffset.py

RUN LOCALLY - matlib drives over MCP.

THE FAULT. mk_endgrain centres the polar sample on ObjectPositionWS, so every
block's rings are perfectly concentric about its own middle. That reads as a
TARGET, not a sawn end. On a real block the pith is off centre and usually
OUTSIDE the piece entirely - what crosses a small end face is a set of gentle
ARCS, not closed circles.

THE FIX. Offset the polar centre by a per-block pseudo-random vector derived
from the block's own world position:

    off = (frac(ObjectPos * k) - 0.5) * PithOffset

frac of a scaled position is the standard way to get a stable per-object
value with no extra data: two blocks at different places get different
offsets, the same block gets the same offset every frame, and nothing has to
be authored or stored. PithOffset defaults large (1800 uu) so the centre lands
well outside a typical block and the rings arrive as arcs.

STILL GATED. This sits inside the GrainMask term, which is multiplied out at
GrainGain 0, so every flagship material remains untouched by arithmetic - the
same guarantee the first two master edits carry.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import matlib as ml  # noqa: E402
import ue  # noqa: E402

PATH = '/Game/Stacktown/Materials/M_StacktownMaster'
MAT = ml.mat(PATH + '.M_StacktownMaster')
M, E = ml.M, ml.E


def pn(e):
    try:
        return ml.props(e, ['parameterName']).get('parameterName') or ''
    except Exception:
        return ''


def main():
    have = json.loads(ue.tool(
        'editor_toolset.toolsets.material_instance.MaterialInstanceTools',
        'list_parameters', {'material': MAT}))['returnValue']
    if any(p.get('name') == 'PithOffset' for p in have):
        print('PithOffset already present - nothing to do')
        return 0

    allx = ml.exprs(MAT)
    # the DotProduct built by mk_endgrain takes the xy ComponentMask twice;
    # that mask is the polar centre we need to shift.
    dots = [e for e in allx if 'DotProduct' in e['refPath']]
    assert len(dots) == 1, 'expected 1 DotProduct, found %d' % len(dots)
    ins = json.loads(ue.tool(M, 'get_expression_inputs',
                             {'material_or_function': MAT,
                              'expression': dots[0]}))['returnValue']
    xy = ins[0]['expression']
    print('polar centre currently: %s' % xy['refPath'].split(':')[-1])

    op = ml.addx(MAT, E + 'ObjectPositionWS')
    k = ml.addx(MAT, E + 'Constant')
    ml.setp(k, {'R': 0.0173})          # arbitrary, coprime-ish scatter
    sc = ml.addx(MAT, E + 'Multiply')
    ml.wire(op, sc, 'A')
    ml.wire(k, sc, 'B')
    fr = ml.addx(MAT, E + 'Frac')
    ml.wire(sc, fr, ml.pins(fr)[0] if ml.pins(fr) else '')
    half = ml.addx(MAT, E + 'Constant')
    ml.setp(half, {'R': 0.5})
    ctr = ml.addx(MAT, E + 'Subtract')
    ml.wire(fr, ctr, 'A')
    ml.wire(half, ctr, 'B')
    amt = ml.addx(MAT, E + 'ScalarParameter')
    ml.setp(amt, {'ParameterName': 'PithOffset', 'DefaultValue': 1800.0})
    off = ml.addx(MAT, E + 'Multiply')
    ml.wire(ctr, off, 'A')
    ml.wire(amt, off, 'B')
    offxy = ml.addx(MAT, E + 'ComponentMask')
    ml.setp(offxy, {'R': True, 'G': True, 'B': False, 'A': False})
    ml.wire(off, offxy, ml.pins(offxy)[0] if ml.pins(offxy) else '')

    shifted = ml.addx(MAT, E + 'Subtract')
    ml.wire(xy, shifted, 'A')
    ml.wire(offxy, shifted, 'B')
    # repoint BOTH DotProduct inputs and the Arctangent2Fast components
    ml.wire(shifted, dots[0], 'A')
    ml.wire(shifted, dots[0], 'B')
    print('pith offset wired into the polar centre')

    ml.finish(MAT, PATH, save=True)
    print('recompiled and SAVED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
