"""The per-model gate: judge ONE model, alone, BEFORE it is baked.

Why this exists, stated plainly because it is the whole design:

    Baking destroys the thing the invariant suite measures.

Every rule in invariants.py reads a level snapshot and counts COMPONENTS.
DETAIL-01 asks "does this building carry 0.70 parts per m2 of elevation" by
counting boxes. Merge that building into one StaticMesh and it becomes ONE
component - the rule does not fail, it silently stops having an opinion, which
is worse than failing. A catalogue of baked meshes cannot be checked the way
the sandbox city is.

So the check moves to the only moment it can see anything: after the roles are
bound and before the merge. What the merge then produces carries a STAMP
saying which gate it passed, so a mesh in the catalogue is evidence rather
than an assurance.

Pure functions over plain data, no `unreal` import, for the same reason
invariants.py is: a rule that cannot be run against a synthetic defect cannot
be proved able to detect a real one. gate_run.py supplies the real snapshot.

Thresholds come from qc.py - the SAME numbers the suite uses. A gate that
passed a model the suite would fail is worse than no gate at all.

ARCHETYPES. The rules above encode "articulated street building" as the one
definition of good, and GATE-03/07/08 would refuse a CORRECT warehouse or
barn - which teaches people to pass the gate with --force, the failure mode
that must never install itself. So every rule declares, via `judges=`, which
archetypes it is entitled to judge, and archetypes.py declares the other half
of the ledger: what "good" means per archetype, which rules are exempt (with
reasons), and which thresholds are overridden (still qc.py constants). With
`archetype` absent or 'street' the verdict is byte-identical to the
pre-archetype gate - archetypes.py proves that against planted defects. An
exempted rule is SKIPPED WITH AN EXPLICIT LINE in the verdict, never
silently; an unknown archetype raises, never defaults.
"""
import math
import sys

import labels
import archetypes
from qc import DETAIL_MIN, MAT_MIN, AUTO_NAME, DEFAULT_MATS

RULES = []
SELFTESTS = {}

# every archetype, spelled out - a rule that judges everything says so
# explicitly, because a NEW archetype must be a decision on every rule, not
# an inheritance
ALL_ARCHES = ('street', 'industrial', 'agricultural-structure')


def rule(rid, statement, judges=None):
    """`judges` is the rule's half of the applicability ledger: the
    archetypes this rule is entitled to judge. archetypes.check_declarations
    fails the gate if it is missing or disagrees with the registry."""
    def deco(fn):
        RULES.append(dict(id=rid, statement=statement, check=fn,
                          judges=judges))
        return fn
    return deco


def selftest(rid):
    def deco(fn):
        SELFTESTS[rid] = fn
        return fn
    return deco


# --- the model, as plain data ----------------------------------------------
def model(spec, actors):
    """spec: the recipe spec. actors: snapshot actors belonging to this model."""
    return dict(spec=spec, actors=list(actors))


def comps(m):
    """Every component that will end up inside the baked mesh."""
    return [c for a in m['actors'] for c in a['comps']]


# The families step_roles actually binds by role prefix. A CORE_ is a single
# StaticMeshActor whose material is assigned directly by core_stage, so
# demanding a role prefix on it is asking the wrong question - and GATE-01 duly
# refused all five vernacular tiers the moment cores were added.
ROLE_BOUND = ('BLD2', 'ELEV', 'ZONE', 'LAMP', 'PLOT')


def role_comps(m):
    """Components the role sweep is responsible for."""
    return [c for a in m['actors']
            if a['label'].split('_')[0] in ROLE_BOUND
            for c in a['comps']]


def building_comps(m):
    """Only the BUILDING's components - not the plot furniture.

    DETAIL-01 counts BLD2_ and ELEV_ and deliberately ignores PLOT_, because
    garden fences are not architectural detail. The gate has to draw the line
    in the SAME place: counting plot furniture toward elevation density would
    let a thin building pass here by having a well-dressed garden, and then
    fail the suite the moment it was placed. That is precisely the "gate more
    lenient than the rule it derives from" this file exists to avoid.
    """
    return [c for a in m['actors']
            if a['label'].split('_')[0] in ('BLD2', 'ELEV')
            for c in a['comps']]


def elevation_m2(spec):
    """Street elevation in square metres - the same measure DETAIL-01 uses."""
    h = (spec.get('gf_h', 300.0) + spec.get('floors', 4)*spec.get('fl_h', 260.0)
         + spec.get('parapet', 0.0))
    return (spec['width']/100.0) * (h/100.0)


def bounds(m):
    """XY min/max of the model, from component AABBs. None if unmeasurable."""
    lo = [1e18, 1e18]
    hi = [-1e18, -1e18]
    seen = False
    for c in comps(m):
        b = c.get('aabb')
        if not b:
            continue
        seen = True
        for i in (0, 1):
            lo[i] = min(lo[i], b[0][i])
            hi[i] = max(hi[i], b[1][i])
    return (lo, hi) if seen else None


def span(m):
    """XY extent of the model. None if unmeasurable."""
    b = bounds(m)
    return (b[1][0]-b[0][0], b[1][1]-b[0][1]) if b else None


# =========================== the rules ======================================
@rule('GATE-01', 'every component carries a role from labels.ROLES',
      judges=ALL_ARCHES)
def gate_01(m):
    return [(c['name'], 'no role prefix') for c in role_comps(m)
            if not labels.role(c['name'])]


@rule('GATE-02', 'no component sits on a default or missing material',
      judges=ALL_ARCHES)
def gate_02(m):
    out = []
    for c in comps(m):
        mats = c.get('mats') or []
        if not mats:
            out.append((c['name'], 'no material slots'))
        elif any(x is None or x in DEFAULT_MATS for x in mats):
            out.append((c['name'], 'default material: %s' % (mats,)))
    return out


# street's density, and industrial's LOWER density (qc.DETAIL_MIN_INDUSTRIAL,
# via the registry override) - but a barn is exempt: plainness is its point
@rule('GATE-03', 'the model carries at least %.2f parts per m2 of elevation'
                 % DETAIL_MIN, judges=('street', 'industrial'))
