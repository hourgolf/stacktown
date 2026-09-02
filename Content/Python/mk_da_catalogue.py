"""Populate DA_Catalogue's mesh references from real baked assets - rerunnable.

WHY THIS EXISTS: DA_Catalogue declared 6 rows (vernacular t0-t5 @ w1230) with
every StaticMesh reference None - both the Meshes array and MeshByKey, the
field ResolveMesh actually reads - found 2026-08-31 despite every backing
.uasset existing on disk. Same soft-reference-nulling shape as the S17
re-bake trap (HANDOFF.md Sec5, "re-baking nulls every placed actor
reference"), just landing on a DataAsset instead of a placed actor. A
hand-edit fixes it once and rots at the next full-catalogue rebake wave.
This script is the rerunnable fix - meant to run again after any wave that
touches a recipe declared in a pinned lot below, same discipline as the
placers.

KEY FORMAT, EXTENDED 2026-09-01 (owner-approved via the coordinator, part of
the "play from scratch" wave-1 amendment - PARCELIZATION_CONTRACT.md's
Amendment section A0). The original key was "{rid}_{tier}" - no width, no
corner - discovered too narrow the moment more than one recipe/width needed
the catalogue at once (only vernacular@1230 was ever populated; Phase A's
"proven" claim only ever exercised PARCEL_Demo0, which happens to be
vernacular). New key: "{rid}_{tier}_{width}" for a plain lot,
"{rid}_{tier}_{width}_{corner}" for a corner lot - corner is "L" or "R",
matching citylayout.cross_street_end's turn side. width is an
INTEGER-rounded string. THIS MATTERS: WidthUU is a Blueprint Float
(double-precision) - an unrounded ToString would render "1640.000000" and
silently never match this script's "1640" key. ResolveMesh explicitly
Math|Float|Round()s before ToString() for the same reason - both sides of
this key must agree byte-for-byte or the lookup fails silently (Map|Find
returns nothing, SetStaticMesh clears the mesh - looks fine in the log,
wrong only in a screenshot, the exact class of bug this project watches for).

THIS FORMAT IS BINDING ON THE FUTURE WOODEN CATALOGUE TOO (owner's word via
the coordinator, 2026-09-01) - the beta twin's whole premise is one pin
table serving two catalogues through one key space. BETA_TWIN_PLAN records
this beside seam 6 so phase F inherits it knowingly.

POPULATION IS DRIVEN BY testcity_pins.PINS for WHICH (recipe, width,
corner) combinations gameplay needs at all, not a hand-maintained width
table (the old WID dict) - one source of truth instead of a second list
that can drift from it (testcity_pins.py's own docstring on why
identities are pinned, not drawn, is the same principle applied here).

TIER RANGE IS THE RECIPE'S FULL DECLARED RANGE, NOT THE PIN'S DECLARED
TIER - corrected 2026-09-01 after testing the buy verb live caught a real
gap the design missed. First cut of this script populated only
t0-through-each-pin's-declared-tier, reasoning that a fresh purchase
starts at t0 and grows up so nothing further should be reachable in one
short session. Live buy test on NE1 (vernacular8, pin declares t0)
disproved that within seconds: econrules.tick() has no concept of a
pin's declared tier as a ceiling - nothing in the "play from scratch"
redesign asked it to - so NE1 grew itself to tier 1, MeshByKey had no
vernacular8_1_820 entry (SM_Bld_vernacular8_t1_w820 exists on disk, six
tiers of it do, none were catalogued), and ResolveMesh's Map|Find
returned nothing: a real, live-observed instance of "looks fine in the
log, wrong only in a screenshot" - the mesh silently cleared, no crash,
no warning. The pin's declared tier is a massing-design choice for the
pre-built-demo case, never a bound on live growth; the catalogue has to
cover what growth can actually reach, which is the recipe's whole
declared tier range, not a session-scoped guess at it.

A recipe/tier/width/corner combination that resolves to an asset NOT on
disk is skipped and reported, never guessed - same "failure is loud, never
a fallback" doctrine as testcity_pins.require().

Runs LOCALLY over MCP (import ue) - never via remote exec. See HANDOFF's "An
MCP call from inside a rung script DEADLOCKS" trap: this script calls MCP
from outside the editor process, the only safe direction.
"""
import json

import _path  # noqa: F401
import citylayout as L
import recipes
import testcity_pins
import ue

