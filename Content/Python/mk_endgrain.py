#!/usr/bin/env python3
"""END GRAIN: make the grain a property of the SOLID, not of the surface.

    python3 Content/Python/mk_endgrain.py

RUN LOCALLY - matlib drives over MCP and an MCP call from inside a remote-exec
script waits on its own thread.

THE FAULT, in the owner's words on the first grained board: "the grain of the
wood is not consistent like a block of carved wood would be... it goes
vertically and then horizontally on other building faces. It doesn't look like
these buildings are carved out of one continuous piece of wood."

That is physically exact. A block sawn from stock has grain running ONE way
through the solid: long grain on the four faces parallel to it, and END GRAIN
- rings and swirl - on the two faces the saw crossed. Half the fault was the
source maps disagreeing with each other, fixed in mk_grain_masks. This is the
other half.

WHAT WAS WRONG. GrainMask sampled a single plane, the world XY, inherited from
PaperDetail's UVs. One projection cannot describe a solid: on a wall it gave
streaks running whichever way that plane happened to cut, and on a roof it gave
the same streaks again. Veneer wrapped round a box.

WHAT REPLACES IT. Three samplers blended by the vertex normal, as the paper
normal already does - but the Z-facing plane is POLAR rather than planar:

    rel   = WorldPosition - ObjectPositionWS      per-block, so rings centre
                                                  on each block and not on
                                                  some shared world origin
    sides = (y,z) and (x,z)                       long grain, running along Z
    end   = (|rel.xy| * tiling, atan2(y,x) / 2pi) concentric rings

Sampling a STRIPED map in polar coordinates produces concentric rings, which
is what end grain is - the same growth rings, crossed instead of followed. So
the end faces need no second texture and cannot disagree with the sides about
which tree they came from.

GRAIN RUNS ALONG Z, the common way to cut a standing block. Per-block grain
AXIS - some stock sawn on its side - is a further step and is deliberately not
attempted here.

WHY THIS IS SAFE ON A SHARED MASTER. The GrainMask term is gated by GrainGain,
which defaults to ZERO, so the whole term is multiplied out for any material
that has not opted in. Every change here is therefore a no-op by construction
for every flagship material, whatever the sampling does - a stronger guarantee
than the first master edit had, and the reason that edit put the gate in.
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
M = ml.M
E = ml.E
TWO_PI_INV = 0.15915494


def sh(e):
    return e['refPath'].split(':')[-1]


def pn(e):
    try:
        return ml.props(e, ['parameterName']).get('parameterName') or ''
    except Exception:
        return ''


def mask(src, r, g, b):
    m = ml.addx(MAT, E + 'ComponentMask')
    ml.setp(m, {'R': r, 'G': g, 'B': b, 'A': False})
    ml.wire(src, m, ml.pins(m)[0] if ml.pins(m) else '')
    return m


def main():
    allx = ml.exprs(MAT)
    samplers = [e for e in allx if 'TextureSampleParameter2D' in e['refPath']]
    grain = [e for e in samplers if pn(e) == 'GrainMask']
    if len(grain) != 1:
        print('expected exactly 1 GrainMask sampler, found %d - already '
              'converted? nothing done' % len(grain))
        return 0
    old = grain[0]
    tiling = [e for e in allx if pn(e) == 'PaperTiling']
    assert tiling, 'PaperTiling not found'
    tiling = tiling[0]

    # who consumes the old sampler? it feeds the Subtract of the grain term.
    sub = None
    for e in allx:
        if 'Subtract' not in e['refPath']:
            continue
        ins = json.loads(ue.tool(M, 'get_expression_inputs',
                                 {'material_or_function': MAT,
                                  'expression': e}))['returnValue']
        if any(isinstance(i.get('expression'), dict)
               and i['expression']['refPath'] == old['refPath'] for i in ins):
            sub = e
            break
    assert sub, 'could not find the Subtract fed by GrainMask'
    print('grain term Subtract: %s' % sh(sub))

    # object-relative position, so rings centre per block
    wp = ml.addx(MAT, E + 'WorldPosition')
    op = ml.addx(MAT, E + 'ObjectPositionWS')
    rel = ml.addx(MAT, E + 'Subtract')
    ml.wire(wp, rel, 'A', 'XYZ')
    ml.wire(op, rel, 'B')
    scaled = ml.addx(MAT, E + 'Multiply')
    ml.wire(rel, scaled, 'A')
    ml.wire(tiling, scaled, 'B')
    print('object-relative position built (rings centre per block)')

    # --- the two SIDE planes: long grain, running along Z ---------------
    uv_yz = mask(scaled, False, True, True)     # (y, z)
    uv_xz = mask(scaled, True, False, True)     # (x, z)

    # --- the END plane: polar, so stripes become concentric rings -------
    xy = mask(rel, True, True, False)
    dot = ml.addx(MAT, E + 'DotProduct')
    ml.wire(xy, dot, 'A')
    ml.wire(xy, dot, 'B')
    rad = ml.addx(MAT, E + 'SquareRoot')
    ml.wire(dot, rad, ml.pins(rad)[0] if ml.pins(rad) else '')
    radt = ml.addx(MAT, E + 'Multiply')
    ml.wire(rad, radt, 'A')
    ml.wire(tiling, radt, 'B')
    rx = mask(rel, True, False, False)
    ry = mask(rel, False, True, False)
    ang = ml.addx(MAT, E + 'Arctangent2Fast')
    ml.wire(ry, ang, 'Y')
    ml.wire(rx, ang, 'X')
    angn = ml.addx(MAT, E + 'Multiply')
    ml.wire(ang, angn, 'A')
    k = ml.addx(MAT, E + 'Constant')
    ml.setp(k, {'R': TWO_PI_INV})
    ml.wire(k, angn, 'B')
    uv_end = ml.addx(MAT, E + 'AppendVector')
    ml.wire(radt, uv_end, 'A')
    ml.wire(angn, uv_end, 'B')
    print('polar end-grain UVs built')

    # --- three samplers on one parameter, as the paper normal already does
    samps = []
    for uv, label in ((uv_yz, 'side X'), (uv_xz, 'side Y'), (uv_end, 'END Z')):
        s = ml.addx(MAT, E + 'TextureSampleParameter2D')
        ml.setp(s, {'ParameterName': 'GrainMask',
                    'SamplerType': 'SAMPLERTYPE_LinearGrayscale',
                    'Texture': ml.props(old, ['texture']).get('texture')
                    or {'refPath': '/Game/Stacktown/Textures/'
                                   'T_grain_white.T_grain_white'}})
        ml.wire(uv, s, 'UVs')
        samps.append(s)
        print('  sampler for %s' % label)

    # --- blend by |vertex normal|, same construction as the paper normal
    vn = ml.addx(MAT, E + 'VertexNormalWS')
    av = ml.addx(MAT, E + 'Abs')
    ml.wire(vn, av, ml.pins(av)[0] if ml.pins(av) else '')
    comps = [mask(av, True, False, False), mask(av, False, True, False),
             mask(av, False, False, True)]
    s1 = ml.addx(MAT, E + 'Add'); ml.wire(comps[0], s1, 'A'); ml.wire(comps[1], s1, 'B')
    s2 = ml.addx(MAT, E + 'Add'); ml.wire(s1, s2, 'A'); ml.wire(comps[2], s2, 'B')
    terms = []
    for s, c in zip(samps, comps):
        d = ml.addx(MAT, E + 'Divide'); ml.wire(c, d, 'A'); ml.wire(s2, d, 'B')
        t = ml.addx(MAT, E + 'Multiply'); ml.wire(s, t, 'A'); ml.wire(d, t, 'B')
        terms.append(t)
    b1 = ml.addx(MAT, E + 'Add'); ml.wire(terms[0], b1, 'A'); ml.wire(terms[1], b1, 'B')
    b2 = ml.addx(MAT, E + 'Add'); ml.wire(b1, b2, 'A'); ml.wire(terms[2], b2, 'B')

    ml.wire(b2, sub, 'A')
    print('blend wired into %s.A (was the single-plane sampler)' % sh(sub))

    ml.finish(MAT, PATH, save=True)
    print('recompiled and SAVED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
