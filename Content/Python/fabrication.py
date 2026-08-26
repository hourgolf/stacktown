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
"""

# stock            tooth   amount  rough_min rough_max   what it is
STOCK = {
    'card_heavy':  (0.006,  2.0,   0.62, 0.80),  # mounting board: walls
    'card_smooth': (0.014,  1.2,   0.55, 0.70),  # thin cut card: bands, trim
    'print':       (0.010,  1.4,   0.60, 0.76),  # printed paper: shingles
    'chipboard':   (0.004,  2.6,   0.70, 0.88),  # the base board
    'basswood':    (0.020,  1.6,   0.48, 0.64),  # carved + sanded timber
    'wire':        (0.000,  0.0,   0.28, 0.42),  # aluminium rod, drawn smooth
    'brass':       (0.000,  0.0,   0.22, 0.34),  # turned brass detail
    'acetate':     (0.000,  0.0,   0.04, 0.12),  # glazing film
    'resin':       (0.030,  0.5,   0.38, 0.52),  # cast resin: fittings
    'clay':        (0.008,  2.2,   0.72, 0.90),  # modelling putty: ground
    'flock':       (0.003,  3.0,   0.85, 0.98),  # scatter/foam: planting
    'glue':        (0.024,  0.8,   0.30, 0.46),  # dried PVA
}

# Which stock each material is cut from. Matched longest-prefix-first so
# MI_glass_pent can differ from MI_glass without a special case.
MATERIAL_STOCK = {
    'MI_paint_cream': 'card_heavy',
    'MI_paint_accent': 'card_heavy',
    'MI_precast': 'card_heavy',
    'MI_card': 'card_heavy',
    'MI_concrete': 'card_heavy',
    'MI_studio_grey': 'card_heavy',
    'MI_mural': 'card_heavy',      # paint ON card - same stock, painted
    'MI_frame_print': 'card_smooth',
    'MI_canopy_accent': 'card_smooth',
    'MI_interior': 'card_smooth',
    'MI_shingle': 'print',
    'MI_model_board': 'chipboard',
    'MI_wood': 'basswood',
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
    tooth, amount, rmin, rmax = STOCK[stock_for(name)]
    return dict(PaperTiling=tooth, PaperNormalAmount=amount,
                RoughMin=rmin, RoughMax=rmax)


def _selftest():
    assert stock_for('MI_paint_cream') == 'card_heavy'
    assert stock_for('MI_paint_cream_2S') == 'card_heavy'
    assert stock_for('MI_dark_metal') == 'wire'
    assert stock_for('MI_glass_b') == 'acetate'
    assert stock_for('MI_glass_pent') == 'acetate'
    assert stock_for('MI_wood') == 'basswood'
    assert stock_for('MI_bloom_warm') == 'flock'
    assert stock_for('MI_model_board') == 'chipboard'
    assert stock_for('MI_mural_a') == 'card_heavy'
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
        t, a, lo, hi = STOCK[s]
        used = sorted(k for k, v in MATERIAL_STOCK.items() if v == s)
        print('  %-12s tooth %.3f amount %.1f rough %.2f-%.2f   %s'
              % (s, t, a, lo, hi, ', '.join(used) or '(unused)'))
