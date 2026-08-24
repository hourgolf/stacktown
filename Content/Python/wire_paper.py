"""Wire the paper textures into M_StacktownMaster.

The meshes carry no UVs (the chamfered OBJs were authored without them), so the
textures are projected from WORLD POSITION instead - masked to X and Z, which is
the correct plane for the facade, the dominant visible surface.

Tiling: one 512 px tile per 20 uu (200 mm) gives ~0.39 mm per texel, matching
MASTER_MATERIAL_SPEC's "~0.5 mm micro-normal feature size".

The roughness alpha moves from the old procedural Noise node - which varied over
~1 cm and simply averaged to flat at any real viewing distance - to the paper
detail map, so roughness now varies at paper scale.
"""
import ue, json

M = 'editor_toolset.toolsets.material.MaterialTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
MAT = {'refPath': '/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster'}
TEX = '/Game/Stacktown/Textures'


def addx(cls):
    r = ue.tool(M, 'add_expression',
                {'material_or_function': MAT, 'expression_class': {'refPath': cls}})
    if 'ERROR' in r:
        raise SystemExit('add_expression failed: ' + r[:160])
    return json.loads(r)['returnValue']


def setp(ref, vals):
    r = ue.tool(O, 'set_properties', {'instance': ref, 'values': json.dumps(vals)})
    if '"returnValue":true' not in r:
        print('   warn set', list(vals), r[:120])


def wire(frm, to, pin, out=''):
    r = ue.tool(M, 'connect_expressions',
                {'from_expression': frm, 'from_output_name': out,
                 'to_expression': to, 'to_input_name': pin})
    return 'ERROR' not in r


# --- world-aligned UVs: WorldPosition.XZ * (1/20) ---
wp = addx('/Script/Engine.MaterialExpressionWorldPosition')
mask = addx('/Script/Engine.MaterialExpressionComponentMask')
setp(mask, {'R': True, 'G': False, 'B': True, 'A': False})
scale = addx('/Script/Engine.MaterialExpressionScalarParameter')
setp(scale, {'ParameterName': 'PaperTiling', 'DefaultValue': 0.05})
mul = addx('/Script/Engine.MaterialExpressionMultiply')
wire(wp, mask, 'Input')
wire(mask, mul, 'A')
wire(scale, mul, 'B')
print('world-aligned UVs built (XZ, 1 tile per 20 uu)')

# --- fibre normal ---
nrm = addx('/Script/Engine.MaterialExpressionTextureSampleParameter2D')
setp(nrm, {'ParameterName': 'PaperNormal',
           'Texture': {'refPath': '%s/T_PaperNormal.T_PaperNormal' % TEX},
           'SamplerType': 'SAMPLERTYPE_Normal'})
wire(mul, nrm, 'UVs')

# keep the fibre subtle - spec says intensity 0.05-0.10
flat = addx('/Script/Engine.MaterialExpressionConstant3Vector')
setp(flat, {'Constant': {'r': 0.0, 'g': 0.0, 'b': 1.0}})
amt = addx('/Script/Engine.MaterialExpressionScalarParameter')
setp(amt, {'ParameterName': 'PaperNormalAmount', 'DefaultValue': 0.55})
nlerp = addx('/Script/Engine.MaterialExpressionLinearInterpolate')
wire(flat, nlerp, 'A')
wire(nrm, nlerp, 'B')
wire(amt, nlerp, 'Alpha')
print('normal chain built')

# --- roughness detail replaces the old world-scale Noise alpha ---
det = addx('/Script/Engine.MaterialExpressionTextureSampleParameter2D')
setp(det, {'ParameterName': 'PaperDetail',
           'Texture': {'refPath': '%s/T_PaperDetail.T_PaperDetail' % TEX},
           'SamplerType': 'SAMPLERTYPE_LinearGrayscale'})
wire(mul, det, 'UVs')

# find the existing roughness Lerp and repoint its Alpha
exprs = json.loads(ue.tool(M, 'get_expressions', {'material_or_function': MAT}))['returnValue']
lerps = [e for e in exprs if 'LinearInterpolate' in e['refPath']]
target = None
for e in lerps:
    if e['refPath'] != nlerp['refPath']:
        target = e
        break
if target:
    ue.tool(M, 'disconnect_expressions',
            {'to_expression': target, 'to_input_name': 'Alpha'})
    wire(det, target, 'Alpha')
    print('roughness alpha repointed to PaperDetail')
else:
    print('WARNING: roughness Lerp not found')

print('normal ->', ue.tool(M, 'connect_to_output',
      {'expression': nlerp, 'output_name': '', 'material_property': 'MP_Normal'})[:60])

ue.tool(M, 'layout_expressions', {'material_or_function': MAT})
ue.tool(M, 'recompile', {'material_or_function': MAT})
ue.tool(AS, 'save_assets', {'asset_paths': ['/Game/Stacktown/Materials/M_StacktownMaster']})
print('master material recompiled and saved')
