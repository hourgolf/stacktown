"""Re-place props with a rule about WHAT each asset is, and a footprint test.

The water tank is 877 uu - 8.8 m - and is a ROOFTOP asset. It was dropped at
Y-160, mid-sidewalk, intersecting a facade, because props were placed at
arbitrary coordinates with no thought about what they are.

Two rules now:
  rooftop assets  -> on a roof deck, at that building's parapet height
  street assets   -> sidewalk band only, and rejected if their footprint
                     overlaps a building or another prop
"""
import unreal, sys, math, random
import _path  # repo tool paths; replaces a dead scratchpad path
import citygeom as G
import zonelayout
from city import BLOCKS, STREETS, AVENUES, BOARD_E

AV = '/Game/AssetsvilleTown/Meshes'
F = '/Game/Stacktown/Materials'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def M(n): return unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))

# WIPE EVERY SUR_ ACTOR, not two prefixes of it.
#
# This matched only 'SUR_prop' and 'SUR_tree'. Everything added since - zone
# planting (SUR_zone_*), traffic signals (SUR_signal_*), rooftop units
# (SUR_roof_*) and street furniture (SUR_kit_*) - was never removed, so every
# run of this script ADDED another full set. The plaza ended up roofed over
# with accumulated trees from repeated runs, which looked like a density
# problem and was not.
#
# SUR_ is this script's own prefix. Anything wearing it is ours to clear.
_before = 0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('SUR_'):
        eas.destroy_actor(a); _before += 1
print('cleared %d existing SUR_ props' % _before)

placed = []

# Building FOOTPRINTS, not facade lines.
#
# The old test compared against a single hardcoded BUILDING_FRONT of -60 -
# block A's line and nothing else - so it could not place a prop on any other
# street. Replacing it with one half-plane per block was no better: a
# half-plane has no back, so every prop behind a block was rejected as inside
# it, and the first street-wide run placed exactly ZERO of 24 props. A lot is a
# rectangle from its facade line to its depth, and that is what a prop has to
# miss.
def _rects():
    out = []
    for b in BLOCKS:
        ox, oy, _ = b['origin']; yaw = math.radians(b['yaw'])
        c, s_ = math.cos(yaw), math.sin(yaw)
        for l in b['lots']:
            xs, ys = [], []
            for lx in (l['x0'], l['x0'] + l['width']):
                for ly in (0.0, l['depth']):
                    xs.append(ox + lx*c - ly*s_)
                    ys.append(oy + lx*s_ + ly*c)
            out.append((min(xs), max(xs), min(ys), max(ys)))
    return out


RECTS = _rects()


def footprint_free(x, y, r):
    for x0_, x1_, y0_, y1_ in RECTS:
        if x0_ - r < x < x1_ + r and y0_ - r < y < y1_ + r:
            return False
    for px, py, pr in placed:
        if ((x - px) ** 2 + (y - py) ** 2) ** 0.5 < (r + pr) * 0.9:
            return False
    return True

def put(folder, name, x, y, z, yaw, label, colour, native=False, radius=None, scale=1.0):
    sm = unreal.EditorAssetLibrary.load_asset('%s/%s/%s.%s' % (AV, folder, name, name))
    if not sm:
        print('  missing', name); return False
    e = sm.get_bounds().box_extent
    # a tree CANOPY is meant to overhang the pavement; only its trunk collides,
    # so foliage passes an explicit trunk radius instead of its bounds
    r = radius if radius is not None else max(e.x, e.y)
    if z == 0.0 and not footprint_free(x, y, r):
        print('  REJECTED %-20s at X%.0f Y%.0f (r=%.0f) - overlap' % (name, x, y, r))
        return False
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label('SUR_' + label)
    if scale != 1.0:
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    c = a.static_mesh_component
    c.set_editor_property('static_mesh', sm)
    for i, s in enumerate(sm.get_editor_property('static_materials')):
        c.set_material(i, s.material_interface if native else M(colour))
    if z == 0.0:
        placed.append((x, y, r))
    return True

# --- rooftop assets, on actual roofs -----------------------------------------
def roof_z(spec):
    if spec['kind'] == 'av': return spec['floors'] * spec['fl_h']
    return spec['gf_h'] + spec['floors'] * spec['fl_h'] + spec['parapet']


def to_world(blk, lx, ly):
    ox, oy, _ = blk['origin']; yaw = math.radians(blk['yaw'])
    return (ox + lx*math.cos(yaw) - ly*math.sin(yaw),
            oy + lx*math.sin(yaw) + ly*math.cos(yaw))


