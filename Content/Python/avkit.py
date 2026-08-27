"""Assetsville pieces we use, with measured sizes. Pure data.

Paths verified on disk. Sizes and triangle counts measured, not guessed, so
placement can be derived from a piece's real footprint and so the detail tier
is on the record next to the thing it describes.

TIER, from the survey: our own parts are 44 triangles a box and a whole
building is ~28,000. Everything below is under 1,300, most under 800 - these
sit beside our geometry as equals, which is the test the studio-director
skill sets ("detail tier must match, at the FABRICATION tier").

MATERIALS ARE OURS. Every piece is bound through `mat` at placement; the
donor's own textures never ship.
"""
MESH = '/Game/AssetsvilleTown/Meshes/'
OFFICE = MESH + 'InteriorProps/Office/'
NATURE = MESH + 'Nature/'
STREET = MESH + 'StreetProps/'
TILE = MESH + 'BuildingTilset/'

# name: (path, (x, y, z) size uu, tris, our material)
PIECES = {
    # planting - a bed wants something growing in it, and a box never will
    'plant_s':   (OFFICE + 'SM_Plant_01',      (39, 39, 101),   334, 'MI_bloom_warm'),
    'plant_m':   (OFFICE + 'SM_Plant_02',      (62, 101, 165),  654, 'MI_bloom_warm'),
    'plant_l':   (OFFICE + 'SM_Plant_03',      (44, 47, 82),    742, 'MI_bloom_cool'),
    # fallback only - its slots resolve through rolemap.SLOT like the trees
    'bush':      (NATURE + 'SM_bush_01',       (614, 641, 485), 1217, 'MI_leaf_card'),
    # park planting. Both pivot at their base, so they seat on a deck by z
    # alone. tree_02 is 3,194 tris and stays out; tree_03 is 1,916 and is in
    # HERO, not here.
    'grass_tuft': (NATURE + 'SM_grassVerticalSingle', (498, 479, 122), 18, 'MI_grass'),
    'rock':      (NATURE + 'SM_rock_01',       (21, 22, 6),       36, 'MI_gravel'),
    'bench':     (STREET + 'SM_bench_02',      (68, 150, 92),    452, 'MI_wood'),
    # rooftop equipment
    'ac_small':  (STREET + 'SM_airCondition_02', (51, 76, 93),  112, 'MI_dark_metal'),
    'ac_large':  (STREET + 'SM_airCondition_01', (42, 108, 63), 496, 'MI_dark_metal'),
    'antenna':   (STREET + 'SM_AntennaBig_01', (322, 322, 968), 960, 'MI_dark_metal'),
    'chimney':   (STREET + 'SM_chimney_02',    (225, 100, 240), 250, 'MI_dist_brick'),
    'vent_tank': (STREET + 'SM_tank',          (183, 512, 277), 988, 'MI_dark_metal'),
    'drainpipe': (TILE + 'SM_drainPipe',       (27, 27, 300),    72, 'MI_dark_metal'),
    'drainpipe_end': (TILE + 'SM_drainPipe_ending', (47, 27, 60), 136, 'MI_dark_metal'),
    # facade kit - the parts a card builder cannot cut but a modelmaker buys
    'cornice':   (TILE + 'SM_cornice_01',      (96, 800, 113),  364, 'MI_paint_cream'),
    'cornice_corner': (TILE + 'SM_cornice_01_corner', (71, 71, 113), 132, 'MI_paint_cream'),
    'shop_top':  (TILE + 'SM_shopTop_01',      (44, 814, 177),  234, 'MI_paint_cream'),
    'pillar':    (TILE + 'SM_pillar_01',       (40, 40, 300),     8, 'MI_paint_cream'),
    # FREESTANDING. Four legs to the ground - a market stall canopy, not a
    # wall awning. Rendered side-on before use, which is the only reason this
    # is documented rather than shipped. Keep it for a market, not a facade.
    'awning':    (STREET + 'SM_shopAwing_01',  (293, 1402, 324), 483, 'MI_canopy_accent'),
    # A SLATTED LOUVRE, not a canvas awning - it throws striped shadows and at
    # shopfront size it is a knife edge. Kept because a louvred sunshade is a
    # real thing we may want deliberately; not used as an awning.
    'canopy':    (STREET + 'SM_shopCanopy_01', (155, 700, 78),   152, 'MI_canopy_accent'),
}

