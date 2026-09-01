"""What each role is MADE OF, on a modelmaker's bench. Pure data.

The problem this fixes: one paper tooth was applied to all 37 materials at
once, so aluminium mullions, glazing and brass all wore the same cardstock
grain. At inspection range that reads as everything being cut from the same
sheet, which is the one thing a real model is not - a maker uses card for
walls, wire for railings, acetate for glazing, and sanded basswood for trim.

WHY THIS IS NOT A LONGER MATERIAL LIST. MASTER_MATERIAL_SPEC is explicit:
"Keep the set this small. The last project's palette grew a walnut and a cedar
and a bronze that did nothing a parameter could not have done." So no new
roles and no new masters - the same roles, parameterised to say what they are
made of. "Several weights of cardstock" IS a parameter: tooth scale and
amount.

The spec also says what tooth is FOR: "Fine surface noise - the tooth of paint
or print". Paint and print. Not metal, not glass.

TOOTH is the scale of the fibre (smaller number = coarser weave, measured
0.050 invisible -> 0.003 linen; 0.006 reads as card stock). AMOUNT is how
deep it bites. Roughness is the fabricated band the spec asks to be clamped
narrowly - what actually separates sanded wood from cast resin from wire.

PHASE 0 OF THE card_heavy SPLIT. Cold read #1 said "everything has the same
'paper' texture", and that was not a metaphor: EVERY building in the city
resolved to six stocks, and card_heavy carried brick, slate, bone, ochre,
cream AND concrete - one stock, six paints, one normal map. A brick pier and
a timber shopfront were the same photograph at different scales.

So card_heavy splits, on the principle that A STOCK EXISTS IFF A MODELMAKER
WOULD REACH FOR A DIFFERENT MATERIAL:

    brick_sheet    embossed brick sheet, a real modelmaking product
    plaster_cast   cast or textured plaster: concrete and precast
    render_smooth  painted render / skim
    card_heavy     genuine card, and paint on card, only

THIS PHASE IS A PROVABLE NO-OP. The three new stocks are ALIASES carrying
card_heavy's exact current properties, so the vocabulary widens and the render
does not move - _selftest asserts that byte-identically. The look change is
Phase 1, judged on both acceptance buildings under look-change proof
standards, with the owner's eye on the ensemble. Two phases, two proof
standards, named before either started - the same discipline that caught the
octave work passing its numbers and failing the eye.

SCHEMA. One shape, no special cases: every stock carries a normal map (None =
the master's default paper), a coarse tooth, a FINE tooth for when the
two-octave work revives per-stock, an amount, and a roughness band. Phase 0
leaves normal and tooth_fine unset everywhere, so params_for emits exactly
the four keys it always did.
"""

#   normal:     source map, None = the master's default paper (Phase 0: all None)
#   tooth:      coarse tiling
#   tooth_fine: fine octave tiling, for when route 1 revives per-stock
#   amount:     normal strength - relief honesty, half the point of the split
#   rough:      the narrow fabricated band
def _st(tooth, amount, rlo, rhi, normal=None, tooth_fine=None, source=None,
        needs=None, figure=None, figure_mean=None, figure_sd=None,
        seam=None, roughmap=None):
    """`needs` records the IMPORT SETTINGS an admitted map must carry.

    WHY THIS EXISTS. Content/Uniblocks/ is gitignored - every admitted FAB
    texture lives outside version control, so its import settings are LOCAL
    STATE. The owner spotted that brick read inverted (faces recessed, mortar
    proud); the fix was flip_green_channel on the texture, which is a property
    of the MAP, not of the stock. On a fresh clone that flag is back to the
    pack default and the brick silently renders backwards again - and nothing
    in the acceptance numbers would catch it, because an inverted normal has
    exactly the same amount of high-frequency content, just pointing the wrong
    way. check_textures() turns that into a loud failure.
    """
    return dict(normal=normal, tooth=tooth, tooth_fine=tooth_fine,
                amount=amount, rough=(rlo, rhi), source=source,
                needs=needs or {}, figure=figure,
                figure_mean=figure_mean, figure_sd=figure_sd, seam=seam,
                roughmap=roughmap)


