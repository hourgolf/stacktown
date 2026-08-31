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
    # FILLER. Vernacular is the street-wall building: it fills a block around
    # the buildings that matter and stops at six storeys. CANON slot 5 is
    # blessed for the highrise read - "the city needs true towers" - but a
    # commercial terrace is not what becomes one. Height belongs to the
    # ACTIONABLE recipes; filler gives them something to stand against.
    # Owner's direction, 2026-08-26.
    # THE REAL ESTATE OFFICE. A gameplay building, declared before geometry in
    # Docs/COREBUILDINGS_DECLARATIONS.md and read off the owner's design
    # reference in Docs/OFFICE_RECIPE.md. It is a HOUSE, not a shopfront: a
    # small gable-end-on cottage set back in a fenced yard.
    #
    # WHY fill IS 1.0 ON EVERY TIER. The LOT is fully claimed - as yard - from
    # t0. What grows is `house_width`, so the ladder reads as a building
    # growing INTO its garden rather than a parcel being progressively
    # occupied. That is the owner's "it will grow into it".
    #
    # FOUR TIERS, AND THE STEPS ARE BIG ON PURPOSE. The catalogue's t0..t5 grow
    # gradually by fill fraction, which is right for variety across a street
    # and wrong for one parcel over time: four upgrades a player PAYS for have
    # to read as investment they can see. So each step changes a state -
    # footprint, then the roof breaks, then a storey, then a wing - rather
    # than being a slightly larger version of the last.
    'office': dict(
        label='Real estate office', style='house', district=('mixed',),
        role='civic', max_storeys=2,
        widths=(2050.0,),          # one office-sized parcel, per the owner
        bay_target=680.0,
        base=dict(kind='gen', style='house', use='office', depth=1600.0,
                  gf_h=372.0, fl_h=300.0,
                  # BONE AND SLATE, NOT WHITE AND NAVY. The library has no
                  # white paint and no blue of any kind; these are the nearest
                  # in family. The owner's call was to build in them and judge
                  # the colour on a rendered frame rather than author three
                  # material instances against a guess.
                  wall='MI_paint_white', trim='MI_paint_navy',
                  roofmat='MI_roof_blue', seed=97,
                  # tree_s is the FULLER donor: 656 x 675 x 1379 against
                  # tree_t's 438 x 413 x 1624, which at the scale a cottage
                  # wants reads as a bare pole. 0.85 puts the crown at ~1172
                  # against a 713 apex - a specimen tree the building sits
                  # under, which is what "a big tree" meant.
                  tree='tree_s', tree_scale=0.85, tree_x=420.0,
                  # the gable IS the street elevation here, so it is
                  # stepped finely enough to read as a boarded wall
                  gable_steps=22),
        tiers=[
            # t0 - the reference: a one-room cottage, gable to the street,
            # standing well back with the yard in front of it
            dict(name='cottage', fill=1.0, floors=0, house_width=620.0,
                 house_depth=780.0, garden=520.0, roof_rise=341.0),
            # t1 - it takes more ground and the roof BREAKS: dormers are the
            # cheapest legible change of state a gable can make
            dict(name='dormered', fill=1.0, floors=0, house_width=820.0,
                 house_depth=900.0, garden=470.0, roof_rise=372.0, dormers=2),
            # t2 - a STOREY. The silhouette changes, which is the one thing
            # that reads at block-hero range
            dict(name='two storey', fill=1.0, floors=1, house_width=1020.0,
                 house_depth=1010.0, garden=410.0, roof_rise=392.0, dormers=2),
            # t3 - a WING: the bay breaks the flat elevation, and the yard is
            # squeezed forward as the building finally fills its parcel
            dict(name='established', fill=1.0, floors=1, house_width=1240.0,
                 house_depth=1120.0, garden=350.0, roof_rise=420.0,
                 dormers=2, bay=True),
        ],
    ),
    'vernacular': dict(
        label='Vernacular', style='vernacular', district=('commercial', 'mixed'),
        role='filler', max_storeys=6,
        # No `needs` on any tier: a filler grows on the lot it has. It also
        # does not accept assembled parcels - a lock-up on an XXL lot is not
        # filler, it is a wasted corner.
        # the shared ladder from PARCELS.md; a recipe declares which it accepts
        widths=(820.0, 1230.0, 1640.0),
        bay_target=280.0,
        align='left',          # against a party wall, so a part-built street
                               # still reads as a street rather than gap-toothed
        # wall + TRIM: the body takes one paint and the band courses, plinth
        # and parapet cap take another. One flat colour per building was the
        # monotone the owner called out, and a real building picks its bands
        # out - it is the cheapest variety there is.
        base=dict(kind='gen', style='vernacular', depth=700.0, gf_h=340.0,
                  fl_h=280.0, wall='MI_dist_buff', trim='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=61,
                  # the core stops at the roof line so the roof deck, the
                  # plant and the garden are actually visible; build_vernacular
                  # closes the roof void with a rear parapet in exchange
                  open_roof=True),
        # THE LADDER IS A LIFE STORY, not a size chart. An era commercial
        # building is built (t0-t3), survives, is reclaimed as a creative
        # office (t4), and finally gets a penthouse (t5). t4 and t5 keep the
        # SHELL of t3 - that is what makes them read as the same building with
        # a history rather than three different buildings.
        tiers=[
            # a single-storey lock-up gets a hatch and a vent, not a stair house
            dict(name='lock-up',       fill=0.55, floors=0, parapet=40,
                 roof_units=1, stair_head=False),
            # A ROOF IS AN ELEVATION. These carried nothing at all and baked
            # out as bare slabs - the one face a diorama shows the viewer for
            # free. Each tier now gets a stair head plus plant in proportion.
            dict(name='shop & flat',   fill=0.72, floors=1, parapet=40,
                 canopy=90, roof_units=1),
            dict(name='chambers',      fill=1.00, floors=2, parapet=45,
                 canopy=110, roof_units=2),
            dict(name='the building',  fill=1.00, floors=4, parapet=90,
                 canopy=110, cornice=55, roof_units=3),
            # RECLAIMED. Same shell, same floors, same cornice - what changes
            # is the glazing (mullions stripped, cills dropped: new glass in
            # old holes), a mural on the exposed flank, and a roof put to work.
            dict(name='creative office', fill=1.00, floors=4, parapet=90,
                 canopy=110, cornice=55, glaze='large', mural=True,
                 # ONE unit, not zero. A reclaimed roof still has a tank and a
                 # vent behind the planting; the garden zones the FRONT of the
                 # roof, so there is room at the back and nothing to crowd.
                 roof_garden=True, roof_units=1),
            # PENTHOUSE. t4 untouched below; two glass storeys added on top,
            # set back behind a terrace.
            # roof_garden OFF: the penthouse takes the roof. t5 is t4 after
            # the air rights were sold, not t4 with a hut added beside the
            # pergola.
            dict(name='penthouse',     fill=1.00, floors=4, parapet=90,
                 canopy=110, cornice=55, glaze='large', mural=True,
                 # a penthouse terrace still has a tank and a vent on it;
                 # what it does not have is a garden competing with the glass
                 roof_garden=False, roof_units=2,
                 penthouse=dict(floors=2, inset=95.0, fl_h=260.0)),
        ],
        fits=lambda w, d: 700.0 <= w <= 1700.0 and d >= 600.0),

    # VERNACULAR II - THE LOFT. Same era and the same generator as the high
    # street block, a completely different building: a goods warehouse. Where
    # v1 meets the street with a shopfront and a canopy, this one meets it
    # with a loading dock, cast-iron columns and a pair of timber doors, and
    # crowns itself by corbelling brick courses out instead of buying a stone
    # cornice. The hoist gantry over the street is the tell from a block away.
    #
    # Proportions differ too, which matters more than ornament: a warehouse
    # has fewer, taller floors and a tall ground storey to get a cart in.
    'vernacular2': dict(
        label='Loft', style='vernacular', district=('goods', 'mixed'),
        role='filler', max_storeys=6,
        widths=(1230.0, 1640.0),
        bay_target=330.0,
        align='left',
        base=dict(kind='gen', style='vernacular', depth=760.0, gf_h=420.0,
                  fl_h=312.0, wall='MI_dist_brick', trim='MI_dist_oxblood',
                  roofmat='MI_shingle_grey', seed=1889, open_roof=True),
        tiers=[
            dict(name='yard store',  fill=0.60, floors=0, parapet=40,
                 roof_units=1, stair_head=False),
            dict(name='goods shed',  fill=0.82, floors=1, parapet=44,
                 loft=True, roof_units=1),
            dict(name='warehouse',   fill=1.00, floors=3, parapet=58,
                 loft=True, corbel=True, cornice=58, roof_units=2),
            dict(name='the loft',    fill=1.00, floors=5, parapet=72,
                 loft=True, corbel=True, cornice=64, hoist=True,
                 roof_units=3),
            # RECLAIMED, exactly as v1's creative office is: same shell, new
            # glass in the old holes, and the roof put to work.
            dict(name='loft conversion', fill=1.00, floors=5, parapet=72,
                 loft=True, corbel=True, cornice=64, hoist=True,
                 glaze='large', mural=True, roof_garden=True, roof_units=1),
            dict(name='loft penthouse', fill=1.00, floors=5, parapet=72,
                 loft=True, corbel=True, cornice=64, glaze='large',
                 mural=True, roof_garden=False, roof_units=2,
                 penthouse=dict(floors=2, inset=110.0, fl_h=270.0)),
        ],
        fits=lambda w, d: 900.0 <= w <= 1800.0 and d >= 640.0),

    # VERNACULAR III - THE TERRACE. The residential building of the same era.
    # v1 is a shop, v2 is a warehouse, this is where people live: a row of
    # houses behind one facade. It meets the street with front doors up their
    # own steps behind area railings, carries a canted bay per house on the
    # lower floors, and is the only ladder you can COUNT the units on - from
    # the stoops at the bottom and the chimney stacks at the top.
    'vernacular3': dict(
        label='Terrace', style='vernacular', district=('resi', 'mixed'),
        role='filler', max_storeys=5,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=420.0,
        align='left',
        base=dict(kind='gen', style='vernacular', depth=680.0, gf_h=360.0,
                  fl_h=272.0, wall='MI_dist_ochre', trim='MI_paint_cream',
                  roofmat='MI_shingle_brown', seed=1876, open_roof=True,
                  terrace=True),
        tiers=[
            dict(name='the plots',   fill=0.62, floors=0, parapet=30,
                 roof_units=1, stair_head=False),
            dict(name='cottages',    fill=0.88, floors=1, parapet=34,
                 stacks=3, roof_units=1),
            dict(name='the terrace', fill=1.00, floors=2, parapet=40,
                 bay_floors=1, stacks=4, roof_units=1),
            dict(name='the tenement', fill=1.00, floors=3, parapet=48,
                 bay_floors=2, stacks=4, cornice=44, roof_units=2),
            dict(name='mansion flats', fill=1.00, floors=4, parapet=56,
                 needs='M', bay_floors=2, stacks=5, cornice=52, roof_units=2),
            # the same row, converted: the bays stay, the roof gets used
            dict(name='converted flats', fill=1.00, floors=4, parapet=56,
                 needs='M', bay_floors=2, stacks=5, cornice=52,
                 glaze='large', roof_garden=True, roof_units=1),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2200.0 and d >= 620.0),

    # VERNACULAR IV - CIVIC. The public building of the period: a bank, a
    # library, an institute. It sells nothing to the street so it has no
    # shopfront - a rusticated base of deep courses, a flight of steps to a
    # central door, a giant order of engaged columns carrying the cornice,
    # and a stepped pediment over the middle. Symmetry is the point; every
    # other vernacular ladder is asymmetric.
    'vernacular4': dict(
        label='Civic', style='vernacular', district=('civic', 'core'),
        role='actionable', max_storeys=4,
        widths=(1640.0, 2050.0, 2460.0),
        bay_target=430.0,
        align='left',
        base=dict(kind='gen', style='vernacular', depth=800.0, gf_h=470.0,
                  fl_h=330.0, wall='MI_dist_bone', trim='MI_precast_grey',
                  roofmat='MI_shingle_grey', seed=1892, open_roof=True,
                  civic=True),
        tiers=[
            dict(name='the offices', fill=0.70, floors=1, parapet=52,
                 roof_units=1),
            dict(name='the institute', fill=0.90, floors=2, parapet=64,
                 cornice=62, roof_units=1),
            dict(name='the library',  fill=1.00, floors=2, parapet=76,
                 cornice=70, pediment=120.0, roof_units=1, needs='L'),
            dict(name='the bank',     fill=1.00, floors=3, parapet=88,
                 cornice=78, pediment=150.0, roof_units=2, needs='L'),
            dict(name='the exchange', fill=1.00, floors=3, parapet=96,
                 cornice=86, pediment=180.0, pediment_w=0.56,
                 roof_units=2, needs='XL'),
            dict(name='the courthouse', fill=1.00, floors=4, parapet=108,
                 cornice=94, pediment=210.0, pediment_w=0.62,
                 roof_units=3, needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2600.0 and d >= 740.0),

    # VERNACULAR V - THE CORNER. A pub or commercial hotel on a street
    # corner: the corner cut away, the entrance set in the chamfer at an
    # angle to both streets, a cupola over it. The only vernacular designed
    # to be seen from two directions at once, and the one that gives a block
    # its bookend.
    'vernacular5': dict(
        label='The Corner', style='vernacular', district=('mixed', 'resi'),
        role='filler', max_storeys=5,
        widths=(1230.0, 1640.0),
        bay_target=340.0, align='left',
        base=dict(kind='gen', style='vernacular', depth=720.0, gf_h=390.0,
                  fl_h=286.0, wall='MI_dist_oxblood', trim='MI_dist_bone',
                  roofmat='MI_shingle_grey', seed=1884, open_roof=True,
                  chamfer=150.0, corner_side='left'),
        tiers=[
            dict(name='the corner shop', fill=0.72, floors=1, parapet=38,
                 canopy=92, roof_units=1),
            dict(name='the public house', fill=0.92, floors=2, parapet=46,
                 canopy=104, cornice=48, roof_units=1),
            dict(name='the commercial hotel', fill=1.00, floors=3, parapet=58,
                 canopy=104, cornice=56, cupola=190.0, roof_units=2),
            dict(name='the grand', fill=1.00, floors=4, parapet=68,
                 canopy=104, cornice=64, cupola=240.0, roof_units=2, needs='M'),
            dict(name='the station hotel', fill=1.00, floors=5, parapet=78,
                 canopy=104, cornice=72, cupola=290.0, roof_units=3, needs='M'),
            dict(name='the corner conversion', fill=1.00, floors=5, parapet=78,
                 canopy=104, cornice=72, cupola=290.0, glaze='large',
                 roof_garden=True, roof_units=1, needs='M'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 1900.0 and d >= 660.0),

    # VERNACULAR VI - THE MARKET. One big room behind one big wall: a run of
    # tall arched openings with almost no pier between them. A shed with a
    # dignified face, which is what a market hall is.
    'vernacular6': dict(
        label='Market Hall', style='vernacular', district=('mixed', 'goods'),
        role='actionable', max_storeys=3,
        widths=(1640.0, 2050.0, 2460.0),
        bay_target=400.0, align='left',
        base=dict(kind='gen', style='vernacular', depth=860.0, gf_h=520.0,
                  fl_h=300.0, wall='MI_dist_buff', trim='MI_precast_grey',
                  roofmat='MI_shingle_grey', seed=1871, open_roof=True,
                  market=True),
        tiers=[
            dict(name='the stalls',   fill=0.66, floors=0, parapet=44, roof_units=1, stair_head=False),
            dict(name='the arcade',   fill=0.86, floors=0, parapet=54, roof_units=1),
            dict(name='the market',   fill=1.00, floors=1, parapet=66, cornice=54, roof_units=2, needs='L'),
            dict(name='the exchange', fill=1.00, floors=1, parapet=78, cornice=62, roof_units=2, needs='L'),
            dict(name='the corn hall', fill=1.00, floors=2, parapet=88, cornice=70, roof_units=3, needs='XL'),
            dict(name='the market hall', fill=1.00, floors=3, parapet=98, cornice=78, roof_units=3, needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2600.0 and d >= 800.0),

    # VERNACULAR VII - THE CHAPEL. The roof turned end-on to the street so
    # the building shows its section: a stepped gable with a rose window in
    # it, and buttresses stepping back up the flanks. The only vernacular
    # whose silhouette is not a parapet line.
    'vernacular7': dict(
        label='Chapel', style='vernacular', district=('civic', 'resi'),
        role='filler', max_storeys=3,
        widths=(1230.0, 1640.0),
        bay_target=380.0, align='left',
        base=dict(kind='gen', style='vernacular', depth=780.0, gf_h=430.0,
                  fl_h=330.0, wall='MI_dist_bone', trim='MI_precast_grey',
                  roofmat='MI_shingle_brown', seed=1868, open_roof=True,
                  civic=True, buttress=True),
        tiers=[
            dict(name='the mission',  fill=0.70, floors=0, parapet=34, gable=190.0, roof_units=1, stair_head=False),
            dict(name='the meeting house', fill=0.88, floors=1, parapet=40, gable=240.0, roof_units=1),
            dict(name='the chapel',   fill=1.00, floors=1, parapet=48, gable=300.0, cornice=44, roof_units=1),
            dict(name='the institute', fill=1.00, floors=2, parapet=56, gable=350.0, cornice=52, roof_units=2, needs='M'),
            dict(name='the hall',     fill=1.00, floors=2, parapet=64, gable=410.0, cornice=58, roof_units=2, needs='M'),
            dict(name='the church',   fill=1.00, floors=3, parapet=72, gable=470.0, cornice=64, roof_units=2, needs='M'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 1900.0 and d >= 720.0),

    # VERNACULAR VIII - THE MEWS. The smallest building in the catalogue and
    # the one a city is actually mortared together with: a low workshop with
    # wide doors and very little else. Every street needs something that is
    # not trying.
    'vernacular8': dict(
        label='Mews', style='vernacular', district=('goods', 'resi'),
        role='filler', max_storeys=3,
        widths=(820.0, 1230.0),
        bay_target=300.0, align='left',
        base=dict(kind='gen', style='vernacular', depth=620.0, gf_h=330.0,
                  fl_h=248.0, wall='MI_dist_slate', trim='MI_dist_bone',
                  roofmat='MI_shingle_brown', seed=1897, open_roof=True,
                  loft=True),
        tiers=[
            dict(name='the lock-up',  fill=0.62, floors=0, parapet=26, roof_units=1, stair_head=False),
            dict(name='the workshop', fill=0.84, floors=1, parapet=30, roof_units=1),
            dict(name='the mews',     fill=1.00, floors=2, parapet=34, roof_units=1),
            dict(name='the mews flat', fill=1.00, floors=2, parapet=38, corbel=True, cornice=34, roof_units=1),
            dict(name='the yard house', fill=1.00, floors=3, parapet=42, corbel=True, cornice=38, roof_units=2),
            dict(name='the mews conversion', fill=1.00, floors=3, parapet=42, corbel=True,
                 cornice=38, glaze='large', roof_garden=True, roof_units=1),
        ],
        fits=lambda w, d: 700.0 <= w <= 1400.0 and d >= 560.0),

    # ACTIONABLE. The building a player places and grows on purpose, and the
    # one that answers CANON slot 5: tight-packed towers of real height,
    # silhouette and massing carrying everything, printed-grid facades that
    # are exactly enough at city range. Seven tiers, ending at 24 storeys.
    #
    # The ladder is a DEVELOPMENT story rather than a life story: a cleared
    # site becomes a podium, the podium grows a shaft, the shaft grows a
    # crown. Slot 5's towers all carry a rooftop hut, which is where
    # roof_units earns its place at every tier above the podium.
    'tower': dict(
        label='Tower', style='modern', district=('office', 'core'),
        role='actionable', max_storeys=24,
        # A tower needs LAND before it needs height. `needs` on each tier is
        # the minimum parcel it can stand on, so a tower on an M lot tops out
        # as a low block and the only way up is to assemble the parcel next
        # door - see parcels.py. That is the mechanic: growth is a decision
        # with a cost, not a timer.
        widths=(1230.0, 1640.0, 2050.0, 2460.0),
        bay_target=300.0,
        align='left',
        base=dict(kind='gen', style='modern', depth=760.0, gf_h=420.0,
                  fl_h=300.0, wall='MI_dist_slate', trim='MI_dist_bone',
                  roofmat='MI_shingle_grey', seed=907,
                  # core stops at the roof line so the deck, plant and stair
                  # head are visible; build_modern closes the void with a
                  # rear parapet in exchange
                  open_roof=True),
        tiers=[
            dict(name='hoarding',    fill=0.55, floors=0,  parapet=30),
            dict(name='podium',      fill=0.85, floors=1,  parapet=40),
            dict(name='low block',   fill=1.00, floors=3,  parapet=45,
                 roof_units=1),
            dict(name='mid rise',    fill=1.00, floors=7,  parapet=55,
                 needs='L', roof_units=1),
            dict(name='high rise',   fill=1.00, floors=12, parapet=70,
                 needs='L', setback=80, setback_floors=1, roof_units=2),
            dict(name='tower',       fill=1.00, floors=18, parapet=85,
                 needs='XL', setback=90, setback_floors=2, roof_units=2),
            dict(name='landmark',    fill=1.00, floors=23, parapet=110,
                 needs='XXL', setback=100, setback_floors=3, roof_units=3),
        ],
        # Up to XXL, not 1800. `widths` declared 2050 and 2460 while `fits`
        # capped at 1800, so grammar.candidates returned NOTHING for an
        # assembled parcel - the whole assembly mechanic was unreachable
        # through the grammar. The two must agree; _selftest asserts it now.
        fits=lambda w, d: 1100.0 <= w <= 2500.0 and d >= 700.0),

    # MODERN II - BRUTALIST PRECAST. Same decade as the ribbon block and its
    # opposite. v1 hangs glass behind a proud spandrel band; this is a heavy
    # precast frame with the windows sunk 46 uu inside it, so the shadow does
    # the work. That is why it reads at city range where a curtain wall needs
    # its mullions to be legible.
    #
    # The expressed service shaft running past the parapet is the other half
    # of the idea: the one thing that stops a brutalist block being a box.
    'modern2': dict(
        label='Precast', style='modern', district=('civic', 'office'),
        role='actionable', max_storeys=16,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=310.0,
        align='left',
        base=dict(kind='gen', style='modern', depth=780.0, gf_h=430.0,
                  fl_h=292.0, wall='MI_concrete', trim='MI_dist_slate',
                  roofmat='MI_shingle_grey', seed=1971, open_roof=True,
                  precast=True),
        tiers=[
            dict(name='cleared site', fill=0.55, floors=0, parapet=28,
                 roof_units=1, stair_head=False),
            dict(name='the deck',     fill=0.85, floors=1, parapet=34,
                 roof_units=1),
            dict(name='civic block',  fill=1.00, floors=4, parapet=42,
                 roof_units=1, service_tower=True),
            dict(name='the ministry', fill=1.00, floors=8, parapet=50,
                 needs='M', roof_units=2, service_tower=True),
            dict(name='the estate',   fill=1.00, floors=12, parapet=58,
                 needs='L', roof_units=2, service_tower=True),
            dict(name='the megastructure', fill=1.00, floors=16, parapet=66,
                 needs='L', roof_units=3, service_tower=True,
                 setback=70.0, setback_floors=1),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # MODERN III - THE PAVILION. The Miesian box. Not ribbon glazing behind a
    # band (v1), not a precast frame with sunk windows (v2), but floor-to-
    # ceiling glass with the STEEL SHOWN: I-section mullions standing proud
    # of the glass the full height of every storey, and a hairline slab edge
    # between floors. Dark metal against clear glass, nothing else.
    #
    # The most restrained facade in the catalogue, and the hardest: with
    # nothing else on the elevation, the mullion rhythm IS the building.
    'modern3': dict(
        label='Pavilion', style='modern', district=('office', 'core'),
        role='actionable', max_storeys=14,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=300.0,
        align='left',
        base=dict(kind='gen', style='modern', depth=770.0, gf_h=440.0,
                  fl_h=284.0, wall='MI_dark_metal', trim='MI_precast_grey',
                  roofmat='MI_shingle_grey', seed=1958, open_roof=True,
                  steel_frame=True, mull_step=118.0),
        tiers=[
            dict(name='the plaza',   fill=0.55, floors=0, parapet=24,
                 roof_units=1, stair_head=False),
            dict(name='the lobby',   fill=0.85, floors=1, parapet=28,
                 roof_units=1),
            dict(name='low pavilion', fill=1.00, floors=3, parapet=32,
                 roof_units=1),
            dict(name='the office',  fill=1.00, floors=6, parapet=36,
                 needs='M', roof_units=1),
            dict(name='the seagram', fill=1.00, floors=10, parapet=40,
                 needs='L', roof_units=2),
            dict(name='the plaza tower', fill=1.00, floors=14, parapet=46,
                 needs='L', roof_units=2),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # MODERN IV - THE SLAB. Postwar housing: a continuous access deck the
    # full length of the building at every floor, a solid balustrade in front
    # of it, front doors and small windows in shadow behind. The horizontal
    # repeat is relentless on purpose - that IS the building, and it is the
    # exact opposite of the pavilion's restraint while belonging to the same
    # fifteen years.
    'modern4': dict(
        label='Slab', style='modern', district=('resi', 'mixed'),
        role='filler', max_storeys=12,
        widths=(1640.0, 2050.0, 2460.0),
        bay_target=300.0,
        align='left',
        base=dict(kind='gen', style='modern', depth=740.0, gf_h=360.0,
                  fl_h=268.0, wall='MI_precast_grey', trim='MI_dist_slate',
                  roofmat='MI_shingle_grey', seed=1966, open_roof=True,
                  deck_access=True),
        tiers=[
            dict(name='the maisonettes', fill=0.80, floors=2, parapet=26,
                 roof_units=1),
            dict(name='low rise',    fill=1.00, floors=4, parapet=30,
                 roof_units=1),
            dict(name='the block',   fill=1.00, floors=6, parapet=34,
                 roof_units=1, needs='L'),
            dict(name='the estate',  fill=1.00, floors=8, parapet=38,
                 roof_units=2, needs='L'),
            dict(name='point block', fill=1.00, floors=10, parapet=42,
                 roof_units=2, needs='XL'),
            dict(name='the slab',    fill=1.00, floors=12, parapet=46,
                 roof_units=3, needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2600.0 and d >= 700.0),

    # MODERN V - SPANDREL. The 1960s curtain wall whose panels are a COLOUR.
    # Same generator and same geometry as the tower, one role changed: the
    # spandrel takes the accent instead of the wall, so the district palette
    # drives a band of real colour across every floor. The cheapest distinct
    # building in the catalogue, and it belongs here precisely because
    # "buildings are parameter sets" is meant to buy exactly this.
    'modern5': dict(
        label='Spandrel', style='modern', district=('office', 'mixed'),
        role='filler', max_storeys=14,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=290.0, align='left',
        base=dict(kind='gen', style='modern', depth=750.0, gf_h=400.0,
                  fl_h=276.0, wall='MI_dist_bone', trim='MI_precast_grey',
                  roofmat='MI_shingle_grey', seed=1963, open_roof=True,
                  spandrel_colour=True),
        tiers=[
            dict(name='the showroom', fill=0.80, floors=1, parapet=28, roof_units=1),
            dict(name='low block',    fill=1.00, floors=3, parapet=32, roof_units=1),
            dict(name='the offices',  fill=1.00, floors=6, parapet=36, roof_units=1, needs='M'),
            dict(name='the centre',   fill=1.00, floors=9, parapet=40, roof_units=2, needs='L'),
            dict(name='the point',    fill=1.00, floors=12, parapet=44, roof_units=2, needs='L'),
            dict(name='the spandrel tower', fill=1.00, floors=14, parapet=48,
                 roof_units=3, needs='XL', setback=64.0, setback_floors=1),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # MODERN VI - PODIUM. A wide retail podium with a slim slab set back on
    # top of it: the planning diagram of the era made into a building, and the
    # only modern here whose interest is entirely in the massing.
    #
    # This is the recipe that forced P12. It was drawn as a podium, could not
    # be built because cores only did PROGRESSIVE setbacks - eight stepping
    # floors accumulated to 800 uu on an 820-deep building and GATE-05 refused
    # it at 991 - and shipped as a taper instead. `setback_mode='constant'`
    # exists now, so it is a podium again: every floor above the podium sits
    # back by the SAME amount. One step, not a stair.
    'modern6': dict(
        label='Podium', style='modern', district=('core', 'office'),
        role='actionable', max_storeys=15,
        widths=(1640.0, 2050.0, 2460.0),
        bay_target=310.0, align='left',
        base=dict(kind='gen', style='modern', depth=820.0, gf_h=440.0,
                  fl_h=282.0, wall='MI_dist_slate', trim='MI_precast_grey',
                  roofmat='MI_shingle_grey', seed=1969, open_roof=True,
                  setback_mode='constant'),
        tiers=[
            dict(name='the podium',   fill=0.92, floors=2, parapet=30, roof_units=1),
            dict(name='podium + 2',   fill=1.00, floors=4, parapet=34, roof_units=1, setback=150.0, setback_floors=2),
            dict(name='podium + 4',   fill=1.00, floors=7, parapet=38, roof_units=2, setback=165.0, setback_floors=4, needs='L'),
            dict(name='podium + 6',   fill=1.00, floors=10, parapet=42, roof_units=2, setback=175.0, setback_floors=6, needs='L'),
            dict(name='the civic centre', fill=1.00, floors=13, parapet=46, roof_units=3, setback=185.0, setback_floors=8, needs='XL'),
            dict(name='the complex',  fill=1.00, floors=15, parapet=50, roof_units=3, setback=195.0, setback_floors=10, needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2600.0 and d >= 760.0),

    # MODERN VII - CHEQUERBOARD. The window is not a hole in a wall, it is
    # the bottom of a deep square box, so every opening carries a full frame
    # of shadow on all four sides. The most three-dimensional facade in the
    # catalogue and the most repetitive - exactly the trade the era made.
    'modern7': dict(
        label='Chequerboard', style='modern', district=('office', 'civic'),
        role='filler', max_storeys=14,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=270.0, align='left',
        base=dict(kind='gen', style='modern', depth=760.0, gf_h=400.0,
                  fl_h=280.0, wall='MI_precast_grey', trim='MI_dist_bone',
                  roofmat='MI_shingle_grey', seed=1964, open_roof=True,
                  coffer=True),
        tiers=[
            dict(name='the annexe',   fill=0.82, floors=2, parapet=28, roof_units=1),
            dict(name='low block',    fill=1.00, floors=4, parapet=32, roof_units=1),
            dict(name='the offices',  fill=1.00, floors=7, parapet=36, roof_units=1, needs='M'),
            dict(name='the ministry', fill=1.00, floors=10, parapet=40, roof_units=2, needs='L'),
            dict(name='the tower',    fill=1.00, floors=12, parapet=44, roof_units=2, needs='L'),
            dict(name='the chequerboard', fill=1.00, floors=14, parapet=48, roof_units=3, needs='XL'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 720.0),

    # MODERN VIII - ROADSIDE. Googie: the mass lifted on splayed legs over a
    # glazed void, the slab cantilevering past them. Not one vertical on it,
    # which is the opposite of every other modern here.
    'modern8': dict(
        label='Roadside', style='modern', district=('mixed', 'goods'),
        role='filler', max_storeys=4,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=340.0, align='left',
        base=dict(kind='gen', style='modern', depth=760.0, gf_h=430.0,
                  fl_h=272.0, wall='MI_dist_teal', trim='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=1959, open_roof=True,
                  canted=True),
        tiers=[
            dict(name='the stand',    fill=0.66, floors=0, parapet=24, roof_units=1, stair_head=False),
            dict(name='the diner',    fill=0.84, floors=1, parapet=28, roof_units=1),
            dict(name='the motel',    fill=1.00, floors=2, parapet=32, roof_units=1),
            dict(name='the showroom', fill=1.00, floors=2, parapet=36, roof_units=2),
            dict(name='the lanes',    fill=1.00, floors=3, parapet=40, roof_units=2, needs='M'),
            dict(name='the plaza',    fill=1.00, floors=4, parapet=44, roof_units=2, needs='M'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # ACTIONABLE, and deliberately the OPPOSITE of the tower. Modern is
    # horizontal - ribbon glazing behind a proud spandrel band. Deco is
    # vertical: unbroken fluted pilasters from base to parapet with the
    # glazing recessed into the channels between them. Set beside the
    # vernacular bay rhythm the three read as three eras, which is the whole
    # point of having more than one generator.
    #
    # THE LADDER GROWS AT THE TOP, not in the middle. build_deco runs its
    # pilasters as single pieces the full height of the building, so a floor
    # setback would tear the shaft apart - `setback` is not used here and that
    # is a property of the style, not an omission. What grows instead is the
    # CROWN: `crown_step` takes the stepped parapet from a flat coping on a
    # showroom to a ziggurat on the beacon, and the top tier earns a mast.
    'deco': dict(
        label='Deco', style='deco', district=('civic', 'core'),
        role='actionable', max_storeys=12,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=330.0,
        align='left',
        base=dict(kind='gen', style='deco', depth=740.0, gf_h=460.0,
                  fl_h=290.0, wall='MI_dist_bone', trim='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=1931, open_roof=True),
        tiers=[
            dict(name='showroom',   fill=0.60, floors=0,  parapet=34,
                 crown_step=1.00, roof_units=1, stair_head=False),
            dict(name='emporium',   fill=0.85, floors=1,  parapet=42,
                 crown_step=1.25, roof_units=1),
            dict(name='chambers',   fill=1.00, floors=3,  parapet=54,
                 crown_step=1.55, roof_units=1),
            dict(name='the exchange', fill=1.00, floors=5, parapet=74,
                 crown_step=1.90, roof_units=2, needs='M'),
            dict(name='ziggurat',   fill=1.00, floors=8,  parapet=96,
                 crown_step=2.30, roof_units=2, needs='L'),
            dict(name='the beacon', fill=1.00, floors=11, parapet=124,
                 crown_step=2.80, roof_units=3, needs='L', mast=340.0),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2100.0 and d >= 680.0),

    # DECO II - STREAMLINE MODERNE. The same decade turned on its side.
    # Deco proper (v1) pulls the eye up with unbroken fluted pilasters and
    # crowns itself with a ziggurat. Streamline drives it ALONG: three speed
    # stripes wrapping the whole frontage, ribbon glazing that never breaks,
    # a rounded end stepped in plan the way a modelmaker fakes a radius, and
    # one vertical fin as the single upright in a building of horizontals.
    #
    # Lower and longer than v1 on purpose - streamline is a cinema, a bus
    # station, a department store, not a tower.
    'deco2': dict(
        label='Streamline', style='deco', district=('civic', 'mixed'),
        role='filler', max_storeys=6,
        widths=(1640.0, 2050.0),
        bay_target=360.0,
        align='left',
        base=dict(kind='gen', style='deco', depth=760.0, gf_h=420.0,
                  fl_h=286.0, wall='MI_dist_bone', trim='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=1937, open_roof=True,
                  streamline=True, corner_side='left', corner_radius=170.0),
        tiers=[
            dict(name='parade',      fill=0.70, floors=0, parapet=44,
                 crown_step=1.0, roof_units=1, stair_head=False),
            dict(name='showrooms',   fill=0.88, floors=1, parapet=52,
                 crown_step=1.0, roof_units=1),
            dict(name='the picture house', fill=1.00, floors=2, parapet=68,
                 crown_step=1.0, roof_units=1, fin=180.0),
            dict(name='the emporium', fill=1.00, floors=4, parapet=78,
                 crown_step=1.0, roof_units=2, needs='L', fin=230.0),
            dict(name='terminal',    fill=1.00, floors=5, parapet=88,
                 crown_step=1.0, roof_units=2, needs='L', fin=280.0,
                 corner_radius=210.0),
            dict(name='the airline building', fill=1.00, floors=6, parapet=96,
                 crown_step=1.0, roof_units=3, needs='XL', fin=340.0,
                 corner_radius=240.0),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2300.0 and d >= 700.0),

    # DECO III - THE WORKS. Deco industrial: a power station or pumping
    # works. Brick piers run the FULL height with one enormous arched bay
    # between each pair and no storeys expressed at all, which is what makes
    # it read as industry rather than offices. The arch is stepped in five
    # courses - how a card model makes a semicircle, and how a bricklayer
    # makes a relieving arch anyway.
    #
    # Cites CANON SLOT 4 (worksyard), blessed for "works massing & rooftop
    # kit - pier-and-spandrel mill blocks with banded brick, lattice water
    # tower, stack". The stack is the silhouette that carries it.
    'deco3': dict(
        label='The Works', style='deco', district=('works', 'civic'),
        role='actionable', max_storeys=6,
        widths=(1640.0, 2050.0, 2460.0),
        bay_target=430.0,
        align='left',
        base=dict(kind='gen', style='deco', depth=820.0, gf_h=430.0,
                  fl_h=300.0, wall='MI_dist_brick', trim='MI_precast_grey',
                  roofmat='MI_shingle_grey', seed=1934, open_roof=True,
                  giant_order=True),
        tiers=[
            dict(name='the shed',     fill=0.66, floors=1, parapet=48,
                 crown_step=1.0, roof_units=1),
            dict(name='pump house',   fill=0.86, floors=2, parapet=58,
                 crown_step=1.0, roof_units=1, stack=260.0),
            dict(name='the works',    fill=1.00, floors=3, parapet=70,
                 crown_step=1.0, roof_units=2, stack=380.0, needs='L'),
            dict(name='turbine hall', fill=1.00, floors=4, parapet=84,
                 crown_step=1.0, roof_units=2, stack=520.0, needs='L'),
            dict(name='the generating station', fill=1.00, floors=5,
                 parapet=96, crown_step=1.0, roof_units=3, stack=700.0,
                 needs='XL'),
            dict(name='the power station', fill=1.00, floors=6, parapet=110,
                 crown_step=1.0, roof_units=3, stack=880.0, needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2600.0 and d >= 760.0),

    # DECO IV - THE PICTURE PALACE. A cinema. The blade sign standing clear
    # of the parapet is the tallest thing on a low building and the reason
    # you can find it from the end of the street; the marquee is deco's one
    # horizontal gesture on a facade of verticals, and it is what turns a
    # frontage into an entrance.
    'deco4': dict(
        label='Picture Palace', style='deco', district=('civic', 'mixed'),
        role='actionable', max_storeys=5,
        widths=(1640.0, 2050.0),
        bay_target=380.0,
        align='left',
        base=dict(kind='gen', style='deco', depth=800.0, gf_h=480.0,
                  fl_h=300.0, wall='MI_dist_ochre', trim='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=1929, open_roof=True),
        tiers=[
            dict(name='the nickelodeon', fill=0.70, floors=1, parapet=48,
                 crown_step=1.2, roof_units=1),
            dict(name='the picture house', fill=0.88, floors=1, parapet=58,
                 crown_step=1.5, roof_units=1, marquee=92.0),
            dict(name='the odeon',    fill=1.00, floors=2, parapet=72,
                 crown_step=1.9, roof_units=1, marquee=98.0, blade=200.0),
            dict(name='the roxy',     fill=1.00, floors=3, parapet=86,
                 crown_step=2.2, roof_units=2, marquee=98.0, blade=280.0,
                 needs='L'),
            dict(name='the palace',   fill=1.00, floors=4, parapet=98,
                 crown_step=2.5, roof_units=2, marquee=98.0, blade=360.0,
                 needs='L'),
            dict(name='the picture palace', fill=1.00, floors=5, parapet=110,
                 crown_step=2.8, roof_units=3, marquee=98.0, blade=440.0,
                 needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2300.0 and d >= 740.0),

    # DECO V - ZIGZAG. The deco most people picture: a chevron band across
    # every spandrel, built as a stepped V from short boxes. Cut card does
    # chevrons beautifully and curves badly, which is most of why deco
    # ornament suits this project - the ornament IS the fabrication method.
    'deco5': dict(
        label='Zigzag', style='deco', district=('core', 'civic'),
        role='actionable', max_storeys=11,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=320.0, align='left',
        base=dict(kind='gen', style='deco', depth=740.0, gf_h=440.0,
                  fl_h=284.0, wall='MI_dist_ochre', trim='MI_dist_bone',
                  roofmat='MI_shingle_grey', seed=1926, open_roof=True,
                  chevron=True),
        tiers=[
            dict(name='the frontage', fill=0.68, floors=1, parapet=40, crown_step=1.15, roof_units=1),
            dict(name='the chambers', fill=0.90, floors=3, parapet=52, crown_step=1.45, roof_units=1),
            dict(name='the emporium', fill=1.00, floors=5, parapet=66, crown_step=1.80, roof_units=2, needs='M'),
            dict(name='the tower',    fill=1.00, floors=7, parapet=80, crown_step=2.15, roof_units=2, needs='L'),
            dict(name='the zigzag',   fill=1.00, floors=9, parapet=94, crown_step=2.50, roof_units=3, needs='L'),
            dict(name='the chrysler', fill=1.00, floors=11, parapet=110, crown_step=2.85,
                 roof_units=3, needs='XL', mast=300.0),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # DECO VI - APARTMENTS. The same elevation turned residential by one
    # move: a shallow balcony with a solid front and a banded rail on every
    # other bay. The period put these on every block of flats it built.
    'deco6': dict(
        label='Deco Flats', style='deco', district=('resi', 'mixed'),
        role='filler', max_storeys=9,
        widths=(1230.0, 1640.0, 2050.0),
        # WIDER BAYS and shallower floors than the office recipes. Flats have
        # rooms, not office floorplates, and the proportion is half of why
        # this now reads as a different building.
        bay_target=430.0, align='left',
        base=dict(kind='gen', style='deco', depth=740.0, gf_h=360.0,
                  fl_h=252.0, wall='MI_dist_buff', trim='MI_dist_oxblood',
                  roofmat='MI_shingle_grey', seed=1935, open_roof=True,
                  deco_balcony=True, flats=True),
        tiers=[
            dict(name='the maisonettes', fill=0.78, floors=2, parapet=36, crown_step=1.1, roof_units=1),
            dict(name='the mansions',    fill=1.00, floors=4, parapet=44, crown_step=1.3, roof_units=1),
            dict(name='the court',       fill=1.00, floors=5, parapet=52, crown_step=1.5, roof_units=2, needs='M'),
            dict(name='the apartments',  fill=1.00, floors=7, parapet=60, crown_step=1.7, roof_units=2, needs='M'),
            dict(name='the sun flats',   fill=1.00, floors=8, parapet=68, crown_step=1.9, roof_units=2, needs='L'),
            dict(name='the lido block',  fill=1.00, floors=9, parapet=76, crown_step=2.1, roof_units=3, needs='L'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # DECO VII - TERMINAL. A civic timepiece on the skyline: a square clock
    # tower stepping in twice before the dial stage, set at one end of a long
    # low front. Station, town hall, ferry terminal.
    'deco7': dict(
        label='Terminal', style='deco', district=('civic', 'core'),
        role='actionable', max_storeys=5,
        widths=(2050.0, 2460.0),
        bay_target=400.0, align='left',
        base=dict(kind='gen', style='deco', depth=840.0, gf_h=460.0,
                  fl_h=300.0, wall='MI_precast_buff', trim='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=1932, open_roof=True),
        tiers=[
            dict(name='the halt',     fill=0.70, floors=1, parapet=42, crown_step=1.1, roof_units=1),
            dict(name='the booking hall', fill=0.90, floors=1, parapet=52, crown_step=1.3, roof_units=1, clock=260.0),
            dict(name='the station',  fill=1.00, floors=2, parapet=64, crown_step=1.5, roof_units=2, clock=340.0, needs='XL'),
            dict(name='the terminal', fill=1.00, floors=3, parapet=76, crown_step=1.7, roof_units=2, clock=430.0, needs='XL'),
            dict(name='the union station', fill=1.00, floors=4, parapet=86, crown_step=1.9, roof_units=3, clock=520.0, needs='XL'),
            dict(name='the city hall', fill=1.00, floors=5, parapet=96, crown_step=2.1, roof_units=3, clock=620.0, needs='XXL'),
        ],
        fits=lambda w, d: 1800.0 <= w <= 2600.0 and d >= 800.0),

    # DECO VIII - THE SLAB. Deco with the ornament taken off: banded, plain,
    # and relying entirely on proportion and the horizontal courses. What
    # the style built when there was no budget, and every district needs its
    # quiet buildings.
    'deco8': dict(
        label='Deco Slab', style='deco', district=('office', 'mixed'),
        role='filler', max_storeys=8,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=300.0, align='left',
        base=dict(kind='gen', style='deco', depth=730.0, gf_h=400.0,
                  fl_h=268.0, wall='MI_precast_grey', trim='MI_dist_bone',
                  roofmat='MI_shingle_grey', seed=1938, open_roof=True,
                  banded=True),
        tiers=[
            dict(name='the frontage', fill=0.80, floors=2, parapet=32, crown_step=1.0, roof_units=1),
            dict(name='the offices',  fill=1.00, floors=3, parapet=38, crown_step=1.0, roof_units=1),
            dict(name='the chambers', fill=1.00, floors=5, parapet=44, crown_step=1.1, roof_units=1, needs='M'),
            dict(name='the block',    fill=1.00, floors=6, parapet=50, crown_step=1.2, roof_units=2, needs='M'),
            dict(name='the works office', fill=1.00, floors=7, parapet=56, crown_step=1.3, roof_units=2, needs='L'),
            dict(name='the slab',     fill=1.00, floors=8, parapet=62, crown_step=1.4, roof_units=2, needs='L'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 690.0),

    # THE WORKHORSE. Vernacular is period filler, deco a civic landmark, the
    # tower a highrise - and none of them is what a city actually gets built
    # out of now. This is the contemporary mixed-use mid-rise: retail at
    # grade, five or six floors over it, two claddings, loggias and balconies.
    #
    # It grows by MASSING. `shift` steps the top volume back to make a
    # terrace, `loggia_frac` and `balcony_frac` are fractions rather than bay
    # indices so the same recipe survives every parcel on the ladder, and the
    # stagger walks the openings diagonally up the elevation.
    'contemporary': dict(
        label='Contemporary', style='contemporary',
        district=('mixed', 'core'),
        role='actionable', max_storeys=17,
        widths=(1230.0, 1640.0, 2050.0, 2460.0),
        bay_target=340.0,
        align='left',
        # CANON SLOT 5 (highrise). Blessed for "the highrise city read - tight
        # packed towers of real height, silhouette and massing carrying
        # everything, printed-grid facades that are exactly enough at city
        # range", and for kit-family coherence. Its design signal - "recipe
        # ladders must grow past t5" - is why this one runs to seven tiers
        # and seventeen storeys rather than stopping at nine.
        #
        # COLOUR IS THE IDENTITY. Slot 5's towers are teal, green, black,
        # cream: each tower is one colour and the variety lives BETWEEN
        # buildings. The glass is therefore a real choice here, and the
        # district palette drives it per instance.
        base=dict(kind='gen', style='contemporary', depth=780.0, gf_h=400.0,
                  fl_h=272.0, wall='MI_dist_slate', trim='MI_paint_cream',
                  panel_b='MI_dist_bone', panels={'B': 'MI_dist_bone'},
                  roofmat='MI_shingle_grey', seed=2019, open_roof=True,
                  mullion_step=88.0, core_bays=1),
        tiers=[
            dict(name='hoarding',    fill=0.55, floors=0, parapet=26,
                 roof_units=1, stair_head=False),
            dict(name='retail pavilion', fill=0.80, floors=1, parapet=30,
                 roof_units=1),
            dict(name='the podium',  fill=1.00, floors=3, parapet=34,
                 roof_units=1, core_side='right'),
            dict(name='office block', fill=1.00, floors=6, parapet=38,
                 needs='M', roof_units=1, core_side='right',
                 mech=dict(w=0.30, h=110.0, at=0.26)),
            dict(name='the tower',   fill=1.00, floors=10, parapet=42,
                 needs='L', roof_units=1, core_side='left',
                 mech=dict(w=0.32, h=140.0, at=0.34)),
            dict(name='the high tower', fill=1.00, floors=14, parapet=46,
                 needs='L', roof_units=1, core_side='right',
                 mech=dict(w=0.34, h=165.0, at=0.28)),
            # ONE step, right at the top, and only on the last tier. A prism
            # is the canon read; this is the single concession to a crown.
            dict(name='the landmark', fill=1.00, floors=17, parapet=52,
                 needs='XL', roof_units=1, core_side='left',
                 setback=70.0, setback_floors=1,
                 mech=dict(w=0.30, h=185.0, at=0.36)),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2500.0 and d >= 700.0),

    # CONTEMPORARY II - MASS TIMBER. The other building of the last fifteen
    # years, and the Portland one: a CLT frame with its glulam columns and
    # beams SHOWN on the elevation instead of a curtain wall hiding the
    # structure behind glass. Punched openings with deep timber reveals,
    # slat balustrades, warm cladding between the members.
    #
    # It stops at eight storeys ON PURPOSE. CLT builds six to eight; a
    # mass-timber tower would be a lie about the material, and the whole
    # value of a second contemporary recipe is that it is honestly a
    # different building rather than the first one in a different colour.
    'contemporary2': dict(
        label='Mass Timber', style='contemporary',
        district=('mixed', 'green'),
        role='filler', max_storeys=8,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=350.0,
        align='left',
        base=dict(kind='gen', style='contemporary', depth=760.0, gf_h=390.0,
                  fl_h=280.0, wall='MI_wood', trim='MI_paint_cream',
                  panel_b='MI_dist_bone', panels={'B': 'MI_dist_bone'},
                  roofmat='MI_shingle_grey', seed=2021, open_roof=True,
                  timber=True),
        tiers=[
            dict(name='hoarding',     fill=0.55, floors=0, parapet=24,
                 roof_units=1, stair_head=False),
            dict(name='the pavilion', fill=0.80, floors=1, parapet=28,
                 roof_units=1),
            dict(name='timber walk-up', fill=1.00, floors=3, parapet=32,
                 roof_units=1),
            dict(name='the CLT block', fill=1.00, floors=5, parapet=36,
                 needs='M', roof_units=2),
            dict(name='the timber loft', fill=1.00, floors=7, parapet=40,
                 needs='M', roof_units=2, roof_garden=True),
            dict(name='the tall timber', fill=1.00, floors=8, parapet=44,
                 needs='L', roof_units=2, roof_garden=True),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 680.0),

    # CONTEMPORARY III - RAINSCREEN. A skin of flat metal panels with REVEAL
    # JOINTS between them and the windows placed in a rhythm that refuses to
    # line up into a grid. The irregularity is a RULE, not a scatter: the
    # openings walk by a co-prime step so they never stack into a stripe. A
    # random facade reads as broken; a syncopated one reads as designed.
    'contemporary3': dict(
        label='Rainscreen', style='contemporary',
        district=('mixed', 'office'),
        role='filler', max_storeys=10,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=330.0,
        align='left',
        base=dict(kind='gen', style='contemporary', depth=760.0, gf_h=380.0,
                  fl_h=266.0, wall='MI_dist_slate', trim='MI_dark_metal',
                  panel_b='MI_precast_grey', panels={'B': 'MI_precast_grey'},
                  roofmat='MI_shingle_grey', seed=2023, open_roof=True,
                  rainscreen=True),
        tiers=[
            dict(name='hoarding',    fill=0.55, floors=0, parapet=24,
                 roof_units=1, stair_head=False),
            dict(name='the unit',    fill=0.82, floors=1, parapet=28,
                 roof_units=1),
            dict(name='the studios', fill=1.00, floors=4, parapet=32,
                 roof_units=1),
            dict(name='the works building', fill=1.00, floors=6, parapet=36,
                 needs='M', roof_units=2),
            dict(name='the stack',   fill=1.00, floors=8, parapet=40,
                 needs='M', roof_units=2, roof_garden=True),
            dict(name='the long block', fill=1.00, floors=10, parapet=44,
                 needs='L', roof_units=2, roof_garden=True),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 680.0),

    # CONTEMPORARY IV - STACKED. The contemporary building that is COMPOSED
    # rather than clad: blocks of floors each stepping the opposite way from
    # the last, so the mass cantilevers over itself. The whole read is the
    # shadow under a cantilever, which is why the shifts are large and the
    # elevation carries almost nothing else.
    'contemporary4': dict(
        label='Stacked', style='contemporary', district=('mixed', 'core'),
        role='actionable', max_storeys=12,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=330.0,
        align='left',
        base=dict(kind='gen', style='contemporary', depth=800.0, gf_h=390.0,
                  fl_h=272.0, wall='MI_dist_bone', trim='MI_paint_cream',
                  panel_b='MI_dist_slate', panels={'B': 'MI_dist_slate'},
                  roofmat='MI_shingle_grey', seed=2018, open_roof=True,
                  stacked=True),
        tiers=[
            dict(name='hoarding',    fill=0.55, floors=0, parapet=24,
                 roof_units=1, stair_head=False),
            dict(name='the base',    fill=0.82, floors=2, parapet=28,
                 roof_units=1, stack_blocks=2, stack_shift=70.0),
            dict(name='two boxes',   fill=1.00, floors=4, parapet=32,
                 roof_units=1, stack_blocks=2, stack_shift=95.0),
            dict(name='three boxes', fill=1.00, floors=7, parapet=36,
                 needs='M', roof_units=2, stack_blocks=3, stack_shift=105.0),
            dict(name='the cantilever', fill=1.00, floors=10, parapet=40,
                 needs='L', roof_units=2, stack_blocks=4, stack_shift=115.0,
                 roof_garden=True),
            dict(name='the stack',   fill=1.00, floors=12, parapet=44,
                 needs='L', roof_units=2, stack_blocks=4, stack_shift=125.0,
                 roof_garden=True),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 720.0),

    # CONTEMPORARY V - BRICK. The quiet contemporary building: a brick
    # rainscreen with large punched openings and deep reveals, and none of
    # v3's syncopation - the panels are big, the rhythm lines up, and the
    # interest is entirely in the depth of the reveal and the warmth of the
    # material. Every district needs buildings that do not shout.
    'contemporary5': dict(
        label='Brick', style='contemporary', district=('mixed', 'resi'),
        role='filler', max_storeys=9,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=340.0, align='left',
        base=dict(kind='gen', style='contemporary', depth=750.0, gf_h=370.0,
                  fl_h=274.0, wall='MI_dist_brick', trim='MI_precast_grey',
                  panel_b='MI_dist_oxblood', panels={'B': 'MI_dist_oxblood'},
                  roofmat='MI_shingle_grey', seed=2016, open_roof=True,
                  rainscreen=True, regular=True),
        tiers=[
            dict(name='hoarding',   fill=0.55, floors=0, parapet=22, roof_units=1, stair_head=False),
            dict(name='the shop',   fill=0.82, floors=2, parapet=26, roof_units=1),
            dict(name='the block',  fill=1.00, floors=4, parapet=30, roof_units=1),
            dict(name='the courtyard', fill=1.00, floors=6, parapet=34, needs='M', roof_units=2),
            dict(name='the brick building', fill=1.00, floors=8, parapet=38,
                 needs='M', roof_units=2, roof_garden=True),
            dict(name='the warehouse flats', fill=1.00, floors=9, parapet=42,
                 needs='L', roof_units=2, roof_garden=True),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 700.0),

    # CONTEMPORARY VI - TERRACES. The building as a hillside: every storey
    # steps back from the one below and the slab it leaves is planted. The
    # only recipe where the greenery is structural - take the planting away
    # and it is just a ziggurat.
    'contemporary6': dict(
        label='Terraces', style='contemporary', district=('green', 'resi'),
        role='actionable', max_storeys=10,
        widths=(1640.0, 2050.0, 2460.0),
        bay_target=350.0, align='left',
        base=dict(kind='gen', style='contemporary', depth=900.0, gf_h=380.0,
                  fl_h=278.0, wall='MI_dist_bone', trim='MI_paint_cream',
                  panel_b='MI_wood', panels={'B': 'MI_wood'},
                  roofmat='MI_shingle_grey', seed=2020, open_roof=True,
                  green_terrace=True),
        tiers=[
            dict(name='the beds',     fill=0.72, floors=1, parapet=22, roof_units=1, terrace_step=40.0),
            dict(name='two terraces', fill=0.90, floors=3, parapet=24, roof_units=1, terrace_step=42.0),
            dict(name='the garden block', fill=1.00, floors=5, parapet=26, roof_units=1, terrace_step=44.0, needs='L'),
            dict(name='the hanging gardens', fill=1.00, floors=7, parapet=28, roof_units=2, terrace_step=46.0, needs='L'),
            dict(name='the hillside', fill=1.00, floors=9, parapet=30, roof_units=2, terrace_step=48.0, needs='XL'),
            dict(name='the terraces', fill=1.00, floors=10, parapet=32, roof_units=2, terrace_step=50.0, needs='XL'),
        ],
        fits=lambda w, d: 1400.0 <= w <= 2600.0 and d >= 860.0),

    # CONTEMPORARY VII - BRISE-SOLEIL. A glass box behind a screen of
    # vertical fins standing well clear of it. The fins ARE the facade; the
    # glass barely registers. A sunshade doing the architecture, and it
    # throws a different shadow every hour, which no printed grid does.
    'contemporary7': dict(
        label='Brise-Soleil', style='contemporary', district=('office', 'core'),
        role='filler', max_storeys=12,
        widths=(1230.0, 1640.0, 2050.0),
        bay_target=320.0, align='left',
        base=dict(kind='gen', style='contemporary', depth=780.0, gf_h=390.0,
                  fl_h=270.0, wall='MI_precast_grey', trim='MI_dark_metal',
                  panel_b='MI_dist_bone', panels={'B': 'MI_dist_bone'},
                  roofmat='MI_shingle_grey', seed=2017, open_roof=True,
                  brise=True),
        tiers=[
            dict(name='hoarding',    fill=0.55, floors=0, parapet=22, roof_units=1, stair_head=False),
            dict(name='the screen',  fill=0.84, floors=2, parapet=26, roof_units=1, fin_step=104.0),
            dict(name='the block',   fill=1.00, floors=4, parapet=30, roof_units=1, fin_step=100.0),
            dict(name='the institute', fill=1.00, floors=7, parapet=34, roof_units=2, fin_step=96.0, needs='M'),
            dict(name='the shaded tower', fill=1.00, floors=10, parapet=38, roof_units=2, fin_step=92.0, needs='L'),
            dict(name='the louvre',  fill=1.00, floors=12, parapet=42, roof_units=2, fin_step=88.0, fin_proj=98.0, needs='L'),
        ],
        fits=lambda w, d: 1100.0 <= w <= 2300.0 and d >= 740.0),

    # CONTEMPORARY VIII - THE SLENDER. A small retail podium with a very
    # thin tower on it. The contemporary answer to an expensive small site,
    # and the only recipe whose value is its PROPORTION rather than its
    # skin - it must be built narrow to be itself.
    'contemporary8': dict(
        label='Slender', style='contemporary', district=('core', 'resi'),
        role='actionable', max_storeys=16,
        widths=(1230.0, 1640.0),
        bay_target=300.0, align='left',
        base=dict(kind='gen', style='contemporary', depth=720.0, gf_h=400.0,
                  fl_h=266.0, wall='MI_dist_bone', trim='MI_dark_metal',
                  panel_b='MI_dist_slate', panels={'B': 'MI_dist_slate'},
                  roofmat='MI_shingle_grey', seed=2022, open_roof=True,
                  core_bays=1, mullion_step=78.0),
        tiers=[
            dict(name='the shop',    fill=0.80, floors=1, parapet=24, roof_units=1),
            dict(name='the podium',  fill=1.00, floors=3, parapet=26, roof_units=1),
            dict(name='the sliver',  fill=1.00, floors=7, parapet=30, roof_units=1,
                 mech=dict(w=0.36, h=110.0, at=0.30)),
            dict(name='the needle',  fill=1.00, floors=11, parapet=34, needs='M', roof_units=1,
                 mech=dict(w=0.38, h=130.0, at=0.32)),
            dict(name='the pencil',  fill=1.00, floors=14, parapet=38, needs='M', roof_units=1,
                 mech=dict(w=0.40, h=150.0, at=0.30)),
            dict(name='the slender', fill=1.00, floors=16, parapet=42, needs='L', roof_units=1,
                 mech=dict(w=0.40, h=170.0, at=0.34), setback=60.0, setback_floors=1),
        ],
        fits=lambda w, d: 1100.0 <= w <= 1900.0 and d >= 680.0),
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


DEPTH_DEFAULT = None      # absent suffix == the recipe's own base['depth']


# THE ONE DEEP VALUE, and it is derived rather than chosen. A corner building
# has to present a real elevation to the CROSS street, not a stub: the flank
# is the corner's whole argument. The catalogue's own depths are 680-860,
# which is roughly half the 1500 uu block depth the placer lays out - so a
# corner built at its base depth leaves the back half of its parcel empty and
# its flank stops two thirds of the way along the side street.
#
# So the deep value is the PARCEL DEPTH: a corner fills its lot front to back.
# 1500 is citylayout's BLOCK_DEPTH, restated here rather than imported -
# recipes is the lower layer and must not depend on the placer - and this
# comment is the link between them. If the block depth changes, this changes.
#
# EVERY fits() ALREADY ACCEPTS IT. All 32 predicates lower-bound depth
# (d >= 560..800) and none upper-bound it, so the deep variant needed no
# fits() change at all - checked rather than assumed.
DEPTH_CORNER = 1500.0


def depths(rid):
    """Every depth a recipe can be baked at, shallowest first.

    Two values: the recipe's own base depth, and the corner depth. The second
    is DECLARED here and BAKED ON DEMAND - only where the placer actually
    sites a corner - so declaring it costs nothing and no catalogue-wide
    corner bake is implied.
    """
    base = RECIPES[rid]['base'].get('depth', 700.0)
    return (base, DEPTH_CORNER) if DEPTH_CORNER > base else (base,)


def asset_name(rid, tier, width, depth=None, corner=None):
    """One baked mesh per recipe, tier and PARCEL width. Width is part of the
    identity because the generator lays bays out across it, and because `fill`
    means the same tier occupies a different share of a different parcel.

    THE SAME ARGUMENT CARRIES TO DEPTH, on the other axis: the generator lays
    the FLANK out across the depth, and a corner parcel gives the same tier a
    different share of a different depth. So depth joins the identity - but
    as an axis that is DECLARED now and SHIPS ONE VALUE, baked on demand where
    the placer sites it. No ladder until placement demand proves one.

    CORNER joins it too, and it is HANDED: corner_side left and right are two
    real buildings, not one mirrored, so a corner parcel needs the hand it
    actually uses and no more.

    THE GRAMMAR, in one place, because an implicit default is exactly the kind
    of thing that dies in a parser:

        SM_Bld_<rid>_t<tier>_w<width>                  default depth, no corner
        SM_Bld_<rid>_t<tier>_w<width>_d<depth>         explicit depth
        SM_Bld_<rid>_t<tier>_w<width>_d<depth>_cL      handed corner, left
        SM_Bld_<rid>_t<tier>_w<width>_d<depth>_cR      handed corner, right

    ABSENT SUFFIX MEANS THE RECIPE'S OWN base['depth']. The existing 548 keep
    their names, stay valid, and are not re-baked: adding the axis is not a
    staleness event.

    WHO PARSES THIS GRAMMAR - enumerated rather than discovered, because on
    2026-08-30 a name-keyed lookup over non-unique names silently returned the
    wrong geometry for an unknown period. Checked across Content/Python and
    Tools/measure: NOTHING decomposes a baked name back into its parts. This
    function is the sole constructor (23 call sites) and every consumer treats
    the result as opaque. The one name-KEYED store is
    Saved/coplanar_baselines.json, whose keys are whole asset names and which
    therefore gains keys for new variants without disturbing existing ones.
    If that ever stops being true, the parser goes here, beside the grammar.
    """
    n = 'SM_Bld_%s_t%d_w%d' % (rid, tier, int(round(width)))
    if depth is not None:
        n += '_d%d' % int(round(depth))
    if corner is not None:
        if corner not in ('left', 'right'):
            raise ValueError('corner must be left or right, got %r' % corner)
        if depth is None:
            raise ValueError('a corner variant must state its depth')
        n += '_c%s' % ('L' if corner == 'left' else 'R')
    return n


def _selftest():
    """Every width a recipe declares must satisfy its own `fits`.

    These are two statements of the same fact - which is exactly how they
    drift. The tower declared XL and XXL while its `fits` stopped at 1800, so
    the grammar silently refused to place one on an assembled parcel.
    """
    for rid, r in RECIPES.items():
        # ITERATE (width, depth) PAIRS FROM DAY ONE OF THE AXIS. With depth in
        # the identity, checking only the recipe's own depth would leave the
        # new axis silently uncovered - the identical drift this test was
        # written to catch, when the tower declared XL and XXL while its fits
        # stopped at 1800.
        for w in widths(rid):
            for d in depths(rid):
                assert r['fits'](w, d), (
                    '%s declares width %.0f at depth %.0f but its own fits()'
                    ' rejects it' % (rid, w, d))
        # a filler must not claim to be actionable, and vice versa
        assert r.get('role') in ('filler', 'actionable'), rid
    return True


if __name__ == '__main__':
    print('recipes self-test:', _selftest())
    for rid in sorted(RECIPES):
        print('  %-11s %-10s %d tiers  widths %s' % (
            rid, RECIPES[rid]['role'], tier_count(rid),
            '/'.join('%.0f' % w for w in widths(rid))))