# Above our scatter tier, admitted deliberately and only where a roof wants one
# big legible object. Kept separate so the <=1300 rule below stays a real rule
# instead of being widened until it stops catching anything.
HERO = {
    'water_tank': (STREET + 'SM_Water_Tank_01', (288, 295, 877), 1720, 'MI_wood'),
    # A TREE IS NOT SCATTER. These are 1,391 and 1,401 triangles - over the
    # scatter tier, and the self-test refused them there, correctly. A roof
    # park has two or three trees and they are the thing the eye goes to, so
    # they are heroes by the same argument as the water tank. tree_02 (3,194)
    # stays out entirely; tree_lp is the 8-triangle cone in REJECTED.
    # `mat` is only the FALLBACK now - these meshes carry their role in the
    # material SLOT names (testleaf_01/02, testtrunk_01) and rolemap.SLOT
    # binds each slot properly through the masked leaf materials.
    'tree_s':    (NATURE + 'SM_tree_01',       (656, 675, 1379), 1391, 'MI_leaf_card'),
    'tree_t':    (NATURE + 'SM_tree_04',       (438, 413, 1624), 1401, 'MI_leaf_card'),
}
PIECES.update(HERO)

# Enlisted on the strength of their names, rendered, and thrown out. Recorded
# rather than deleted so the next pass does not re-pick them: a name is not a
# measurement and a triangle count is not a picture.
REJECTED = {
    'roof_stand': (STREET + 'SM_roofStand_donut',
                   'a rooftop stand carrying a GIANT DONUT ADVERT - it sits in '
                   'the folder next to SM_billboard_Donuts_01. Shipped on the '
                   'crown of all three towers, where it read as a car tyre.'),
    'tree_lp': (NATURE + 'SM_treeLowPoly_01',
                'an 8-triangle CONE. The triangle count was in the survey and '
                'should have been the tell: no tree is 8 triangles.'),
    'blind': (MESH + 'InteriorProps/House/SM_rollerBlind_01',
              'exists, but it is interior dressing - a blind seen from inside '
              'a room. Nothing on an exterior elevation needs it.'),
}


def path(key):
    return PIECES[key][0]


def size(key):
    return PIECES[key][1]


def mat(key):
    return PIECES[key][3]


def downpipe(z_bottom, z_top, x, y, rnd):
    """A run of drainpipe from z_bottom to z_top, plus its shoe at the foot.

    Returns [(key, loc, yaw)].

    THE SHOE HANGS BELOW ITS PIVOT. SM_drainPipe_ending measures local
    z -59.8..0, so placing it at `z_bottom - 60` put it at world -84..-24 -
    entirely underground, and it dragged the baked mesh's bounding box down
    to -83.8 with it. Any stage that seats a model by its BOUNDS then lifted
    the whole building 84 uu into the air. One mis-signed offset on a 40
    triangle part, and every building with a downpipe floated.

    So the shoe is placed by where its BOTTOM should land, and the pipe run
    starts at the shoe's head rather than at the ground.
    """
    out = []
    shoe_h = size('drainpipe_end')[2]          # 60, measured
    z_shoe = z_bottom + shoe_h                 # pivot: bottom lands on z_bottom
    out.append(('drainpipe_end', (x, y, z_shoe), 0.0))
    seg = size('drainpipe')[2]
    n = max(1, int(round((z_top - z_shoe) / seg)))
    for i in range(n):
        out.append(('drainpipe', (x, y, z_shoe + i * seg), 0.0))
    return out


