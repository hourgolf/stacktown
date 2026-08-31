"""Role prefix -> material name. Pure, so both backends read the same table.

step_roles.py held this and imports `unreal`, so the fast bake path could not
reach it. Copying the table into fastbake would be two answers to "what colour
is a Timber_", and this project has been bitten by a duplicated table roughly
once a session. So the table moved here and step_roles imports it.

`material_for` is the whole contract: give it a component name and the lot's
wall/roof choices, get the material instance name back.
"""
import labels

SHARED = {
    'Glass_': 'MI_glass_b',
    'Interior_': 'MI_interior',
    'Frame_': 'MI_frame_print',
    'Mullion_': 'MI_frame_print',
    'Accent_': 'MI_canopy_accent',
    'Roof_': 'MI_concrete',
    # ground roles, for zones that are not buildings
    'Ground_': 'MI_concrete',
    'Grass_': 'MI_grass',
    # GrassCard_ is the alpha-cut TUFT, Grass_ is the solid lawn box. Two
    # roles because they are two fabrications: a flock surface and a cut card
    # standing in it. They were one role until 29 Aug, which put a cutout mesh
    # on an opaque material and rendered every tuft as a solid quad.
    'GrassCard_': 'MI_grass_card',
    'Kerbing_': 'MI_paint_cream',
    # a yard is not a car park: the apron is laid concrete, the rest compacted
    # ground. NOT MI_precast_buff - measured, that is (0.745,0.700,0.612)
    # against concrete's (0.700,0.672,0.616) and the two do not separate.
    'Gravel_': 'MI_gravel',
    # a rail or post is dark painted metal, not window-frame print
    'Rail_': 'MI_dark_metal',
    # decking, planters and pergolas on a reclaimed roof
    'Timber_': 'MI_wood',
    # paint on a wall; the panel suffix picks which of the three
    'Mural_': 'MI_mural_a',
    # a raised bed is PLANTING; on MI_grass it is a raised bed of grass
    'Bloom_': 'MI_bloom_warm',
    # DONOR ROLES, 2026-08-27. See labels.ROLES for why the vocabulary grew
    # rather than the donor names being bent to fit an existing role.
    'Leaf_': 'MI_leaf_card',
    'Planter_': 'MI_planter',
    'Brick_': 'MI_dist_brick',
}

# Bloom_ is one role with two temperatures, resolved by SUFFIX rather than by
# a second top-level role - the same shape as MURAL below, and for the same
# reason: warm and cool planting are the same THING, and role-in-the-name is
# about what a part is.
BLOOM = {'Cool': 'MI_bloom_cool', 'Warm': 'MI_bloom_warm'}

# Some families want a different material for the SAME role. A lamp column is
# dark painted metal, not the window-frame print - both are 'Frame_' because
# both are a frame, and role-in-the-name is about what a part IS.
FAMILY = {'LAMP': {'Frame_': 'MI_dark_metal'}}

# A mural is three colours, so panels differ by SUFFIX rather than role.
# NOT the card colours: measured against MI_paint_cream their smallest
# per-channel deltas are 0.020, 0.040 and 0.163 - invisible. See mk_mural.py.
MURAL = {'A': 'MI_mural_a', 'B': 'MI_mural_b', 'C': 'MI_mural_c'}