def gate_03(m):
    area = elevation_m2(m['spec'])
    n = len(building_comps(m))
    if area <= 0 or not n:
        return [(m['spec'].get('name', '?'), 'nothing to measure')]
    d = n/area
    if d < DETAIL_MIN:
        return [(m['spec'].get('name', '?'),
                 '%d parts over %.0f m2 = %.2f/m2, under %.2f'
                 % (n, area, d, DETAIL_MIN))]
    return []


@rule('GATE-04', 'the model uses at least %d distinct materials' % MAT_MIN,
      judges=ALL_ARCHES)
def gate_04(m):
    seen = {x for c in building_comps(m) for x in (c.get('mats') or []) if x}
    if len(seen) < MAT_MIN:
        return [(m['spec'].get('name', '?'),
                 '%d materials: %s' % (len(seen), sorted(seen)))]
    return []


# A cornice, a canopy and a plinth all oversail the pavement - that is what
# they are for, and a building whose ornament stops dead at the property line
# is not a building anyone has seen. So DEPTH allows a bounded front oversail
# while WIDTH stays strict, because width is where neighbours actually collide:
# two parcels sit side by side, and 22 uu of garage roof over the boundary is
# 22 uu inside the house next door. Front oversail hangs over a footway.
OVERSAIL = 130.0          # 1.3 m of ornament over the pavement
SIDE_TOL = 8.0            # a plinth's 6 uu passes; a 22 uu garage roof fails


@rule('GATE-05', 'the model fits its parcel: each SIDE within %.0f uu, %.0f '
                 'uu front oversail allowed' % (SIDE_TOL, OVERSAIL),
      judges=ALL_ARCHES)
def gate_05(m):
    sp = m['spec']
    b = bounds(m)
    if not b:
        return [(sp.get('name', '?'), 'no measurable bounds')]
    out = []
    # parcel_width, not width: the CORE is built narrower than its parcel so
    # the flank slabs can stand proud and still land on the parcel line. The
    # gate must judge against the land the model claims, not the core.
    #
    # PER SIDE, not by span: the old span*1.02 test allowed a one-sided
    # overhang the size of the tolerance plus however far the other side was
    # inset - which is exactly the 22-uu garage-roof case the comment above
    # cites, and it passed.
    pw = sp.get('parcel_width') or sp.get('width')
    # parcel_x0, not x0. In the bake pipeline `x0` is where the CORE starts -
    # inset by half the flank allowance so the flank slabs land on the parcel
    # line - and reading it as the parcel's edge shifted the whole test by 78
    # uu, failing a model that fitted exactly. Same distinction as
    # parcel_width vs width, and for the same reason.
    x0 = sp.get('parcel_x0', sp.get('x0', 0.0))
    if pw:
        if b[0][0] < x0 - SIDE_TOL:
            out.append((sp.get('name', '?'),
                        'low side %.0f uu over the parcel line'
                        % (x0 - b[0][0])))
        if b[1][0] > x0 + pw + SIDE_TOL:
            out.append((sp.get('name', '?'),
                        'high side %.0f uu over the parcel line'
                        % (b[1][0] - (x0 + pw))))
    d = sp.get('parcel_depth') or sp.get('depth', 0.0)
    if d and (b[1][1]-b[0][1]) > d + OVERSAIL:
        out.append((sp.get('name', '?'),
                    'depth %.0f exceeds %.0f + %.0f oversail'
                    % (b[1][1]-b[0][1], d, OVERSAIL)))
    return out


@rule('GATE-06', 'no component was auto-renamed by a name collision',
      judges=ALL_ARCHES)
def gate_06(m):
    # Only on MULTI-PART actors, exactly as NAME-02 does it: the engine calls
    # a StaticMeshActor's one component StaticMeshComponent0 and always has.
    # That is a default name, not a collision, and every CORE_ band has one.
    return [(c['name'], 'auto-renamed') for a in m['actors']
            if len(a['comps']) > 1
            for c in a['comps'] if AUTO_NAME.match(c['name'] or '')]


# =========================== self-tests =====================================
# Every rule must prove it can see its own defect against synthetic data, and
# must ALSO prove it passes a clean model - a rule that fails everything is as
# useless as one that passes everything, and only the pair catches that.
def _c(name, mats=('MI_a', 'MI_b', 'MI_c', 'MI_d'), aabb=None):
    return dict(name=name, mesh='SM', aabb=aabb, mats=list(mats))


def _a(label, comps_):
    return dict(label=label, family=labels.family(label), cls='Actor',
                loc=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), comps=list(comps_))


SPEC = dict(name='Probe', style='house', width=820.0, depth=1500.0,
            gf_h=200.0, fl_h=190.0, floors=1, parapet=0.0)


