"""Per-parcel metadata emission for the district placer. SCHEMA v0.

DECLARED BEFORE THE PLACER EMITS A SINGLE FIELD, per the contract in
Docs/DISTRICT_PLACER_CONTRACT.md. Nothing here places anything; this module
is the schema, its known-answer test, and the identity registry. The placer
imports it and is refused if the schema does not agree with itself.

WHAT IS NOT HERE, AND WHY. econ, parking and ambience were cut from v0. The
contract's own rule is that a field lands WITH the system that reads it, and
none of the three has a consumer. The defence for keeping them - "a
reservation of names, not a build list" - was rejected with same-day
evidence: on 2026-08-30 preview.py wrote the RAW coplanar pair count into the
regression ledger while gate_11 judges the scatter-EXEMPT count. A field was
emitted that its consumer did not use, nobody noticed until a 548-model wave,
and the ledger's max read 86 against a budget of 75 the gate had correctly
passed at 42. That is what emission-before-consumer costs. The three names
live in the contract's futures paragraph and may return WITH their systems.

THE FIVE THINGS THIS SCHEMA REFUSES TO GET WRONG, each from a measured
failure rather than from taste:

  IDENTITY      parcel_id is (block, ordinal-at-first-placement) and never
                renumbers. The 2026-08-30 coplanar bug was an identity bug -
                geometry keyed by component names that were not unique, so
                every lookup on a duplicated name silently returned the wrong
                box. An ordinal that shifts on insertion is the same hazard.
  STALENESS     geometry-derived fields carry geometry_head, the catalogue
                commit they were measured against. 548 meshes changed in one
                wave that day; an emission read after a rebake is stale in
                exactly the way MESHES CURRENT THROUGH exists to catch.
  IMPOSSIBILITY camera_poi emits None WITH A REASON when the framing does not
                exist. Measured that day: a works shed with a 1,936 uu stack
                needs more standoff than the board has clear. A schema that
                always promises a number makes the placer emit a distance
                nobody can stand at.
  METHOD        frontage is measured from PER-COMPONENT mesh bounds against
                world transforms. The obvious accessor lies: get_actor_bounds
                gave the Depot a 3,604 uu width when its meshes span 1,552,
                because the actor's bounds start at its neighbour's edge.
  VERSION       consumers assert on META_VERSION and refuse data they do not
                understand, rather than reading a field that has moved.
"""
import math

META_VERSION = 0

# the project's camera - 70 mm on a 36x24 back. ASPECT matches
# Tools/measure/framing.py (live viewport 2313 x 1542), not 16:9; the
# difference is 250 uu of standoff on the easy parcel and is why this is a
# constant here rather than a number remembered at each call site.
FOV_H = 28.84
ASPECT = 1.5
MARGIN = 1.12

TAN_H = math.tan(math.radians(FOV_H / 2.0))
TAN_V = TAN_H / ASPECT

# fields computed FROM THE MESHES - these and only these carry geometry_head
GEOMETRY_DERIVED = ('frontage', 'camera_poi')

SELFTESTS = {}


def selftest(name):
    """Register a self-test. Every one must FAIL if its rule is broken."""
    def deco(fn):
        SELFTESTS[name] = fn
        return fn
    return deco


# ---------------------------------------------------------------------------
# identity
# ---------------------------------------------------------------------------

class ParcelRegistry(object):
    """Mints parcel ids that survive re-placement.

    The ordinal is assigned ONCE, at first placement, and never recomputed.
    A lot that splits RETIRES its id and mints new ones - it does not hand its
    ordinal to one of its children, because a consumer holding the old id
    would then silently follow the wrong half.
    """

    def __init__(self):
        self._next = {}
        self._ids = {}
        self.retired = set()

    def mint(self, block, key):
        """Stable id for `key` within `block`. Idempotent."""
        if (block, key) in self._ids:
            return self._ids[(block, key)]
        n = self._next.get(block, 0)
        self._next[block] = n + 1
        pid = (block, n)
        if pid in self.retired:
            raise ValueError('minted a retired id: %r' % (pid,))
        self._ids[(block, key)] = pid
        return pid

    def retire(self, block, key):
        self.retired.add(self._ids.pop((block, key)))

    def ids(self):
        return sorted(self._ids.values())


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------

def span(boxes, axis):
    """(lo, hi) across PER-COMPONENT boxes. boxes: [((x,y,z),(x,y,z)), ...]"""
    if not boxes:
        raise ValueError('no components to measure')
    return (min(b[0][axis] for b in boxes), max(b[1][axis] for b in boxes))


def frontage(boxes, along=0, street_axis=1, street_side='min'):
    """Street edge: MEASURED centre and width.

    Method is contractual, not incidental - see the module note on the Depot.
    """
    lo, hi = span(boxes, along)
    edge = span(boxes, street_axis)[0 if street_side == 'min' else 1]
    return {'centre': (lo + hi) / 2.0, 'width': hi - lo, 'edge': edge,
            'along_axis': along, 'street_axis': street_axis}


