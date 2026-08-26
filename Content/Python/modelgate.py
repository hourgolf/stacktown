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
"""
import labels
from qc import DETAIL_MIN, MAT_MIN, AUTO_NAME, DEFAULT_MATS

RULES = []
SELFTESTS = {}


def rule(rid, statement):
    def deco(fn):
        RULES.append(dict(id=rid, statement=statement, check=fn))
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


def span(m):
    """XY extent of the model, from component AABBs. None if unmeasurable."""
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
    return (hi[0]-lo[0], hi[1]-lo[1]) if seen else None


# =========================== the rules ======================================
@rule('GATE-01', 'every component carries a role from labels.ROLES')
def gate_01(m):
    return [(c['name'], 'no role prefix') for c in role_comps(m)
            if not labels.role(c['name'])]


@rule('GATE-02', 'no component sits on a default or missing material')
def gate_02(m):
    out = []
    for c in comps(m):
        mats = c.get('mats') or []
        if not mats:
            out.append((c['name'], 'no material slots'))
        elif any(x is None or x in DEFAULT_MATS for x in mats):
            out.append((c['name'], 'default material: %s' % (mats,)))
    return out


@rule('GATE-03', 'the model carries at least %.2f parts per m2 of elevation'
                 % DETAIL_MIN)
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


@rule('GATE-04', 'the model uses at least %d distinct materials' % MAT_MIN)
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


@rule('GATE-05', 'the model fits its parcel: width strict, %.0f uu front '
                 'oversail allowed' % OVERSAIL)
def gate_05(m):
    sp = m['spec']
    s = span(m)
    if not s:
        return [(sp.get('name', '?'), 'no measurable bounds')]
    out = []
    # parcel_width, not width: the CORE is built narrower than its parcel so
    # the flank slabs can stand proud and still land on the parcel line. The
    # gate must judge against the land the model claims, not the core.
    pw = sp.get('parcel_width') or sp.get('width')
    if pw and s[0] > pw*1.02:
        out.append((sp.get('name', '?'),
                    'width %.0f exceeds the %.0f parcel it is baked for'
                    % (s[0], pw)))
    d = sp.get('parcel_depth') or sp.get('depth', 0.0)
    if d and s[1] > d + OVERSAIL:
        out.append((sp.get('name', '?'),
                    'depth %.0f exceeds %.0f + %.0f oversail'
                    % (s[1], d, OVERSAIL)))
    return out


@rule('GATE-06', 'no component was auto-renamed by a name collision')
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
    """A model that every rule must pass."""
    area = elevation_m2(SPEC)
    n = n if n is not None else int(area*DETAIL_MIN) + 20
    box = ([0.0, 0.0, 0.0], [SPEC['width'], SPEC['depth'], 400.0])
    return model(SPEC, [_a('BLD2_Probe_H',
                           [_c('Wall_P%d' % i, aabb=box if aabb else None)
                            for i in range(n)])])


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
    # depth: a cornice oversailing the pavement is allowed...
    m = _clean()
    orn = ([0.0, -OVERSAIL + 20.0, 0.0], [SPEC['width'], SPEC['depth'], 400.0])
    m['actors'][0]['comps'].append(_c('Band_Cornice', aabb=orn))
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


@rule('GATE-07', 'at least %.0f%% of the model sits behind its own front third'
                 % (REAR_MIN*100))
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
                 % REAR_PARTS)
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


def run(m, verbose=True):
    """Returns (ok, findings, facts). Self-tests run FIRST, as in the suite:
    if a rule cannot prove it sees its own defect, the gate reports nothing."""
    broken = [r['id'] for r in RULES
              if not SELFTESTS.get(r['id'], lambda: False)()]
    if broken:
        print('GATE SELF-TEST FAILED: %s - reporting nothing' % broken)
        return False, [('selftest', ','.join(broken))], {}
    if verbose:
        print('  gate self-tests: %d/%d rules see their own defect'
              % (len(RULES), len(RULES)))
    findings = []
    for r in RULES:
        for subj, detail in r['check'](m):
            findings.append((r['id'], subj, detail))
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
                 rules=len(RULES))
    return (not findings), findings, facts


if __name__ == '__main__':
    ok, f, facts = run(_clean())
    print('clean model passes:', ok, facts)
