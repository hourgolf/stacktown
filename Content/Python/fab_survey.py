"""Measure a representative donor sample: size, triangles, material slots.

The studio-director skill's warning is the reason this is measured rather
than browsed: "Photoreal donor assets dropped next to flat-shaded ones.
Detail tier must match, and it must match at the FABRICATION tier."

Our own parts run ~44 triangles a box and a whole building is ~28,000. A prop
carrying 5,000 triangles is not a prop at this tier, it is a hero asset that
will make everything beside it look unfinished.
"""
import unreal

SAMPLE = [
    ('Mega_Street_Props_Pack/Street_Props_Pack_V1/Mesh',
     ['SM_Flower_Pot', 'SM_Flower_Pot_4', 'SM_Flower_Pot_7', 'SM_Bench',
      'SM_Bench_2', 'SM_Lamp', 'SM_Trash_Can', 'SM_Bicycle_01']),
    ('AssetsvilleTown/Meshes', ['SM_Plant_01', 'SM_Plant_02', 'SM_bush_01',
                                'SM_tree_01', 'SM_tree_03', 'SM_tree_04']),
    ('Deko_MatrixDemo/City/Meshes', ['SM_BLDG_Prop_BA_Awning_A01_N1',
                                     'SM_BLDG_Prop_BA_Sign_A01_N1',
                                     'SM_BLDG_Prop_BA_Banner_A01_N1',
                                     'SM_BLDG_Prop_Lamp_Wall_A01_N1',
                                     'SM_BLDG_Prop_AC_Window_A01_N1',
                                     'SM_BLDG_Prop_Clock_Corner_A01_N1']),
]
eal = unreal.EditorAssetLibrary
print('%-34s %7s %7s %6s %5s  %s'
      % ('mesh', 'w', 'h', 'tris', 'slots', 'verdict'))
for folder, names in SAMPLE:
    for n in names:
        found = None
        for root in ('/Game/%s' % folder,):
            for p in eal.list_assets(root, recursive=True, include_folder=False):
                if p.split('/')[-1].split('.')[0] == n:
                    found = p
                    break
            if found:
                break
        if not found:
            print('%-34s  (not found)' % n)
            continue
        sm = eal.load_asset(found)
        if not sm:
            continue
        e = sm.get_bounds().box_extent
        tri = sm.get_num_triangles(0)
        slots = len(sm.get_editor_property('static_materials'))
        # our own tier: ~44 tris per part, a whole building ~28,000
        v = 'fits' if tri <= 900 else ('heavy' if tri <= 3000 else 'HERO TIER')
        print('%-34s %7.0f %7.0f %6d %5d  %s'
              % (n[:34], e.x*2, e.z*2, tri, slots, v))
