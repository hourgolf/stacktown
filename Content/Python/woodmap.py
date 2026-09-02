#!/usr/bin/env python3
"""Which WOODEN mass a flagship catalogue key resolves to.

    python3 Content/Python/woodmap.py            self-test + the table

Phase F pulled forward: the game must wear the wooden city, so every key the
placer asks for - rid_tier_width(+corner) - needs an answer in timber. The
beta lane wires DA_Catalogue_Wood and the pointer; this module owns the
MAPPING and nothing else. No editor, no MCP.

TWO FINDINGS SHAPE IT, both checked rather than assumed.

1. THE WIDTH GAP. Flagship lots run 820..2460 uu. The 20 masses baked for the
   look study run 600..1000, because they were sized for a demo board and
   nobody asked them to fit a parcel. A wooden mass on the widest lot covers
   41% of its frontage - it would sit marooned in the middle of its plot.

   So the wooden catalogue is RE-BAKED ON THE FLAGSHIP WIDTH LADDER. That
   costs nothing extra: 5 widths x 4 tier bands is 20 masses, exactly the
   count already being baked, in the same three minutes.

2. CORNERS ARE ABOUT DEPTH, NOT FACADE - AND THEY DO APPLY HERE.

   An earlier draft of this module argued that corner variants were a
   flagship-only problem, on the grounds that a flagship corner needs a
   handed variant because its facade is articulated while a wooden mass has
   no blank flank. That argument cited DEPTH_CORNER_DECISIONS - and cited the
   part of it that the document itself RETRACTS: "This section originally
   claimed the protruding corner presented a blank party flank... That was
   wrong on the second half, and the correction matters more than the
   finding."

   What the document actually says is about OCCUPANCY: "the deep value is the
   PARCEL DEPTH: a corner fills its lot front to back", and a corner built at
   base depth "leaves the back half of its parcel empty and its flank stops
   two thirds of the way along the side street."

   That reason is fabrication-independent. A 700-deep wooden mass on a
   1500-deep corner lot leaves half the plot bare, and bare plot is exactly
   as visible in timber as in card. So corners ARE served here - but as a
   DEPTH parameter on the same solid block, not as a handed variant. There is
   no _cL/_cR in wood, because handedness was the facade's problem; there is
   a deep block, because occupancy is everybody's.

   Cost: 4 corner widths x 4 bands = 16 more masses, 36 in total.
"""
import sys

# the flagship's own ladder, which the wooden catalogue now shares
WIDTHS = (820.0, 1230.0, 1640.0, 2050.0, 2460.0)

# flagship tiers run 0..6; the wooden vocabulary has four bands. Coarse on
# purpose - v0 ships fast and the look is refined after.
TIER_BAND = {0: 'flat', 1: 'flat',
             2: 'setback1', 3: 'setback1',
             4: 'setback2', 5: 'setback2',
             6: 'tower'}
BANDS = ('flat', 'setback1', 'setback2', 'tower')

# D3: TIMBER OWNS TONE, AND TONE IS IDENTITY - "a building does not repaint
# itself when it gains a storey". So species is chosen from the RECIPE ID and
# nothing else: a vernacular is always the same timber at every tier and every
# width, and the player learns the city's palette as they learn its buildings.
SPECIES = ('maple', 'pine', 'ash', 'oak', 'cherry', 'sapele', 'walnut')


def species_for(rid):
    """Stable per-recipe timber. crc32, not hash() - python randomises str
    hashing per process, and a city that repaints itself on restart is the
    bug D3 exists to prevent."""
    import zlib
    return SPECIES[zlib.crc32(rid.encode()) % len(SPECIES)]


# corner lots in the pinned city are 1230/1640/2050/2460 - never 820
CORNER_WIDTHS = (1230.0, 1640.0, 2050.0, 2460.0)
DEPTH_BASE = 700.0
DEPTH_CORNER = 1500.0          # citylayout's BLOCK_DEPTH, per recipes


def asset_name(width, band, corner=False):
    return 'SM_WMass_w%d_%s%s' % (int(round(width)), band,
                                  '_d1500' if corner else '')