STOCK = {
    'card_heavy':  _st(0.006, 2.0, 0.62, 0.80),   # mounting board, and paint on it
    'card_smooth': _st(0.014, 1.2, 0.55, 0.70),   # thin cut card: bands, trim
    # PROP SCALE. PaperTiling is WORLD-scale, so the value that gives a 12 m
    # wall a card tooth gives a 0.5 m planter burlap. Measured on three
    # Uniblocks planters side by side: 0.006 reads as sacking, 0.080 is
    # nearly smooth, 0.030 reads as card. Anything hand-sized takes this.
    'card_prop':   _st(0.030, 1.6, 0.58, 0.74),   # cut card at prop scale
    'print':       _st(0.010, 1.4, 0.60, 0.76),   # printed paper: shingles
    'chipboard':   _st(0.004, 2.6, 0.70, 0.88),   # the base board
    'basswood':    _st(0.020, 1.6, 0.48, 0.64),   # carved + sanded timber
    'wire':        _st(0.000, 0.0, 0.28, 0.42),   # aluminium rod, drawn smooth
    'brass':       _st(0.000, 0.0, 0.22, 0.34),   # turned brass detail
    'acetate':     _st(0.000, 0.0, 0.04, 0.12),   # glazing film
    'resin':       _st(0.030, 0.5, 0.38, 0.52),   # cast resin: fittings
    'clay':        _st(0.008, 2.2, 0.72, 0.90),   # modelling putty: ground
    # FLOCK WAS WEARING THE PAPER TOOTH, and wearing it worse than anything
    # else in the table: amount 3.0 (the highest here) at tiling 0.003 (the
    # lowest), with no normal of its own, so it inherited the master's card
    # weave at triple amplitude and three times concrete's feature size. On a
    # roof lawn that reads as bright green felt with rectangular print
    # blotches - the most visible fault in any frame of 29 Aug, and visible
    # without an instrument, which is more than the coplanar debt can say.
    #
    # Scatter is not paper. Flock at 1:87 is ground foam: fine, soft, and
    # near-grainless at any distance a building is seen from. So it gets its
    # own micro-relief, tiled FINE rather than coarse, at an amplitude below
    # card rather than above it.
    #
    # T_Grass002 is a photographic grass normal from Mega_Street_Props_Pack,
    # an OWNED pack - recorded as owned, NOT as CC0, because this project has
    # already shipped one provenance claim it could not support. Tiled this
    # fine the blades fall below a pixel and what survives is granularity,
    # which is exactly what ground foam is. Their micro-relief, our colour and
    # sheen - the admitted scope of the rule.
    'flock':       _st(0.060, 0.9, 0.85, 0.98,
                       normal='/Game/Mega_Street_Props_Pack/Street_Props_pack_V2'
                              '/Textures/Grass/T_Grass002_4K_Normal',
                       source='Mega_Street_Props_Pack (owned donor pack) - '
                              'normal map only, no colour or roughness shipped',
                       needs={'srgb': False}),   # scatter/foam: planting
    'glue':        _st(0.024, 0.8, 0.30, 0.46),   # dried PVA
    # --- the card_heavy split. PHASE 1: each stock is its own material now.
    #
    # TILING IS DERIVED FROM WHAT THE MAP DEPICTS, not inherited. The world is
    # 1:1, so a brick course is ~7.5 uu; card_heavy's 0.006 puts one texture
    # tile across 167 uu and would make a course 1.4-2 m. Every value below is
    # feature-size arithmetic, not a number that looked right on a panel.
    #
    # AMPLITUDE IS HALF THE POINT. It was ONE constant (2.0) for all of
    # card_heavy, so brick, concrete and skimmed render were pushed at
    # identical strength regardless of what their relief actually is. Embossed
    # brick sheet has real depth; a skim coat has almost none.
    'brick_sheet':  _st(0.0133, 2.4, 0.64, 0.82,
                        # POLY HAVEN Brick Wall 001, CC0, copied into tracked
                        # content with its settings baked in. It replaces the
                        # Uniblocks pack brick, whose provenance could not be
                        # established: machine-regular running bond against
                        # Poly Haven's photogrammetry, most plausibly the pack
                        # author's own work - which is why their PolyHaven_CC0
                        # folder excluded it. That map was also the one whose
                        # green-convention fix could not be committed, so
                        # replacing it closes the fresh-clone regression class
                        # for brick outright rather than guarding it.
                        #
                        # nor_gl source: OpenGL green, UE samples DirectX, so
                        # flip_green_channel is set AT IMPORT and recorded in
                        # needs. The owner caught the pack brick rendering
                        # inverted - faces recessed, mortar proud - and the
                        # detail metric read it identically either way,
                        # because it sees quantity and not direction.
                        normal='/Game/Stacktown/Textures/T_brick_wall_001_N',
                        source='Poly Haven "Brick Wall 001" CC0 - '
                               'https://polyhaven.com/a/brick_wall_001 - '
                               'see Tools/textures/source/polyhaven/PROVENANCE.md',
                        needs={'flip_green_channel': True, 'srgb': False}),
    'plaster_cast': _st(0.0100, 1.6, 0.62, 0.80,
                        normal='/Game/Uniblocks/Textures/T_UB_concrete_1_N',
                        # same as brick: root Textures, not the CC0 folder
                        source='Uniblocks pack (root Textures) - PROVENANCE '
                               'UNVERIFIED, not in the pack PolyHaven_CC0 folder',
                        needs={'srgb': False}),
    # 0.9 was an over-correction: at 800 uu the pier read as untextured
    # plastic, not as a skim coat. The split's purpose is that brick is
    # DEEPER than render, not that render is bare.
    'render_smooth': _st(0.0080, 1.4, 0.58, 0.74,
                         # COPIED INTO TRACKED CONTENT. Its settings are now
                         # versioned with it, so a fresh clone cannot render it
                         # with the pack's defaults. The two maps still living
                         # in the ignored pack are the ones whose provenance is
                         # unverified - they stay under check_textures.
                         normal='/Game/Stacktown/Textures/T_UB_plaster_2_N',
                         # the one of the three that IS in the pack's own
                         # PolyHaven_CC0 folder - the author's own CC0 assertion
                         source='Uniblocks/Textures/PolyHaven_CC0 - CC0 per '
                                'the pack author\'s own segregation',
                         needs={'srgb': False}),
}

