"""Populate DA_Catalogue_Wood's mesh references from woodmap.py - rerunnable.

Phase F pulled forward (owner's direct word, 2026-09-01: "flagship is a
totally different game skin, it shouldn't be here"). This is the wood
mirror of mk_da_catalogue.py, not a fresh design: same key format
("{rid}_{tier}_{width}" plain, "{rid}_{tier}_{width}_{corner}" corner,
corner is "L"/"R", width is INTEGER-rounded), same testcity_pins.PINS
-driven population, same full-recipe-tier-range coverage, same
clear-then-set/read-back-verify/save discipline. mk_da_catalogue.py's own
docstring already declared this format "BINDING ON THE FUTURE WOODEN
CATALOGUE TOO" the same day it was written, so this script inherits it
knowingly rather than re-deriving it.

WHAT'S DIFFERENT FROM THE FLAGSHIP SCRIPT: only the mesh-resolution step.
Growth eligibility (econrules.tier_up_allowed) checks FLAGSHIP asset
existence on disk, completely independent of ActiveCatalogue - the
pointer swap doesn't change how far a parcel can grow. So this script
walks the IDENTICAL (rid, tier, width, corner) key space
mk_da_catalogue.py already proved reachable, and asks woodmap.resolve()
for the wood asset at each key instead of recipes.asset_name() for the
flagship one. Two lookups can legitimately produce the SAME wood asset
for different keys (woodmap collapses tiers into 4 bands, and collapses
L/R corner into one depth-only block, on purpose, per its own
docstring) - that is not a bug here, it is the coarse-mapping-first
design speed pass asked for.

CORNER IN WOOD IS DEPTH, NOT HANDEDNESS - but the KEY still carries L/R,
because BP_Parcel's ResolveMesh looks up CornerSide regardless of which
catalogue is active. Both letters resolve to the same wood asset at a
given (rid, tier, width); that is correct, not a missed distinction.

WOOD_BAKED confirmed by the coordinator 2026-09-01: /Game/Stacktown/BakedWood,
no subfolder, the 36 new SM_WMass_* names verified collision-free against
the folder's 31 existing look-study assets. That folder mixes shipped
catalogue meshes with disposable rig output (prefix-distinguished only) -
see build_rows()'s `have` construction for why that's safe to populate
from anyway. A wrong folder or an unbaked name still fails LOUD (missing,
skipped, reported - never guessed), matching testcity_pins.require() and
mk_da_catalogue.py's own doctrine.

Runs LOCALLY over MCP (import ue) - never via remote exec, same reason
mk_da_catalogue.py gives: an MCP call from inside a rung.sh-injected
script deadlocks (HANDOFF.md Sec5).
"""
import json

import _path  # noqa: F401
import citylayout as L
import testcity_pins
import woodmap
import ue

RT = '/Game/Stacktown/Runtime'
CATALOGUE_PATH = '%s/DA_Catalogue_Wood' % RT
CATALOGUE_REF = '%s.DA_Catalogue_Wood' % CATALOGUE_PATH
WOOD_BAKED = '/Game/Stacktown/BakedWood'  # PROVISIONAL - confirm before trusting a run
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
ASSET = 'editor_toolset.toolsets.asset.AssetTools'

_SIDE_LETTER = {'left': 'L', 'right': 'R'}


def call(toolset, name, args):
    """ue.tool() returns the raw MCP text content, which is the tool's
    JSON-serialised output ({"returnValue": ...}) as a string - unwrap it."""
    raw = ue.tool(toolset, name, args)
    return json.loads(raw)['returnValue']


def asset_ref(name):
    return '%s/%s.%s' % (WOOD_BAKED, name, name)


def _corner_letters():
    """{lot_key: 'L'/'R'/None} - None for non-corner lots. Same derivation
    mk_da_catalogue.py uses, from the layout itself, not stored twice."""
    out = {}
    for bname in sorted(L.blocks()):
        _end, turn_side = L.cross_street_end(bname)
        letter = _SIDE_LETTER[turn_side]
        for key, _x0, _x1, corner in L.lots(bname):
            out[key] = letter if corner else None
    return out


