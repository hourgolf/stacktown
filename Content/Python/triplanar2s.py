"""Bring M_StacktownMaster_2S's paper projection up to the main master's.

The 2S master never received the triplanar rewrite. Its normal is still
Lerp(flat, PaperNormal sampled on WorldPosition.XZ, PaperNormalAmount) - the
single-plane projection triplanar.py existed to remove. On a face whose normal
is X the X coordinate does not vary across the surface, so the texture varies
only in Z: corduroy, not paper. The original measured 13.5x anisotropy on a
block end wall against 0.7x on a -Y facade.

MINIMAL CHANGE. The amplitude Lerp is left exactly where it is and only its B
input is rewired, from the single sampler to the triplanar sum. That is the
same shape the main master now has after fix_amp.py, so the two masters differ
only in sidedness again - which is the whole point of there being a 2S at all.

Blend weights come from VertexNormalWS, not PixelNormalWS: using the pixel
normal to weight the normal map that produces it is circular.
"""
import matlib as ml, json

PATH = '/Game/Stacktown/Materials/M_StacktownMaster_2S'
MAT  = ml.mat(PATH + '.M_StacktownMaster_2S')
E    = ml.E

def inputs(e):
    r = ml.ue.tool(ml.M,'get_expression_inputs',
                   {'material_or_function':MAT,'expression':e})
    try: return json.loads(r)['returnValue']
    except Exception: return []

def pin(e, name):
    for i in inputs(e):
        if i.get('input_name') == name and isinstance(i.get('expression'), dict):
            return i['expression']
    return None

def cls(e): return e['refPath'].split(':')[-1].rstrip('0123456789_')

def one(cls_path, src, out=''):
    n = ml.addx(MAT, cls_path)
    p = ml.pins(n)
    ml.wire(src, n, p[0] if p else '', out)
    return n

# --- locate, never guess -----------------------------------------------------
lerp = ml.property_input(MAT, 'MP_Normal')
if not lerp or not cls(lerp).endswith('LinearInterpolate'):
    raise SystemExit('MP_Normal is not driven by a Lerp - refusing to guess: %s'
                     % (cls(lerp) if lerp else None))
amt = pin(lerp, 'Alpha')
if ml.props(amt, ['parameterName']).get('parameterName') != 'PaperNormalAmount':
    raise SystemExit('Lerp alpha is not PaperNormalAmount')
old = pin(lerp, 'B')
print('MP_Normal <- Lerp(A=%s, B=%s, Alpha=PaperNormalAmount)'
      % (cls(pin(lerp,'A')), cls(old)))

tiling = ml.find_param(MAT, 'PaperTiling')
if not tiling: raise SystemExit('PaperTiling not found')
tex = ml.props(old, ['texture']).get('texture')
print('reusing PaperTiling; PaperNormal texture: %s'
      % (tex.get('refPath','?').split('.')[-1] if isinstance(tex, dict) else tex))

# --- triplanar sum -----------------------------------------------------------
wp = ml.addx(MAT, E + 'WorldPosition')
scaled = ml.addx(MAT, E + 'Multiply')
ml.wire(wp, scaled, 'A', 'XYZ'); ml.wire(tiling, scaled, 'B')

MASKS = (('g','b','YZ'), ('r','b','XZ'), ('r','g','XY'))
samples = []
for a, b, label in MASKS:
    m = ml.addx(MAT, E + 'ComponentMask')
    ml.setp(m, {'r': 'r' in (a,b), 'g': 'g' in (a,b), 'b': 'b' in (a,b), 'a': False})
    ml.wire(scaled, m, ml.pins(m)[0])
    s = ml.addx(MAT, E + 'TextureSampleParameter2D')
    ml.setp(s, {'parameterName':'PaperNormal','samplerType':'SAMPLERTYPE_Normal'})
    if isinstance(tex, dict): ml.setp(s, {'texture': tex})
    ml.wire(m, s, 'UVs')
    samples.append(s)
    print('  plane %s sampled' % label)

vn = ml.addx(MAT, E + 'VertexNormalWS')
av = one(E + 'Abs', vn)
comps = []
for ch in ('r','g','b'):
    m = ml.addx(MAT, E + 'ComponentMask')
    ml.setp(m, {'r': ch=='r', 'g': ch=='g', 'b': ch=='b', 'a': False})
    ml.wire(av, m, ml.pins(m)[0]); comps.append(m)
s1 = ml.addx(MAT, E + 'Add'); ml.wire(comps[0], s1, 'A'); ml.wire(comps[1], s1, 'B')
s2 = ml.addx(MAT, E + 'Add'); ml.wire(s1, s2, 'A');       ml.wire(comps[2], s2, 'B')
weights = []
for c in comps:
    d = ml.addx(MAT, E + 'Divide'); ml.wire(c, d, 'A'); ml.wire(s2, d, 'B')
    weights.append(d)

terms = []
for s, w in zip(samples, weights):
    mul = ml.addx(MAT, E + 'Multiply'); ml.wire(s, mul, 'A'); ml.wire(w, mul, 'B')
    terms.append(mul)
a1 = ml.addx(MAT, E + 'Add'); ml.wire(terms[0], a1, 'A'); ml.wire(terms[1], a1, 'B')
a2 = ml.addx(MAT, E + 'Add'); ml.wire(a1, a2, 'A');       ml.wire(terms[2], a2, 'B')

ml.wire(a2, lerp, 'B')
print('rewired Lerp.B <- triplanar sum (amplitude Lerp untouched)')
print(ml.finish(MAT, PATH, save=True)[:100])