RT = '/Game/Stacktown/Runtime'
CATALOGUE_PATH = '%s/DA_Catalogue' % RT
CATALOGUE_REF = '%s.DA_Catalogue' % CATALOGUE_PATH
BAKED = '/Game/Stacktown/Baked'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
ASSET = 'editor_toolset.toolsets.asset.AssetTools'

_SIDE_LETTER = {'left': 'L', 'right': 'R'}


def call(toolset, name, args):
    """ue.tool() returns the raw MCP text content, which is the tool's
    JSON-serialised output ({"returnValue": ...}) as a string - unwrap it."""
    raw = ue.tool(toolset, name, args)
    return json.loads(raw)['returnValue']


def asset_ref(name):
    return '/Game/Stacktown/Baked/%s.%s' % (name, name)


def _corner_letters():
    """{lot_key: 'L'/'R'/None} - None for non-corner lots. Derived from the
    layout, same source testcity_pins.require() itself uses, not stored
    twice."""
    out = {}
    for bname in sorted(L.blocks()):
        _end, turn_side = L.cross_street_end(bname)
        letter = _SIDE_LETTER[turn_side]
        for key, _x0, _x1, corner in L.lots(bname):
            out[key] = letter if corner else None
    return out


def build_rows():
    have = set()
    for a in call(ASSET, 'find_assets',
                  {'folder_path': BAKED, 'name': '', 'recursive': False}):
        have.add(a.split('.')[0].rsplit('/', 1)[-1])

    letters = _corner_letters()
    ids, tiers, widths, names, mesh_refs = [], [], [], [], []
    key_map = {}
    missing = []
    seen = set()   # (rid, t, w, side) - two pins can share a (rid, w) pair;
                   # don't add the same signature twice
    for lot_key, p in sorted(testcity_pins.PINS.items()):
        rid, w = p['rid'], float(p['w'])
        side = letters[lot_key] if p['corner'] else None
        # FULL TIER RANGE, NOT JUST UP TO THE PIN'S DECLARED TIER. Found
        # live 2026-09-01: econrules.tick() has no concept of a pin's
        # declared tier as a ceiling (nothing asked it to - see the
        # amendment's A2), so a parcel can and did grow past its pin's
        # declared massing within seconds of being bought. The pin's tier
        # was never a bound on gameplay growth, only a massing-design
        # choice for the pre-built-demo case - scoping the catalogue to it
        # was a mistake this session made and caught by testing the buy
        # verb live, not by re-reading the design. Every tier the recipe
        # DECLARES gets checked; only what's missing from disk is skipped.
        for t in range(recipes.tier_count(rid)):
            sig = (rid, t, w, side)
            if sig in seen:
                continue
            seen.add(sig)
            if side:
                name = recipes.asset_name(
                    rid, t, w, depth=recipes.DEPTH_CORNER,
                    corner={'L': 'left', 'R': 'right'}[side])
            else:
                name = recipes.asset_name(rid, t, w)
            if name not in have:
                missing.append(name)
                continue
            key = '%s_%d_%d' % (rid, t, round(w))
            if side:
                key = '%s_%s' % (key, side)
            ids.append(rid)
            tiers.append(t)
            widths.append(w)
            names.append(recipes.tier_name(rid, t))
            mesh_refs.append(asset_ref(name))
            key_map[key] = asset_ref(name)
    return ids, tiers, widths, names, mesh_refs, key_map, missing


def main():
    ids, tiers, widths, names, mesh_refs, key_map, missing = build_rows()
    if missing:
        print('  not on disk, skipped: %s' % ', '.join(sorted(set(missing))))
    if not ids:
        print('  NOTHING TO WRITE - is testcity_pins.PINS empty, or is '
              'nothing in it baked yet?')
        return

    # CLEAR FIRST, THEN SET. The key format changed shape 2026-09-01 (width
    # and corner joined the key) - none of the new keys match any of the
    # old ones, so this is a full reshape, not an incremental update.
    # set_properties refuses that in one call ("elements changed alongside
    # the size change; insertion points are ambiguous") because its diff
    # can't tell which old entry maps to which new one. Going from EMPTY to
    # the real content is unambiguous - every entry is purely an addition.
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

    print('  DA_Catalogue: %d rows written and verified non-None, saved '
          '(%d distinct lot/tier/width[/corner] keys)'
          % (len(ids), len(key_map)))


if __name__ == '__main__':
    main()
