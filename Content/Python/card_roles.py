"""Three more card colours for the block.

Desaturated on purpose. The recipe's trap is large-scale albedo variation: a
block wants VARIETY between buildings, not saturation within one. All three sit
in the card band - roughness 0.62-0.80, specular 0.20 - so they differ in hue
and never in material.
"""
import unreal
L=unreal.MaterialEditingLibrary
F='/Game/Stacktown/Materials'
master=unreal.EditorAssetLibrary.load_asset(F+'/M_StacktownMaster.M_StacktownMaster')
at=unreal.AssetToolsHelpers.get_asset_tools()
CARD={'RoughMin':0.62,'RoughMax':0.80,'Metallic':0.0,'Specular':0.20,'Opacity':1.0,
      'PaperTiling':0.05,'PaperNormalAmount':0.55,'EdgeWearWidth':0.30,
      'EdgeWearLift':1.42,'SeamSpacing':380.0,'SeamWidth':6.0,'SeamDarken':0.88}
COLS={'MI_card_ochre':(0.700,0.598,0.442),
      'MI_card_sage' :(0.600,0.638,0.548),
      'MI_card_rose' :(0.742,0.622,0.578)}
for n,c in COLS.items():
    p='%s/%s'%(F,n)
    mi=(unreal.EditorAssetLibrary.load_asset(p+'.'+n)
        if unreal.EditorAssetLibrary.does_asset_exist(p)
        else at.create_asset(n,F,unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew()))
    L.set_material_instance_parent(mi,master)
    L.set_material_instance_vector_parameter_value(mi,'BaseColour',
        unreal.LinearColor(c[0],c[1],c[2],1.0))
    for k,v in CARD.items():
        L.set_material_instance_scalar_parameter_value(mi,k,v)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%-16s %.3f %.3f %.3f'%(n,c[0],c[1],c[2]))
