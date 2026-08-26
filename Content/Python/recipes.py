"""A building is a RECIPE, not a model.

This is the thing the sandbox has actually been building for a week, and the
reason it is worth more than a folder of meshes: genbuild.build(spec) takes a
parameter set and emits geometry, so a new variant costs a parameter rather
than a modelling day.

A recipe is: a style, a base spec that never changes, and a list of TIERS. A
tier is the same building further along - more floors, a porch instead of a
stoop, dormers, a garage. Upgrading is moving up a tier and rebaking.

THE SEED LIVES IN THE BASE, NOT THE TIER. That is the whole trick: an upgraded
building keeps its jitter, its colour and its roof pitch, so it reads as the
same house grown rather than a different house swapped in.

COTTAGE AND WALKUP WERE RETIRED 25 Aug 2026. They were the first two written
and the least refined - the cottage rendered with a blank front and blank
dormers after three separate rounds of "these need more detail", which is the
clearest possible signal that they were not the set to build a catalogue on.
Retiring walkup also removes the need for a flank_walkup: it was the only
style that fell through to a COMMERCIAL side elevation, and a residential
building wearing a shopfront grammar is two buildings pretending to be one.

`fits(width, depth)` is what the grammar asks when it has a parcel and needs to
know which recipes could stand on it. Pure functions, no Unreal import.
"""

RECIPES = {
    'vernacular': dict(
        label='Vernacular', style='vernacular', district=('commercial', 'mixed'),
        # the shared ladder from PARCELS.md; a recipe declares which it accepts
        widths=(820.0, 1230.0, 1640.0),
        bay_target=280.0,
        align='left',          # against a party wall, so a part-built street
                               # still reads as a street rather than gap-toothed
        base=dict(kind='gen', style='vernacular', depth=700.0, gf_h=340.0,
                  fl_h=280.0, wall='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=61),
        # THE LADDER IS A LIFE STORY, not a size chart. An era commercial
        # building is built (t0-t3), survives, is reclaimed as a creative
        # office (t4), and finally gets a penthouse (t5). t4 and t5 keep the
        # SHELL of t3 - that is what makes them read as the same building with
        # a history rather than three different buildings.
        tiers=[
            dict(name='lock-up',       fill=0.55, floors=0, parapet=40),
            dict(name='shop & flat',   fill=0.72, floors=1, parapet=40,
                 canopy=90),
            dict(name='chambers',      fill=1.00, floors=2, parapet=45,
                 canopy=110),
            dict(name='the building',  fill=1.00, floors=4, parapet=90,
                 canopy=110, cornice=55, roof_units=1),
            # RECLAIMED. Same shell, same floors, same cornice - what changes
            # is the glazing (mullions stripped, cills dropped: new glass in
            # old holes), a mural on the exposed flank, and a roof put to work.
            dict(name='creative office', fill=1.00, floors=4, parapet=90,
                 canopy=110, cornice=55, glaze='large', mural=True,
                 roof_garden=True, roof_units=0),
            # PENTHOUSE. t4 untouched below; two glass storeys added on top,
            # set back behind a terrace.
            # roof_garden OFF: the penthouse takes the roof. t5 is t4 after
            # the air rights were sold, not t4 with a hut added beside the
            # pergola.
            dict(name='penthouse',     fill=1.00, floors=4, parapet=90,
                 canopy=110, cornice=55, glaze='large', mural=True,
                 roof_garden=False, roof_units=0,
                 penthouse=dict(floors=2, inset=95.0, fl_h=260.0)),
        ],
        fits=lambda w, d: 700.0 <= w <= 1700.0 and d >= 600.0),
}


def widths(rid):
    return RECIPES[rid].get('widths', (1230.0,))


def spec_for(rid, tier, name, x0, width):
    """The full spec for one recipe at one tier, on a parcel of `width`.

    `fill` is the fraction of the parcel the BUILDING occupies - tier 1 sits
    small on its plot and later tiers grow into it, which is what makes a wide
    parcel and a narrow one different growth stories rather than the same
    building at two sizes.

    `bays` is DERIVED from the built width against the recipe's bay target,
    not fixed per tier. Fixed bays gave a 1640 parcel the same four openings
    as an 820 one, which is one building stretched.
    """
    r = RECIPES[rid]
    t = r['tiers'][tier]
    s = dict(r['base'])
    s.update({k: v for k, v in t.items() if k not in ('fill', 'name')})
    s['name'] = name
    fill = t.get('fill', 1.0)
    bw = width * fill
    slack = width - bw
    s['x0'] = x0 + (0.0 if r.get('align') == 'left' else slack/2.0)
    s['width'] = bw
    s['bays'] = max(2, int(round(bw / r.get('bay_target', 300.0))))
    return s


def tier_count(rid):
    return len(RECIPES[rid]['tiers'])


def tier_name(rid, tier):
    return RECIPES[rid]['tiers'][tier]['name']


def asset_name(rid, tier, width):
    """One baked mesh per recipe, tier and PARCEL width. Width is part of the
    identity because the generator lays bays out across it, and because `fill`
    means the same tier occupies a different share of a different parcel."""
    return 'SM_Bld_%s_t%d_w%d' % (rid, tier, int(round(width)))
