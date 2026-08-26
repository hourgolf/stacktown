"""Whole-level invariants, each with a known-answer self-test.

WHY THIS EXISTS. `AGENTS.md` says "Never turn the owner into the regression
suite." It was being violated every session: pedestrians, translucent vehicles,
cars laid out at random, lamps through cars, the sand-pit plaza, tree scale -
every one of them found by the owner's eye, none by a check.

TWO RULES ABOUT THE RULES, both bought with real failures:

1. EVERY INVARIANT SCANS THE WHOLE LEVEL. `check_block.py` records in its own
   header that it printed "PASS (0 failures)" through the entire construction of
   blocks B and C while only ever looking at block A. No check here takes a
   "which block" argument, ever.

2. EVERY INVARIANT PROVES IT CAN SEE ITS OWN DEFECT. Each carries a self-test
   that builds a SYNTHETIC level containing one clean case and one defective
   case, and asserts the rule finds exactly the defective one. The self-tests
   run FIRST; if any fails the suite reports nothing else, because a suite that
   cannot detect a planted defect has no standing to call the level clean.
   `check_clear.py` reported "0 intersections" while searching for actors that
   do not exist. That is the failure this is aimed at.

Thresholds are drawn from measured distributions, not invented - see
`Docs/INVARIANTS.md` for the numbers each one came from.
"""
import re
import _path
import labels
import citygeom as G
import snapshot

POLE_HALF      = 20.0     # a lamp column footprint; its arm reaches over the road
KERB_TOLERANCE = 200.0    # a street tree may overhang the kerb this far
PRACTICAL_MAX_PITCH = 60.0
# UE names an unnamed component 'StaticMeshComponent_0' as well as
# 'StaticMesh12'; the first pattern only caught the second, and a stray
# probe actor slipped past it and was found by MAT-01 instead.
from qc import AUTO_NAME  # noqa: F401  - one definition, in qc.py

RULES = []


def rule(rid, statement):
    def deco(fn):
        RULES.append(dict(id=rid, statement=statement, check=fn, selftest=None))
        return fn
    return deco


def selftest(rid):
    def deco(fn):
        for r in RULES:
            if r['id'] == rid:
                r['selftest'] = fn
                return fn
        raise KeyError(rid)
    return deco


# --- synthetic level construction, for the self-tests only ------------------
def _c(name, mesh=None, rect=None, z=(0.0, 100.0), mats=()):
    box = None
    if rect:
        box = ([rect[0], rect[1], z[0]], [rect[2], rect[3], z[1]])
    return dict(name=name, mesh=mesh, aabb=box, mats=list(mats))


def _a(label, cls='StaticMeshActor', loc=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), comps=()):
    return dict(label=label, family=labels.family(label), cls=cls,
                loc=loc, rot=rot, comps=list(comps))


def _snap(*actors):
    return dict(actors=list(actors), unread_material_slots=0, seconds=0.0)


def _one(got, needle):
    """The rule found exactly one violation, and it is the planted one."""
    return len(got) == 1 and needle in got[0][0]


# =========================== NAME =========================================
@rule('NAME-01', 'every actor label family appears in labels.REGISTRY')
def name_01(snap):
    bad = {}
    for a in snap['actors']:
        if a['family'] not in labels.REGISTRY:
            bad.setdefault(a['family'] or '<none>', []).append(a['label'])
    return [(f, '%d actors, e.g. %s' % (len(v), v[0])) for f, v in sorted(bad.items())]


@selftest('NAME-01')
def _t_name_01():
    s = _snap(_a('BLD2_Narrow_GF'), _a('XYZ_invented_prefix'))
    return _one(name_01(s), 'XYZ')


@rule('NAME-02', 'no component was auto-renamed to StaticMesh<N> by a name collision')
def name_02(snap):
    # Only on MULTI-PART actors. A StaticMeshActor's single mesh component is
    # called StaticMeshComponent0 by the engine and always has been - that is a
    # default name, not a collision. Widening the pattern without this caught
    # every AV_ tile in the level.
    return [(a['label'], c['name']) for a in snap['actors'] if len(a['comps']) > 1
            for c in a['comps'] if AUTO_NAME.match(c['name'] or '')]