# --- DIRECTION B: THE SEVEN TIMBERS -------------------------------------
#
# SPECIES IS A STOCK, not a colour on a shared one (D5). Grain is as much a
# species trait as hue, and a stock is what carries a map - so one stock per
# timber, resolved by the same longest-prefix rule that lets MI_dist_brick
# leave the MI_dist paint family. `basswood` above is untouched and keeps its
# flagship users (Timber_ decking, planters, pergolas).
#
# EACH CARRIES TWO MAPS. `normal` is the species' nor_dx map - DirectX
# convention, so flip_green_channel is not needed and cannot be forgotten,
# which closes the inverted-brick class by construction rather than guarding
# it. `figure` is the luminance-only grain mask derived from the same
# species' CC0 diffuse by Tools/textures/mk_grain_masks.py, under D8's
# "their pattern, our palette" - no donor hue reaches Content/ at all.
#
# TOOTH IS DERIVED, and the arithmetic is written down because this table's
# own rule is that tiling comes from what the map depicts. tooth = 1/tile_uu
# (card_heavy's 0.006 puts one tile across 167 uu). The fiction is a building
# CARVED FROM ONE BLOCK: at model scale a block is ~10 cm showing perhaps 30
# to 100 growth lines, and the engine world is 1:1 with a building ~1000 uu,
# so a grain line wants to land every 10-30 uu. These maps depict 1 m of real
# timber carrying on the order of 100-300 lines, which puts one tile across
# roughly 1,000-9,000 uu. 0.0005 (one tile per 2,000 uu) is the middle of
# that band and is a STARTING POINT to be trimmed on a building, never a
# value that looked right on a panel.
#
# AMPLITUDE starts at 1.8 because a sanded veneer's relief is genuinely
# shallow (D7 measured it); the figure carries the read, not the normal.
#
# figure_mean / figure_sd are MEASURED, emitted by the generator. The sd is
# load-bearing: figure strength varies TENFOLD across these sources
# (sd/mean 0.176 pine to 0.018 maple) because they are photographs exposed by
# different people. The material normalises by sd so one gain gives every
# species comparable amplitude - the card_heavy amplitude fault, caught
# before it shipped this time.
_TX = '/Game/Stacktown/Textures'
_PH = 'Poly Haven, CC0 (https://polyhaven.com/license) - normal (DirectX) ' \
      'and a luminance-only grain mask; no donor colour shipped'