ROOF = (('SM_Water_Tank_01', 'MI_concrete'), ('SM_airCondition_01', 'MI_frame_print'),
        ('SM_airCondition_02', 'MI_frame_print'), ('SM_AntennaBig_01', 'MI_frame_print'))
rnd = random.Random(4242)
ri = 0
for blk in BLOCKS:
    for spec in blk['lots']:
        # A zone has no roof and no gf_h. roof_z indexed those keys directly and
        # raised KeyError, which killed the whole props step - the second time
        # this session a lot without building keys has taken a sweep down with
        # it (step_roles was the first). Guard on kind, not on presence.
        if spec['kind'] not in ('gen', 'av'):
            continue
        if rnd.random() > 0.55:            # not every roof, or it reads as a rule
            continue
        nm, col = ROOF[ri % len(ROOF)]; ri += 1
        wx, wy = to_world(blk, spec['x0'] + spec['width']*rnd.uniform(0.3, 0.65),
                          rnd.uniform(280.0, 460.0))
        put('StreetProps', nm, wx, wy, roof_z(spec), rnd.uniform(-40, 40),
            'roof_%s' % spec['name'], col)

# --- street furniture and trees, on EVERY street's pavements -----------------
# --- planting plan: the ground decides the species --------------------------
# The mix was a hand-weighted bag, and scale then multiplied the crown back up:
# SM_tree_02 stood in a 1280 uu park lot at a 1613 uu crown, and a dozen street
# trees reached 500 uu past the kerb into a 1400 uu carriageway. A planting
# plan works the other way round - measure the ground, then choose what can
# stand on it.
#
# The number that matters is REACH: the yaw-independent radius of the canopy
# about the actor's PIVOT. Two earlier attempts used the bounds extent as a
# diameter, wrong twice over. The bounds are not centred on the pivot (a tree
# pivots at its trunk), and the actor is placed at a random yaw, so what a rule
# measures is the circumscribed box - up to sqrt(2) larger than the extent.
# Measured: SM_tree_01's extent says 675 across; its placed crown measured 916.
# reach_of() returns the corner distance, which bounds every yaw.
KERB_TOLERANCE  = 200.0   # must match invariants.KERB_TOLERANCE
BUILDING_MARGIN = 40.0    # keep the trunk off the facade line
_reach = {}


def reach_of(name, folder='Nature'):
    if name not in _reach:
        sm = unreal.EditorAssetLibrary.load_asset('%s/%s/%s.%s' % (AV, folder, name, name))
        if not sm:
            _reach[name] = 1e9
        else:
            b = sm.get_bounds(); o, e = b.origin, b.box_extent
            _reach[name] = math.hypot(abs(o.x) + e.x, abs(o.y) + e.y)
    return _reach[name]


def fits_footway(name, walk, smax):
    """A tree may be pushed back as far as the facade line. It is admissible if
    even there its canopy overhangs the kerb by no more than the tolerance."""
    return reach_of(name)*smax <= (walk - BUILDING_MARGIN) + KERB_TOLERANCE


def fits_lot(name, room, smax):
    return 2.0*reach_of(name)*smax <= room


def admissible(bag, test):
    fit = [n for n in bag if test(n)]
    # an empty verge is a worse answer than a small tree
    return fit or [min(bag, key=reach_of)]


def kerb_offset(name, scale, walk):
    """How far back from the kerb to stand this tree: far enough that its canopy
    stays within tolerance, never past the facade line."""
    return min(max(walk*0.45, reach_of(name)*scale - KERB_TOLERANCE),
               walk - BUILDING_MARGIN)


# Street trees. The previous pass alternated two species on a fixed 1120 uu
# grid down both pavements of all three streets, which closed the canyon views
# down and read as a hedge rather than a planting.
#
# Three things changed. SPECIES: tree_03 and tree_04 are ~450 uu across and suit
# a 430 uu pavement; tree_01 at 656 is occasional; tree_02 at 1223 would swallow
# the footway and appears rarely; bush_01 fills. SPACING: ~1900 uu with +/-420
# of jitter, and the two sides offset by half a step so they never line up
# across the road. SCALE: +/-15%, because a handmade model's trees are not
# stamped from one part.
TREE_MIX = (('SM_tree_03', 6), ('SM_tree_04', 6), ('SM_tree_01', 3),
            ('SM_bush_01', 3), ('SM_tree_02', 1))
