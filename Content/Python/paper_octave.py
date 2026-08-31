"""The second grain octave: card has fine tooth AND sheet-level fibre.

RUN LOCALLY. matlib drives over MCP.

WHY TWO OCTAVES AND NOT A DISTANCE-DRIVEN TILING. The study wall measured a
single-octave grain being correct at exactly one distance: 0.006 gives 5.02
detail at the 3189 uu player-zoom standoff and 2.14 at 800 where it reads as
coarse woven linen; 0.025 gives 4.71 at 800 and 0.80 at 3189, where it is a
flat grey plane. There is no single value, and the first instinct - drive the
tiling from camera distance - was argued down and correctly:

  - real card genuinely HAS multi-scale structure, so two static octaves are
    a PHYSICAL property the camera resolves naturally at each range, not a
    screen trick that happens to score well at two measured standoffs;
  - THE PLAYER'S CORE VERB IS THE ZOOM. A view-dependent material morphs
    during the exact gesture the project is built around, and a surface that
    changes while you look at it is a tell a reader feels before they can
    name it. Octaves are stable through the whole zoom.

THIS IS A LOOK CHANGE BY DESIGN and its proof is NOT a no-op. The offset half
of this graph work proves byte-equivalence at (0,0); this half proves itself
on the study wall at BOTH standoffs plus owner eyes. Two verification
standards, one chain opening, named before either started.

The fine octave reuses the coarse octave's PLANE WEIGHTS. They derive from
the vertex normal alone and have nothing to do with scale, so recomputing
them would be three more divides saying the same thing.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'Tools', 'measure'))
import matlib as ml

PATH = '/Game/Stacktown/Materials/M_StacktownMaster'
MAT = ml.mat(PATH + '.M_StacktownMaster')
E = '/Script/Engine.MaterialExpression'

FINE_SCALE = 4.0     # x the coarse tiling: card_heavy 0.006 -> 0.024, which
                     # is where the wall study read as card rather than linen
FINE_WEIGHT = 0.5    # equal voice; the wall decides whether it stays there

MASKS = ((False, True, True), (True, False, True), (True, True, False))
WEIGHTS = ('Divide_7', 'Divide_8', 'Divide_9')


def main():
    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    N = lambda s: by['MaterialExpression' + s]
    for p in ('PaperFineScale', 'PaperFineWeight'):
        if ml.find_param(MAT, p, 'ScalarParameter'):
            raise SystemExit('%s already exists - refusing to add it twice' % p)
    tex = ml.props(N('TextureSampleParameter2D_2'), ['Texture']).get('Texture')
    if not tex:
        raise SystemExit('could not read the PaperNormal texture off the coarse sampler')

    def add(cls, **kw):
        n = ml.addx(MAT, E + cls)
        if kw:
            ml.setp(n, kw)
        return n

    def w(a, b, pin=None, out=''):
        if not ml.wire(a, b, pin, out):
            raise SystemExit('failed wiring into %s' % pin)

    scale = add('ScalarParameter', ParameterName='PaperFineScale',
                DefaultValue=FINE_SCALE)
    fine = add('Multiply'); w(N('AppendVector_1'), fine, 'A'); w(scale, fine, 'B')

    terms = []
    for (r, g, b), wt in zip(MASKS, WEIGHTS):
        m = add('ComponentMask', R=r, G=g, B=b, A=False)
        w(fine, m, ml.pins(m)[0])
        s = add('TextureSampleParameter2D', ParameterName='PaperNormal',
                SamplerType='SAMPLERTYPE_Normal', Texture=tex)
        w(m, s, 'UVs')
        t = add('Multiply'); w(s, t, 'A'); w(N(wt), t, 'B')
        terms.append(t)
    f1 = add('Add'); w(terms[0], f1, 'A'); w(terms[1], f1, 'B')
    f2 = add('Add'); w(f1, f2, 'A'); w(terms[2], f2, 'B')

    fw = add('ScalarParameter', ParameterName='PaperFineWeight',
             DefaultValue=FINE_WEIGHT)
    blend = add('LinearInterpolate')
    w(N('Add_5'), blend, 'A')      # coarse octave, unchanged
    w(f2, blend, 'B')              # fine octave
    w(fw, blend, 'Alpha')
    w(blend, N('LinearInterpolate_4'), 'B')   # into the amplitude lerp

    ml.finish(MAT, PATH, save=True)
    print('two-octave grain wired: coarse x1, fine x%.1f, weight %.2f'
          % (FINE_SCALE, FINE_WEIGHT))


if __name__ == '__main__':
    main()
