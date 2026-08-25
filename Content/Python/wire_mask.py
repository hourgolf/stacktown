"""Wire the leaf cut into M_StacktownMaster_Masked's opacity mask.

The cut comes from the donor pack's own leaf texture - that is the one thing
the pack gets right and we have no reason to re-author. Everything the leaf
is MADE of (colour, roughness band, paper fibre, edge wear) comes from the
card master, which is the whole point: the shape is theirs, the fabrication is
ours.

The mask reads the texture's ALPHA. The pack's own M_Plants does the same, and
both leaf textures import with compression_no_alpha=False, so the alpha channel
survives compression.
"""
import matlib as ml, json

PATH = '/Game/Stacktown/Materials/M_StacktownMaster_Masked'
MAT  = ml.mat(PATH + '.M_StacktownMaster_Masked')

existing = ml.find_param(MAT, 'LeafMask', 'TextureSampleParameter2D')
if existing:
    print('LeafMask already present')
    tex = existing
else:
    tex = ml.addx(MAT, ml.E + 'TextureSampleParameter2D')
    ml.setp(tex, {'parameterName': 'LeafMask',
                  'samplerType': 'SAMPLERTYPE_Color',
                  'texture': {'refPath': '/Game/AssetsvilleTown/Textures/Foliage/T_leaf_01a'}})
    print('LeafMask sampler added:', ml.props(tex, ['parameterName','samplerType','texture']))

outs = json.loads(ml.ue.tool(ml.M,'get_expression_output_names',{'expression':tex}))['returnValue']
print('sampler outputs:', outs)
alpha = 'A' if 'A' in outs else outs[-1]
r = ml.ue.tool(ml.M,'connect_to_output',
               {'expression':tex,'output_name':alpha,'material_property':'MP_OpacityMask'})
print('MP_OpacityMask <- %s   %s' % (alpha, r[:60]))
print(ml.finish(MAT, PATH, save=True)[:100])