@selftest('NAME-02')
def _t_name_02():
    multi = _a('ELEV_Mid_E', comps=[_c('Wall_Pier0'), _c('StaticMesh12')])
    single = _a('AV_shop0', comps=[_c('StaticMeshComponent0')])
    got = name_02(_snap(multi, single))
    return len(got) == 1 and got[0][1] == 'StaticMesh12'


@rule('NAME-03', 'no two actors share a label')
def name_03(snap):
    """A sweep that does not wipe before it builds doubles its own output, and
    the level looks fine because the copies sit exactly on top of each other.
    Four times now: lamps twice, zones once, elevations and practicals once.
    DRESS-06 only watches the dressing families; this watches everything."""
    seen, out = {}, []
    for a in snap['actors']:
        if a['label'] in seen:
            seen[a['label']] += 1
        else:
            seen[a['label']] = 1
    for lbl, n in sorted(seen.items()):
        if n > 1:
            out.append((lbl, '%d actors share this label' % n))
    return out


@selftest('NAME-03')
def _t_name_03():
    s = _snap(_a('ELEV_Mid_E'), _a('ELEV_Mid_E'), _a('ELEV_Mid_W'))
    return _one(name_03(s), 'ELEV_Mid_E')


# =========================== MAT ==========================================
@rule('MAT-01', 'zero unassigned or engine-default material slots  [gate B1]')
def mat_01(snap):
    out = []
    for a in snap['actors']:
        for c in a['comps']:
            for i, m in enumerate(c['mats']):
                if m is None or m in snapshot.DEFAULT_MATS:
                    out.append((a['label'], '%s slot %d = %s' % (c['name'], i, m)))
    return out


@selftest('MAT-01')
def _t_mat_01():
    s = _snap(_a('BLD2_X', comps=[_c('Wall_A', mats=['MI_wood']),
                                  _c('Wall_B', mats=['WorldGridMaterial'])]))
    return _one(mat_01(s), 'BLD2_X') and 'Wall_B' in mat_01(s)[0][1]


# =========================== DRESS ========================================
def _poles(snap):
    for a in snap['actors']:
        if labels.is_lamp(a['label'], None):
            x, y, _ = a['loc']
            yield a, (x - POLE_HALF, y - POLE_HALF, x + POLE_HALF, y + POLE_HALF)


def _vehicles(snap):
    for a, c in snapshot.mesh_actors(snap, labels.is_vehicle):
        r = snapshot.rect_of(c)
        if r:
            yield a, r


@rule('DRESS-01', 'no lamp column stands inside a parked vehicle')
def dress_01(snap):
    veh = list(_vehicles(snap))
    return [(a['label'], 'through %s' % va['label'])
            for a, pole in _poles(snap) for va, vr in veh if G.intersect(pole, vr)]


@selftest('DRESS-01')
def _t_dress_01():
    s = _snap(_a('LAMP_s1F_9', cls='Actor', loc=(1000.0, 0.0, 0.0)),
              _a('BAKED_veh1', comps=[_c('m', 'SM_Baked_Sedan', (900, -130, 1440, 130))]),
              _a('BAKED_veh2', comps=[_c('m', 'SM_Baked_Sedan', (5000, -130, 5540, 130))]))
    return _one(dress_01(s), 'LAMP_s1F_9')


@rule('DRESS-02', 'nothing is parked inside a junction keep-clear')
def dress_02(snap):
    jn = G.junction_rects()
    return [(a['label'], 'in junction %s' % (tuple(int(v) for v in j),))
            for a, r in _vehicles(snap) for j in jn if G.intersect(j, r)]