def _timber(rlo, rhi, species, mean, sd, amount=1.8, tooth=0.0005):
    # seam=False: A CARVED SOLID HAS NO PANEL JOINTS. The master draws
    # vertical panel seams every 380 uu because that is CARD-MODEL fabrication
    # grammar, and it is right for card. On a 700 uu timber block it put one
    # joint down every face in the first capture - fabrication grammar from
    # one story leaking into another. The one-block fiction is declared
    # direction-B doctrine (this table's own tooth arithmetic is built on it),
    # so timber turns the seam off. Flagship card stocks are untouched.
    #
    # Off is SeamDarken 1.0 - a darken factor of 1 darkens nothing - which is
    # the idiom mark_mats.py and paint_roles.py already use ("Seams off - glue
    # is not a sheet"), not a second way of saying the same thing.
    return _st(tooth, amount, rlo, rhi,
               normal='%s/T_%s_N' % (_TX, species),
               figure='%s/T_grain_%s' % (_TX, species),
               roughmap='%s/T_rough_%s' % (_TX, species),
               figure_mean=mean, figure_sd=sd, seam=False,
               source=_PH, needs={'srgb': False})


STOCK.update({
    # pale to dark. ROUGH BANDS WIDENED AND RAISED after the first boards read
    # as VENEER: the old 0.46-0.66 was inherited from basswood, which tiles
    # decking, and a whole carved city wants more spread and less sheen. Open
    # -grained species (oak, ash, sapele, pine) get the widest bands because
    # open pores scatter and dense latewood does not - the spread IS the
    # difference between those two tissues, not decoration.
    #
    # The band is only as useful as the map that drives it: the raw figure
    # mask reached 9-26% of it, which is why `roughmap` is a separate
    # contrast-stretched twin rather than the figure map reused.
    'maple':  _timber(0.50, 0.74, 'maple',  212.9, 3.8),
    'pine':   _timber(0.52, 0.82, 'pine',    63.1, 11.1),
    'ash':    _timber(0.54, 0.88, 'ash',    151.2, 9.4),
    'oak':    _timber(0.54, 0.88, 'oak',    123.9, 8.3),
    'cherry': _timber(0.50, 0.74, 'cherry', 182.5, 4.2),
    'sapele': _timber(0.53, 0.84, 'sapele', 139.9, 9.0),
    'walnut': _timber(0.52, 0.80, 'walnut', 110.3, 6.8),
})

TIMBERS = ('maple', 'pine', 'ash', 'oak', 'cherry', 'sapele', 'walnut')

# THE BOARD'S OWN STOCK (D10, settled by the owner in D11). Roads are STAINED
# TIMBER bedded into the plate, not district paint borrowed for being nearby -
# the first boards used MI_dist_slate and it read as blue-grey plastic, the one
# element in a wooden picture that said "engine".
#
# It KEEPS ITS GRAIN. A stained board still shows figure; what the stain
# changes is colour, not material. So road_inlay is a timber stock like the
# seven, and takes maple's fine, quiet mask - a road wants the least assertive
# figure in the set, since it is what the buildings stand on and must never
# out-read them (D10's "nothing on the board out-saturates the timber").
#
# KERBS AND CROSSINGS ARE TONES OF THIS STOCK, not stocks of their own. D10
# proposed a separate kerb_card and flagged it as the one it was least sure
# of; the owner's answer confirms the doubt. Two stocks differing only in tone
# is precisely the walnut-and-cedar prohibition, and this lane already
# committed to that standard in D6.
STOCK['road_inlay'] = _st(
    0.0016, 1.4, 0.62, 0.90,          # matter than any building timber: a
                                      # laid, worn surface, not a sanded face
    normal='%s/T_maple_N' % _TX,
    figure='%s/T_grain_maple' % _TX,
    roughmap='%s/T_rough_maple' % _TX,
    figure_mean=212.9, figure_sd=3.8, seam=False,
    source=_PH, needs={'srgb': False})