_BAG = [n for n, w in TREE_MIX for _ in range(w)]
KIT = (('SM_Bicycle_01', 'MI_frame_print'), ('SM_barrel_1', 'MI_frame_print'))
X0, X1 = -300.0, BOARD_E     # the board grew east for the avenue
STEP = 1900.0
ti = ki = 0
AVENUE_ROADS = G.avenue_road_rects()
BOARD = G.board_rect()
for si, (y_far, y_near, walk) in enumerate(STREETS, 1):
    # street 3 is a service road at the back - it gets a thinner planting
    density = 0.55 if si == len(STREETS) else 1.0
    smax = 1.15
    bag = admissible(_BAG, lambda n: fits_footway(n, walk, smax))
    k_far, k_near = y_far + walk, y_near - walk
    for half, (side, kerb, inward) in enumerate(
            (('F', k_far, -1.0), ('N', k_near, +1.0))):
        x = X0 + 600.0 + half*STEP*0.5
        while x < X1 - 400.0:
            if rnd.random() <= density:
                nm = bag[rnd.randrange(len(bag))]; ti += 1
                sc = rnd.uniform(0.85, smax)
                reach = reach_of(nm)*sc
                wx = x + rnd.uniform(-90, 90)
                wy = kerb + inward*kerb_offset(nm, sc, walk)
                crown = (wx - reach, wy - reach, wx + reach, wy + reach)
                # A pavement line runs the full width of the board, so it
                # crosses every avenue. Same junction skip the lamps and the
                # parked cars needed, reading the same rectangles they read.
                if (G.contains(BOARD, crown)
                        and not any(G.intersect(r, crown) for r in AVENUE_ROADS)):
                    put('Nature', nm, wx, wy, 0.0, rnd.uniform(0, 360),
                        'tree_s%d%s_%d' % (si, side, ti), '',
                        native=True, radius=45.0, scale=sc)
            x += STEP + rnd.uniform(-420, 420)
        nm, col = KIT[ki % len(KIT)]; ki += 1
        put('StreetProps', nm, X0 + 1400.0 + si*900.0, kerb + inward*walk*0.5, 0.0,
            rnd.uniform(0, 90), 'kit_s%d%s' % (si, side), col)
# --- planting and seating inside open zones ---------------------------------
# A plaza is a place props go, not a thing that carries its own: the footprint
# test lives here, so the trees and benches do too.
def _zone_world(blk, lx, ly):
    ox, oy, _ = blk['origin']; yaw = math.radians(blk['yaw'])
    return (ox + lx*math.cos(yaw) - ly*math.sin(yaw),
            oy + lx*math.sin(yaw) + ly*math.cos(yaw))

n_zone = 0


def _fits_in(rect, reach):
    """Can a canopy of this reach stand anywhere inside this rectangle?"""
    return (rect[2] - rect[0]) > 2*reach and (rect[3] - rect[1]) > 2*reach


