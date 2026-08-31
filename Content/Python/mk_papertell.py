"""Study panels for the paper-tell, cold read #1's named player-zoom cause.

PROTOCOL, inherited from mk_study.py: one baseline, one term moved per panel,
so whatever the capture shows can be attributed. Anything else is N new looks
and no information.

WHAT THE EARLIER STUDY DOES NOT SETTLE. Round 1 of mk_study found PaperTiling
was the only term that moved the render AT BUILDING DISTANCE - everything
else fell under the noise. The reader failed us at PLAYER ZOOM, which that
study never tested, so none of that result carries over. It only tells us
which lever moved at one distance.

GROUP C - grain SCALE (hypothesis c). A pure tiling sweep, genuinely one
variable. The UV is worldPos * PaperTiling, so 0.006 is about one tile per
167 uu: 1.7 m of wall per tile of paper fibre at 1:87. That arithmetic is the
reason to suspect the close read turns tooth into wallpaper.

GROUP A - fabrication FAMILY (hypothesis a). NOT one variable, and labelled
so: a family is a bundle of tooth, amount and roughness, and swapping one
term of it would not be a family. These are candidates to LOOK at, in the
same sense mk_study's panel 5 was, with the difference that the baseline
panel here is not hypothetical - MI_card_rose_2S is what the cold reader
actually saw on the vehicles, and it carries byte-identical paper parameters
to a building wall.

No new master. No new stock in fabrication.py either: declaring a 'diecast'
stock before the study runs would be deciding the answer and then measuring
it. These set parameters on instances; the vocabulary changes only if the
frames earn it.
"""
import unreal

MATS = '/Game/Stacktown/Materials'
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

# (name, source, {scalar overrides}, note)
PANELS = [
    # --- GROUP C: one variable, PaperTiling, off the wall baseline ---------
    ('MI_pt_c0_t006', 'MI_paint_cream', {'PaperTiling': 0.006}, 'C baseline, card_heavy as shipped'),
    ('MI_pt_c1_t012', 'MI_paint_cream', {'PaperTiling': 0.012}, 'C 2x finer'),
    ('MI_pt_c2_t025', 'MI_paint_cream', {'PaperTiling': 0.025}, 'C 4x finer'),
    ('MI_pt_c3_t050', 'MI_paint_cream', {'PaperTiling': 0.050}, 'C 8x finer'),
    # --- GROUP A: family swaps on the 2S master the vehicles wear ----------
    ('MI_pt_a0_card', 'MI_card_rose_2S',
     {'PaperTiling': 0.006, 'PaperNormalAmount': 2.0, 'RoughMin': 0.62,
      'RoughMax': 0.80, 'Metallic': 0.0}, 'A as the reader saw it: card_heavy'),
    ('MI_pt_a1_resin', 'MI_card_rose_2S',
     {'PaperTiling': 0.030, 'PaperNormalAmount': 0.5, 'RoughMin': 0.38,
      'RoughMax': 0.52, 'Metallic': 0.0}, 'A cast resin, a stock we already have'),
    ('MI_pt_a2_diecast', 'MI_card_rose_2S',
     {'PaperTiling': 0.000, 'PaperNormalAmount': 0.0, 'RoughMin': 0.22,
      'RoughMax': 0.34, 'Metallic': 0.35}, 'A no tooth, glossier, part-metallic'),
    ('MI_pt_a3_wire', 'MI_card_rose_2S',
     {'PaperTiling': 0.000, 'PaperNormalAmount': 0.0, 'RoughMin': 0.28,
      'RoughMax': 0.42, 'Metallic': 0.60}, 'A drawn metal, the far end of the range'),
]


def build():
    made = []
    for name, src, scal, note in PANELS:
        dst = '%s/%s' % (MATS, name)
        if EAL.does_asset_exist(dst):
            EAL.delete_asset(dst)
        if not EAL.duplicate_asset('%s/%s' % (MATS, src), dst):
            raise SystemExit('could not duplicate %s' % src)
        mi = unreal.load_asset(dst)
        for k, v in scal.items():
            mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
        EAL.save_asset(dst)
        made.append((name, src, scal, note))
    return made


def verify():
    """READ BACK what the editor holds. A study whose panels are not the
    values it claims measures nothing, and set_..._parameter_value returns
    None whether or not the parameter exists on the parent."""
    bad = []
    for name, src, scal, note in PANELS:
        mi = unreal.load_asset('%s/%s' % (MATS, name))
        if not mi:
            bad.append((name, 'MISSING')); continue
        got = {}
        for k, want in scal.items():
            got[k] = mel.get_material_instance_scalar_parameter_value(mi, k)
            if abs(got[k] - float(want)) > 1e-4:
                bad.append((name, '%s wanted %.3f got %.3f' % (k, want, got[k])))
        print('  %-18s %-16s %s   %s'
              % (name, src, ' '.join('%s=%.3f' % (k, got[k]) for k in sorted(got)), note))
    return bad


if __name__ == '__main__':
    build()
    print('PANELS BUILT, reading back from the editor:')
    bad = verify()
    if bad:
        print('MISMATCH - study is NOT usable:')
        for n, w in bad:
            print('   %s %s' % (n, w))
    else:
        print('all %d panels verified against the editor' % len(PANELS))
