"""Leaf-card instances of the masked master.

Wear is switched OFF (EdgeWearLift 1.0) rather than left at 1.42. The wear term
now reads VertexColor.R, and these tree meshes are licensed donor content that
has NOT been curvature-baked - SM_tree_01 carries (1,1,1) and SM_tree_03
carries (1,0,0). Both happen to have R=1, so wear would be zero anyway, but
"happens to be safe" is not a reason to leave a term reading a channel the pack
authored for its own purposes. Turn it off explicitly.

Seams are off too (SeamDarken 1.0). The seam chain draws fabrication lines at
SeamSpacing in world X; on a leaf card that is an architectural feature landing
on the wrong object.
"""
import unreal

MASTER = '/Game/Stacktown/Materials/M_StacktownMaster_Masked'
LEAVES = [
    ('MI_leaf_card',   '/Game/AssetsvilleTown/Textures/Foliage/T_leaf_01a', (0.300, 0.420, 0.215)),
    ('MI_leaf_card_b', '/Game/AssetsvilleTown/Textures/Foliage/T_leaf_02',  (0.335, 0.445, 0.230)),
]
CARD = {'RoughMin':0.62,'RoughMax':0.80,'Metallic':0.0,'Specular':0.20,
        'PaperTiling':0.05,'PaperNormalAmount':2.0,
        'EdgeWearLift':1.0,'EdgeWearWidth':0.30,'SeamDarken':1.0}

tools = unreal.AssetToolsHelpers.get_asset_tools()
master = unreal.load_asset(MASTER)
for name, tex, col in LEAVES:
    path = '/Game/Stacktown/Materials/%s' % name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = tools.create_asset(name, '/Game/Stacktown/Materials',
                                unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, master)
    for k, v in CARD.items():
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, k, v)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    t = unreal.load_asset(tex)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, 'LeafMask', t)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    got = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, 'LeafMask')
    print('%-16s parent=%s  LeafMask=%s  BaseColour=(%.3f %.3f %.3f)' % (
        name, mi.get_editor_property('parent').get_name(),
        got.get_name() if got else 'NONE', col[0], col[1], col[2]))
