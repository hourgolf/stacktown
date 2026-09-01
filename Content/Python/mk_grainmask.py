#!/usr/bin/env python3
"""Insert the GRAIN MASK into M_StacktownMaster's base-colour chain.

    python3 Content/Python/mk_grainmask.py

RUN LOCALLY. matlib drives over MCP and an MCP call from inside a remote-exec
script waits on its own thread.

THIS EDITS THE SHARED MASTER - the one material every asset in the project
uses - so it carries the split proof standard named BEFORE it started
(DIRECTION_B_DECLARATIONS D8):

  no-op half   an existing FLAGSHIP material rendered before and after, mean
               absolute difference inside the measured noise floor
  look half    judged on a wooden building at the show camera, owner's eye

WHY IT IS SAFE BY ARITHMETIC, not just by a white default. The obvious design
gives GrainMask a white texture and multiplies: white is 1.0, so identity.
That is true and it is fragile - it depends on a TEXTURE being right, and a
mask is mean-normalised luminance whose average is nowhere near 1.0, so any
instance that assigns a real mask without also setting the gain would HALVE
its own brightness.

So the factor is:

    factor = 1 + GrainGain * (GrainMask - GrainMean)

with GrainGain defaulting to ZERO. At the default the multiply-by-zero kills
the whole term whatever the texture holds, and 1.0 * BaseColour is an exact
float identity. The no-op is a property of the ARITHMETIC, and a material that
has not opted in cannot be affected by a mask assigned to it by accident.

WHERE. BaseColour (VectorParameter_0) feeds TWO consumers, walked rather than
assumed: LinearInterpolate_2 input 0 (the unworn colour) and Multiply_1
input 0 (the same colour times EdgeWearLift). Both are repointed at the
grained colour, so the figure sits UNDER the wear and seam treatment - edge
wear lightens grained wood, which is the right order; grain applied after
wear would paint over the polished arris.
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
WHITE = '/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture'


def sh(e):
    return e['refPath'].split(':')[-1]


def ins(e):
    return json.loads(ue.tool(M, 'get_expression_inputs',
                              {'material_or_function': MAT,
                               'expression': e}))['returnValue']


def pname(e):
    try:
        return ml.props(e, ['parameterName']).get('parameterName') or ''
    except Exception:
        return ''


def main():
    # IDEMPOTENCY IN ONE CALL. The first version asked every expression for
    # its parameterName - 141 round trips - and the script died on a two
    # minute timeout before creating a single node. list_parameters answers
    # the same question about the whole material at once. A check that costs
    # more than the work it guards is a check that stops the work happening.
    have = json.loads(ue.tool(
        'editor_toolset.toolsets.material_instance.MaterialInstanceTools',
        'list_parameters', {'material': MAT}))['returnValue']
    if any(p.get('name') == 'GrainMask' for p in have):
        print('GrainMask already present - nothing to do (idempotent)')
        return 0
    allx = ml.exprs(MAT)

    seam = ml.property_input(MAT, 'MP_BaseColor')
    wear = ins(seam)[0]['expression']
    a0 = ins(wear)[0]['expression']       # BaseColour
    lift = ins(wear)[1]['expression']     # Multiply_1 = BaseColour * EdgeWearLift
    assert pname(a0) == 'BaseColour', 'walked to %s, not BaseColour' % sh(a0)
    assert ins(lift)[0]['expression']['refPath'] == a0['refPath'], \
        'Multiply_1 is not fed by BaseColour - the chain moved'
    print('walked: %s -> %s -> BaseColour (%s) and %s'
          % (sh(seam), sh(wear), sh(a0), sh(lift)))

    # the UVs the paper samplers already use, so grain tiles WITH the wood
    # only the texture samplers are candidates - 8 calls, not 141
    det = [e for e in allx if 'TextureSampleParameter2D' in e['refPath']
           and pname(e) == 'PaperDetail']
    assert det, 'PaperDetail sampler not found'
    uv = ins(det[0])[0]['expression']
    print('UV source shared with PaperDetail: %s' % sh(uv))

    E = ml.E
    mask = ml.addx(MAT, E + 'TextureSampleParameter2D')
    ml.setp(mask, {'ParameterName': 'GrainMask',
                   'Texture': {'refPath': WHITE},
                   'SamplerType': 'SAMPLERTYPE_LinearGrayscale'})
    ml.wire(uv, mask, 'UVs')
    mean = ml.addx(MAT, E + 'ScalarParameter')
    ml.setp(mean, {'ParameterName': 'GrainMean', 'DefaultValue': 0.5})
    gain = ml.addx(MAT, E + 'ScalarParameter')
    ml.setp(gain, {'ParameterName': 'GrainGain', 'DefaultValue': 0.0})
    one = ml.addx(MAT, E + 'Constant')
    ml.setp(one, {'R': 1.0})

    sub = ml.addx(MAT, E + 'Subtract')
    ml.wire(mask, sub, 'A')
    ml.wire(mean, sub, 'B')
    scl = ml.addx(MAT, E + 'Multiply')
    ml.wire(sub, scl, 'A')
    ml.wire(gain, scl, 'B')
    add = ml.addx(MAT, E + 'Add')
    ml.wire(one, add, 'A')
    ml.wire(scl, add, 'B')
    grained = ml.addx(MAT, E + 'Multiply')
    ml.wire(a0, grained, 'A')
    ml.wire(add, grained, 'B')
    print('built: BaseColour * (1 + GrainGain * (GrainMask - GrainMean))')

    # repoint BOTH consumers of BaseColour at the grained colour
    ml.wire(grained, wear, 'A')
    ml.wire(grained, lift, 'A')
    print('repointed %s.A and %s.A' % (sh(wear), sh(lift)))

    ml.finish(MAT, PATH, save=True)
    print('recompiled and SAVED %s' % PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