# Components whose ROLE is right but whose SUBJECT wants a different material.
# A penthouse is glazed and has an interior, so Glass_/Interior_ are the
# correct roles - but a window's glass is a dark opening (lum 0.080) and a
# glass penthouse is a lit volume. Matched on prefix, checked BEFORE the role
# table, so nothing else in the project moves.
SPECIAL = {
    # THE SHOP WINDOW. Ordinary Glass_ over an ordinary Interior_ gave a
    # pale panel with the listing cards invisible against it - the cards
    # were built and rendered, they simply had nothing to read against.
    # The reference's display is dark glass over a dark interior with
    # bright printed cards in front of it, which is what makes the
    # display legible at all.
    # NAMED Listing_, NOT Shop_. Interior_Shop is ALREADY a catalogue name -
    # rolemap's own self-test asserts it binds MI_interior - so a SPECIAL on
    # that prefix would have repainted every street-level shop interior in the
    # 548. The self-test caught it on the first run. These are the estate
    # office's LISTING display, which is its own thing.
    # a listing card IS a printed card, so it takes a card colour
    'Frame_Listing': 'MI_card_lift',
    'Glass_Listing': 'MI_glass_listing',
    # LIT, not dark. A near-mirror pane (MI_glass_ink is roughness 0.04-0.12)
    # reflects whatever is in front of it, and on a bench that is a dark room -
    # so the display read as a flat matte field however the ambient was raised,
    # measured up to sky 70. What makes glazing read is something BRIGHT
    # behind it, and the office's own declaration already said so: "a lit
    # interior (practicals) so it reads as OPEN". A lit estate-agent window
    # with the listings on the glass is the reference, and it is the thing a
    # player sees at dusk.
    'Interior_Listing': 'MI_interior_lit',
    'Glass_Pent': 'MI_glass_pent',
    'Interior_Pent': 'MI_interior_lit',
}

DEFAULT_WALL = 'MI_paint_cream'
DEFAULT_ROOF = 'MI_shingle_grey'
# Band_ used to resolve to the wall colour, so a whole building was one paint.
# Owner: "buildings don't need to be just one colour either." A band course,
# a plinth and a parapet cap are the parts a real building picks out in a
# second colour, and they are already their own role - they just pointed at
# the same material. `trim` falls back to `wall` when a recipe declares none,
# so nothing that has not opted in changes.

# roles bound by prefix here, plus the three resolved per-lot below
BOUND = set(SHARED) | {'Tile_', 'Wall_', 'Band_'} | {
    r for o in FAMILY.values() for r in o}


# DONOR MESHES CARRY ROLE IN THE MATERIAL SLOT NAME, not the component name -
# that is what makes the Assetsville tileset usable. A tree is bark plus
# alpha-masked leaf cards, and the leaf materials are instances of the MASKED
# master carrying the pack's own leaf texture as their opacity mask
# (see mk_leaf_mi.py). Binding one opaque material across every slot of such a
# mesh renders the leaf cards as solid dark quads - which is exactly what the
# fastbake merge did to every tree and bush it was given.
#
# This vocabulary was in step_foliage.py, where only the level sweep could
# reach it. It lives here now for the same reason ROLES does: one resolver.
SLOT = {'testleaf_01': 'MI_leaf_card',
        'testleaf_02': 'MI_leaf_card_b'}


def material_for_slot(slot, fallback=None):
    """Material for one MATERIAL SLOT of a donor mesh, or `fallback`."""
    s = str(slot)
    if s in SLOT:
        return SLOT[s]
    low = s.lower()
    if 'leaf' in low or 'foliage' in low:
        return 'MI_leaf_card'
    if 'trunk' in low or 'bark' in low:
        return 'MI_wood'
    return fallback


def material_for(comp, wall=None, roofmat=None, family='BLD2', trim=None):
    """The material instance name for one component. None if nothing binds it."""
    if comp.startswith('Mural_'):
        return MURAL.get(comp[-1], SHARED['Mural_'])
    # Bloom_Cool / Bloom_Warm resolve by suffix; a bare Bloom_ stays warm, so
    # nothing that already used the role moves.
    if comp.startswith('Bloom_'):
        for suf, mi in BLOOM.items():
            if comp[len('Bloom_'):].startswith(suf):
                return mi
        return SHARED['Bloom_']
    for pre, mi in SPECIAL.items():
        if comp.startswith(pre):
            return mi
    fam = FAMILY.get(family, {})
    for r in fam:
        if comp.startswith(r):
            return fam[r]
    for r in SHARED:
        if comp.startswith(r):
            return SHARED[r]
    if comp.startswith('Tile_'):
        return roofmat or DEFAULT_ROOF
    if comp.startswith('Band_'):
        return trim or wall or DEFAULT_WALL
    if comp.startswith('Wall_'):
        return wall or DEFAULT_WALL
    return None


