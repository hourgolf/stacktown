import unreal
D = '/Game/Deko_MatrixDemo/City/Meshes'
want = ['SM_ShippingContainer_A01_N1','SM_ShippingContainer_B01_N1','SM_ShippingContainer_C01_N1',
        'SM_ShippingContainer_A03_N1','SM_ShippingContainer_B03_N1',
        'SM_Fence_ChainLink_A01_N1','SM_Fence_ChainLink_A02_N1','SM_Fence_ChainLink_A03_N1',
        'SM_Fence_ChainLink_B01_N1','SM_Fence_Post_A01_N1',
        'SM_WoodenPallet_A01_N1','SM_WoodenPallet_B01_N1','SM_WoodenPallet_C01_N1',
        'SM_LumberStack_A01_N1','SM_LumberStack_B01_N1','SM_LumberPile_A02_N1','SM_LumberPile_B01_N1',
        'SM_PlywoodBoards_A01_N1','SM_PlywoodBoards_D01_N1',
        'SM_Scaffolding_A01_N1','SM_Scaffolding_E01_N1','SM_Scaffolding_I01_N1','SM_Scaffolding_L01_N1',
        'SM_Ladder_A01_N1','SM_StandingSignAd_A01_N1','SM_BLDG_Prop_Sign_Parking_A01_N1']
for n in want:
    sm = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (D, n, n))
    if not sm:
        print('%-36s MISSING' % n); continue
    b = sm.get_bounds(); e = b.box_extent; o = b.origin
    slots = [str(s.material_slot_name) for s in sm.get_editor_property('static_materials')]
    print('%-36s size %6.0f x %6.0f x %6.0f  origin z %6.0f  slots %s'
          % (n.replace('SM_','').replace('_N1',''), e.x*2, e.y*2, e.z*2, o.z, slots))
