"""District colour schemes. Pure data.

WHY A SCHEME AND NOT A COLOUR. The shelf picked one wall colour per MODEL,
which meant vernacular t0..t5 - the same building growing - came out in six
unrelated colours. A building does not repaint itself when it gains a storey.
A scheme is picked once per BUILDING and holds for every tier it climbs.

WHY MORE THAN TWO. Two colours (wall + trim) is a rule that reads as a rule.
A real painted model has a body, a trim, a base course that is usually darker
because it is the dirty end of the wall, and one small accent that is allowed
to be loud because there is so little of it. Four roles, and the accent is the
only saturated one - which is the palette discipline in the studio-director
skill: when adding a colour, the question is what it replaces.
"""

# GLASS IS A SCHEME ROLE. Canon slot 5 (highrise) is blessed for the highrise
# city read, and its towers are teal, green, black and cream - each tower one
# colour, the variety living BETWEEN buildings. A curtain-wall tower is mostly
# glass, so on that style the glass IS the identity and a single grey for
# every tower throws away the thing that image says carries a skyline.
#
# name: (wall, trim, base, accent, glass)
SCHEMES = {
    'buff_cream':   ('MI_dist_buff',    'MI_paint_cream', 'MI_concrete',    'MI_canopy_accent', 'MI_glass_bronze'),
    'brick_bone':   ('MI_dist_brick',   'MI_dist_bone',   'MI_dist_oxblood', 'MI_paint_accent', 'MI_glass_bronze'),
    'slate_bone':   ('MI_dist_slate',   'MI_dist_bone',   'MI_concrete',    'MI_canopy_accent', 'MI_glass_ink'),
    'olive_cream':  ('MI_dist_olive',   'MI_paint_cream', 'MI_dist_forest', 'MI_paint_accent',  'MI_glass_green'),
    'teal_bone':    ('MI_dist_teal',    'MI_dist_bone',   'MI_dist_slate',  'MI_canopy_accent', 'MI_glass_teal'),
    'oxblood_bone': ('MI_dist_oxblood', 'MI_dist_bone',   'MI_dist_brick',  'MI_paint_cream',   'MI_glass_ink'),
    'ochre_cream':  ('MI_dist_ochre',   'MI_paint_cream', 'MI_dist_brick',  'MI_canopy_accent', 'MI_glass_bronze'),
    'bone_slate':   ('MI_dist_bone',    'MI_dist_slate',  'MI_concrete',    'MI_paint_accent',  'MI_glass_sky'),
    'forest_bone':  ('MI_dist_forest',  'MI_dist_bone',   'MI_dist_slate',  'MI_canopy_accent', 'MI_glass_green'),
}
ROLES = ('wall', 'trim', 'base', 'accent', 'glass')
ORDER = sorted(SCHEMES)


def scheme(name):
    return dict(zip(ROLES, SCHEMES[name]))


# BRICK IS AN ERA MATERIAL, NOT AN EVEN ONE. The hash rotation gave every
# scheme a flat 1-in-9, spreading brick uniformly across contemporary towers
# and vernacular shopfronts alike - a distribution nothing in the world
# justifies. The owner chose brick concentrated in the vernacular era at ONE
# IN THREE.
#
# PROMOTION, NOT A LONGER DRAW LIST. The first attempt appended brick to a
# 12-entry vernacular list, which changed hash % len and therefore REPAINTED
# EVERY VERNACULAR BUILDING, not just the ones gaining brick - a far bigger
# change than the one asked for, and visible in the before/after as colours
# moving around the street. This keeps the original draw intact and applies a
# SECOND, INDEPENDENT draw that only ever promotes TO brick. A vernacular
# building that is not promoted keeps exactly the paint it had.
#
# The promotion rate is 1 in 4 rather than 1 in 3 because the base draw
# already yields brick 1 time in 9:
#     1/9 + (8/9)(1/4) = 1/3
PROMOTE_ONE_IN = 4


def _hash(building_id):
    h = 0
    for ch in str(building_id):
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h