def build_rows():
    # Ground truth for WHICH NAMES ARE VALID is woodmap.catalogue() itself,
    # never a reconstructed pattern - the wood lane's own binding
    # instruction, so a future ladder change reaches this script without an
    # edit. WOOD_BAKED mixes shipped catalogue meshes with disposable rig
    # output (same folder, prefix-distinguished only, per the wood lane) -
    # intersecting with catalogue()'s 36 names is what keeps this script
    # from ever treating disposable output as a resolvable asset.
    on_disk = set()
    for a in call(ASSET, 'find_assets',
                  {'folder_path': WOOD_BAKED, 'name': '', 'recursive': False}):
        on_disk.add(a.split('.')[0].rsplit('/', 1)[-1])
    have = on_disk & set(woodmap.catalogue())

    letters = _corner_letters()
    ids, tiers, widths, names, mesh_refs = [], [], [], [], []
    key_map = {}
    missing = []
    seen = set()   # (rid, t, w, side) - two pins can share a (rid, w) pair;
                   # don't add the same signature twice
    for lot_key, p in sorted(testcity_pins.PINS.items()):
        rid, w = p['rid'], float(p['w'])
        side = letters[lot_key] if p['corner'] else None
        # SAME tier range mk_da_catalogue.py proved reachable for this
        # recipe - see module docstring on why that range doesn't change
        # with the active catalogue.
        for t in range(7):
            sig = (rid, t, w, side)
            if sig in seen:
                continue
            seen.add(sig)
            try:
                r = woodmap.resolve(rid, t, w,
                                     corner={'L': 'left', 'R': 'right'}.get(side))
            except (KeyError, ValueError) as e:
                missing.append('%s t%d w%d%s: %s' % (rid, t, int(w),
                                                       ('_' + side) if side else '',
                                                       e))
                continue
            name = r['asset']
            if name not in have:
                missing.append(name)
                continue
            key = '%s_%d_%d' % (rid, t, round(w))
            if side:
                key = '%s_%s' % (key, side)
            ids.append(rid)
            tiers.append(t)
            widths.append(w)
            names.append('%s %s' % (r['species'], r['band']))
            mesh_refs.append(asset_ref(name))
            key_map[key] = asset_ref(name)
    return ids, tiers, widths, names, mesh_refs, key_map, missing


def main():
    ids, tiers, widths, names, mesh_refs, key_map, missing = build_rows()
    if missing:
        print('  not on disk / not resolvable, skipped: %s'
              % ', '.join(sorted(set(missing))))
    if not ids:
        print('  NOTHING TO WRITE - is WOOD_BAKED (%s) wrong, or is nothing '
              'baked there yet?' % WOOD_BAKED)
        return

    # CLEAR FIRST, THEN SET - same reshape-ambiguity reason mk_da_catalogue.py
    # documents: set_properties can't diff an old key set against a new one
    # when both size and keys change in the same call.
    empty = json.dumps({
        'RecipeIds': [], 'Tiers': [], 'Widths': [],
        'TierNames': [], 'Meshes': [], 'MeshByKey': {},
    })
    ok = call(OBJ, 'set_properties',
              {'instance': {'refPath': CATALOGUE_REF}, 'values': empty})
    assert ok is True, 'set_properties (clear) refused: %s' % ok

    values = json.dumps({
        'RecipeIds': ids, 'Tiers': tiers, 'Widths': widths,
        'TierNames': names, 'Meshes': mesh_refs, 'MeshByKey': key_map,
    })
    ok = call(OBJ, 'set_properties',
              {'instance': {'refPath': CATALOGUE_REF}, 'values': values})
    assert ok is True, 'set_properties refused: %s' % ok

    # READ BACK - state changes prove themselves by read-back, never by
    # printing intent (HANDOFF's rung.sh/wave_throttle.py lesson).
    back = json.loads(call(OBJ, 'get_properties', {
        'instance': {'refPath': CATALOGUE_REF},
        'properties': ['RecipeIds', 'Meshes', 'MeshByKey'],
    }))
    bad_meshes = [m for m in back['Meshes'] if m == 'None']
    bad_keys = [k for k, v in back['MeshByKey'].items() if v == 'None']
    assert not bad_meshes, 'Meshes still None after write: %r' % bad_meshes
    assert not bad_keys, 'MeshByKey still None after write: %r' % bad_keys
    assert len(back['RecipeIds']) == len(ids), \
        'row count mismatch after write: wrote %d, read %d' % (
            len(ids), len(back['RecipeIds']))
    assert len(back['MeshByKey']) == len(key_map), \
        'MeshByKey row count mismatch after write: wrote %d, read %d' % (
            len(key_map), len(back['MeshByKey']))

    saved = call(ASSET, 'save_assets', {'asset_paths': [CATALOGUE_PATH]})
    assert saved is True, 'save_assets refused: %s' % saved

    print('  DA_Catalogue_Wood: %d rows written and verified non-None, saved '
          '(%d distinct lot/tier/width[/corner] keys, %d distinct wood '
          'assets used)'
          % (len(ids), len(key_map), len(set(mesh_refs))))


if __name__ == '__main__':
    main()
