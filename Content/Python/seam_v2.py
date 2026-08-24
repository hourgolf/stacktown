"""Panel seams v2 — vertical, irregular, low-frequency.

v1 was a uniform square grid at 150 uu. Cranked to 0.55 for a diagnostic it is
unmistakably bathroom tile, and even softened it says "cladding panels on a
building", which is the opposite of the cue we want.

Two corrections:

1. VERTICAL ONLY. The horizontal division is already carried by the floor-band
   mouldings, which are geometry and throw real shadows. Adding a second
   horizontal set on top of them is what produced the grid. Card sheets butt
   vertically; the horizontal joints are the section stack, and those exist.

2. IRREGULAR. Evenly spaced anything reads as machined. Offsetting world X by a
   low-frequency sine before the frac keeps every line perfectly vertical (the
   offset depends on X alone) while making the spacing uneven. A second sine
   varies joint strength so they are not all the same weight.

Spacing goes 150 -> 380 uu. At 150 the facade carried ~9 joints across three
bays; a card model has a joint per sheet, not per window.

Rebuilds the mask only and rewires the existing seam lerp's Alpha, so the
SeamSpacing / SeamWidth / SeamDarken parameter names and every instance
override survive.
"""
import ue, json

M = 'editor_toolset.toolsets.material.MaterialTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
E = '/Script/Engine.MaterialExpression'
MAT = {'refPath': '/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster'}


def addx(cls):
    r = ue.tool(M, 'add_expression',
                {'material_or_function': MAT, 'expression_class': {'refPath': cls}})
    if 'ERROR' in r:
        raise SystemExit('add %s failed: %s' % (cls, r[:140]))
    return json.loads(r)['returnValue']


def setp(ref, vals):
    r = ue.tool(O, 'set_properties', {'instance': ref, 'values': json.dumps(vals)})
    if '"returnValue":true' not in r:
        print('   warn set', list(vals), r[:90])


def getp(ref, names):
    r = ue.tool(O, 'get_properties', {'instance': ref, 'properties': names})
    try:
        return json.loads(json.loads(r)['returnValue'])
    except Exception:
        return {}


def pins(e):
    return json.loads(ue.tool(M, 'get_expression_input_names',
                              {'expression': e}))['returnValue']


def wire(frm, to, pin=None, out=''):
    cands = [pin] if pin else (pins(to) or [''])
    for p in cands:
        r = ue.tool(M, 'connect_expressions',
                    {'from_expression': frm, 'from_output_name': out,
                     'to_expression': to, 'to_input_name': p})
        if 'ERROR' not in r and 'TOOL-ERROR' not in r:
            return True
    print('   FAILED wire into', pins(to))
    return False


def one(cls, src, out=''):
    n = addx(cls)
    p = pins(n)
    wire(src, n, p[0] if p else '', out)
    return n


# --- reuse the existing scalar parameters so instance overrides survive -------
exprs = json.loads(ue.tool(M, 'get_expressions',
                           {'material_or_function': MAT}))['returnValue']
params = {}
for e in exprs:
    if 'ScalarParameter' in e['refPath']:
        nm = getp(e, ['ParameterName']).get('ParameterName')
        if nm:
            params.setdefault(nm, e)
for need in ('SeamSpacing', 'SeamWidth'):
    if need not in params:
        raise SystemExit('parameter %s not found — was panel_seams.py run?' % need)
spacing, width = params['SeamSpacing'], params['SeamWidth']
setp(spacing, {'DefaultValue': 380.0})
print('reusing SeamSpacing / SeamWidth; spacing default -> 380 uu')

# --- vertical position with low-frequency jitter ------------------------------
wp = addx(E + 'WorldPosition')
mx = addx(E + 'ComponentMask')
setp(mx, {'R': True, 'G': False, 'B': False, 'A': False})
wire(wp, mx, pins(mx)[0], 'XYZ')

jit = addx(E + 'Sine')                       # out = sin(2*pi*in/Period)
setp(jit, {'Period': 900.0})
wire(mx, jit, pins(jit)[0])
amp = addx(E + 'Constant'); setp(amp, {'R': 55.0})
jm = addx(E + 'Multiply'); wire(jit, jm, 'A'); wire(amp, jm, 'B')
px = addx(E + 'Add'); wire(mx, px, 'A'); wire(jm, px, 'B')

# --- seam profile -------------------------------------------------------------
dv = addx(E + 'Divide'); wire(px, dv, 'A'); wire(spacing, dv, 'B')
fr = one(E + 'Frac', dv)
inv = one(E + 'OneMinus', fr)
mn = addx(E + 'Min'); wire(fr, mn, 'A'); wire(inv, mn, 'B')
sc = addx(E + 'Multiply'); wire(mn, sc, 'A'); wire(spacing, sc, 'B')
dw = addx(E + 'Divide'); wire(sc, dw, 'A'); wire(width, dw, 'B')
seam = one(E + 'OneMinus', one(E + 'Saturate', dw))

# --- vary joint strength so they are not all equal weight ---------------------
s2 = addx(E + 'Sine'); setp(s2, {'Period': 1700.0})
wire(mx, s2, pins(s2)[0])
half = addx(E + 'Constant'); setp(half, {'R': 0.32})
hm = addx(E + 'Multiply'); wire(s2, hm, 'A'); wire(half, hm, 'B')
base = addx(E + 'Constant'); setp(base, {'R': 0.68})
stren = addx(E + 'Add'); wire(hm, stren, 'A'); wire(base, stren, 'B')
alpha = addx(E + 'Multiply'); wire(seam, alpha, 'A'); wire(stren, alpha, 'B')

# --- rewire the existing seam lerp's Alpha ------------------------------------
cur = json.loads(ue.tool(M, 'get_property_input',
                         {'material': MAT,
                          'material_property': 'MP_BaseColor'}))['returnValue']
lerp = cur['expression']
print('base colour driven by', lerp['refPath'].split(':')[-1])
if not wire(alpha, lerp, 'Alpha'):
    raise SystemExit('could not rewire Alpha')

ue.tool(M, 'layout_expressions', {'material_or_function': MAT})
print('recompile', ue.tool(M, 'recompile', {'material_or_function': MAT})[:50])
ue.tool(AS, 'save_assets',
        {'asset_paths': ['/Game/Stacktown/Materials/M_StacktownMaster']})
print('saved')
