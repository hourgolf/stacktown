"""The vehicle body materials, cast from resin instead of cut from card.

ONE SOURCE FOR THE NUMBERS. The parameters are not written out here - they
come from fabrication.params_for(), the same resolver step_roles and the
bakes use. Typing 0.030 into a second place is how a stock and the materials
that claim it drift apart, and nothing would notice.

Colour is untouched. The palette was not what the cold reader objected to;
the material was. Each new instance is duplicated from the card material it
replaces, so it keeps that body colour exactly and differs only in stock.
"""
import os, sys
import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fabrication

MATS = '/Game/Stacktown/Materials'
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

# (new, source it inherits its COLOUR from)
PAIRS = [('MI_veh_lift_2S',  'MI_card_lift_2S'),
         ('MI_veh_ochre_2S', 'MI_card_ochre_2S'),
         ('MI_veh_rose_2S',  'MI_card_rose_2S'),
         ('MI_veh_sage_2S',  'MI_card_sage_2S'),
         ('MI_veh_cream_2S', 'MI_paint_cream_2S')]


def build():
    made = []
    for new, src in PAIRS:
        sp, dp = '%s/%s' % (MATS, src), '%s/%s' % (MATS, new)
        if not EAL.does_asset_exist(sp):
            raise SystemExit('source material missing: %s' % sp)
        if EAL.does_asset_exist(dp):
            EAL.delete_asset(dp)
        if not EAL.duplicate_asset(sp, dp):
            raise SystemExit('could not duplicate %s' % sp)
        mi = unreal.load_asset(dp)
        for k, v in fabrication.params_for(new).items():
            mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
        EAL.save_asset(dp)
        made.append(new)
    return made


def verify():
    """Read back from the editor, and check against fabrication rather than
    against the literals this script asked for - so the assertion is that the
    asset and the stock table agree, which is the thing that matters."""
    bad = []
    for new, src in PAIRS:
        mi = unreal.load_asset('%s/%s' % (MATS, new))
        if not mi:
            bad.append((new, 'MISSING')); continue
        want = fabrication.params_for(new)
        got = {k: mel.get_material_instance_scalar_parameter_value(mi, k)
               for k in want}
        for k in want:
            if abs(got[k] - want[k]) > 1e-4:
                bad.append((new, '%s stock says %.3f, asset holds %.3f'
                            % (k, want[k], got[k])))
        c = mel.get_material_instance_vector_parameter_value(mi, 'BaseColour')
        s = mel.get_material_instance_vector_parameter_value(
            unreal.load_asset('%s/%s' % (MATS, src)), 'BaseColour')
        if abs(c.r-s.r) + abs(c.g-s.g) + abs(c.b-s.b) > 1e-4:
            bad.append((new, 'colour drifted from %s' % src))
        print('  %-18s <- %-20s tiling %.3f amount %.1f rough %.2f-%.2f  '
              'colour %.3f %.3f %.3f'
              % (new, src, got['PaperTiling'], got['PaperNormalAmount'],
                 got['RoughMin'], got['RoughMax'], c.r, c.g, c.b))
    return bad


if __name__ == '__main__':
    assert fabrication._selftest()
    build()
    print('VEHICLE MATERIALS, read back from the editor:')
    bad = verify()
    if bad:
        print('MISMATCH:')
        for n, w in bad:
            print('   %s %s' % (n, w))
    else:
        print('all %d verified against fabrication.STOCK["resin"]' % len(PAIRS))
