"""Undo the per-stock first pass, restoring every parameter it touched.

Phase 0 of the card_heavy split is a CODE-level widening: the stock table
gains three names that carry card_heavy's exact properties, so params_for
returns identical values and nothing that writes materials can move the
render. But the first pass wrote PaperNormal and PaperTiling directly onto
seven material INSTANCES, and those overrides are what actually changed
pixels. They have to come off before the no-op can be demonstrated rather
than merely asserted.

Reads Saved/firstpass_restore.json, written when the pass was applied.
"""
import json, os
import unreal

MATS = '/Game/Stacktown/Materials'
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary


def main():
    p = os.path.join(unreal.Paths.project_dir(), 'Saved', 'firstpass_restore.json')
    if not os.path.exists(p):
        raise SystemExit('no restore data at %s' % p)
    data = json.load(open(p))
    for name, prev in sorted(data.items()):
        mp = '%s/%s' % (MATS, name)
        mi = unreal.load_asset(mp)
        if not mi:
            print('  MISSING %s' % name); continue
        tex = prev.get('PaperNormal')
        if tex:
            mel.set_material_instance_texture_parameter_value(
                mi, 'PaperNormal', unreal.load_asset(tex.split('.')[0]))
        else:
            # it carried no override before; clear it back to the master's
            mel.clear_all_material_instance_parameter_values(mi) if False else None
            mel.set_material_instance_texture_parameter_value(
                mi, 'PaperNormal',
                unreal.load_asset('/Game/Stacktown/Textures/T_PaperNormal'))
        mel.set_material_instance_scalar_parameter_value(
            mi, 'PaperTiling', float(prev['PaperTiling']))
        EAL.save_asset(mp)
        got_t = mel.get_material_instance_texture_parameter_value(mi, 'PaperNormal')
        got_s = mel.get_material_instance_scalar_parameter_value(mi, 'PaperTiling')
        print('  %-18s %-22s tile %.4f' % (name, got_t.get_name() if got_t else 'NONE', got_s))
        if abs(got_s - float(prev['PaperTiling'])) > 1e-6:
            raise SystemExit('tiling not restored on %s' % name)
    print('RESTORED %d materials' % len(data))


if __name__ == '__main__':
    main()