@selftest('DRESS-02')
def _t_dress_02():
    j = G.junction_rects()[0]
    cx, cy = (j[0] + j[2])/2.0, (j[1] + j[3])/2.0
    b = G.board_rect()
    s = _snap(
        _a('BAKED_veh7', comps=[_c('m', 'SM_Baked_Sedan',
                                   (cx-270, cy-126, cx+270, cy+126))]),
        _a('BAKED_veh8', comps=[_c('m', 'SM_Baked_Sedan',
                                   (b[0]+40, b[1]+40, b[0]+580, b[1]+292))]))
    return _one(dress_02(s), 'BAKED_veh7')


@rule('DRESS-03', 'no lamp column stands inside a carriageway')
def dress_03(snap):
    roads = G.road_rects()
    return [(a['label'], 'in carriageway')
            for a, pole in _poles(snap) if any(G.intersect(rd, pole) for rd in roads)]


@selftest('DRESS-03')
def _t_dress_03():
    rd = G.road_rects()[0]
    cx, cy = (rd[0] + rd[2])/2.0, (rd[1] + rd[3])/2.0
    # the clean lamp must be clear of EVERY carriageway, not just this one -
    # the first version of this test put it at the same X, which is inside the
    # avenue, so the rule correctly found two and the self-test correctly
    # refused to pass. Keep it well west of the avenue.
    clean_x = (G.board_rect()[0] + G.avenue_road_rects()[0][0]) / 2.0
    s = _snap(_a('LAMP_s1F_1', cls='Actor', loc=(cx, cy, 0.0)),
              _a('LAMP_s1F_2', cls='Actor', loc=(clean_x, rd[1] - 300.0, 0.0)))
    return _one(dress_03(s), 'LAMP_s1F_1')


@rule('DRESS-04', 'every dressing actor stands on the board')
def dress_04(snap):
    b = G.board_rect()
    out = []
    for a in snap['actors']:
        if a['family'] not in labels.DRESSING:
            continue
        for c in a['comps']:
            r = snapshot.rect_of(c)
            if r and G.overhang(b, r) > 0.0:
                out.append((a['label'], 'off board by %.0f uu' % G.overhang(b, r)))
                break
    return out


@selftest('DRESS-04')
def _t_dress_04():
    b = G.board_rect()
    s = _snap(_a('SUR_tree_s1F_1', comps=[_c('m', 'SM_tree_03',
                    (b[0]+100, b[1]+100, b[0]+500, b[1]+500))]),
              _a('SUR_tree_s1F_2', comps=[_c('m', 'SM_tree_03',
                    (b[2]+900, b[3]+900, b[2]+1300, b[3]+1300))]))
    return _one(dress_04(s), 'SUR_tree_s1F_2')


# =========================== SCALE ========================================
@rule('SCALE-01', 'a street tree overhangs the kerb by no more than %.0f uu' % KERB_TOLERANCE)
def scale_01(snap):
    out = []
    for a, c in snapshot.mesh_actors(snap, labels.is_planting):
        if not a['label'].startswith('SUR_tree_'):
            continue
        r = snapshot.rect_of(c)
        if not r:
            continue
        # Measure penetration PERPENDICULAR to the road's own axis. The first
        # version took min(width, height) of the overlap, which reports the
        # whole crown for a tree standing inside the avenue - the avenue rect
        # spans the full board depth, so the overlap is the tree itself. That
        # read 523 uu of "kerb overhang" for a tree whose canopy is 237 uu.
        worst = 0.0
        for rd in G.street_road_rects():          # streets run in X: kerbs are Y
            i = G.intersect(rd, r)
            if i:
                worst = max(worst, i[3] - i[1])
        for rd in G.avenue_road_rects():          # avenues run in Y: kerbs are X
            i = G.intersect(rd, r)
            if i:
                worst = max(worst, i[2] - i[0])
        if worst > KERB_TOLERANCE:
            out.append((a['label'], '%s overhangs carriageway %.0f uu' % (c['mesh'], worst)))
    return out


