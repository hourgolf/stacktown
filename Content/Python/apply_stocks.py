"""Push every stock's properties onto the material instances that name it.

THIS IS WHAT MAKES THE STOCK TABLE REAL. fabrication.py has always been the
single source for tooth, amount and roughness, but nothing pushed it: the
values reached materials only when a bake or step_roles happened to write
them. With the card_heavy split the table now also carries a NORMAL MAP per
stock, and the whole point of the split is that a brick pier and a skimmed
wall stop being the same photograph. So this walks MATERIAL_STOCK and writes
the stock's properties to each instance.

SCALARS AND TEXTURES TAKE DIFFERENT SETTERS, which is why params_for emits
only scalars and normal_for is separate - folding a texture into the scalar
dict would have broken every existing caller silently.

VERIFIES BY READ-BACK and refuses to report success on a mismatch. Writes the
prior values to Saved/stocks_restore.json so the whole pass is reversible.
"""
import json, os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import fabrication as F
# THE EDITOR CACHES MODULES FOR THE WHOLE SESSION. fabrication was imported
# hours ago by another script, so without this the split simply is not there
# and normal_for raises AttributeError - or worse, silently returns the old
# table's values and writes a stale look while reporting success.
importlib.reload(F)

MATS = '/Game/Stacktown/Materials'
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary


def instances():
    """Every MI under the Stacktown material folder, longest-prefix matched by
    fabrication itself - so this cannot disagree with the resolver."""
    out = []
    for p in unreal.EditorAssetLibrary.list_assets(MATS, recursive=False):
        n = p.split('/')[-1].split('.')[0]
        if not n.startswith('MI_'):
            continue
        a = unreal.load_asset(p.split('.')[0])
        if isinstance(a, unreal.MaterialInstanceConstant):
            out.append((n, a))
    return sorted(out)


def main():
    restore, changed = {}, 0
    for name, mi in instances():
        stock = F.stock_for(name)
        want = F.params_for(name)
        tex = F.normal_for(name)
        prev = {k: mel.get_material_instance_scalar_parameter_value(mi, k)
                for k in want}
        pt = mel.get_material_instance_texture_parameter_value(mi, 'PaperNormal')
        prev['PaperNormal'] = pt.get_path_name() if pt else None
        restore[name] = prev
        for k, v in want.items():
            mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
        if tex:
            t = unreal.load_asset(tex)
            if not t:
                raise SystemExit('%s names a missing map: %s' % (stock, tex))
            mel.set_material_instance_texture_parameter_value(mi, 'PaperNormal', t)
        EAL.save_asset('%s/%s' % (MATS, name))
        bad = [k for k, v in want.items()
               if abs(mel.get_material_instance_scalar_parameter_value(mi, k) - v) > 1e-6]
        if tex:
            g = mel.get_material_instance_texture_parameter_value(mi, 'PaperNormal')
            if not g or tex.split('/')[-1] not in g.get_name():
                bad.append('PaperNormal')
        if bad:
            raise SystemExit('%s did not take: %s' % (name, bad))
        changed += 1
        print('  %-20s %-14s tile %.4f amt %.1f  %s'
              % (name, stock, want['PaperTiling'], want['PaperNormalAmount'],
                 tex.split('/')[-1] if tex else 'T_PaperNormal'))
    # WRITE-ONCE. The first version overwrote this every run, so the second
    # apply (an amplitude tweak) replaced the pre-split values with the
    # intermediate ones and quietly destroyed the only route back to the
    # original look. A restore file that a re-run can clobber is not a
    # restore file - the FIRST capture is the one worth keeping.
    p = os.path.join(unreal.Paths.project_dir(), 'Saved', 'stocks_restore.json')
    if os.path.exists(p):
        print('  restore data already on disk from an earlier run - KEPT.')
        print('  (it holds the pre-split values; this run did not overwrite it)')
    else:
        with open(p, 'w') as f:
            json.dump(restore, f, indent=1, sort_keys=True)
        print('  restore data written to %s' % p)
    print('APPLIED %d material instances from the stock table' % changed)


if __name__ == '__main__':
    main()