def _clean(n=None, aabb=True):
    """A model that every rule must pass.

    The parts need a REAR contingent: GATE-08 locates a part by its centre,
    and a part spanning the full depth centres at 50%, so a clean model built
    only of full-depth boxes read as having a blank back and the __main__
    footer printed 'clean model passes: False' from the day it was written."""
    area = elevation_m2(SPEC)
    n = n if n is not None else int(area*DETAIL_MIN) + 20
    D = SPEC['depth']
    box = ([0.0, 0.0, 0.0], [SPEC['width'], D, 400.0])
    rear = ([0.0, D*0.9, 0.0], [SPEC['width'], D, 400.0])
    # the LAST dozen of the SAME n parts sit at the rear, so every count a
    # self-test does against n still holds
    k = min(n, REAR_PARTS + 2)
    # ...and a few of the FRONT contingent are GLAZING, for the same reason
    # and by the same trick. GATE-09 asks a building with floors for at least
    # GLASS_PER_FLOOR openings per floor; this fixture had none, so the
    # __main__ footer printed 'clean model passes: False' and a reader would
    # reasonably conclude the gate was broken rather than the fixture. A model
    # every rule must pass has to actually pass every rule - a fixture that
    # fails is a self-test suite quietly disagreeing with itself. Converted
    # rather than appended so the part count stays exactly n.
    _fl = max(1, int(SPEC.get('floors') or 1))
    g = min(max(1, int(GLASS_PER_FLOOR * _fl + 0.999)), max(0, n - k))
    # EVERY PART GETS ITS OWN CELL. This fixture used to be n copies of one
    # identical box stacked on the same coordinates - which passed every rule
    # only because no rule had ever looked at whether parts overlap. GATE-11
    # looks, and called it what it is: forty coincident surfaces. A model that
    # every rule must pass cannot be built out of the defect one rule hunts.
    # Counts, names, y-ranges and the rear/glazing structure are unchanged, so
    # every other self-test that counts against n still holds; only the x and
    # z positions are new. The 1 uu inset leaves a 2 uu gap between
    # neighbours, well inside GATE-05's 8 uu side tolerance.
    cols = int(math.ceil(math.sqrt(max(n, 1))))
    rows = int(math.ceil(float(n) / cols))
    cw, ch = SPEC['width'] / cols, 400.0 / rows

    def cell(i, y0, y1):
        if not aabb:
            return None
        cx, cz = (i % cols) * cw, (i // cols) * ch
        return ([cx + 1.0, y0, cz + 1.0], [cx + cw - 1.0, y1, cz + ch - 1.0])

    comps, i = [], 0
    for j in range(n - k - g):
        comps.append(_c('Wall_P%d' % j, aabb=cell(i, 0.0, D))); i += 1
    for j in range(g):
        comps.append(_c('Glass_G%d' % j, aabb=cell(i, 0.0, D))); i += 1
    for j in range(k):
        comps.append(_c('Wall_R%d' % j, aabb=cell(i, D*0.9, D))); i += 1
    return model(SPEC, [_a('BLD2_Probe_H', comps)])


@selftest('GATE-01')
def _t01():
    if gate_01(_clean()):
        return False
    # a CORE_ actor's default component name must NOT be a violation
    m = _clean()
    m['actors'].append(_a('CORE_Probe', [_c('StaticMeshComponent0')]))
    if gate_01(m):
        return False
    m = _clean()
    m['actors'][0]['comps'].append(_c('Bogus_Thing'))
    return len(gate_01(m)) == 1


@selftest('GATE-02')
def _t02():
    if gate_02(_clean()):
        return False
    m = _clean()
    m['actors'][0]['comps'].append(_c('Wall_X', mats=['WorldGridMaterial']))
    return len(gate_02(m)) == 1


@selftest('GATE-03')
def _t03():
    if gate_03(_clean()):
        return False
    thin = max(1, int(elevation_m2(SPEC)*DETAIL_MIN) - 5)
    if len(gate_03(_clean(n=thin))) != 1:
        return False
    # and a thin building must STAY failed when its garden is well dressed -
    # otherwise the gate is more lenient than DETAIL-01 and passes models the
    # suite will reject the moment they are placed
    m = _clean(n=thin)
    m['actors'].append(_a('PLOT_Probe',
                          [_c('Frame_Post%d' % i) for i in range(60)]))
    return len(gate_03(m)) == 1


@selftest('GATE-04')
def _t04():
    if gate_04(_clean()):
        return False
    m = model(SPEC, [_a('BLD2_Probe_H',
                        [_c('Wall_P%d' % i, mats=['MI_a'])
                         for i in range(60)])])
    return len(gate_04(m)) == 1


@selftest('GATE-05')
def _t05():
    if gate_05(_clean()):
        return False
    # width: strict, and a garage roof 22 uu over the boundary must fail
    m = _clean()
    wide = ([0.0, 0.0, 0.0], [SPEC['width']*1.5, SPEC['depth'], 400.0])
    m['actors'][0]['comps'].append(_c('Wall_Wide', aabb=wide))
    if len(gate_05(m)) != 1:
        return False
    # the calibration case the old span test PASSED: one side inset 8, the
    # other 22 uu over the line - span only W+14, but the neighbour still
    # has a garage roof in it
    m = _clean()
    over = ([8.0, 0.0, 0.0], [SPEC['width'] + 22.0, SPEC['depth'], 400.0])
    m['actors'][0]['comps'].append(_c('Roof_Garage', aabb=over))
    if len(gate_05(m)) != 1:
        return False
    # a plinth 6 uu proud on both sides is fabrication, not trespass
    m = _clean()
    pl = ([-6.0, 0.0, 0.0], [SPEC['width'] + 6.0, SPEC['depth'], 30.0])
    m['actors'][0]['comps'].append(_c('Wall_Plinth', aabb=pl))
    if gate_05(m):
        return False
    # depth: a cornice oversailing the pavement is allowed...
    m = _clean()
    orn = ([0.0, -OVERSAIL + 20.0, 0.0], [SPEC['width'], SPEC['depth'], 400.0])
    m['actors'][0]['comps'].append(_c('Band_Cornice', aabb=orn))
    if gate_05(m):
        return False
    # a core INSET from its parcel, whose flanks then land exactly on the
    # parcel line, must pass - that is how every catalogue model is built
    inset = dict(SPEC, x0=78.0, width=SPEC['width'] - 156.0,
                 parcel_x0=0.0, parcel_width=SPEC['width'])
    box_ = ([0.0, 0.0, 0.0], [SPEC['width'], SPEC['depth'], 400.0])
    m = model(inset, [_a('BLD2_Probe_H',
                         [_c('Wall_P%d' % i, aabb=box_) for i in range(30)])])
    if gate_05(m):
        return False
    # ...but a building that simply runs off the back of its plot is not
    m = _clean()
    deep = ([0.0, 0.0, 0.0], [SPEC['width'], SPEC['depth'] + OVERSAIL + 60.0, 400.0])
    m['actors'][0]['comps'].append(_c('Wall_Deep', aabb=deep))
    return len(gate_05(m)) == 1


@selftest('GATE-06')
def _t06():
    if gate_06(_clean()):
        return False
    # a single-component actor called StaticMeshComponent0 is the engine's
    # default, not a collision - every CORE_ band is one
    m = _clean()
    m['actors'].append(_a('CORE_Probe', [_c('StaticMeshComponent0')]))
    if gate_06(m):
        return False
    m = _clean()
    m['actors'][0]['comps'].append(_c('StaticMesh12'))
    return len(gate_06(m)) == 1


# Measured across the built city, share of a building's parts sitting behind
# the front third of its own depth:
#
#     Court  (modern)   1%      Narrow (vern)   2%      Civic   18%
#     Rowan  (walkup)  17%      Terrace/Tower  32%      Depot   44%
#     houses        36-41%      Bijou (deco)   59%
#
# The low ones are FACADES: build_vernacular/modern/deco emit a street front
# and a roof, and the flanks arrive later from step_elevations - which only
# treats the two END lots of a block, because a mid-terrace flank is a party
# wall buried against its neighbour. Correct for a fixed city.
#
# A CATALOGUE MESH CANNOT ASSUME A NEIGHBOUR. It is placed wherever the
# grammar or the player puts it, so a blind flank is a hole in the model from
# any angle that is not head-on. 0.20 sits well above the facades (1-2%) and
# below every model that is genuinely built on all sides.
REAR_MIN = 0.20


# the street question only: an industrial or agricultural shell is one honest
# volume, and "articulation behind the front third" is exactly the measure it
# is defined by not having - see archetypes.py for the exemption reasons
@rule('GATE-07', 'at least %.0f%% of the model sits behind its own front third'
                 % (REAR_MIN*100), judges=('street',))
def gate_07(m):
    cs = [c for c in building_comps(m) if c.get('aabb')]
    if len(cs) < 8:
        return []                       # too small to say anything about
    lo = min(c['aabb'][0][1] for c in cs)
    hi = max(c['aabb'][1][1] for c in cs)
    if hi - lo <= 1.0:
        return [(m['spec'].get('name', '?'), 'no depth at all')]
    cut = lo + (hi - lo)/3.0
    deep = sum(1 for c in cs
               if (c['aabb'][0][1] + c['aabb'][1][1])/2.0 > cut)
    f = deep/float(len(cs))
    if f < REAR_MIN:
        return [(m['spec'].get('name', '?'),
                 '%d of %d parts (%.0f%%) behind the front third, under %.0f%%'
                 ' - flanks and rear are missing'
                 % (deep, len(cs), f*100, REAR_MIN*100))]
    return []


@selftest('GATE-07')
def _t07():
    # a building with parts spread through its depth passes
    box = lambda y0, y1: ([0.0, y0, 0.0], [SPEC['width'], y1, 400.0])
    solid = model(SPEC, [_a('BLD2_Probe_H',
                            [_c('Wall_P%d' % i, aabb=box(i*40.0, i*40.0 + 30.0))
                             for i in range(30)])])
    if gate_07(solid):
        return False
    # a facade plus one roof deck spanning the depth does not
    comps_ = [_c('Wall_F%d' % i, aabb=box(0.0, 40.0)) for i in range(29)]
    comps_.append(_c('Roof_Deck', aabb=box(0.0, 1200.0)))
    return len(gate_07(model(SPEC, [_a('BLD2_Probe_H', comps_)]))) == 1


# GATE-07 asks "is there a building behind the front?" and the walk-up passes
# it comfortably - balconies, stairs and mass all through its depth. Its REAR
# FACE was still a blank wall, which the contact sheet found by eye after the
# gate had already passed and baked all three tiers. Two different defects,
# and writing one rule for both is how the second one shipped.
#
# So this asks the other question: does the back of the model carry anything?
# Measured over the built city, parts in the rearmost 30% of a building:
#
#     Rowan (walkup)   0        Terrace/Tower   14-18
#     Alder/Hazel     33        Depot/Foundry   44-49
#
# A blank rear is the wall plus its parapet - a handful of parts. A treated
# rear carries windows, frames, sills and a downpipe, which is dozens.
REAR_FACE = 0.18          # the back band, as a fraction of model depth
REAR_PARTS = 10           # parts that must sit in it


@rule('GATE-08', 'the rear face carries at least %d parts, not a blank wall'
                 % REAR_PARTS, judges=('street',))
def gate_08(m):
    cs = [c for c in building_comps(m) if c.get('aabb')]
    if len(cs) < 8:
        return []
    lo = min(c['aabb'][0][1] for c in cs)
    hi = max(c['aabb'][1][1] for c in cs)
    D = hi - lo
    if D <= 1.0:
        return []                       # GATE-07 owns the no-depth case
    cut = hi - D*REAR_FACE
    n = sum(1 for c in cs if (c['aabb'][0][1] + c['aabb'][1][1])/2.0 > cut)
    if n < REAR_PARTS:
        return [(m['spec'].get('name', '?'),
                 'only %d parts in the rear %.0f%% - the back reads as a blank '
                 'wall' % (n, REAR_FACE*100))]
    return []


@selftest('GATE-08')
def _t08():
    box = lambda y0, y1: ([0.0, y0, 0.0], [SPEC['width'], y1, 400.0])
    # a treated rear: plenty of parts sitting on the back face
    good = [_c('Wall_F%d' % i, aabb=box(0.0, 60.0)) for i in range(20)]
    good += [_c('Glass_R%d' % i, aabb=box(1160.0, 1200.0)) for i in range(14)]
    if gate_08(model(SPEC, [_a('BLD2_Probe_H', good)])):
        return False
    # a blank rear: mass through the depth, but nothing ON the back face
    bad = [_c('Wall_P%d' % i, aabb=box(i*50.0, i*50.0 + 40.0)) for i in range(22)]
    bad.append(_c('Wall_Rear', aabb=box(1150.0, 1200.0)))
    return len(gate_08(model(SPEC, [_a('BLD2_Probe_H', bad)]))) == 1


GLASS_PER_FLOOR = 1.0     # a habitable floor has at least one opening


# a habitable floor has a window whether the building is a terrace or a
# works office - but a barn's hay loft carries no window mandate, so the
# agricultural archetype is exempt
@rule('GATE-09', 'a building with floors carries at least %.0f Glass_ part '
                 'per floor' % GLASS_PER_FLOOR,
      judges=('street', 'industrial'))
def gate_09(m):
    """WHY THIS EXISTS. `build_deco`'s floor loop was written inverted and ran
    ZERO floors for seven of the eight deco recipes - every one of them baked
    with no glazing whatsoever, and the gate passed all seven. GATE-05 checks
    the parcel, GATE-01/06 check naming, MAT_MIN is 4 and DENSITY_MIN is 0.10,
    so a building with no windows clears every one of them comfortably. Four
    rounds of looking at renders went by before anyone noticed that the pale
    stripes between the pilasters were the CORE showing through.

    A floor someone is meant to stand on has a window. That is the whole rule,
    and it is cheap: measured across the catalogue the tightest healthy model
    sits at 1.08 parts per floor, so a threshold of 1.0 fires on the defect
    and on nothing that works.
    """
    sp = m['spec']
    F = int(sp.get('floors') or 0)
    if F <= 0:
        return []                       # a hoarding or a lock-up has no floors
    n = sum(1 for c in building_comps(m)
            if str(c.get('name', '')).startswith('Glass_'))
    if n < F * GLASS_PER_FLOOR:
        return [(sp.get('name', '?'),
                 '%d Glass_ parts for %d floors - the elevation has no '
                 'openings' % (n, F))]
    return []


@selftest('GATE-09')
def _t09():
    sp = dict(SPEC)
    sp['floors'] = 4
    good = [_c('Wall_A%d' % i) for i in range(12)]
    good += [_c('Glass_W%d' % i) for i in range(6)]
    if gate_09(model(sp, [_a('BLD2_Probe_H', good)])):
        return False
    # the exact defect: a full elevation of walls and not one opening
    bad = [_c('Wall_A%d' % i) for i in range(30)]
    bad += [_c('Mullion_M%d' % i) for i in range(8)]
    if len(gate_09(model(sp, [_a('BLD2_Probe_H', bad)]))) != 1:
        return False
    # and a hoarding, which legitimately has none
    sp0 = dict(SPEC)
    sp0['floors'] = 0
    return not gate_09(model(sp0, [_a('BLD2_Probe_H',
                                      [_c('Wall_A%d' % i) for i in range(9)])]))


COPLANAR_TOL = 0.06       # uu; below this the depth buffer cannot choose


@rule('GATE-10', 'no part sits exactly on the core top plane (z-fighting)',
      judges=ALL_ARCHES)
def gate_10(m):
    """WHY THIS EXISTS. Capping the core at the roof line so the roof would be
    VISIBLE (see cores.ROOF_CLEAR) put its top face at exactly ztop - which is
    also where every flat roof puts its deck's top face, its parapet's base,
    and its top-floor wall boxes. Three coplanar surfaces, nothing for the
    depth buffer to choose between them, and the result was jagged white
    patches crawling across every roof in the catalogue, frame after frame.

    It was reported as "flickering" and chased as a lighting fault for a long
    time. It is not one: two faces at the same depth are a GEOMETRY fault and
    no amount of GI tuning will fix one. This rule sees it at bake time.

    Only parts that actually sit OVER the core in plan can fight it - a vent
    on the facade at y < the core front is at the same height and never
    touches it.
    """
    sp = m['spec']
    try:
        import cores
    except Exception:
        return []
    bands = cores.bands_for(sp)
    if not bands:
        return []                       # a detached style has no core
    ct = max(b[1] for b in bands)
    front = bands[-1][2]
    hits = []
    for c in building_comps(m):
        ab = c.get('aabb')
        if not ab:
            continue
        if ab[1][1] <= front + 1.0:
            continue                    # in front of the core: cannot fight it
        for z in (ab[0][2], ab[1][2]):
            if abs(z - ct) < COPLANAR_TOL:
                hits.append(str(c.get('name', '?')))
                break
    if hits:
        return [(sp.get('name', '?'),
                 '%d part(s) coplanar with the core top at z=%.1f: %s'
                 % (len(hits), ct, ', '.join(sorted(set(hits))[:4])))]
    return []


@selftest('GATE-10')
def _t10():
    import cores
    sp = dict(SPEC)
    sp.update(floors=4, gf_h=400.0, fl_h=280.0, parapet=40.0, open_roof=True,
              style='vernacular')
    ct = max(b[1] for b in cores.bands_for(sp))
    fr = cores.bands_for(sp)[-1][2]

    def bx(z0, z1, y0=None, dy=200.0):
        y0 = fr + 20.0 if y0 is None else y0
        return ([0.0, y0, z0], [SPEC['width'], y0 + dy, z1])
    # clear of the core top: fine
    good = [_c('Tile_Deck', aabb=bx(ct - 30.0, ct - 8.0))]
    good += [_c('Wall_A%d' % i, aabb=bx(0.0, ct - 40.0)) for i in range(9)]
    if gate_10(model(sp, [_a('BLD2_Probe_H', good)])):
        return False
    # a deck whose top face lands exactly on the core top: the defect
    bad = list(good) + [_c('Tile_Deck2', aabb=bx(ct - 8.0, ct))]
    if len(gate_10(model(sp, [_a('BLD2_Probe_H', bad)]))) != 1:
        return False
    # same height but wholly IN FRONT of the core: never touches it, must
    # pass. `dy` matters - the first version of this test made the box 200
    # deep starting at y 0, so it ran straight through the core front at 62
    # and was flagged correctly. The rule was right; the test was wrong.
    infront = list(good) + [_c('Glass_Vent',
                               aabb=bx(ct - 8.0, ct, y0=0.0, dy=40.0))]
    return not gate_10(model(sp, [_a('BLD2_Probe_H', infront)]))


# uu. Was justified as "sub-pixel at zoom", which was a feel rather than a
# derivation. Measured against the 0.4% table on 29 Aug so the number has a
# provenance: a feature must subtend ~0.4% of frame width to read, and at
# player zoom (900 uu distance, 463 uu frame width) that is 1.85 uu. This
# constant is 4.3x stricter than the threshold it was guessing at.
#
# KEEP IT STRICTER, DELIBERATELY. Relaxing to the principled 1.85 would let
# in patches nobody can resolve, and judging each face at only the framing it
# is "usually" seen from would forgive 52.5% of the catalogue's debt on the
# grounds that nobody looks closely - which is the argument the gate exists
# to refuse. HANDOFF requires Stage 2 work to read at BOTH block hero and
# player zoom, so the strictest framing governs and player zoom is it.
COPLANAR_MIN_OVERLAP = 8.0


def coplanar_pairs(cs, tol=COPLANAR_TOL, minov=COPLANAR_MIN_OVERLAP, cap=None):
    """Parts whose LIKE-FACING faces share a plane AND overlap behind it.

    LIKE-FACING is the whole discrimination, and getting it wrong makes the
    rule useless in one direction or the other:

      max vs max, or min vs min - two surfaces pointing the SAME way at the
      same depth. Nothing for the depth buffer to choose between them. This
      is the defect.

      max vs min - one part's top at another's bottom. That is a JOINT, how
      every stacked wall in the catalogue is built, and flagging it would
      condemn the entire library.

    The second discrimination is the overlap test on the other two axes. An
    elevation of wall panels all sharing a front plane is normal and correct
    - they sit side by side and do not overlap. Two parts that share a plane
    AND overlap behind it are fighting, and that also catches a band which
    was meant to PROJECT and was left flush: the reveal doctrine says a model
    reads as physical because light catches real edges, and a band at the
    same depth as the wall has no edge to catch.

    Sorted sweep with a break, not the O(n^2) pair loop: a building carries
    ~640 boxes and the gate runs over hundreds of models.
    """
    boxes = [(str(c.get('name', '?')), c['aabb']) for c in cs if c.get('aabb')]
    seen, out = set(), []
    for k in (0, 1, 2):
        o1, o2 = [a for a in (0, 1, 2) if a != k]
        for side in (0, 1):
            order = sorted(range(len(boxes)), key=lambda i: boxes[i][1][side][k])
            for ai in range(len(order)):
                na, ba = boxes[order[ai]]
                va = ba[side][k]
                for bi in range(ai + 1, len(order)):
                    nb, bb = boxes[order[bi]]
                    if bb[side][k] - va >= tol:
                        break               # sorted: nothing further is close
                    ov1 = (min(ba[1][o1], bb[1][o1])
                           - max(ba[0][o1], bb[0][o1]))
                    ov2 = (min(ba[1][o2], bb[1][o2])
                           - max(ba[0][o2], bb[0][o2]))
                    if ov1 < minov or ov2 < minov:
                        continue
                    key = (order[ai], order[bi])
                    if key in seen:
                        continue            # a coincident pair fights on all
                    seen.add(key)           # three axes; report it once
                    out.append((na, nb, 'xyz'[k]))
                    if cap and len(out) >= cap:
                        return out
    return out


# --- EXPOSURE: is the shared plane one the camera can ever see? -------------
#
# GATE-11 measured 32,060 coplanar pairs over the 548-model catalogue and I
# was about to go and fix them. Then the same question that has caught this
# project twice already: is the instrument measuring what its name says?
#
# It was not. coplanar_pairs asks whether two faces share a plane and overlap
# behind it. It does NOT ask whether that plane is ever PRESENTED to a camera.
# 28.1% of the debt was boxes sharing their UNDERSIDES on the board - a plinth,
# a column base and a column all correctly starting at z=0 - which is not a
# fight anyone can photograph, it is three parts standing on the same floor.
# Another 8.0% was planes with a third box built straight across them.
#
# So 36% of GATE-11's verdict was geometry, not defect. That matters twice
# over: it is a third of the work, and a rule that refuses correct models is
# the documented road to passing gates with --force.
#
# Direction-blindness again, one level up. The detail metric counted quantity
# and not direction; this counted coincidence and not visibility.

def _shared_plane(A, B, k, tol=COPLANAR_TOL):
    """The plane two like-facing boxes share on axis k, and which way it looks.

    Returns (value, outward) where outward is -1 if the shared faces are the
    boxes' MIN faces (they look toward -k) and +1 if they are the MAX faces.
    None when the boxes do not actually share a like-facing plane.
    """
    for side, outward in ((0, -1), (1, 1)):
        if abs(A[side][k] - B[side][k]) < tol:
            return A[side][k], outward
    return None


def _occluded(v, outward, k, A, B, boxes, skip, tol=COPLANAR_TOL):
    """Does a THIRD box sit against this plane on its outward side?

    Conservative on purpose: the occluder must cover the whole shared
    footprint in the other two axes and must reach the plane. Anything it
    cannot prove buried is reported as exposed, so the error runs toward
    MORE work rather than toward a gate that quietly forgives real faults.
    """
    lo = [max(A[0][i], B[0][i]) for i in range(3)]
    hi = [min(A[1][i], B[1][i]) for i in range(3)]
    for j, (_n, C) in enumerate(boxes):
        if j in skip:
            continue
        if outward < 0:
            if not (C[0][k] < v - tol and C[1][k] > v - tol):
                continue
        else:
            if not (C[1][k] > v + tol and C[0][k] < v + tol):
                continue
        if all(C[0][i] <= lo[i] + tol and C[1][i] >= hi[i] - tol
               for i in range(3) if i != k):
            return True
    return False


def visible_coplanar_pairs(cs, ground=None, cap=None, **kw):
    """coplanar_pairs, minus the planes nothing can ever look at.

    ground defaults to the lowest face in the set: the board the model stands
    on. The board is an opaque occluder that is not one of the building's own
    components, so it has to be supplied rather than discovered.
    """
    boxes = [(str(c.get('name', '?')), c['aabb']) for c in cs if c.get('aabb')]
    if not boxes:
        return []
    if ground is None:
        ground = min(b[1][0][2] for b in boxes)
    idx = {n: i for i, (n, _) in enumerate(boxes)}
    out = []
    for na, nb, ax in coplanar_pairs(cs, cap=None, **kw):
        A, B = boxes[idx[na]][1], boxes[idx[nb]][1]
        skip = {idx[na], idx[nb]}
        # EVERY shared plane, not just the reported one. coplanar_pairs
        # dedupes a pair to the first axis it finds it on, so a pair that
        # fights on two planes arrives labelled with one; judging only that
        # label would forgive a pair whose x faces are buried and whose y
        # faces are wide open, purely because of axis order. The pair
        # survives if ANY like-facing plane it shares is exposed.
        keep = False
        for k in (0, 1, 2):
            sp = _shared_plane(A, B, k)
            if sp is None:
                continue
            v, outward = sp
            if k == 2 and outward < 0 and abs(v - ground) < 1.0:
                continue                       # undersides, on the board
            if _occluded(v, outward, k, A, B, boxes, skip):
                continue
            keep = True
            break
        if keep:
            out.append((na, nb, ax))
            if cap and len(out) >= cap:
                break
    return out


# GATE-11 IS WRITTEN, SELF-TESTED, AND DELIBERATELY NOT YET ENFORCED.
#
# Measured over a 24-model sample of the catalogue on 2026-08-27: ZERO models
# carry no coplanar pairs, and the median model carries 84. Registering it in
# RULES today would refuse 100% of the library - and this file's own header
# says what happens next when a gate refuses everything correct: "that teaches
# people to pass the gate with --force, the failure mode that must never
# install itself." GATE-01 already did this once when donors became real.
#
# So it sits in PENDING: it runs its self-test with the rules, so it cannot
# rot, and it does not vote. It moves into RULES when the generator pass
# lands, and the move is one line.
PENDING = []


def pending(rid, statement, judges=None):
    def deco(fn):
        PENDING.append(dict(id=rid, statement=statement, check=fn,
                            judges=judges))
        return fn
    return deco


@pending('GATE-11', 'no two parts share a face plane while overlapping behind it',
         judges=ALL_ARCHES)
def gate_11(m):
    """The class rule GATE-10 is one member of.

    GATE-10 knows about ONE plane - the core top - because that is the one
    that was found by chasing jagged white patches across every roof in the
    catalogue for a long time, as a lighting fault, which it never was. Cold
    read #1 found the rest of the class from the other side: a stranger
    looking closely said rendering artifacts and clipping gave it away.

    Keeping both is deliberate. GATE-10 names the specific plane and explains
    the specific cause, which is what makes a verdict actionable; this one
    catches the members nobody has met yet.
    """
    # VISIBLE pairs, not all pairs. 36% of the raw count is boxes sharing
    # undersides on the board or planes with a third box built across them -
    # coincidence the camera never sees. See visible_coplanar_pairs.
    hits = visible_coplanar_pairs(building_comps(m), cap=40)
    if not hits:
        return []
    shown = ', '.join('%s/%s(%s)' % h for h in hits[:3])
    return [(m['spec'].get('name', '?'),
             '%d coplanar overlapping pair(s)%s: %s'
             % (len(hits), '+' if len(hits) >= 40 else '', shown))]


@selftest('GATE-11/visible')
def _t11v():
    """The exposure filter, against answers worked out by hand.

    Written because the filter is the thing that decides how much of the
    catalogue is actually broken, and an instrument that has not been checked
    against a known answer is not a measurement. Each fixture below has one
    obvious right answer that does not depend on the implementation.
    """
    def bx(x0, x1, y0, y1, z0, z1):
        return ([x0, y0, z0], [x1, y1, z1])
    C = lambda n, b: _c(n, aabb=b)

    # 1. THREE PARTS STANDING ON THE BOARD. A plinth, a column base and a
    #    column, all correctly starting at z=0, all overlapping in plan.
    #    Raw: undersides coincide, three pairs. Visible: none - it is a floor.
    stack = [C('Wall_Plinth',  bx(0.0, 300.0, 0.0, 300.0, 0.0,  30.0)),
             C('Wall_ColBase', bx(40.0, 260.0, 40.0, 260.0, 0.0, 80.0)),
             C('Wall_Col',     bx(60.0, 240.0, 60.0, 240.0, 0.0, 600.0))]
    if len(coplanar_pairs(stack)) != 3:
        return False
    if visible_coplanar_pairs(stack):
        return False

    # 2. THE SAME STACK LIFTED OFF THE BOARD. Identical geometry, ground now
    #    below it, so those undersides ARE presented and must all come back.
    lift = [C(n, ([a[0][0], a[0][1], a[0][2] + 500.0],
                  [a[1][0], a[1][1], a[1][2] + 500.0]))
            for n, a in ((c['name'], c['aabb']) for c in stack)]
    if len(visible_coplanar_pairs(lift, ground=0.0)) != 3:
        return False

    # 3. A PLANE WITH A THIRD BOX BUILT ACROSS IT. Two boxes share their max-y
    #    face; a facing panel covers that whole face. Nothing to see.
    #    Written wrong the first time: the two boxes also shared their x
    #    faces, so the pair was reported on x and the y panel was irrelevant.
    #    These share exactly ONE plane - the max-y face - and nothing else.
    hidden = [C('Wall_A', bx(0.0, 200.0, 0.0, 100.0, 0.0, 300.0)),
              C('Wall_B', bx(20.0, 180.0, 40.0, 100.0, 50.0, 250.0)),
              C('Wall_Face', bx(-10.0, 210.0, 100.0, 140.0, -10.0, 310.0))]
    if not coplanar_pairs(hidden):
        return False
    if any(set(h[:2]) == {'Wall_A', 'Wall_B'}
           for h in visible_coplanar_pairs(hidden)):
        return False

    # 4. THE SAME PAIR WITH THE PANEL PULLED CLEAR. Now it is a real fight.
    shown = hidden[:2] + [C('Wall_Face', bx(-10.0, 210.0, 200.0, 240.0,
                                            -10.0, 310.0))]
    if not coplanar_pairs(hidden):
        return False
    if not any(set(h[:2]) == {'Wall_A', 'Wall_B'}
               for h in visible_coplanar_pairs(shown)):
        return False

    # 5. THE FILTER MUST NEVER INVENT. Visible is a subset of raw, always.
    for fx in (stack, lift, hidden, shown):
        raw = {tuple(sorted(h[:2])) for h in coplanar_pairs(fx)}
        vis = {tuple(sorted(h[:2])) for h in visible_coplanar_pairs(fx)}
        if not vis <= raw:
            return False
    return True


@selftest('GATE-11')
def _t11():
    def bx(x0, x1, y0, y1, z0, z1):
        return ([x0, y0, z0], [x1, y1, z1])
    # side by side on one front plane: the normal elevation, must pass
    ok = [_c('Wall_%d' % i, aabb=bx(i*100.0, i*100.0 + 90.0, 0.0, 300.0,
                                    0.0, 260.0)) for i in range(6)]
    if gate_11(model(SPEC, [_a('BLD2_Probe_H', ok)])):
        return False
    # stacked: A's top IS B's bottom. A joint, not a fight, must pass
    joint = [_c('Wall_L', aabb=bx(0.0, 200.0, 0.0, 300.0, 0.0, 260.0)),
             _c('Wall_U', aabb=bx(0.0, 200.0, 0.0, 300.0, 260.0, 520.0))]
    if gate_11(model(SPEC, [_a('BLD2_Probe_H', joint)])):
        return False
    # two tops at the same z, overlapping in plan: the defect
    fight = [_c('Deck_A', aabb=bx(0.0, 200.0, 0.0, 300.0, 0.0, 260.0)),
             _c('Deck_B', aabb=bx(100.0, 300.0, 0.0, 300.0, 40.0, 260.0))]
    if len(gate_11(model(SPEC, [_a('BLD2_Probe_H', fight)]))) != 1:
        return False
    # a band left FLUSH with the wall it was meant to project from
    flush = [_c('Wall_A', aabb=bx(0.0, 400.0, 0.0, 300.0, 0.0, 600.0)),
             _c('Band_B', aabb=bx(0.0, 400.0, 0.0, 300.0, 200.0, 260.0))]
    if len(gate_11(model(SPEC, [_a('BLD2_Probe_H', flush)]))) != 1:
        return False
    # ...and the same band PROJECTING, which is the fix, must pass.
    # It has to stand proud on the faces it actually EXPOSES, not just the
    # front: the first version of this fixture pushed the band 12 uu forward
    # in y but left it exactly as wide as its wall, so both END faces still
    # sat at x=0 and x=400 over a shared y/z patch and fought there. The rule
    # was right and the fixture was wrong - the same way round as GATE-10's.
    # ...and shallow, for the same reason at the back: a band is a strip on
    # the front, not a block running the wall's full depth.
    proud = [_c('Wall_A', aabb=bx(0.0, 400.0, 0.0, 300.0, 0.0, 600.0)),
             _c('Band_B', aabb=bx(-6.0, 406.0, -12.0, 20.0, 200.0, 260.0))]
    if gate_11(model(SPEC, [_a('BLD2_Probe_H', proud)])):
        return False
    # a sliver overlap is sub-pixel even at zoom: not worth a refusal
    sliver = [_c('Deck_A', aabb=bx(0.0, 200.0, 0.0, 300.0, 0.0, 260.0)),
              _c('Deck_B', aabb=bx(197.0, 400.0, 0.0, 300.0, 40.0, 260.0))]
    return not gate_11(model(SPEC, [_a('BLD2_Probe_H', sliver)]))


def judge(m, arch=None):
    """(findings, skips) for one model under one archetype. No self-tests -
    run() adds those.

    For 'street' - which is every spec that carries no `archetype` key, the
    entire existing catalogue - this loop reduces EXACTLY to the
    pre-archetype gate loop: every rule runs, no skips, no overrides, and
    archetypes.py's ARCH-STREET-IDENTICAL selftest proves the findings are
    byte-identical against planted defects.

    An unknown archetype raises UnknownArchetype - fail closed, never
    default to street. An exempted rule contributes an explicit SKIPPED
    entry, never silence. An override rebinds this module's constant for
    one rule call via archetypes.patched, so the rule bodies stay untouched.
    """
    if arch is None:
        arch = archetypes.of_spec(m['spec'])
    else:
        archetypes.get(arch)            # spelled but unknown: raise here too
    findings, skips = [], []
    for r in RULES:
        ok, why = archetypes.applies(arch, r)
        if not ok:
            skips.append((r['id'],
                          'SKIPPED for archetype %s: %s' % (arch, why)))
            continue
        ov = archetypes.overrides_for(arch, r['id'])
        with archetypes.patched(sys.modules[__name__], ov):
            for subj, detail in r['check'](m):
                findings.append((r['id'], subj, detail))
    return findings, skips


def run(m, verbose=True):
    """Returns (ok, findings, facts). Self-tests run FIRST, as in the suite:
    if a rule cannot prove it sees its own defect, the gate reports nothing.
    The archetype machinery is held to the same bar: its selftests (unknown
    names raise, skips are visible, street stays byte-identical) run with
    the rules', and the gate reports nothing if any fail."""
    broken = [r['id'] for r in RULES + PENDING
              if not SELFTESTS.get(r['id'], lambda: False)()]
    # HELPERS GET TESTED TOO. A selftest whose id is not a rule id was, until
    # 29 Aug, registered and never called - GATE-11/visible sat there passing
    # by never running. Anything in SELFTESTS that no rule claims runs here,
    # so a test cannot be silently orphaned by the name it was given.
    claimed = {r['id'] for r in RULES + PENDING}
    broken += [rid for rid in sorted(SELFTESTS)
               if rid not in claimed and not SELFTESTS[rid]()]
    if not archetypes.selftest():
        broken.append('ARCHETYPES')
    if broken:
        print('GATE SELF-TEST FAILED: %s - reporting nothing' % broken)
        return False, [('selftest', ','.join(broken))], {}
    if verbose:
        _helpers = len([r for r in SELFTESTS
                        if r not in {x['id'] for x in RULES + PENDING}])
        print('  gate self-tests: %d/%d rules see their own defect'
              ' (%d pending, not voting) + %d helper test(s)'
              % (len(RULES) + len(PENDING), len(RULES) + len(PENDING),
                 len(PENDING), _helpers))
    findings, skips = judge(m)
    if verbose:
        for rid, line in skips:
            print('  %s %s' % (rid, line))
    s = span(m)
    facts = dict(parts=len(building_comps(m)),
                 parts_total=len(comps(m)),
                 materials=len({x for c in building_comps(m)
                                for x in (c.get('mats') or []) if x}),
                 elevation_m2=round(elevation_m2(m['spec']), 1),
                 density=round(len(building_comps(m))
                               / max(elevation_m2(m['spec']), 1e-6), 3),
                 span_x=round(s[0], 1) if s else None,
                 span_y=round(s[1], 1) if s else None,
                 rules=len(RULES),
                 # which definition of good judged this model, and which
                 # rules stood aside - in the FACTS so the stamp carries
                 # them: a skip that is not in the verdict is a check that
                 # silently stopped having an opinion. Empty/'street' for
                 # every spec without an archetype key.
                 archetype=archetypes.of_spec(m['spec']),
                 skipped=['%s %s' % (rid, line) for rid, line in skips])
    return (not findings), findings, facts


if __name__ == '__main__':
    ok, f, facts = run(_clean())
    print('clean model passes:', ok, facts)