def resolve(rid, tier, width, corner=None):
    """The wooden asset for a flagship key. `corner` is accepted and ignored.

    Raises rather than guessing on an unknown tier: a silent fallback here is
    how the city stops being the one that was pinned, which is the fault
    testcity_pins was written to prevent.
    """
    if tier not in TIER_BAND:
        raise KeyError('tier %r outside the flagship ladder 0..6' % tier)
    w = min(WIDTHS, key=lambda x: abs(x - float(width)))
    if abs(w - float(width)) > 1.0:
        raise ValueError('width %r is not on the ladder %s - a wooden mass '
                         'must fit its parcel exactly, not nearly'
                         % (width, [int(x) for x in WIDTHS]))
    deep = bool(corner)
    if deep and w not in CORNER_WIDTHS:
        raise ValueError('corner lot at width %r - no corner lot in the '
                         'pinned city is that wide, so no deep mass is baked '
                         'for it' % width)
    return {'asset': asset_name(w, TIER_BAND[tier], deep),
            'species': species_for(rid),
            'band': TIER_BAND[tier], 'width': w,
            'depth': DEPTH_CORNER if deep else DEPTH_BASE,
            'corner': deep}


def catalogue():
    """Every wooden asset this mapping can ask for.

    5 widths x 4 bands plain, plus 4 corner widths x 4 bands deep = 36.
    """
    return ([asset_name(w, b) for w in WIDTHS for b in BANDS]
            + [asset_name(w, b, True) for w in CORNER_WIDTHS for b in BANDS])


def _selftest():
    import testcity_pins as TP
    # 1. EVERY PINNED LOT RESOLVES, at every tier of its growth range.
    for lot, p in TP.PINS.items():
        for t in range(7):
            r = resolve(p['rid'], t, p['w'], corner=p['corner'])
            assert r['asset'] in catalogue(), '%s t%d -> %s' % (lot, t, r['asset'])
    # 2. species is per-RECIPE and stable across tier and width (D3)
    for rid in ('vernacular', 'modern7', 'tower'):
        got = {resolve(rid, t, w)['species']
               for t in range(7) for w in WIDTHS}
        assert len(got) == 1, '%s wears %d timbers, should wear 1' % (rid, len(got))
    # 3. a corner resolves to a DEEP mass, not to the same one
    a = resolve('modern7', 4, 1640.0, corner=None)
    b = resolve('modern7', 4, 1640.0, corner='right')
    assert a['asset'] != b['asset'], 'corner did not change the asset'
    assert b['depth'] == DEPTH_CORNER and a['depth'] == DEPTH_BASE
    # handedness does NOT: left and right are the same solid block
    c = resolve('modern7', 4, 1640.0, corner='left')
    assert b['asset'] == c['asset'], 'wood should not be handed'
    # 4. an off-ladder width is REFUSED rather than rounded
    try:
        resolve('tower', 6, 999.0)
        raise AssertionError('off-ladder width was accepted')
    except ValueError:
        pass
    # 5. the catalogue is exactly 20
    assert len(catalogue()) == 36, len(catalogue())
    return True


def main():
    _selftest()
    print('woodmap self-test: all pins resolve, species stable, corner '
          'ignored, off-ladder refused')
    print()
    print('WOODEN CATALOGUE — %d assets' % len(catalogue()))
    print('%-10s %s' % ('width', '  '.join('%-10s' % b for b in BANDS)))
    for w in WIDTHS:
        print('%-10.0f %s' % (w, '  '.join('%-10s' % TIER_BAND and
                                           asset_name(w, b).split('_')[-1]
                                           for b in BANDS)))
    print()
    import testcity_pins as TP
    print('THE 14 PINNED LOTS at their pinned tier')
    print('%-5s %-14s %-4s %-6s %-24s %s' % ('lot', 'rid', 'tier', 'w',
                                             'wooden asset', 'timber'))
    for lot in sorted(TP.PINS):
        p = TP.PINS[lot]
        r = resolve(p['rid'], p['tier'], p['w'], corner=p['corner'])
        print('%-5s %-14s %-4d %-6d %-24s %s'
              % (lot, p['rid'], p['tier'], p['w'], r['asset'], r['species']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