def bed_planting(x0, y0, x1, y1, z, rnd):
    """Fill a bed rectangle with plants. Returns [(key, (x,y,z), yaw)].

    A GRID, not a line. This laid one row down the bed's long axis whatever
    the bed's depth, so a 300 x 160 planter got the same six plants as a
    300 x 50 trough and read as a border round a patch of bare soil. A t4
    roof came out with 42 bed boxes and 14 plants in them.

    Placed from the pieces' own measured footprints, so nothing overhangs.
    """
    out = []
    long_x = (x1 - x0) >= (y1 - y0)
    span = (x1 - x0) if long_x else (y1 - y0)
    depth = (y1 - y0) if long_x else (x1 - x0)
    keys = ['plant_m', 'plant_s', 'plant_l', 'plant_s', 'plant_m', 'plant_l']
    step = 42.0
    n = max(1, int((span - 30.0) // step))
    # rows across the bed, one per 58 uu of depth - a trough gets one, a
    # planter gets two or three
    rows = max(1, int((depth - 24.0) // 58.0))
    start = (span - (n - 1) * step) / 2.0
    rstep = (depth - 24.0) / rows if rows > 1 else 0.0
    rstart = (depth - rstep * (rows - 1)) / 2.0
    i = 0
    for r in range(rows):
        cross = (y0 if long_x else x0) + rstart + r * rstep
        for c in range(n):
            k = keys[i % len(keys)]
            i += 1
            d = start + c * step + (step * 0.5 if r % 2 else 0.0)
            if d > span - 14.0:
                continue
            px = x0 + d if long_x else cross
            py = cross if long_x else y0 + d
            out.append((k, (px, py, z), rnd.uniform(0, 360)))
    return out


def _selftest():
    import random
    for k, (p, s, t, m) in PIECES.items():
        assert p.startswith('/Game/AssetsvilleTown/'), (k, p)
        assert len(s) == 3 and all(v > 0 for v in s), (k, s)
        if k not in HERO:
            assert t <= 1300, ('%s is above our tier at %d tris' % (k, t))
        assert m.startswith('MI_'), (k, m)
    r = random.Random(1)
    ps = bed_planting(0.0, 0.0, 300.0, 50.0, 10.0, r)
    assert ps, 'a 300 uu bed must hold planting'
    assert len(ps) >= 6, 'a 300 uu bed should be planted, not dotted: %d' % len(ps)
    # a DEEP bed must get more than a deep-less one, or the grid is a line
    deep = bed_planting(0.0, 0.0, 300.0, 180.0, 10.0, random.Random(1))
    assert len(deep) > len(ps) * 1.6, (
        'a 300x180 planter got %d plants and a 300x50 trough got %d - '
        'bed_planting is still laying one row' % (len(deep), len(ps)))
    dp = downpipe(10.0, 900.0, 5.0, 5.0, r)
    assert len(dp) == 4, dp          # the shoe plus three 300 uu runs
    # NOTHING MAY GO BELOW THE FOOT. This is the whole point of the rewrite:
    # the shoe used to sit 84 uu underground and take the model's bounds
    # with it.
    lo_pv, hi_pv = -59.8, 0.0        # drainpipe_end's measured local z
    shoe = [e for e in dp if e[0] == 'drainpipe_end'][0]
    assert abs((shoe[1][2] + lo_pv) - 10.0) < 0.5, (
        'shoe bottom lands at %.1f, asked for 10.0' % (shoe[1][2] + lo_pv))
    for k, loc, _y in dp:
        assert loc[2] + (lo_pv if k == 'drainpipe_end' else 0.0) >= 9.5, (
            '%s reaches below the foot at z=%.1f' % (k, loc[2]))
    # a rejected mesh must never be reachable through the normal accessors
    for k in REJECTED:
        assert k not in PIECES, ('%s was rejected and is back in PIECES' % k)
    for k, (px, py, _pz), _y in ps:
        assert 0.0 <= px <= 300.0 and 0.0 <= py <= 50.0, (k, px, py)
    # a tiny bed still gets one plant rather than none
    assert len(bed_planting(0.0, 0.0, 60.0, 50.0, 0.0, r)) == 1
    return True


if __name__ == '__main__':
    print('avkit self-test:', _selftest())
    for k in sorted(PIECES):
        p, s, t, m = PIECES[k]
        print('  %-11s %5.0f x %5.0f x %5.0f  %5d tris  %s'
              % (k, s[0], s[1], s[2], t, m))