MATERIAL_STOCK_BOARD = ('MI_board_road', 'road_inlay')

# the three that must stay identical to card_heavy until Phase 1 tunes them
SPLIT_OF_CARD_HEAVY = ('brick_sheet', 'plaster_cast', 'render_smooth')

# Which stock each material is cut from. Matched longest-prefix-first so
# MI_glass_pent can differ from MI_glass without a special case.
MATERIAL_STOCK = {
    'MI_paint_cream': 'card_heavy',
    'MI_paint_accent': 'card_heavy',
    'MI_precast': 'plaster_cast',   # precast concrete is cast, not cut
    'MI_card': 'card_heavy',
    # THE DISTRICT PALETTE IS PAINTED RENDER, except where it is brick. That
    # sentence used to read "one family, many paints", which is exactly the
    # condition cold read #1 described. Longest-prefix matching does the work:
    # MI_dist_brick beats MI_dist, so brick leaves the family without a
    # special case in the resolver.
    'MI_dist': 'render_smooth',
    'MI_dist_brick': 'brick_sheet',
    'MI_concrete': 'plaster_cast',
    'MI_studio_grey': 'card_heavy',
    'MI_mural': 'card_heavy',      # paint ON card - same stock, painted
    'MI_frame_print': 'card_smooth',
    'MI_canopy_accent': 'card_smooth',
    'MI_interior': 'card_smooth',
    'MI_shingle': 'print',
    'MI_model_board': 'chipboard',
    'MI_wood': 'basswood',
    # DIRECTION B's timbers. Longest prefix wins, so MI_wood_oak leaves the
    # basswood family the same way MI_dist_brick leaves MI_dist - and plain
    # MI_wood keeps resolving to basswood for every flagship user of it.
    'MI_wood_maple': 'maple',
    'MI_wood_pine': 'pine',
    'MI_wood_ash': 'ash',
    'MI_wood_oak': 'oak',
    'MI_wood_cherry': 'cherry',
    'MI_wood_sapele': 'sapele',
    'MI_wood_walnut': 'walnut',
    'MI_board_road': 'road_inlay',   # the board's inlaid streets, D11
    'MI_planter': 'card_prop',    # kit beds and pots - prop scale, fine tooth
    # VEHICLES ARE CAST, NOT CUT. Cold read #1 said the paper texture was
    # most visible on the vehicles, and it was: they borrowed the buildings'
    # MI_card_*_2S, so stock_for() handed a car the same card_heavy a wall
    # gets - byte-identical tooth and amount. The study wall settled it at
    # inspection range: card at 0.006 wraps the bodywork like canvas, card at
    # 0.025 reads as papercraft, and resin reads as a cast and painted model
    # car. 'resin' was already declared here and had no user; a modelmaker
    # casts what cannot be cut from card, which is exactly a car.
    'MI_veh': 'resin',
    'MI_dark_metal': 'wire',
    'MI_brass': 'brass',
    'MI_glass': 'acetate',
    'MI_glue': 'glue',
    'MI_gravel': 'clay',
    'MI_grass': 'flock',
    'MI_grass_card': 'flock',
    'MI_bloom': 'flock',
    'MI_leaf': 'flock',
}

DEFAULT = 'card_heavy'


def stock_for(name):
    """Longest matching prefix wins, so MI_card_lift_2S resolves like MI_card."""
    best = ''
    for pre in MATERIAL_STOCK:
        if name.startswith(pre) and len(pre) > len(best):
            best = pre
    return MATERIAL_STOCK.get(best, DEFAULT)


