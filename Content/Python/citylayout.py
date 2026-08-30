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

BLOCK_LEN = 4800.0                      # along the arterial
BLOCK_DEPTH = 1500.0                    # back from the arterial
LOTS_PER_FRONT = 6                      # 4800 / 6 = 800 each, hand-divisible

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


def lots(block_name, n=LOTS_PER_FRONT):
    """Divide a block's arterial frontage into n lots, west to east.

    Returns (lot_key, x0, x1, is_corner). Corners are the lots at either end -
    they carry a second frontage onto the cross street and the placer must
    treat them differently.
    """
    b = blocks()[block_name]
    x0, _, x1, _ = b['env']
    w = (x1 - x0) / float(n)
    out = []
    for i in range(n):
        lx0 = x0 + i * w
        corner = (i == 0) or (i == n - 1)
        out.append(('%s%d' % (block_name, i), lx0, lx0 + w, corner))
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
    return (b['NE']['env'] == (1130.0, 1130.0, 5930.0, 2630.0)
            and b['NW']['env'] == (-5930.0, 1130.0, -1130.0, 2630.0)
            and b['SE']['env'] == (1130.0, -2630.0, 5930.0, -1130.0)
            and b['SW']['env'] == (-5930.0, -2630.0, -1130.0, -1130.0))


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
    ls = lots('NE')
    first, last = ls[0], ls[-1]
    return (len(ls) == 6
            and abs(first[1] - 1130.0) < 1e-9 and abs(first[2] - 1930.0) < 1e-9
            and abs(last[2] - 5930.0) < 1e-9
            and first[3] and last[3]
            and not any(l[3] for l in ls[1:-1]))


@selftest('LOTS-TILE-THE-FRONT')
def _lots_tile():
    """Contiguous, no gap and no overlap - the frontage is fully consumed."""
    ls = lots('SW')
    if abs(ls[0][1] - (-5930.0)) > 1e-9 or abs(ls[-1][2] - (-1130.0)) > 1e-9:
        return False
    return all(abs(ls[i][2] - ls[i + 1][1]) < 1e-9 for i in range(len(ls) - 1))


@selftest('EMISSION-END-TO-END')
def _emission_end_to_end():
    """The layout feeds parcelmeta and survives its gate."""
    r = parcelmeta.ParcelRegistry()
    es = emit_block('NE', r, 'd90957f')
    if len(es) != 6:
        return False
    ok, _ = parcelmeta.accept(es[0], geometry_head='d90957f')
    f = es[0]['frontage']
    # lot NE0 spans x 1130..1930 -> centre 1530, width 800
    return (ok and abs(f['centre'] - 1530.0) < 1e-9
            and abs(f['width'] - 800.0) < 1e-9
            and len({e['parcel_id'] for e in es}) == 6)


@selftest('IDS-SURVIVE-REPLACEMENT')
def _ids_survive():
    r = parcelmeta.ParcelRegistry()
    a = [e['parcel_id'] for e in emit_block('NE', r, 'd90957f')]
    emit_block('NW', r, 'd90957f')                 # another block placed
    b = [e['parcel_id'] for e in emit_block('NE', r, 'd90957f')]
    return a == b


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
            print('  block %-3s x %8.0f..%-8.0f y %8.0f..%-8.0f  %d lots,'
                  ' 2 corners' % (n, x0, x1, y0, y1, LOTS_PER_FRONT))
    sys.exit(0 if ok else 1)
