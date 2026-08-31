"""Test-city layout: one arterial crossing, four blocks, derived not placed.

ROADS ARE DERIVED, NOT PLACED - city.py's doctrine, reused rather than
restated. The widths are the input and every facade line falls out of them,
so changing a road width moves the city instead of invalidating six
hand-written constants. This module imports those widths; it does not own a
second copy of them.

DECLARED BEFORE ANYTHING IS PLACED. The layout is data with a known-answer
test, exactly as parcelmeta is, because the placer's frontage and camera_poi
are computed off these lines - a layout that is wrong by 30 uu produces a
whole city of parcels whose measured frontage is wrong by 30 uu, and the
census would not notice.

THE SHAPE, and why this one. One crossing, four quadrant blocks. Every block
therefore has TWO street frontages and a corner at the crossing, which is the
condition the placer is most likely to get wrong - corner-origin errors have
cost this project twice. Blocks are long enough to carry mid-block lots as
well, so the easy case is tested beside the awkward one rather than instead
of it.

    y
    ^   NW block          |  NE block
        facade y +1130    |  facade y +1130
    ----------------------+----------------------  arterial, CORRIDOR wide
        SW block          |  SE block
                          ^ cross street, CORRIDOR wide
"""
import city as _c
import parcelmeta

# derived, not chosen
CORRIDOR = _c.CORRIDOR                  # 1400 carriageway + 2 * 430 footway
HALF = CORRIDOR / 2.0                   # facade line offset from a centreline

# THE CATALOGUE'S WIDTH LADDER IS THE INPUT, not a number that divided
# nicely. recipes offers 820 / 1230 / 1640 / 2050 / 2460, which is
# 410 x {2,3,4,5,6} - so a block length that is NOT a multiple of 410 cannot
# be tiled by catalogue buildings at all. BLOCK_LEN was 4800, chosen because
# it divided by six; lots came out 800 wide and NOTHING IN THE CATALOGUE FITS
# THEM, which is why the first placement could only be placeholder boxes.
# 4920 = 410 x 12 = 6 lots of 820, the narrowest real width.
WIDTH_QUANTUM = 410.0
BLOCK_LEN = 4920.0                      # along the arterial, 12 quanta
BLOCK_DEPTH = 1500.0                    # back from the arterial

# EACH BLOCK GETS A DIFFERENT PARTITION, and that is not decoration.
# Six equal lots of 820 is a valid tiling, and it was the first one - but
# ONLY vernacular and vernacular8 are baked at w820, so a city of 820 lots
# is a city of ONE ERA. Worse, vernacular is the era palette.scheme_for
# promotes to brick, so half the parcels drew MI_dist_brick and the whole
# city measured R-B +23.6 against the sandbox board frame's +8.4. "Very
# brown" was a width decision, not a lighting one.
# Every partition below sums to BLOCK_LEN and uses only catalogue widths.
PARTITIONS = {'NE': (2460.0, 1640.0, 820.0),
              'NW': (1230.0, 1230.0, 1230.0, 1230.0),
              'SE': (2050.0, 1640.0, 1230.0),
              'SW': (820.0, 1230.0, 1230.0, 1640.0)}

SELFTESTS = {}


def selftest(name):
    def deco(fn):
        SELFTESTS[name] = fn
        return fn
    return deco


def blocks():
    """The four quadrant envelopes, keyed by compass name.

    Each is (x0, y0, x1, y1) with the ARTERIAL FRONTAGE named separately -
    a block knows which of its edges faces the main street, because that is
    the edge the placer measures frontage against and it is not recoverable
    from the envelope alone.
    """
    out = {}
    for name, sx, sy in (('NE', 1, 1), ('NW', -1, 1),
                         ('SE', 1, -1), ('SW', -1, -1)):
        x_in = sx * HALF
        y_in = sy * HALF
        x0, x1 = sorted((x_in, x_in + sx * BLOCK_LEN))
        y0, y1 = sorted((y_in, y_in + sy * BLOCK_DEPTH))
        out[name] = {'env': (x0, y0, x1, y1),
                     'arterial_edge': y_in,       # the y facing the arterial
                     'cross_edge': x_in,          # the x facing the cross st
                     'faces': 'south' if sy > 0 else 'north'}
    return out


def lots(block_name):
    """Lay the block's partition along its arterial frontage, west to east.

    Returns (lot_key, x0, x1, is_corner). Corners are the lots at either end -
    they carry a second frontage onto the cross street and the placer must
    treat them differently.
    """
    b = blocks()[block_name]
    x0, _, x1, _ = b['env']
    part = PARTITIONS[block_name]
    out, lx = [], x0
    for i, w in enumerate(part):
        corner = (i == 0) or (i == len(part) - 1)
        out.append(('%s%d' % (block_name, i), lx, lx + w, corner))
        lx += w
    return out


def parcel_boxes(block_name, lot, height=1200.0):
    """A placeholder mass for one lot, as PER-COMPONENT boxes.

    Not a building - the shape the placer will hand parcelmeta once genbuild
    fills the lot. Present so the layout can be measured end to end before a
    single recipe is chosen.
    """
    b = blocks()[block_name]
    _, y0, _, y1 = b['env']
    _key, lx0, lx1, _corner = lot
    return [((lx0, y0, 0.0), (lx1, y1, height))]


def emit_block(block_name, registry, geometry_head, clear_standoff=9000.0):
    """Full v0 emission for every lot on a block's arterial frontage."""
    out = []
    for lot in lots(block_name):
        pid = registry.mint(block_name, lot[0])
        out.append(parcelmeta.emit(pid, 'pending', 0, lot[2] - lot[1],
                                   parcel_boxes(block_name, lot),
                                   clear_standoff, geometry_head))
    return out