def params_for(name):
    """Scalars only - the four keys this has always emitted, plus SeamDarken
    for the stocks that explicitly ask for it.

    The normal map is deliberately NOT in here. Callers write scalars with
    set_material_instance_scalar_parameter_value and a texture needs a
    different setter, so folding it in would silently break every existing
    caller. normal_for() is the separate accessor; apply_stocks.py uses both.

    SeamDarken is emitted ONLY when a stock declares `seam`. A stock that
    says nothing about seams gets exactly the four keys it always got, so
    every existing material's parameter set is byte-identical - the emission
    grows for the stocks that need it and for nobody else.
    """
    st = STOCK[stock_for(name)]
    out = dict(PaperTiling=st['tooth'], PaperNormalAmount=st['amount'],
               RoughMin=st['rough'][0], RoughMax=st['rough'][1])
    if st.get('seam') is not None:
        out['SeamDarken'] = 1.0 if st['seam'] is False else float(st['seam'])
    return out


def texture_requirements():
    """(path, {property: value}) for every admitted map that states them.

    Checked against the live assets by check_textures.py. Kept here rather
    than in the checker so the requirement sits beside the map it belongs to.
    """
    out = []
    for st in STOCK.values():
        if st.get('normal') and st.get('needs'):
            out.append((st['normal'], dict(st['needs'])))
    return out


def normal_for(name):
    """The admitted map for this material's stock, or None for the master's
    default paper. Under the texture rule an admitted map lends MICRO-RELIEF
    only - never albedo, colour or weathering - so this is the whole of what a
    FAB texture contributes."""
    return STOCK[stock_for(name)].get('normal')


def figure_for(name):
    """The GRAIN MASK for this material's stock, or None.

    A sibling of normal_for rather than a key in params_for, for the same
    reason normal_for is: params_for emits SCALARS and its callers write them
    with set_material_instance_scalar_parameter_value. A texture folded in
    there breaks every one of them silently.

    Under D8 the mask is LUMINANCE ONLY and carries no donor colour - the
    greyscale conversion happens in Tools/textures/mk_grain_masks.py, so this
    accessor cannot hand back a coloured map even by mistake.
    """
    return STOCK[stock_for(name)].get('figure')


def roughmap_for(name):
    """The stock's contrast-stretched ROUGHNESS map, or None.

    Separate from figure_for because the two maps do different jobs: the
    figure is faithful luminance and modulates colour by a few percent, while
    this one is stretched to fill 0..1 so it actually reaches the roughness
    band. Feeding the figure map into the roughness Lerp reached 9-26% of the
    band and produced the uniform, veneer-like surface the first boards had.
    """
    return STOCK[stock_for(name)].get('roughmap')


def figure_levels(name):
    """(mean, sd) of the stock's grain mask, or (None, None).

    The material centres on mean and normalises by sd. Both are MEASURED and
    emitted by the generator - see the TIMBERS comment for why the sd is not
    optional.
    """
    st = STOCK[stock_for(name)]
    return st.get('figure_mean'), st.get('figure_sd')


