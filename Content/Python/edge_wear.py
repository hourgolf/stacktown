"""Edge wear — the last MASTER_MATERIAL_SPEC feature never built.

Spec: "Edge wear width ~2 mm world. Curvature-driven lightening. Reads as a
brush edge." There is no curvature data on these meshes (no vertex colour, no
baked maps), which is why it was skipped.

But the geometry is entirely axis-aligned boxes with 45 degree chamfer facets.
So the world normal IS a curvature proxy:
    flat face   -> one component is 1.0, max(|n|) = 1.0
    chamfer     -> two components ~0.707, max(|n|) ~0.707
    corner tri  -> three components ~0.577

wear = saturate((1 - max(|n|)) / 0.30) gives 0 on flat faces and ~1 on every
chamfer and corner. Lightening the albedo there reads as a cut card edge where
the fibre has been crushed and lifted.

Pin names are discovered rather than assumed - ComponentMask's input is unnamed
and reports as "None", and guessing it silently produced a broken material and
a scene of muddy brown default-material surfaces.
"""
import ue, json

M = 'editor_toolset.toolsets.material.MaterialTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
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
        print('   warn', list(vals), r[:100])


def pins(e):
    return json.loads(ue.tool(M, 'get_expression_input_names', {'expression': e}))['returnValue']


def wire(frm, to, pin=None, out=''):
    """Connect, discovering the pin name when not given."""
    names = pins(to)
    cands = [pin] if pin else (names or [''])
    for p in cands:
        r = ue.tool(M, 'connect_expressions',
                    {'from_expression': frm, 'from_output_name': out,
                     'to_expression': to, 'to_input_name': p})
        if 'ERROR' not in r and 'TOOL-ERROR' not in r:
            return True
    print('   FAILED wire into', names)
    return False


def single(cls, src, out=''):
    """Add a one-input node and connect src into whatever its input is called."""
    n = addx(cls)
    wire(src, n, pins(n)[0] if pins(n) else '', out)
    return n


E = '/Script/Engine.MaterialExpression'

nrm = addx(E + 'PixelNormalWS')
a = single(E + 'Abs', nrm)

comps = []
for r, g, b in ((True, False, False), (False, True, False), (False, False, True)):
    m = addx(E + 'ComponentMask')
    setp(m, {'R': r, 'G': g, 'B': b, 'A': False})
    wire(a, m, pins(m)[0])
    comps.append(m)

mx1 = addx(E + 'Max'); wire(comps[0], mx1, 'A'); wire(comps[1], mx1, 'B')
mx2 = addx(E + 'Max'); wire(mx1, mx2, 'A'); wire(comps[2], mx2, 'B')

inv = single(E + 'OneMinus', mx2)
width = addx(E + 'ScalarParameter')
setp(width, {'ParameterName': 'EdgeWearWidth', 'DefaultValue': 0.30})
div = addx(E + 'Divide'); wire(inv, div, 'A'); wire(width, div, 'B')
sat = single(E + 'Saturate', div)

# find the BaseColour parameter already feeding MP_BaseColor
exprs = json.loads(ue.tool(M, 'get_expressions', {'material_or_function': MAT}))['returnValue']
base = None
for e in exprs:
    if 'VectorParameter' in e['refPath']:
        base = e
        break
if not base:
    raise SystemExit('BaseColour parameter not found')

amt = addx(E + 'ScalarParameter')
setp(amt, {'ParameterName': 'EdgeWearLift', 'DefaultValue': 1.42})
lift = addx(E + 'Multiply'); wire(base, lift, 'A'); wire(amt, lift, 'B')

lerp = addx(E + 'LinearInterpolate')
wire(base, lerp, 'A')
wire(lift, lerp, 'B')
wire(sat, lerp, 'Alpha')

print('base colour ->', ue.tool(M, 'connect_to_output',
      {'expression': lerp, 'output_name': '', 'material_property': 'MP_BaseColor'})[:60])

ue.tool(M, 'layout_expressions', {'material_or_function': MAT})
ue.tool(M, 'recompile', {'material_or_function': MAT})
ue.tool(AS, 'save_assets', {'asset_paths': ['/Game/Stacktown/Materials/M_StacktownMaster']})
print('recompiled and saved')