@selftest('SCALE-01')
def _t_scale_01():
    rd = G.road_rects()[0]
    cx = (rd[0] + rd[2])/2.0
    deep = _a('SUR_tree_s1N_9',  comps=[_c('m', 'SM_tree_02',
                (cx, rd[1] - 100, cx + 700, rd[1] + 500))])   # 500 uu into the road
    shy  = _a('SUR_tree_s1N_8',  comps=[_c('m', 'SM_tree_03',
                (cx + 2000, rd[1] - 600, cx + 2700, rd[1] + 50))])  # 50 uu in
    return _one(scale_01(_snap(deep, shy)), 'SUR_tree_s1N_9')


@rule('SCALE-02', 'zone planting is smaller than the narrow dimension of its own lot')
def scale_02(snap):
    zones = {sp['name']: r for _n, sp, r in G.lots(('plaza', 'green', 'park', 'vacant'))}
    out = []
    for a, c in snapshot.mesh_actors(snap, labels.is_planting):
        parts = a['label'].split('_')
        if len(parts) < 3 or parts[1] != 'zone':
            continue
        z = zones.get(parts[2])
        r = snapshot.rect_of(c)
        if not z or not r:
            continue
        crown = max(r[2]-r[0], r[3]-r[1])
        room = min(z[2]-z[0], z[3]-z[1])
        if crown > room:
            out.append((a['label'], '%s crown %.0f uu in a %.0f uu lot (%s)'
                        % (c['mesh'], crown, room, parts[2])))
    return out


@selftest('SCALE-02')
def _t_scale_02():
    z = {sp['name']: r for _n, sp, r in G.lots(('plaza', 'green'))}
    r = list(z.values())[0]
    cx, cy = (r[0]+r[2])/2.0, (r[1]+r[3])/2.0
    name = list(z.keys())[0]
    big = _a('SUR_zone_%s_t90' % name, comps=[_c('m', 'SM_tree_02',
                (cx-800, cy-800, cx+800, cy+800))])
    ok  = _a('SUR_zone_%s_t91' % name, comps=[_c('m', 'SM_tree_04',
                (cx-150, cy-150, cx+150, cy+150))])
    return _one(scale_02(_snap(big, ok)), 't90')


@rule('DRESS-05', 'every lamp has exactly one light, and every light a lamp')
def dress_05(snap):
    fam = {}
    for a in snap['actors']:
        f = labels.family(a['label'])
        if f in ('LAMP', 'LAMPLIGHT'):
            fam.setdefault(f, set()).add(a['label'].split('_', 1)[1])
    lamps = fam.get('LAMP', set())
    lights = fam.get('LAMPLIGHT', set())
    out = [(l, 'lamp with no light') for l in sorted(lamps - lights)]
    out += [(l, 'light with no lamp') for l in sorted(lights - lamps)]
    return out


@selftest('DRESS-05')
def _t_dress_05():
    s = _snap(_a('LAMP_s1F_0', cls='Actor'), _a('LAMPLIGHT_s1F_0', cls='RectLight'),
              _a('LAMP_s1F_1', cls='Actor'))
    return _one(dress_05(s), 's1F_1')


@rule('DRESS-06', 'no two dressing actors of a family stand in the same spot')
def dress_06(snap):
    """Catches a wipe that silently did nothing and left the old set under the
    new one - which has now happened three times, with lamps twice and zones
    once, each time discovered by eye or by a count that looked odd."""
    seen, out = {}, []
    for a in snap['actors']:
        f = labels.family(a['label'])
        if f not in labels.DRESSING:
            continue
        key = (f, round(a['loc'][0]/20.0), round(a['loc'][1]/20.0),
               round(a['loc'][2]/20.0))
        if key in seen:
            out.append((a['label'], 'same spot as %s' % seen[key]))
        else:
            seen[key] = a['label']
    return out


@selftest('DRESS-06')
def _t_dress_06():
    s = _snap(_a('LAMP_s1F_0', cls='Actor', loc=(100.0, 200.0, 0.0)),
              _a('LAMP_s1F_9', cls='Actor', loc=(100.0, 200.0, 0.0)),
              _a('LAMP_s1F_1', cls='Actor', loc=(900.0, 200.0, 0.0)))
    return _one(dress_06(s), 'LAMP_s1F_9')