def _selftest():
    assert stock_for('MI_paint_cream') == 'card_heavy'
    # --- the split: semantic routing -------------------------------------
    assert stock_for('MI_dist_brick') == 'brick_sheet', 'brick must leave the paint family'
    assert stock_for('MI_dist_teal') == 'render_smooth'
    assert stock_for('MI_dist_ochre') == 'render_smooth'
    assert stock_for('MI_concrete') == 'plaster_cast'
    assert stock_for('MI_precast') == 'plaster_cast'
    assert stock_for('MI_card') == 'card_heavy'
    assert stock_for('MI_mural_a') == 'card_heavy'
    # --- PHASE 1: the split stocks are now DISTINCT, which is the point ---
    for _s in SPLIT_OF_CARD_HEAVY:
        assert STOCK[_s] != STOCK['card_heavy'], (
            '%s is still a card_heavy alias - Phase 1 did not happen' % _s)
        assert STOCK[_s]['normal'], '%s has no admitted map' % _s
        assert STOCK[_s]['source'], (
            '%s names a map with no recorded source - the admission list is '
            'closed and every entry carries its provenance' % _s)
    # a modelmaker would not push a skim coat as hard as embossed brick sheet
    assert STOCK['brick_sheet']['amount'] > STOCK['render_smooth']['amount']
    # and card keeps the paper: it is the one stock that really is card
    assert STOCK['card_heavy']['normal'] is None

    # --- DIRECTION B's timbers ------------------------------------------
    # PLAIN MI_wood STILL RESOLVES TO BASSWOOD. Every flagship user of it -
    # Timber_ decking, planters, pergolas - must be untouched by seven new
    # stocks arriving, and longest-prefix is what guarantees it.
    assert stock_for('MI_wood') == 'basswood'
    # the board's road is its own stock, and it is a TIMBER one - stained
    # wood keeps its grain, so a road with no figure would be the fault the
    # stock replaced, wearing a different name
    assert stock_for('MI_board_road') == 'road_inlay'
    assert STOCK['road_inlay']['figure'], 'a stained board still shows figure'
    assert STOCK['road_inlay']['rough'][0] > STOCK['oak']['rough'][0], (
        'the road must be MATTER than the buildings it carries - it is laid '
        'and walked on, they are sanded faces')
    assert stock_for('MI_wood_oak') == 'oak', 'longest prefix did not win'
    assert stock_for('MI_wood_walnut') == 'walnut'
    for _t in TIMBERS:
        st = STOCK[_t]
        # THE D8 LINE, ENFORCED RATHER THAN PROMISED. A species stock exists
        # because it has its own GRAIN. If it cannot be given one it is a
        # colour, and D6 says a colour must be dropped rather than admitted -
        # this is that rule in executable form.
        assert st['figure'], (
            '%s is a species stock with no grain mask - under D6 that makes '
            'it a colour, not a species, and it must be dropped rather than '
            'admitted' % _t)
        assert st['normal'], '%s has no normal map' % _t
        assert st['figure_mean'] and st['figure_sd'], (
            '%s carries a grain mask with no measured levels; the material '
            'normalises by sd and cannot without it' % _t)
        # a mask whose sd is zero is a flat grey and carries no figure at all
        assert st['figure_sd'] > 0.5, '%s grain mask is effectively flat' % _t
        assert st['needs'].get('srgb') is False, (
            '%s must import linear, not sRGB' % _t)
        # A CARVED SOLID HAS NO PANEL JOINTS. The master's card-model seam
        # drew one down every face of the first timber capture; wood turns it
        # off. Asserted so it cannot come back by someone copying a card
        # stock's shape into a new species.
        assert st['roughmap'], (
            '%s has no roughness map - the figure mask reaches only a fifth '
            'of the band and the surface reads as veneer' % _t)
        assert st['rough'][1] - st['rough'][0] >= 0.20, (
            '%s roughness band is %.2f wide; a carved timber wants spread '
            'between open pore and dense latewood' % (
                _t, st['rough'][1] - st['rough'][0]))
        assert st['seam'] is False, (
            '%s must turn the panel seam off - it is card fabrication '
            'grammar and a carved block has no joints' % _t)
    # and the flagship's card stocks keep their seams, which is the other
    # half of the same claim
    assert STOCK['card_heavy'].get('seam') is None
    assert 'SeamDarken' not in params_for('MI_paint_cream')
    assert params_for('MI_wood_oak')['SeamDarken'] == 1.0
    # the tenfold spread is the REASON sd is recorded; assert it is really
    # there, so a future table that quietly equalises them fails here and has
    # to say why rather than dropping the normalisation as unnecessary.
    _r = [STOCK[t]['figure_sd'] / STOCK[t]['figure_mean'] for t in TIMBERS]
    assert max(_r) / min(_r) > 5.0, (
        'figure strength no longer varies across the timbers - if that is '
        'deliberate, the sd normalisation needs revisiting, not deleting')
    assert normal_for('MI_dist_brick') != normal_for('MI_concrete')
    assert normal_for('MI_paint_cream') is None
    # an admitted map that lives outside version control must state what it
    # needs, or a fresh clone renders it with the pack's defaults
    reqs = dict(texture_requirements())
    # the brick map is nor_gl (OpenGL green) and UE samples DirectX. This
    # assertion used to name the Uniblocks path; it names the STOCK now, so
    # swapping the map cannot silently drop the flip that the owner caught
    # missing in the first place.
    _brick = STOCK['brick_sheet']['normal']
    assert _brick in reqs, 'brick_sheet states no import requirements'
    assert reqs[_brick]['flip_green_channel'] is True, (
        'the brick map is nor_gl - without the flip it renders faces '
        'recessed and mortar proud, and no number will catch it')
    # a source string is a CLAIM, and two of these were claims I had not
    # checked. Anything not in the pack's own CC0 folder says so out loud, so
    # it cannot be copied into tracked content by someone reading the table.
    for _s in SPLIT_OF_CARD_HEAVY:
        src = STOCK[_s]['source'] or ''
        nrm = STOCK[_s]['normal'] or ''
        tracked = nrm.startswith('/Game/Stacktown/')
        unverified = 'UNVERIFIED' in src
        # THE INVARIANT: only a map whose provenance is established may be
        # copied into tracked content. Donor packs are never committed; the
        # carve-out is evidence-bound, and this is where the evidence is
        # enforced rather than described.
        assert not (tracked and unverified), (
            '%s: an UNVERIFIED map has been copied into tracked content' % _s)
        # and an unverified one must still be sitting in the ignored pack,
        # where check_textures is the standing guard
        assert unverified == (not tracked), (
            '%s: provenance claim and location disagree' % _s)
    # every stock a material names must still exist, INCLUDING the new ones
    assert set(SPLIT_OF_CARD_HEAVY) <= set(STOCK)
    assert stock_for('MI_paint_cream_2S') == 'card_heavy'
    assert stock_for('MI_dark_metal') == 'wire'
    assert stock_for('MI_glass_b') == 'acetate'
    assert stock_for('MI_glass_pent') == 'acetate'
    assert stock_for('MI_wood') == 'basswood'
    # the board's road is its own stock, and it is a TIMBER one - stained
    # wood keeps its grain, so a road with no figure would be the fault the
    # stock replaced, wearing a different name
    assert stock_for('MI_board_road') == 'road_inlay'
    assert STOCK['road_inlay']['figure'], 'a stained board still shows figure'
    assert STOCK['road_inlay']['rough'][0] > STOCK['oak']['rough'][0], (
        'the road must be MATTER than the buildings it carries - it is laid '
        'and walked on, they are sanded faces')
    # a car is not cut from the same sheet as the wall behind it
    assert stock_for('MI_veh_rose_2S') == 'resin'
    assert stock_for('MI_veh_cream_2S') == 'resin'
    assert stock_for('MI_card_rose_2S') == 'card_heavy'
    assert params_for('MI_veh_rose_2S') != params_for('MI_card_rose_2S')
    assert stock_for('MI_bloom_warm') == 'flock'
    assert stock_for('MI_model_board') == 'chipboard'
    assert stock_for('MI_mural_a') == 'card_heavy'
    # was card_heavy: the district palette is painted render now, and this
    # line is where the pre-split truth used to live
    assert stock_for('MI_dist_teal') == 'render_smooth'
    assert STOCK['card_prop']['tooth'] > STOCK['card_heavy']['tooth'], (
        'prop stock must be FINER (larger tiling) than wall stock')
    # the whole point: metal and glass carry NO tooth
    assert params_for('MI_dark_metal')['PaperNormalAmount'] == 0.0
    assert params_for('MI_glass_b')['PaperNormalAmount'] == 0.0
    # and walls do
    assert params_for('MI_paint_cream')['PaperNormalAmount'] > 1.0
    # every stock a material names must exist
    for m, s in MATERIAL_STOCK.items():
        assert s in STOCK, (m, s)
    return True


if __name__ == '__main__':
    print('fabrication self-test:', _selftest())
    for s in sorted(STOCK):
        st = STOCK[s]
        used = sorted(k for k, v in MATERIAL_STOCK.items() if v == s)
        nm = st['normal'].split('/')[-1] if st['normal'] else 'T_PaperNormal'
        print('  %-14s tooth %.4f amount %.1f rough %.2f-%.2f  %-24s %s'
              % (s, st['tooth'], st['amount'], st['rough'][0], st['rough'][1],
                 nm, ', '.join(used) or '(unused)'))
