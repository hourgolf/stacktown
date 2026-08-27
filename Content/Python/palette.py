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


def scheme_for(building_id):
    """A stable scheme for a building identity.

    Deterministic on the id, so the same building gets the same paint every
    time it is rebuilt - and every tier of it, because the tier is not part
    of the id.
    """
    h = 0
    for ch in str(building_id):
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return scheme(ORDER[h % len(ORDER)])


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
    return True


_selftest()