@rule('DRESS-07', 'commercial roof kit does not stand on a home')
def dress_07(snap):
    """A water tank on a cottage and a comms mast on a walk-up. The roof kit
    was gated on kind, which says whether a lot is built on; style says what
    was built."""
    homes = []
    for _n, sp, r in G.lots(('gen',)):
        if sp.get('style') in ('house', 'walkup'):
            homes.append((sp['name'], r))
    out = []
    for a in snap['actors']:
        if not a['label'].startswith('SUR_roof_'):
            continue
        x, y, _z = a['loc']
        for nm, r in homes:
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                out.append((a['label'], 'on %s, which is a %s'
                            % (nm, 'home')))
    return out


@selftest('DRESS-07')
def _t_dress_07():
    homes = [(sp['name'], r) for _n, sp, r in G.lots(('gen',))
             if sp.get('style') in ('house', 'walkup')]
    assert homes, 'no residential lots in the table - the rule cannot be tested'
    nm, r = homes[0]
    cx, cy = (r[0] + r[2])/2.0, (r[1] + r[3])/2.0
    bad = _a('SUR_roof_%s' % nm, loc=(cx, cy, 400.0))
    # clear of EVERY home, not merely of this one: the first version offset in
    # X by 6000 and landed on a different house down the same lane
    ok = _a('SUR_roof_Narrow', loc=(cx, r[1] - 3000.0, 400.0))
    return _one(dress_07(_snap(bad, ok)), nm)


@rule('CAM-01', 'no saved camera stands inside a building')
def cam_01(snap):
    """Eight blocks have been built since most of the cameras were placed. One
    of them ended up inside block B's Hall - a saved view is a remembered
    number and the city moved underneath it."""
    lots = []
    for _n, sp, r in G.lots(('gen', 'av')):
        h = (sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0)
             + sp.get('parapet', 0.0))
        lots.append((sp['name'], r, h))
    out = []
    for a in snap['actors']:
        if labels.family(a['label']) != 'CAM':
            continue
        x, y, z = a['loc']
        for nm, r, h in lots:
            if r[0] <= x <= r[2] and r[1] <= y <= r[3] and z < h:
                out.append((a['label'], 'inside %s' % nm))
                break
    return out


@selftest('CAM-01')
def _t_cam_01():
    nm, r, h = next(((sp['name'], rr,
                      sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0))
                     for _n, sp, rr in G.lots(('gen',))))
    cx, cy = (r[0] + r[2])/2.0, (r[1] + r[3])/2.0
    bad = _a('CAM_Bad', cls='CineCameraActor', loc=(cx, cy, 100.0))
    ok = _a('CAM_Good', cls='CineCameraActor', loc=(cx, cy, h + 4000.0))
    return _one(cam_01(_snap(bad, ok)), 'CAM_Bad')


@rule('BAKE-01', 'every placed catalogue building is one mesh with its roles intact')
def bake_01(snap):
    """The whole point of the bake is that a 200-box recipe becomes ONE mesh
    that still carries a slot per role. A merge that compacts the materials
    gives one slot and silently loses the role system - which is exactly what
    the first bake did."""
    out = []
    for a in snap['actors']:
        if labels.family(a['label']) != 'CAT' or a['label'] == 'CAT_Pad':
            continue
        if len(a['comps']) != 1:
            out.append((a['label'], '%d components, expected 1' % len(a['comps'])))
            continue
        mats = a['comps'][0]['mats']
        if len(mats) < 2:
            out.append((a['label'], 'only %d material slot(s) - roles were '
                                    'compacted away' % len(mats)))
        elif any(m is None or m in snapshot.DEFAULT_MATS for m in mats):
            out.append((a['label'], 'a slot is unassigned or default'))
    return out


@selftest('BAKE-01')
def _t_bake_01():
    ok = _a('CAT_cottage_t0', comps=[_c('m', 'SM_Bld', mats=['MI_a', 'MI_b'])])
    flat = _a('CAT_cottage_t9', comps=[_c('m', 'SM_Bld', mats=['MI_a'])])
    return _one(bake_01(_snap(ok, flat)), 't9')


