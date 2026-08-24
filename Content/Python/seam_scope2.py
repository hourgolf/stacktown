import unreal
F='/Game/Stacktown/Materials'
L=unreal.MaterialEditingLibrary
# Strength is now modulated 0.36-1.00 by the second sine, so the darken values
# set the ceiling on the strongest joints, not the value every joint gets.
ON={'MI_concrete':0.86,'MI_paint_cream':0.87,'MI_model_board':0.90}
for n,v in ON.items():
    p='%s/%s'%(F,n)
    mi=unreal.EditorAssetLibrary.load_asset(p+'.'+n)
    L.set_material_instance_scalar_parameter_value(mi,'SeamDarken',v)
    unreal.EditorAssetLibrary.save_asset(p)
print('seam ceiling set:',ON)
