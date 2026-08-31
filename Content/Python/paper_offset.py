"""PaperOffset / PaperRotate: per-instance placement of the paper sheet.

RUN LOCALLY (python3 Content/Python/paper_offset.py). matlib drives over MCP,
and an MCP call from inside a remote-exec script waits on its own thread.

WHY. The grain is one world-space field, so every object samples the SAME
sheet at the SAME alignment. Cold read #1's frames show it plainly: the weave
runs across a car's curved bodywork in world axes and continues, unbroken and
identically scaled, onto the wall behind it. No two pieces of card a maker
cuts are like that. These parameters are what will let a study isolate it -
they are the instrument, not the fix.

PROVABLY IDENTITY AT THE DEFAULTS, which is the whole condition this was
approved under. Inserted between WorldPosition_3 and Multiply_9.A - ahead of
the PaperTiling scale, so an offset is in world uu and does not change
meaning when tiling changes:

    x' = x*cos(r) - y*sin(r)      r = 0  ->  cos 1, sin 0  ->  x' = x - 0
    y' = x*sin(r) + y*cos(r)                             ->  y' = 0 + y
    xyz' = (x', y', z) + PaperOffset          (0,0,0)    ->  unchanged

Those are exact in float, not approximately equal: multiplying by 1.0 and
adding 0.0 are identities. The no-op is therefore a claim about arithmetic,
and noopctl.py checks it against the render anyway, because a claim about
arithmetic is not a claim about what the compiler and the sampler do with it.

Rotation is about Z ONLY, applied once to the world position rather than per
plane. Rotating the sheet in the world is both fewer nodes and the more
physical description - a maker turns the card, they do not turn each face of
the model independently.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'Tools', 'measure'))
import matlib as ml

PATH = '/Game/Stacktown/Materials/M_StacktownMaster'
MAT = ml.mat(PATH + '.M_StacktownMaster')
E = '/Script/Engine.MaterialExpression'


def byname(ex):
    return {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ex}


def add(cls, **props):
    n = ml.addx(MAT, E + cls)
    if props:
        ml.setp(n, props)
    return n


def w(frm, to, pin=None, out=''):
    if not ml.wire(frm, to, pin, out):
        raise SystemExit('failed to wire into %s pin %s' % (to, pin))


def main():
    ex = ml.exprs(MAT)
    by = byname(ex)
    if 'MaterialExpressionVectorParameter_0' in by:
        pass
    for probe in ('PaperOffset', 'PaperRotate'):
        if ml.find_param(MAT, probe, 'VectorParameter') or \
           ml.find_param(MAT, probe, 'ScalarParameter'):
            raise SystemExit('%s already exists - refusing to add it twice' % probe)
    wp = by.get('MaterialExpressionWorldPosition_3')
    mul = by.get('MaterialExpressionMultiply_9')
    if not wp or not mul:
        raise SystemExit('the triplanar UV chain is not where this expects it')

    rot = add('ScalarParameter', ParameterName='PaperRotate', DefaultValue=0.0)
    cosn = add('Cosine'); w(rot, cosn)
    sinn = add('Sine');   w(rot, sinn)

    def mask(r, g, b):
        m = add('ComponentMask', R=r, G=g, B=b, A=False)
        w(wp, m, ml.pins(m)[0], 'XYZ')
        return m
    mx, my, mz = mask(True, False, False), mask(False, True, False), mask(False, False, True)

    def mul2(a, b):
        n = add('Multiply'); w(a, n, 'A'); w(b, n, 'B'); return n
    xc, ys = mul2(mx, cosn), mul2(my, sinn)
    xs, yc = mul2(mx, sinn), mul2(my, cosn)
    nx = add('Subtract'); w(xc, nx, 'A'); w(ys, nx, 'B')
    ny = add('Add');      w(xs, ny, 'A'); w(yc, ny, 'B')

    axy = add('AppendVector');  w(nx, axy, 'A');  w(ny, axy, 'B')
    axyz = add('AppendVector'); w(axy, axyz, 'A'); w(mz, axyz, 'B')

    off = add('VectorParameter', ParameterName='PaperOffset',
              DefaultValue={'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 0.0})
    offm = add('ComponentMask', R=True, G=True, B=True, A=False)
    w(off, offm, ml.pins(offm)[0])

    tot = add('Add'); w(axyz, tot, 'A'); w(offm, tot, 'B')
    w(tot, mul, 'A')            # replaces WorldPosition_3 -> Multiply_9.A

    ml.finish(MAT, PATH, save=True)
    print('PaperRotate + PaperOffset spliced ahead of the tiling scale')


if __name__ == '__main__':
    main()