# --- detail density ---------------------------------------------------------
# The F1 reader passed the city on the miniature look and said, unprompted,
# that later blocks were losing architectural detail and material richness.
# Measured with richness.py, and the denominator matters: parts per METRE is
# unfair to a low building, because a two-storey block over 13 m has half the
# elevation of a four-storey one and cannot carry the same count. Parts per
# SQUARE METRE of street elevation is the honest measure.
#
# Deduped and area-normalised, per m2:
#     house 4.26-4.91   walkup 2.66-4.08   deco 1.06-1.41
#     vernacular 0.65-1.71   modern 0.52-1.04
#
# 0.70 is set ABOVE four buildings that are genuinely thin, not below them.
# Tuning it down to green would be the failure the gate warns about in as many
# words - criteria bending to fit what got built.
from qc import DETAIL_MIN, MAT_MIN   # one definition, in qc.py - modelgate
# reads the same two numbers, and a gate that passed a model the suite would
# fail is worse than no gate


@rule('DETAIL-01', 'a building carries at least %.2f parts per m2 of elevation'
                   % DETAIL_MIN)
def detail_01(snap):
    area, parts, mats = {}, {}, {}
    for _n, sp, _r in G.lots(('gen',)):
        h = (sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0)
             + sp.get('parapet', 0.0))
        area[sp['name']] = (sp['width']/100.0) * (h/100.0)
    for a in snap['actors']:
        p = a['label'].split('_')
        if p[0] not in ('BLD2', 'ELEV') or len(p) < 2 or p[1] not in area:
            continue
        parts[p[1]] = parts.get(p[1], 0) + len(a['comps'])
        for c in a['comps']:
            for m in c['mats']:
                if m:
                    mats.setdefault(p[1], set()).add(m)
    out = []
    for nm, ar in sorted(area.items()):
        got = parts.get(nm, 0)
        if not got:
            continue
        if got/ar < DETAIL_MIN:
            out.append((nm, '%d parts over %.0f m2 = %.2f/m2, under %.2f'
                        % (got, ar, got/ar, DETAIL_MIN)))
        if len(mats.get(nm, ())) < MAT_MIN:
            out.append((nm, 'only %d distinct materials' % len(mats.get(nm, ()))))
    return out


# An open lot carries a lot less per square metre than a facade does, because
# it is ground rather than elevation - so DETAIL-01's threshold is meaningless
# here and this needs its own. The number is MEASURED from the lots that were
# built, reviewed and kept, not chosen:
#
#     Square (plaza)  0.162 parts/m2      reworked after the "sand pit" note
#     Yard   (yard)   0.174 parts/m2      dressed 25 Aug
#     Green  (green)  0.130 parts/m2
#     Greens (park)   0.046 parts/m2      <- the outlier
#
# 0.10 sits below every lot that was accepted and well above the one that was
# never looked at closely. It is deliberately NOT set under 0.046 to make the
# suite green: a threshold picked to pass the work is not a threshold.
from qc import DENSITY_MIN   # one definition, in qc.py


@rule('DETAIL-02', 'an open lot carries at least %.2f parts per m2 of ground'
                   % DENSITY_MIN)
def detail_02(snap):
    lots = {sp['name']: (sp, r) for _n, sp, r in
            G.lots(('plaza', 'green', 'park', 'vacant'))}
    out = []
    for nm in sorted(lots):
        sp, r = lots[nm]
        area = (sp['width']/100.0) * (sp['depth']/100.0)
        n = 0
        for a in snap['actors']:
            lbl = a['label']
            if lbl == 'ZONE_%s' % nm:
                n += len(a['comps'])
            elif lbl.startswith(('SUR_', 'PROP_', 'BAKED_')) and a['comps']:
                x, y = a['loc'][0], a['loc'][1]
                if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                    n += len(a['comps'])
        # zero means not built yet rather than built badly - same call
        # DETAIL-01 makes, so a lot added to the table does not fail the
        # suite before anyone has had a chance to build it.
        if n and n/area < DENSITY_MIN:
            out.append((nm, '%d parts over %.0f m2 = %.3f/m2, under %.2f'
                        % (n, area, n/area, DENSITY_MIN)))
    return out