for blk in BLOCKS:
    for spec in blk['lots']:
        if spec['kind'] not in ('plaza', 'green', 'park'):
            continue
        LO = zonelayout.layout(spec)
        smax = 0.8 if spec['kind'] in ('plaza', 'green') else 1.1
        smin = 0.55 if spec['kind'] in ('plaza', 'green') else 0.8
        SHRUBS = ['SM_bush_01']
        TREES = [n for n, _w in TREE_MIX if n not in SHRUBS]

        def place(rects, bag, tag, count, zoff=62.0, avoid=True):
            """Into the authored rectangle, not across the whole lot. A tree
            stands in a lawn panel, a shrub in a bed, a bench on paving."""
            global n_zone
            made = 0
            for i in range(count):
                rect = rects[i % len(rects)]
                room = min(rect[2] - rect[0], rect[3] - rect[1])
                fit = [n for n in bag if 2.0*reach_of(n)*smax <= room]
                if not fit:
                    fit = [min(bag, key=reach_of)]
                nm = fit[rnd.randrange(len(fit))]
                sc = rnd.uniform(smin, smax)
                reach = reach_of(nm)*sc
                if not _fits_in(rect, reach):
                    sc = smin
                    reach = reach_of(nm)*sc
                    if not _fits_in(rect, reach):
                        continue
                lx = rnd.uniform(rect[0] + reach, rect[2] - reach)
                ly = rnd.uniform(rect[1] + reach, rect[3] - reach)
                crown = (lx - reach, ly - reach, lx + reach, ly + reach)
                if avoid and any(G.intersect(av, crown) for av in LO['avoid']):
                    continue
                wx, wy = _zone_world(blk, lx, ly)
                if put('Nature', nm, wx, wy, zoff, rnd.uniform(0, 360),
                       'zone_%s_%s%d' % (spec['name'], tag, i), '',
                       native=True, radius=45.0, scale=sc):
                    n_zone += 1
                    made += 1
            return made

        # Counts still scale with AREA, but with the PLANTABLE area now - a
        # square is not a wood, and six trees at full scale once roofed the
        # whole plaza so the plan view showed foliage and nothing else.
        def place_pits(pits, bag, tag):
            """A pit holds the TRUNK. The canopy overhangs the paving, which is
            what a tree pit is for, so the only things it must clear are the
            fountain and the edge of the lot."""
            global n_zone
            keep = [LO['basin']] if LO.get('basin') else []
            for i, pit in enumerate(pits):
                nm = min(bag, key=reach_of)
                sc = rnd.uniform(smin, smax)
                reach = reach_of(nm)*sc
                px = (pit[0] + pit[2])/2.0 + rnd.uniform(-20, 20)
                py = (pit[1] + pit[3])/2.0 + rnd.uniform(-20, 20)
                crown = (px - reach, py - reach, px + reach, py + reach)
                # The CROWN must stay over the lot. The TRUNK is what must
                # clear the fountain - a keep-off exists to stop things
                # STANDING in the water, and a canopy above it is exactly what
                # a tree beside a fountain does.
                if not G.contains(LO['bounds'], crown):
                    continue
                trunk = (px - 40, py - 40, px + 40, py + 40)
                if any(G.intersect(k, trunk) for k in keep):
                    continue
                wx, wy = _zone_world(blk, px, py)
                if put('Nature', nm, wx, wy, 62.0, rnd.uniform(0, 360),
                       'zone_%s_%s%d' % (spec['name'], tag, i), '',
                       native=True, radius=45.0, scale=sc):
                    n_zone += 1

        if spec['kind'] == 'plaza':
            place_pits(LO['pit'], TREES, 'p')
        else:
            tree_area = sum((r[2]-r[0])*(r[3]-r[1]) for r in LO['tree'])
            place(LO['tree'], TREES, 't',
                  max(2, int(tree_area / (300000.0 if spec['kind'] == 'green'
                                          else 95000.0))))
        if LO['shrub']:
            place(LO['shrub'], SHRUBS, 's', 2*len(LO['shrub']),
                  zoff=62.0 + 28.0, avoid=False)
        # Seating comes from the layout, which knows what each bench looks at.
        for i, (lx, ly, lyaw) in enumerate(zonelayout.seat_plan(LO)):
            wx, wy = _zone_world(blk, lx, ly)
            if put('StreetProps', 'SM_bench', wx, wy, 62.0,
                   blk['yaw'] + lyaw, 'zone_%s_b%d' % (spec['name'], i),
                   'MI_wood', radius=90.0):
                n_zone += 1
print('zone planting and seating: %d' % n_zone)

# --- traffic signals, one per intersection corner ---------------------------
# SM_traffic_lights_1 is a mast-arm signal: 70 x 555 x 518, so its LONG axis is
# local Y and yaw decides which way the arm reaches. Each corner's arm is aimed
# over the crossing it governs - south and north over the street, east and west
# over the avenue - which is what makes it read as a signalled junction rather
# than four poles that happen to be nearby.
n_sig = 0
for si, (y_far, y_near, walk) in enumerate(STREETS, 1):
    sy0, sy1 = y_far + walk, y_near - walk
    for ai, (x_w, x_e, awalk) in enumerate(AVENUES, 1):
        ax0, ax1 = x_w + awalk, x_e - awalk
        OFF = 78.0
        corners = ((ax0 - OFF, sy1 + OFF, 180.0, 'NW'),   # arm reaches south
                   (ax0 - OFF, sy0 - OFF, -90.0, 'SW'),   # arm reaches east
                   (ax1 + OFF, sy1 + OFF,  90.0, 'NE'),   # arm reaches west
                   (ax1 + OFF, sy0 - OFF,   0.0, 'SE'))   # arm reaches north
        for cx, cy, cyaw, tag in corners:
            if put('StreetProps', 'SM_traffic_lights_1', cx, cy, 0.0, cyaw,
                   'signal_s%da%d_%s' % (si, ai, tag), 'MI_frame_print', radius=60.0):
                n_sig += 1
print('traffic signals: %d over %d intersections' % (n_sig, len(STREETS)*len(AVENUES)))
print('props placed: %d street/roof items' % (len(placed)))
les.save_current_level()
