"""Verify every admitted FAB map carries the import settings its stock needs.

WHY THIS IS NOT PARANOIA. Content/Uniblocks/ is gitignored. Every admitted
texture therefore lives OUTSIDE version control, and its import settings are
local machine state that a fresh clone does not inherit. The owner caught
brick rendering inverted - faces recessed, mortar proud - and the fix was
flip_green_channel on the TEXTURE. That flag is not in the repo. On another
machine the brick comes back backwards.

And nothing in the acceptance test would catch it: an inverted normal carries
exactly the same amount of high-frequency detail as a correct one, so the
detail metric reads identically (measured: 2.39 far / 1.24 near either way).
It was found by eye and it can only be re-found by eye - unless this runs.

Run after any fresh clone, any pack re-download, and before any survey.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import fabrication as F
importlib.reload(F)     # the editor caches modules for the whole session


def main():
    reqs = F.texture_requirements()
    if not reqs:
        print('no admitted map states requirements'); return
    bad = []
    for path, needs in reqs:
        t = unreal.load_asset(path)
        if not t:
            bad.append((path, 'MISSING - the pack may not be installed'))
            print('  %-46s MISSING' % path.split('/')[-1])
            continue
        line = []
        for k, want in sorted(needs.items()):
            got = t.get_editor_property(k)
            ok = bool(got) == bool(want) if isinstance(want, bool) else got == want
            line.append('%s=%s%s' % (k, got, '' if ok else ' WANT %s' % want))
            if not ok:
                bad.append((path.split('/')[-1], '%s is %s, needs %s' % (k, got, want)))
        print('  %-34s %s' % (t.get_name(), '  '.join(line)))
    if bad:
        print('\nTEXTURE REQUIREMENTS NOT MET:')
        for n, why in bad:
            print('   %s: %s' % (n, why))
        print('\nThese assets are gitignored, so this is expected on a fresh '
              'clone.\nFix with the settings above, then re-run.')
        raise SystemExit(1)
    print('\nall admitted maps carry the settings their stock requires')


if __name__ == '__main__':
    main()