@selftest('DETAIL-02')
def _t_detail_02():
    nm, sp = next((sp['name'], sp) for _n, sp, _r in
                  G.lots(('plaza', 'green', 'park', 'vacant')))
    area = (sp['width']/100.0) * (sp['depth']/100.0)
    def zone(k):
        return _a('ZONE_%s' % nm,
                  comps=[_c('c%d' % i, 'SM', mats=['MI_a']) for i in range(k)])
    if detail_02(_snap(zone(int(area*DENSITY_MIN) + 10))):
        return False                       # a dressed lot must pass
    return _one(detail_02(_snap(zone(max(1, int(area*DENSITY_MIN) - 5)))), nm)


@selftest('DETAIL-01')
def _t_detail_01():
    nm, sp = next((sp['name'], sp) for _n, sp, _r in G.lots(('gen',)))
    h = sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0)
    ar = (sp['width']/100.0)*(h/100.0)
    def bld(k):
        return _a('BLD2_%s_F0' % nm,
                  comps=[_c('c%d' % i, 'SM', mats=['MI_a', 'MI_b', 'MI_c', 'MI_d'])
                         for i in range(k)])
    if detail_01(_snap(bld(int(ar*DETAIL_MIN) + 30))):
        return False                       # a dense building must pass
    return _one(detail_01(_snap(bld(max(4, int(ar*DETAIL_MIN) - 30)))), nm)


# =========================== ZONE =========================================
BENCH_LOOK = 260.0        # how far ahead of a bench must be open ground


def _zone_actors(snap):
    zl = {n: w for n, _b, w in G.zone_layouts()}
    for a in snap['actors']:
        p = a['label'].split('_')
        if len(p) < 4 or p[0] != 'SUR' or p[1] != 'zone':
            continue
        w = zl.get(p[2])
        if w:
            yield a, w, p[3].startswith('b')


@rule('ZONE-01', 'zone planting sits in a lawn panel or bed; seating sits on ground it can')
def zone_01(snap):
    out = []
    for a, w, is_bench in _zone_actors(snap):
        for c in a['comps']:
            r = snapshot.rect_of(c)
            if not r:
                continue
            if is_bench:
                cx, cy = (r[0]+r[2])/2.0, (r[1]+r[3])/2.0
                pt = (cx - 1, cy - 1, cx + 1, cy + 1)
                if not G.contains(w['bounds'], pt):
                    out.append((a['label'], 'bench is off the lot'))
                elif G.intersect(w['basin'], pt) if w.get('basin') else False:
                    out.append((a['label'], 'bench is standing in the basin'))
                elif any(G.intersect(b, pt) for b in w.get('shrub', [])):
                    out.append((a['label'], 'bench is standing in a planting bed'))
            elif a['label'].split('_')[3].startswith('p'):
                # a pit holds the TRUNK; the canopy is meant to overhang
                x, y, _z = a['loc']
                pt = (x - 1, y - 1, x + 1, y + 1)
                if not any(G.intersect(pit, pt) for pit in w.get('pit', [])):
                    out.append((a['label'], '%s is not standing in a pit' % c['mesh']))
            elif not any(G.contains(pr, r) for pr in w['tree'] + w['shrub']):
                out.append((a['label'], '%s is not in a lawn panel or bed' % c['mesh']))
    return out


@selftest('ZONE-01')
def _t_zone_01():
    name, _blk, w = G.zone_layouts()[0]
    panel = w['tree'][0]
    px, py = (panel[0]+panel[2])/2.0, (panel[1]+panel[3])/2.0
    inside  = _a('SUR_zone_%s_t0' % name,
                 comps=[_c('m', 'SM_tree_04', (px-40, py-40, px+40, py+40))])
    outside = _a('SUR_zone_%s_t1' % name,
                 comps=[_c('m', 'SM_tree_04', (px-40, panel[1]-900, px+40, panel[1]-820))])
    return _one(zone_01(_snap(inside, outside)), 't1')


