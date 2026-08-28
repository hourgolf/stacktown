"""Copy an admitted map into tracked content, with its settings baked in.

WHY THIS EXISTS. Content/Uniblocks/ is gitignored, so an admitted map's import
settings are local machine state. The owner caught brick rendering inverted;
the fix was flip_green_channel on the TEXTURE, and it could not be committed
because the asset could not be. On a fresh clone the pack returns with its own
defaults and the wall renders backwards again, silently, passing every number.

THE CARVE-OUT IS NARROW AND EVIDENCE-BOUND. Donor packs are never committed.
The single exception is a map whose CC0 provenance is established, and the
evidence used here is the pack's OWN segregation: Uniblocks keeps its Poly
Haven material in a folder named PolyHaven_CC0 (56 textures) separate from
the other 77 at the Textures root. A map inside that folder carries the pack
author's own CC0 assertion. A map outside it does not, and this script
REFUSES to copy one - the Fab listing says the set draws on Poly Haven for
SOME textures, and outside-the-folder is evidence against, not merely absence
of evidence for.

Everything else stays pack-resident under check_textures.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import fabrication as F
importlib.reload(F)

DEST = '/Game/Stacktown/Textures'
MARK = 'PolyHaven_CC0'


def main():
    EAL = unreal.EditorAssetLibrary
    copied, refused = [], []
    for path, needs in F.texture_requirements():
        name = path.split('/')[-1]
        if MARK not in path:
            refused.append((name, 'not in the pack\'s own %s folder' % MARK))
            continue
        src = unreal.load_asset(path)
        if not src:
            refused.append((name, 'asset missing - pack not installed?')); continue
        dst = '%s/%s' % (DEST, name)
        if EAL.does_asset_exist(dst):
            EAL.delete_asset(dst)
        if not EAL.duplicate_asset(path, dst):
            refused.append((name, 'duplicate failed')); continue
        t = unreal.load_asset(dst)
        for k, v in needs.items():
            t.set_editor_property(k, v)
        EAL.save_asset(dst)
        bad = [k for k, v in needs.items()
               if bool(t.get_editor_property(k)) != bool(v)]
        if bad:
            raise SystemExit('%s: settings did not bake: %s' % (name, bad))
        copied.append((name, dst, needs))
        print('  COPIED %-24s -> %s   %s' % (name, dst,
              ' '.join('%s=%s' % (k, v) for k, v in sorted(needs.items()))))
    for n, why in refused:
        print('  REFUSED %-23s %s' % (n, why))
    print('\n%d copied into tracked content, %d left pack-resident'
          % (len(copied), len(refused)))
    if copied:
        print('Point the stock at the tracked path and re-run check_textures.')


if __name__ == '__main__':
    main()
