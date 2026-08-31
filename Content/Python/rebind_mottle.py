"""Point the COARSE samplers at T_PaperMottle. RUN LOCALLY (drives over MCP).

Separate from import_mottle.py because the expression API is MCP-side while
the import is unreal-module-side, and an MCP call from inside a remote-exec
script deadlocks. Run import_mottle.py first, then this - ALWAYS both, because
import deletes the asset and that nulls every reference the master holds. A
null sampler renders black; the five-octave sweep measured a black material
and produced a table that looked like a texture failure.

Verifies by read-back and refuses to report success on a null.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'Tools', 'measure'))
import matlib as ml

PATH = '/Game/Stacktown/Materials/M_StacktownMaster'
MAT = ml.mat(PATH + '.M_StacktownMaster')
TEX = {'refPath': '/Game/Stacktown/Textures/T_PaperMottle.T_PaperMottle'}
COARSE = ('TextureSampleParameter2D_2', 'TextureSampleParameter2D_3',
          'TextureSampleParameter2D_4')


def main():
    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    for n in COARSE:
        ml.setp(by['MaterialExpression' + n],
                {'ParameterName': 'PaperMottle', 'Texture': TEX})
    ml.finish(MAT, PATH, save=True)
    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    bad = []
    for n in COARSE:
        p = ml.props(by['MaterialExpression' + n], ['ParameterName', 'Texture'])
        t = p.get('Texture')
        t = (t.get('refPath') if isinstance(t, dict) else t) or 'NULL'
        print('  %-30s %-12s %s' % (n, p.get('ParameterName'), t))
        if 'T_PaperMottle' not in str(t):
            bad.append(n)
    if bad:
        raise SystemExit('COARSE SAMPLERS STILL NULL: %s' % bad)
    print('all three coarse samplers bound and verified')


if __name__ == '__main__':
    main()
