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
        needs=None):
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
                needs=needs or {})


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
    'flock':       _st(0.003, 3.0, 0.85, 0.98),   # scatter/foam: planting
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
                        normal='/Game/Uniblocks/Textures/T_UB_brickwork_N',
                        source='Uniblocks PolyHaven CC0',
                        # authored in the other green convention: without this
                        # the brick faces read RECESSED and the mortar PROUD
                        needs={'flip_green_channel': True,
                               'srgb': False}),
    'plaster_cast': _st(0.0100, 1.6, 0.62, 0.80,
                        normal='/Game/Uniblocks/Textures/T_UB_concrete_1_N',
                        source='Uniblocks PolyHaven CC0',
                        needs={'srgb': False}),
    # 0.9 was an over-correction: at 800 uu the pier read as untextured
    # plastic, not as a skim coat. The split's purpose is that brick is
    # DEEPER than render, not that render is bare.
    'render_smooth': _st(0.0080, 1.4, 0.58, 0.74,
                         normal='/Game/Uniblocks/Textures/PolyHaven_CC0/T_UB_plaster_2_N',
                         source='Uniblocks PolyHaven CC0',
                         needs={'srgb': False}),
}

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
    """Scalars only - the four keys this has always emitted.

    The normal map is deliberately NOT in here. Callers write scalars with
    set_material_instance_scalar_parameter_value and a texture needs a
    different setter, so folding it in would silently break every existing
    caller. normal_for() is the separate accessor; apply_stocks.py uses both.
    """
    st = STOCK[stock_for(name)]
    return dict(PaperTiling=st['tooth'], PaperNormalAmount=st['amount'],
                RoughMin=st['rough'][0], RoughMax=st['rough'][1])


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
    assert normal_for('MI_dist_brick') != normal_for('MI_concrete')
    assert normal_for('MI_paint_cream') is None
    # an admitted map that lives outside version control must state what it
    # needs, or a fresh clone renders it with the pack's defaults
    reqs = dict(texture_requirements())
    assert '/Game/Uniblocks/Textures/T_UB_brickwork_N' in reqs
    assert reqs['/Game/Uniblocks/Textures/T_UB_brickwork_N']['flip_green_channel'] is True
    # every stock a material names must still exist, INCLUDING the new ones
    assert set(SPLIT_OF_CARD_HEAVY) <= set(STOCK)
    assert stock_for('MI_paint_cream_2S') == 'card_heavy'
    assert stock_for('MI_dark_metal') == 'wire'
    assert stock_for('MI_glass_b') == 'acetate'
    assert stock_for('MI_glass_pent') == 'acetate'
    assert stock_for('MI_wood') == 'basswood'
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
