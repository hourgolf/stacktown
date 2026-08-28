"""Park the two-octave work inert: restore single-octave behaviour exactly.

RUN LOCALLY (drives over MCP).

The graph KEEPS every node - PaperOffset, PaperRotate, PaperFineScale,
PaperFineWeight, PaperCoarseWeight and the fine sampler chain all stay, so
none of the proven work is unpicked and restarting is a parameter change.
What is restored is the BEHAVIOUR:

  coarse samplers -> ParameterName PaperNormal, Texture T_PaperNormal
      Both halves must go back. Leaving the name as PaperMottle would keep
      every existing instance's PaperNormal value addressing only the fine
      octave, which is NOT the original behaviour even with the right texture.
  PaperFineWeight -> 0.0
  PaperCoarseWeight -> 1.0
      normal = flat + (coarse-flat)*1 + (fine-flat)*0 = coarse, which is
      exactly what LinearInterpolate_4 saw before any of this.

VERIFIED AGAINST A KNOWN ANSWER, not asserted: the C0 study panel measured
5.035 far / 2.147 near under the original single-octave master, on this wall,
in this level. Parked correctly, it has to return those numbers.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'Tools', 'measure'))
import matlib as ml

PATH = '/Game/Stacktown/Materials/M_StacktownMaster'
MAT = ml.mat(PATH + '.M_StacktownMaster')
NORMAL = {'refPath': '/Game/Stacktown/Textures/T_PaperNormal.T_PaperNormal'}
COARSE = ('TextureSampleParameter2D_2', 'TextureSampleParameter2D_3',
          'TextureSampleParameter2D_4')


def main():
    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    for n in COARSE:
        ml.setp(by['MaterialExpression' + n],
                {'ParameterName': 'PaperNormal', 'Texture': NORMAL})
    for pname, val in (('PaperFineWeight', 0.0), ('PaperCoarseWeight', 1.0)):
        p = ml.find_param(MAT, pname, 'ScalarParameter')
        if p:
            ml.setp(p, {'DefaultValue': val})
    ml.finish(MAT, PATH, save=True)

    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    bad = []
    for n in COARSE:
        p = ml.props(by['MaterialExpression' + n], ['ParameterName', 'Texture'])
        t = p.get('Texture')
        t = (t.get('refPath') if isinstance(t, dict) else t) or 'NULL'
        if p.get('ParameterName') != 'PaperNormal' or 'T_PaperNormal' not in str(t):
            bad.append((n, p.get('ParameterName'), t))
        print('  %-30s %-12s %s' % (n, p.get('ParameterName'), str(t).split('.')[-1]))
    for pname, want in (('PaperFineWeight', 0.0), ('PaperCoarseWeight', 1.0)):
        p = ml.find_param(MAT, pname, 'ScalarParameter')
        got = ml.props(p, ['DefaultValue']).get('DefaultValue') if p else None
        print('  %-30s default %s' % (pname, got))
        if p and abs(float(got) - want) > 1e-6:
            bad.append((pname, got, want))
    if bad:
        raise SystemExit('PARK INCOMPLETE: %s' % bad)
    print('parked: single-octave behaviour restored, all nodes retained')


if __name__ == '__main__':
    main()
