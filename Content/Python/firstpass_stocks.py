"""FIRST PASS: a different micro-relief per stock, so a building stops being
one photograph at seven scales.

THE FINDING THIS ANSWERS. The acceptance building carries 11 material slots
and 7 distinct stocks - brick, timber, shingle, printed trim, metal, glass,
board - and every one of them wears THE SAME normal map, separated only by
tiling number and roughness band. A brick pier and a timber shopfront are
T_PaperNormal at different scales. That is cold read #1's sentence, literally:
"everything has the same 'paper' texture".

A CANDIDATE TO LOOK AT, NOT A MEASUREMENT. Several terms move per material,
so nothing here is attributable - it exists to show the ENSEMBLE, which is the
thing a per-stock change actually risks. Individually good surfaces can still
read as a jumble, and "unified by fabrication" is exactly what guards that.

SCOPE IS THE ADMITTED ONE: normal map and tiling only. No albedo, no colour,
no weathering. The palette, the lamp and the sheen discipline are untouched.

TILING IS DERIVED, NOT INHERITED. The world is 1:1 (this building is 2258 uu
tall), so a brick course is ~7.5 uu. card_heavy's 0.006 puts one texture tile
across 167 uu, which would make a brick course 1.4-2.1 m. Each entry below
sets a tiling from the feature size the texture actually depicts.

REVERSIBLE: writes the prior value of every parameter it touches to
Saved/firstpass_restore.json.
"""
import json, os
import unreal

MATS = '/Game/Stacktown/Materials'
UB = '/Game/Uniblocks/Textures'
PH = '/Game/Uniblocks/Textures/PolyHaven_CC0'
DEKO = '/Game/Deko_MatrixDemo/Shared/Textures'
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

#  material            normal texture                          tiling  why
PASS = [
 ('MI_dist_brick',   '%s/T_UB_brickwork_N' % UB,              0.0133, 'brick: ~10 courses/tile -> 7.5 uu course'),
 ('MI_dist_bone',    '%s/T_UB_plaster_2_N' % PH,              0.0080, 'painted plaster on card'),
 ('MI_dist_forest',  '%s/T_UB_plastered_wall_02_N' % PH,      0.0080, 'a second plaster, so two walls differ'),
 ('MI_concrete',     '%s/T_UB_concrete_1_N' % UB,             0.0100, 'cast concrete'),
 ('MI_wood',         '%s/T_UB_wood_lacquered_N' % UB,         0.0120, 'timber: ~6 boards/tile -> 150 mm board'),
 ('MI_shingle_grey', '%s/T_UB_tile_3_N' % UB,                 0.0150, 'roof tile courses'),
 ('MI_model_board',  '%s/T_Wood_Particle_01_N' % DEKO,        0.0060, 'chipboard is literally particle board'),
]
# untouched and deliberately so: MI_frame_print and MI_canopy_accent stay on
# the paper (they ARE printed card), and wire / brass / acetate carry
# PaperNormalAmount 0, so a normal map on them would render exactly nothing.


def main():
    restore = {}
    done = []
    for name, tex, tiling, why in PASS:
        mp = '%s/%s' % (MATS, name)
        if not EAL.does_asset_exist(mp):
            print('  SKIP %-18s (no such material)' % name); continue
        if not EAL.does_asset_exist(tex):
            print('  SKIP %-18s (missing texture %s)' % (name, tex.split('/')[-1])); continue
        mi = unreal.load_asset(mp)
        prev_t = mel.get_material_instance_texture_parameter_value(mi, 'PaperNormal')
        prev_s = mel.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
        restore[name] = {'PaperNormal': prev_t.get_path_name() if prev_t else None,
                         'PaperTiling': prev_s}
        mel.set_material_instance_texture_parameter_value(
            mi, 'PaperNormal', unreal.load_asset(tex))
        mel.set_material_instance_scalar_parameter_value(mi, 'PaperTiling', tiling)
        EAL.save_asset(mp)
        got_t = mel.get_material_instance_texture_parameter_value(mi, 'PaperNormal')
        got_s = mel.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
        ok = got_t and tex.split('/')[-1] in got_t.get_name() and abs(got_s - tiling) < 1e-6
        print('  %-18s %-32s tile %.4f  %s  %s'
              % (name, got_t.get_name() if got_t else 'NONE', got_s,
                 'ok' if ok else 'MISMATCH', why))
        if not ok:
            raise SystemExit('verify failed on %s' % name)
        done.append(name)
    p = os.path.join(unreal.Paths.project_dir(), 'Saved', 'firstpass_restore.json')
    with open(p, 'w') as f:
        json.dump(restore, f, indent=1, sort_keys=True)
    print('FIRSTPASS applied to %d materials; restore data at %s' % (len(done), p))


if __name__ == '__main__':
    main()
