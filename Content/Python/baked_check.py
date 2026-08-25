import unreal
for t in range(3):
    p = '/Game/Stacktown/Baked/SM_Bld_cottage_t%d_w820' % t
    sm = unreal.load_asset(p)
    if not sm:
        print('missing', p); continue
    mats = [m.material_interface.get_name() if m.material_interface else None
            for m in sm.get_editor_property('static_materials')]
    print('t%d  %s' % (t, sorted(set(mats))))
