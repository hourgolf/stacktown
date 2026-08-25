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
AUTO_NAME = re.compile(r'^StaticMesh\d+$')

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
    return [(a['label'], c['name']) for a in snap['actors'] for c in a['comps']
            if AUTO_NAME.match(c['name'] or '')]


@selftest('NAME-02')
def _t_name_02():
    s = _snap(_a('ELEV_Mid_E', comps=[_c('Wall_Pier0'), _c('StaticMesh12')]))
    return len(name_02(s)) == 1 and name_02(s)[0][1] == 'StaticMesh12'


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
