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
def _st(tooth, amount, rlo, rhi, normal=None, tooth_fine=None, source=None):
    return dict(normal=normal, tooth=tooth, tooth_fine=tooth_fine,
                amount=amount, rough=(rlo, rhi), source=source)


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
    # --- the card_heavy split. PHASE 0: aliases, identical by construction. --
    'brick_sheet': _st(0.006, 2.0, 0.62, 0.80),
    'plaster_cast': _st(0.006, 2.0, 0.62, 0.80),
    'render_smooth': _st(0.006, 2.0, 0.62, 0.80),
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
    """Exactly the four keys this has always emitted. The fine tooth and the
    normal map live in the table but are NOT emitted in Phase 0 - adding a key
    would change what callers write to a material instance, and this phase has
    to be provably invisible."""
    st = STOCK[stock_for(name)]
    return dict(PaperTiling=st['tooth'], PaperNormalAmount=st['amount'],
                RoughMin=st['rough'][0], RoughMax=st['rough'][1])


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
    # --- PHASE 0 IS A NO-OP, asserted rather than asserted-in-prose -------
    for _s in SPLIT_OF_CARD_HEAVY:
        assert STOCK[_s] == STOCK['card_heavy'], (
            '%s has drifted from card_heavy - that is Phase 1, and Phase 1 '
            'is judged on the acceptance buildings, not merged quietly' % _s)
    for _m in ('MI_dist_brick', 'MI_dist_teal', 'MI_concrete', 'MI_precast'):
        assert params_for(_m) == params_for('MI_paint_cream'), (
            '%s no longer renders identically to card_heavy' % _m)
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
        alias = '  = card_heavy (Phase 0)' if s in SPLIT_OF_CARD_HEAVY else ''
        print('  %-14s tooth %.3f amount %.1f rough %.2f-%.2f%s   %s'
              % (s, st['tooth'], st['amount'], st['rough'][0], st['rough'][1],
                 alias, ', '.join(used) or '(unused)'))