# ---------------------------------------------------------------------------
# known answers. HALF = (1400 + 2*430) / 2 = 1130. BLOCK_LEN 4800 over 6 lots
# is 800 each, so every corner below is arithmetic anyone can check.
# ---------------------------------------------------------------------------

@selftest('CORRIDOR-DERIVED')
def _corridor_derived():
    return abs(CORRIDOR - 2260.0) < 1e-9 and abs(HALF - 1130.0) < 1e-9


@selftest('BLOCK-CORNERS')
def _block_corners():
    b = blocks()
    return (b['NE']['env'] == (1130.0, 1130.0, 6050.0, 2630.0)
            and b['NW']['env'] == (-6050.0, 1130.0, -1130.0, 2630.0)
            and b['SE']['env'] == (1130.0, -2630.0, 6050.0, -1130.0)
            and b['SW']['env'] == (-6050.0, -2630.0, -1130.0, -1130.0))


@selftest('BLOCKS-CLEAR-THE-ROADS')
def _blocks_clear_roads():
    """No block may intrude on a carriageway or a footway."""
    for b in blocks().values():
        x0, y0, x1, y1 = b['env']
        if min(abs(x0), abs(x1)) < HALF - 1e-9:
            return False
        if min(abs(y0), abs(y1)) < HALF - 1e-9:
            return False
    return True


@selftest('LOT-DIVISION')
def _lot_division():
    # NE is 2460 + 1640 + 820 from x 1130: 1130..3590..5230..6050
    ls = lots('NE')
    first, last = ls[0], ls[-1]
    return (len(ls) == 3
            and abs(first[1] - 1130.0) < 1e-9 and abs(first[2] - 3590.0) < 1e-9
            and abs(ls[1][2] - 5230.0) < 1e-9
            and abs(last[2] - 6050.0) < 1e-9
            and first[3] and last[3] and not ls[1][3])


@selftest('LOTS-TILE-THE-FRONT')
def _lots_tile():
    """Contiguous, no gap and no overlap - the frontage is fully consumed."""
    ls = lots('SW')
    if abs(ls[0][1] - (-6050.0)) > 1e-9 or abs(ls[-1][2] - (-1130.0)) > 1e-9:
        return False
    return all(abs(ls[i][2] - ls[i + 1][1]) < 1e-9 for i in range(len(ls) - 1))


@selftest('EMISSION-END-TO-END')
def _emission_end_to_end():
    """The layout feeds parcelmeta and survives its gate."""
    r = parcelmeta.ParcelRegistry()
    es = emit_block('NE', r, 'd90957f')
    if len(es) != 3:
        return False
    ok, _ = parcelmeta.accept(es[0], geometry_head='d90957f')
    f = es[0]['frontage']
    # lot NE0 spans x 1130..3590 -> centre 2360, width 2460
    return (ok and abs(f['centre'] - 2360.0) < 1e-9
            and abs(f['width'] - 2460.0) < 1e-9
            and len({e['parcel_id'] for e in es}) == len(es))


@selftest('IDS-SURVIVE-REPLACEMENT')
def _ids_survive():
    r = parcelmeta.ParcelRegistry()
    a = [e['parcel_id'] for e in emit_block('NE', r, 'd90957f')]
    emit_block('NW', r, 'd90957f')                 # another block placed
    b = [e['parcel_id'] for e in emit_block('NE', r, 'd90957f')]
    return a == b


@selftest('LOTS-ARE-CATALOGUE-WIDTHS')
def _lots_are_catalogue_widths():
    """Every lot must be a width the catalogue can actually build.

    This is the test the first layout did not have, which is why it produced
    800 uu lots that no recipe fits and a city of placeholder boxes.
    """
    import recipes
    have = {round(w) for r in recipes.RECIPES for w in recipes.widths(r)}
    for b in blocks():
        for _k, x0, x1, _c in lots(b):
            if round(x1 - x0) not in have:
                return False
    return abs(BLOCK_LEN % WIDTH_QUANTUM) < 1e-9


@selftest('PARTITIONS-TILE-AND-VARY')
def _partitions_tile_and_vary():
    """Each partition sums to the block, and the city spans widths.

    The second half is the point: a single-width city can only reach the
    recipes baked at that width, and at 820 that is vernacular alone.
    """
    seen = set()
    for name, part in PARTITIONS.items():
        if abs(sum(part) - BLOCK_LEN) > 1e-9:
            return False
        seen.update(part)
    return len(seen) >= 4


def selftests(verbose=True):
    broken = sorted(k for k, fn in SELFTESTS.items() if not fn())
    if broken:
        print('CITYLAYOUT SELF-TEST FAILED: %s - laying out nothing' % broken)
        return False
    if verbose:
        print('  citylayout: %d/%d self-tests pass'
              % (len(SELFTESTS), len(SELFTESTS)))
    return True


if __name__ == '__main__':
    import sys
    ok = parcelmeta.selftests() and selftests()
    if ok:
        print('  corridor %.0f (road %.0f + 2 x walk %.0f), facade lines at'
              ' +/-%.0f' % (CORRIDOR, _c.ROAD_W, _c.WALK_W, HALF))
        for n, b in sorted(blocks().items()):
            x0, y0, x1, y1 = b['env']
            print('  block %-3s x %8.0f..%-8.0f y %8.0f..%-8.0f  %s'
                  % (n, x0, x1, y0, y1,
                     ' + '.join('%.0f' % w for w in PARTITIONS[n])))
    sys.exit(0 if ok else 1)