def camera_poi(boxes, clear_standoff, along=0, street_axis=1,
               street_side='min', up=2):
    """Facade centre + whole-building standoff at the gate optic.

    Returns None WITH A REASON when the framing does not exist in the space
    available. The caller gets ('reason', str) rather than a number it cannot
    use - a promised standoff nobody can stand at is worse than an absence.
    """
    f = frontage(boxes, along, street_axis, street_side)
    zlo, zhi = span(boxes, up)
    need_w = (f['width'] / 2.0 * MARGIN) / TAN_H
    need_h = ((zhi - zlo) / 2.0 * MARGIN) / TAN_V
    need = max(need_w, need_h)
    poi = {'facade_centre': (f['centre'], f['edge'], (zlo + zhi) / 2.0),
           'standoff': need,
           'limited_by': 'width' if need_w >= need_h else 'height'}
    if need > clear_standoff:
        return None, {'reason': 'standoff_exceeds_clear',
                      'required': need, 'clear': clear_standoff,
                      'limited_by': poi['limited_by']}
    return poi, None


# ---------------------------------------------------------------------------
# emission
# ---------------------------------------------------------------------------

def emit(parcel_id, recipe, tier, width, boxes, clear_standoff,
         geometry_head, practicals=()):
    """The full v0 emission for one parcel.

    geometry_head is REQUIRED. A geometry-derived field with no record of the
    catalogue it was measured against cannot be checked for staleness, and an
    unstaleable number is the shape of the regression ledger that had never
    once been compared to anything.
    """
    if not geometry_head:
        raise ValueError('geometry_head is required for a v0 emission')
    poi, why = camera_poi(boxes, clear_standoff)
    return {'meta_version': META_VERSION,
            'parcel_id': parcel_id,
            'recipe': recipe, 'tier': tier, 'width': width,
            'geometry_head': geometry_head,
            'frontage': frontage(boxes),
            'camera_poi': poi,
            'camera_poi_absent': why,
            'practicals': list(practicals)}


def accept(emission, want_version=META_VERSION, geometry_head=None):
    """A consumer's gate. Refuses rather than reads a field that has moved."""
    if emission.get('meta_version') != want_version:
        return False, 'meta_version %r, consumer wants %r' % (
            emission.get('meta_version'), want_version)
    if geometry_head and emission.get('geometry_head') != geometry_head:
        return False, 'geometry_head %s, catalogue is %s - re-derive' % (
            emission.get('geometry_head'), geometry_head)
    return True, None


# ---------------------------------------------------------------------------
# the known-answer parcels. EVERY FIELD DERIVABLE BY HAND.
# ---------------------------------------------------------------------------

# EASY: a 1000 x 400 x 600 mass on four components, street to the south.
#   frontage centre  (1000 + 2000) / 2                       = 1500
#   frontage width    2000 - 1000                            = 1000
#   need_w  (1000/2 * 1.12) / 0.257128                       = 2177.9
#   need_h  ( 600/2 * 1.12) / 0.1714187                      = 1960.1097
#   standoff = max                                       = 2177.8996 (width)
EASY = [((1000.0, 3000.0, 0.0), (1400.0, 3400.0, 600.0)),
        ((1400.0, 3000.0, 0.0), (1700.0, 3400.0, 480.0)),
        ((1700.0, 3000.0, 0.0), (2000.0, 3400.0, 520.0)),
        ((1200.0, 3100.0, 0.0), (1800.0, 3300.0, 300.0))]

# UNFRAMEABLE: the works-shed case measured 2026-08-30. 1852 wide, 1936 tall
# with its stack, against 4506 uu of clear board.
#   need_w  (1852/2 * 1.12) / 0.257128                      = 4033.4701
#   need_h  (1936/2 * 1.12) / 0.1714187                     = 6324.6205
#   required 6324.6205 > 4506 clear -> None, standoff_exceeds_clear
#   (height-limited: it is the STACK that makes it unframeable, not
#    the width - the width alone would fit at 4033.5)
UNFRAMEABLE = [((1224.0, 3030.0, 0.0), (3076.0, 4166.0, 1050.0)),
               ((2000.0, 3400.0, 1050.0), (2300.0, 3700.0, 1936.0))]

# The Depot, 2026-08-30: per-component meshes span 1552, while the actor's own
# bounds reported 3604 because they start at the neighbour's edge.
DEPOT_COMPONENTS = [((3124.0, 3030.0, 0.0), (4676.0, 4166.0, 710.0))]
DEPOT_ACTOR_BOUNDS = [((1072.0, 3030.0, 0.0), (4676.0, 4166.0, 710.0))]


