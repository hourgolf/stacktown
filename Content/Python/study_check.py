import unreal
mel = unreal.MaterialEditingLibrary
for n in ('MI_st0_base', 'MI_st1_darker', 'MI_st2_paper', 'MI_st3_coarse',
          'MI_st4_seams', 'MI_st5_wear'):
    mi = unreal.load_asset('/Game/Stacktown/Materials/%s' % n)
    c = mel.get_material_instance_vector_parameter_value(mi, 'BaseColour')
    pt = mel.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
    pn = mel.get_material_instance_scalar_parameter_value(mi, 'PaperNormalAmount')
    sd = mel.get_material_instance_scalar_parameter_value(mi, 'SeamDarken')
    ew = mel.get_material_instance_scalar_parameter_value(mi, 'EdgeWearLift')
    print('%-14s col(%.3f %.3f %.3f)  tile %.3f  norm %.1f  seam %.2f  wear %.2f'
          % (n, c.r, c.g, c.b, pt, pn, sd, ew))