@rule('ZONE-02', 'a bench faces open ground, not a wall')
def zone_02(snap):
    import math as _m
    out = []
    for a, w, is_bench in _zone_actors(snap):
        if not is_bench:
            continue
        # MEASURED: SM_bench faces +X at yaw 0 (backrest at mean X -30.6, seat
        # at +0.8 over 306 vertices). So forward is the yaw bearing.
        yaw = _m.radians(a['rot'][1])
        x, y, _z = a['loc']
        fx, fy = x + BENCH_LOOK*_m.cos(yaw), y + BENCH_LOOK*_m.sin(yaw)
        pt = (fx - 1, fy - 1, fx + 1, fy + 1)
        if not G.contains(w['bounds'], pt):
            out.append((a['label'], 'looks off the lot at yaw %.0f' % a['rot'][1]))
    return out


@selftest('ZONE-02')
def _t_zone_02():
    name, blk, w = G.zone_layouts()[0]
    b = w['bounds']
    cx, cy = (b[0]+b[2])/2.0, (b[1]+b[3])/2.0
    good = _a('SUR_zone_%s_b0' % name, cls='StaticMeshActor',
              loc=(cx, cy, 0.0), rot=(0.0, 90.0, 0.0),
              comps=[_c('m', 'SM_bench', (cx-30, cy-115, cx+30, cy+115))])
    # aimed straight out of the short side of the lot
    edge = _a('SUR_zone_%s_b1' % name, cls='StaticMeshActor',
              loc=(cx, b[1] + 20.0, 0.0), rot=(0.0, -90.0, 0.0),
              comps=[_c('m', 'SM_bench', (cx-30, b[1], cx+30, b[1]+40))])
    return _one(zone_02(_snap(good, edge)), 'b1')


# =========================== LIGHT ========================================
@rule('LIGHT-01', 'no practical is aimed within %.0f degrees of vertical'
                  % (90.0 - PRACTICAL_MAX_PITCH))
def light_01(snap):
    return [(a['label'], 'pitch %.1f' % a['rot'][0]) for a in snap['actors']
            if a['family'] == 'LIGHT' and a['cls'] == 'RectLight'
            and abs(a['rot'][0]) > PRACTICAL_MAX_PITCH]


@selftest('LIGHT-01')
def _t_light_01():
    s = _snap(_a('LIGHT2_Narrow_Interior_Shop', cls='RectLight', rot=(-8.0, 90.0, 0.0)),
              _a('LIGHT_Practical_F1B0',        cls='RectLight', rot=(90.0, 0.0, 0.0)))
    return _one(light_01(s), 'LIGHT_Practical_F1B0')


# =========================== runner =======================================
def run(snap=None, verbose=True):
    broken = [r['id'] for r in RULES if r['selftest'] is None or not r['selftest']()]
    if broken:
        print('SELF-TESTS FAILED: %s' % ', '.join(broken))
        print('The suite cannot detect defects it was written to detect.')
        print('Reporting nothing about the level. Fix the rules first.')
        return 1
    if verbose:
        print('self-tests: %d/%d rules proved they can see their own defect'
              % (len(RULES), len(RULES)))
    snap = snap or snapshot.take()
    if verbose:
        print('level: %d actors, %d visible components, %.1fs\n'
              % (len(snap['actors']),
                 sum(len(a['comps']) for a in snap['actors']), snap['seconds']))
    failed = 0
    for r in RULES:
        v = r['check'](snap)
        print('%-9s %-4s %s' % (r['id'], 'FAIL' if v else 'ok', r['statement']))
        if v:
            failed += 1
            for subj, detail in v[:5]:
                print('              %-26s %s' % (subj, detail))
            if len(v) > 5:
                print('              ... and %d more' % (len(v) - 5))
    print('\ninvariants: %d rules, %d violated' % (len(RULES), failed))
    return failed


if __name__ == '__main__':
    run()