@selftest('KA-EASY')
def _ka_easy():
    e = emit(('H', 0), 'deco', 0, 1230.0, EASY, 4506.0, 'd90957f')
    f, poi = e['frontage'], e['camera_poi']
    return (abs(f['centre'] - 1500.0) < 1e-6
            and abs(f['width'] - 1000.0) < 1e-6
            and abs(f['edge'] - 3000.0) < 1e-6
            and poi is not None and e['camera_poi_absent'] is None
            and abs(poi['standoff'] - 2177.8996) < 1e-3
            and poi['limited_by'] == 'width')


@selftest('KA-UNFRAMEABLE')
def _ka_unframeable():
    e = emit(('H', 1), 'works', 0, 1900.0, UNFRAMEABLE, 4506.0, 'd90957f')
    why = e['camera_poi_absent']
    return (e['camera_poi'] is None and why is not None
            and why['reason'] == 'standoff_exceeds_clear'
            and abs(why['required'] - 6324.6205) < 1e-3
            and why['limited_by'] == 'height')


@selftest('FRONTAGE-METHOD')
def _frontage_method():
    """Per-component measurement, and the lying accessor caught in the act."""
    good = frontage(DEPOT_COMPONENTS)['width']
    bad = frontage(DEPOT_ACTOR_BOUNDS)['width']
    return abs(good - 1552.0) < 1e-6 and abs(bad - 3604.0) < 1e-6 and good < bad


@selftest('ID-NO-RENUMBER')
def _id_no_renumber():
    r = ParcelRegistry()
    first = [r.mint('H', k) for k in ('a', 'b', 'c')]
    r.mint('H', 'inserted')
    return [r.mint('H', k) for k in ('a', 'b', 'c')] == first


@selftest('ID-SPLIT-RETIRES')
def _id_split_retires():
    r = ParcelRegistry()
    r.mint('H', 'a')
    r.retire('H', 'a')
    new = [r.mint('H', 'a1'), r.mint('H', 'a2')]
    return ('H', 0) in r.retired and ('H', 0) not in new and new[0] != new[1]


@selftest('ID-NO-COLLISION')
def _id_no_collision():
    r = ParcelRegistry()
    ids = [r.mint(b, k) for b in ('H', 'J') for k in range(4)]
    return len(ids) == len(set(ids))


@selftest('VERSION-REFUSED')
def _version_refused():
    e = emit(('H', 0), 'deco', 0, 1230.0, EASY, 4506.0, 'd90957f')
    ok, _ = accept(e, want_version=META_VERSION + 1)
    return not ok and accept(e)[0]


@selftest('STALENESS-REFUSED')
def _staleness_refused():
    e = emit(('H', 0), 'deco', 0, 1230.0, EASY, 4506.0, 'd90957f')
    stale, _ = accept(e, geometry_head='31b03b5')
    fresh, _ = accept(e, geometry_head='d90957f')
    return (not stale) and fresh


@selftest('HEAD-REQUIRED')
def _head_required():
    try:
        emit(('H', 0), 'deco', 0, 1230.0, EASY, 4506.0, '')
    except ValueError:
        return True
    return False


@selftest('NO-SPECULATIVE-FIELDS')
def _no_speculative_fields():
    """econ/parking/ambience were CUT. This fails if one grows back."""
    e = emit(('H', 0), 'deco', 0, 1230.0, EASY, 4506.0, 'd90957f')
    return not ({'econ', 'parking', 'ambience'} & set(e))


def selftests(verbose=True):
    broken = sorted(k for k, fn in SELFTESTS.items() if not fn())
    if broken:
        print('PARCELMETA SELF-TEST FAILED: %s - emitting nothing' % broken)
        return False
    if verbose:
        print('  parcelmeta v%d: %d/%d self-tests pass'
              % (META_VERSION, len(SELFTESTS), len(SELFTESTS)))
    return True


if __name__ == '__main__':
    import sys
    ok = selftests()
    if ok:
        e = emit(('H', 0), 'deco', 0, 1230.0, EASY, 4506.0, 'd90957f')
        print('  known-answer parcel %s: frontage %.0f wide at %.0f,'
              ' standoff %.1f (%s-limited)'
              % (e['parcel_id'], e['frontage']['width'],
                 e['frontage']['centre'], e['camera_poi']['standoff'],
                 e['camera_poi']['limited_by']))
        u = emit(('H', 1), 'works', 0, 1900.0, UNFRAMEABLE, 4506.0, 'd90957f')
        print('  unframeable parcel %s: %s, needs %.1f of %.1f clear'
              % (u['parcel_id'], u['camera_poi_absent']['reason'],
                 u['camera_poi_absent']['required'],
                 u['camera_poi_absent']['clear']))
    sys.exit(0 if ok else 1)
