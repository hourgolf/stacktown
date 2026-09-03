#!/usr/bin/env python3
"""Why the corrected edge-wear proxy still moves nothing. One trace, one A/B.

    python3 Content/Python/wear_trace.py --trace   read-only: the lerp chain
    python3 Content/Python/wear_trace.py --ab      drive the branch, measure

STATE: the geometry is right (72.7% non-axis normals, counted), the proxy now
reads VertexNormalWS instead of the shaded normal (a real defect, fixed), and
EdgeWearLift at 12 still peaks at 1.20x drift. Something downstream is eating
the signal.

THE ARITHMETIC SAYS IT SHOULD BE ENORMOUS, which is why the null result is
informative rather than merely disappointing:

    Multiply_34         = EdgeWearLift * (1 + Attention * AttentionGain)
    Multiply_1          = Multiply_24 * Multiply_34          [A * lift]
    LinearInterpolate_2 = lerp(Multiply_24, Multiply_1, curvature)
                        = A * (1 + curvature * (lift - 1))

At lift 12 with curvature 0.97 on a chamfer facet, that is **A x 11.7** - the
arris should be blown out, not subtle. It is not. So the value is being
discarded after it is computed.

THE HYPOTHESIS, and the reason it is first: LinearInterpolate_2 feeds
LinearInterpolate_3 on pin **A**, and pin A of a lerp is the alpha=0 end. If
LinearInterpolate_3's Alpha sits near 1, the entire wear-carrying branch is
lerped AWAY at the last step and BaseColor never sees it. The chain would trace
as fully connected - which it does - while carrying nothing, which is exactly
the reading a connectivity check cannot distinguish.

That would make this a fifth member of the reports-success-while-doing-nothing
family, and the first one where the "success" is a correct graph.

--ab tests it by driving the OTHER end. If forcing LinearInterpolate_3's alpha
moves the frame while driving EdgeWearLift does not, the gate is found.
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
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
MAT = {'refPath': WM.FORK}
PRE = WM.FORK + ':MaterialExpression'


def _ins(short):
    r = json.loads(ue.tool(M, 'get_expression_inputs', {
        'material_or_function': MAT,
        'expression': {'refPath': PRE + short}}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    out = []
    for i in r:
        if not isinstance(i, dict):
            continue
        x = i.get('expression')
        rp = x.get('refPath') if isinstance(x, dict) else x
        out.append((i.get('input_name'), (rp or 'NOTHING').rsplit(':', 1)[-1]))
    return out


def _props(short, names):
    try:
        r = json.loads(ue.tool(OBJ, 'get_properties', {
            'instance': {'refPath': PRE + short},
            'properties': names}))['returnValue']
        return json.loads(r) if isinstance(r, str) else r
    except Exception as e:
        return {'err': str(e)[:60]}


def trace():
    """Walk the last three nodes before BaseColor and read every constant.

    A lerp with an UNWIRED alpha silently uses its own ConstAlpha, so the
    constants are read alongside the wiring - a pin that reads as connected to
    NOTHING is not the same as a pin that does nothing, and only one of those
    is visible in a connectivity dump.
    """
    for node in ('LinearInterpolate_2', 'LinearInterpolate_3', 'Multiply_35',
                 'Multiply_4', 'Multiply_1', 'Multiply_24', 'Saturate_0'):
        wiring = _ins(node)
        consts = _props(node, ['ConstA', 'ConstB', 'ConstAlpha'])
        consts = {k: v for k, v in consts.items() if v is not None}
        print('%-22s %s' % (node, wiring))
        if consts:
            print('%-22s   constants %s' % ('', consts))


if __name__ == '__main__':
    {'--trace': trace}[sys.argv[1] if len(sys.argv) > 1 else '--trace']()