def scheme_for(building_id, rid=None):
    """A stable scheme for a building identity.

    Deterministic on the id, so the same building gets the same paint every
    time it is rebuilt - and every tier of it, because the tier is not part
    of the id.

    `rid` is the RECIPE id and is optional. Omitted, this behaves exactly as
    it always did. Passed, a vernacular building may be PROMOTED to brick;
    every other building, and every unpromoted vernacular one, is untouched.
    """
    h = _hash(building_id)
    name = ORDER[h % len(ORDER)]
    if rid and str(rid).startswith('vernacular') and name != 'brick_bone':
        # a SEPARATE part of the hash, so promotion cannot disturb the base
        # assignment of anyone it does not promote
        if (h // len(ORDER)) % PROMOTE_ONE_IN == 0:
            name = 'brick_bone'
    return scheme(name)


def _selftest():
    for n, vals in SCHEMES.items():
        assert len(vals) == len(ROLES), n
        # a scheme whose wall and trim are the same colour is a one-colour
        # building wearing a two-colour rule
        assert vals[0] != vals[1], '%s: wall and trim are the same' % n
        assert len(set(vals)) == len(vals), '%s repeats a colour' % n
        assert vals[4].startswith('MI_glass_'), (
            '%s: the glass role must be a glass instance, got %s' % (n, vals[4]))
        for v in vals:
            assert v.startswith('MI_'), (n, v)
    # THE POINT OF THE MODULE: tier must not change the paint
    a = scheme_for('vernacular_w1230_p07')
    for _ in range(6):
        assert scheme_for('vernacular_w1230_p07') == a, 'scheme is not stable'
    # and different buildings must not all land on one scheme
    got = {tuple(sorted(scheme_for('bld%d' % i).items())) for i in range(40)}
    assert len(got) >= 5, 'scheme_for spreads over only %d schemes' % len(got)

    # --- the era weighting -------------------------------------------------
    # OMITTING rid MUST BE BYTE-IDENTICAL to the old behaviour.
    for i in range(200):
        b = 'N%d' % i
        assert scheme_for(b) == scheme(ORDER[_hash(b) % len(ORDER)]), (
            'the flat rotation moved for %s' % b)
    # NON-VERNACULAR ERAS ARE UNTOUCHED even when rid is passed
    for i in range(200):
        b = 'M%d' % i
        assert scheme_for(b, 'modern6') == scheme_for(b), (
            'passing a non-vernacular rid changed %s' % b)
    # PRESERVATION: an unpromoted vernacular building keeps its exact paint.
    # This is the property the first attempt broke - it repainted every
    # vernacular building by changing the draw list length.
    moved = kept = 0
    for i in range(400):
        b = 'V%d' % i
        was, now = scheme_for(b), scheme_for(b, 'vernacular3')
        if was == now:
            kept += 1
        else:
            moved += 1
            assert now['wall'] == 'MI_dist_brick', (
                '%s changed to something other than brick' % b)
    assert kept > 0 and moved > 0
    assert moved / 400.0 < 0.30, 'promotion is disturbing too many buildings'
    # and the weighting must actually land where it was aimed
    n = 900
    vern = sum(scheme_for('p%d' % i, 'vernacular3')['wall'] == 'MI_dist_brick'
               for i in range(n)) / float(n)
    other = sum(scheme_for('p%d' % i, 'modern6')['wall'] == 'MI_dist_brick'
                for i in range(n)) / float(n)
    assert 0.28 < vern < 0.39, 'vernacular brick share is %.3f, wanted ~1/3' % vern
    assert 0.07 < other < 0.15, 'non-vernacular share moved: %.3f' % other
    return True


_selftest()

def producible_walls():
    """Every wall material the palette can actually put on a building."""
    return {SCHEMES[n][0] for n in SCHEMES}


def undiscoverable_walls(recipe_walls):
    """Recipe-declared walls no scheme can produce, as {material: [recipes]}.

    THE SILENT-DISCARD CLASS. repaint() maps the slot NAMED after a recipe's
    declared wall onto scheme['wall'], so a recipe can declare a material and
    have it replaced by whatever the scheme says - and if NO scheme carries
    that material, the declaration is discarded with nothing to show for it.
    Five recipes declare precast walls; no scheme carries precast; those
    declarations reached nothing on the street and nobody noticed, because a
    discarded declaration leaves no artifact to look wrong.

    Brick was the visible symptom of the same fault. This makes the invisible
    case audible: a build warns rather than quietly substituting.

    SCOPED HONESTLY: this concerns buildings placed THROUGH repaint. The block
    builders in city.py do not call the palette at all and use their declared
    wall directly, so a material unused here may still be a block's material.
    """
    can = producible_walls()
    out = {}
    for rid, wall in recipe_walls.items():
        if wall and wall not in can:
            out.setdefault(wall, []).append(rid)
    return {k: sorted(v) for k, v in sorted(out.items())}