def _selftest():
    assert material_for('Wall_Pier0', wall='MI_precast_buff') == 'MI_precast_buff'
    assert material_for('Band_Course', wall='MI_precast_buff') == 'MI_precast_buff'
    # a declared trim picks out the bands; without one they follow the wall
    assert material_for('Band_Course', wall='MI_a', trim='MI_b') == 'MI_b'
    assert material_for('Wall_Pier0', wall='MI_a', trim='MI_b') == 'MI_a'
    assert material_for('Tile_Step2', roofmat='MI_shingle_brown') == 'MI_shingle_brown'
    assert material_for('Glass_B0') == 'MI_glass_b'
    assert material_for('Timber_Deck') == 'MI_wood'
    assert material_for('Mural_B') == 'MI_mural_b'
    assert material_for('Frame_Post', family='LAMP') == 'MI_dark_metal'
    assert material_for('Frame_Post', family='BLD2') == 'MI_frame_print'
    assert material_for('StaticMeshComponent0') is None
    # the penthouse takes its own glazing; every other window does not
    assert material_for('Glass_Pent0F') == 'MI_glass_pent'
    assert material_for('Interior_Pent1') == 'MI_interior_lit'
    assert material_for('Glass_B0') == 'MI_glass_b'
    assert material_for('Interior_Shop') == 'MI_interior'
    # the vocabulary must match labels.ROLES exactly, or the gate cannot see
    # a role that is bound, or a listed role binds to nothing
    assert BOUND == set(labels.ROLES), (sorted(BOUND ^ set(labels.ROLES)),)
    return True


if __name__ == '__main__':
    print('rolemap self-test:', _selftest())


# ---- donor component naming -------------------------------------------
# The inverse of the role table, for the one caller that needs it: genbuild
# chooses a donor's material at the call site (often as avkit.mat(key), which
# varies per key), and the component NAME must carry a role that resolves back
# to exactly that material. Deriving the role FROM the material is what makes
# that guarantee hold by construction rather than by a hand-kept list of
# call sites - and step_roles binds material FROM the role, so any mismatch
# would silently repaint the donor.
ROLE_FOR_MAT = {
    'MI_leaf_card': 'Leaf_',
    'MI_planter': 'Planter_',
    'MI_dist_brick': 'Brick_',
    'MI_bloom_warm': 'Bloom_Warm',
    'MI_bloom_cool': 'Bloom_Cool',
    'MI_grass': 'Grass_',
    'MI_grass_card': 'GrassCard_',
    'MI_gravel': 'Gravel_',
    'MI_wood': 'Timber_',
    'MI_dark_metal': 'Rail_',
    'MI_canopy_accent': 'Accent_',
    'MI_paint_cream': 'Kerbing_',
}


def donor_name(mat, stem):
    """Component name for a donor piece: a role that resolves back to `mat`.

    RAISES on an unmapped material rather than returning the bare stem. A
    donor with no role is precisely what GATE-01 refused across all 548
    combinations, and returning something unroled here would push that failure
    to bake time - or worse, past a gate that had been taught to shrug.
    """
    r = ROLE_FOR_MAT.get(mat)
    if not r:
        raise KeyError('no role resolves to donor material %r (component %r) - '
                       'add it to ROLE_FOR_MAT and labels.ROLES' % (mat, stem))
    return r + stem


def _selftest_donor_names():
    """Every mapped material must round-trip: role -> that same material."""
    bad = []
    for mat, role in ROLE_FOR_MAT.items():
        got = material_for(donor_name(mat, 'X0'))
        if got != mat:
            bad.append((mat, role, got))
    return bad
