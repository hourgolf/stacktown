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
for si, (y_far, y_near, walk) in enumerate(STREETS, 1):
    # street 3 is a service road at the back - it gets a thinner planting
    density = 0.55 if si == len(STREETS) else 1.0
    for half, (side, ybase) in enumerate(
            (('F', y_far + walk*0.55), ('N', y_near - walk*0.55))):
        x = X0 + 600.0 + half*STEP*0.5
        while x < X1 - 300.0:
            if rnd.random() <= density:
                nm = _BAG[rnd.randrange(len(_BAG))]; ti += 1
                put('Nature', nm, x + rnd.uniform(-90, 90), ybase + rnd.uniform(-40, 40),
                    0.0, rnd.uniform(0, 360), 'tree_s%d%s_%d' % (si, side, ti), '',
                    native=True, radius=45.0, scale=rnd.uniform(0.85, 1.15))
            x += STEP + rnd.uniform(-420, 420)
        nm, col = KIT[ki % len(KIT)]; ki += 1
        put('StreetProps', nm, X0 + 1400.0 + si*900.0, ybase, 0.0,
            rnd.uniform(0, 90), 'kit_s%d%s' % (si, side), col)
# --- planting and seating inside open zones ---------------------------------
# A plaza is a place props go, not a thing that carries its own: the footprint
# test lives here, so the trees and benches do too.
def _zone_world(blk, lx, ly):
    ox, oy, _ = blk['origin']; yaw = math.radians(blk['yaw'])
    return (ox + lx*math.cos(yaw) - ly*math.sin(yaw),
            oy + lx*math.sin(yaw) + ly*math.cos(yaw))

n_zone = 0
for blk in BLOCKS:
    for spec in blk['lots']:
        if spec['kind'] not in ('plaza', 'park'):
            continue
        W, D = spec['width'], spec['depth']
        # scale planting with AREA. Six trees is right for a 1500 x 600 square
        # and nothing at all for a 4100 x 1280 park.
        area = W * (D - 62.0)
        if spec['kind'] == 'plaza':
            # A SQUARE IS NOT A WOOD. Six trees at 0.8-1.1 scale, with canopies
            # 656 to 1223 uu across, completely roofed a 1500 x 548 plaza: the
            # plan view showed foliage and nothing else - no lawn, no paths, no
            # beds, no basin. The ground IS the subject in a paved square, so
            # the planting has to leave it visible.
            ntree = max(2, int(area / 300000.0))
            nseat = max(3, int(area / 260000.0))
            bag = ['SM_bush_01', 'SM_tree_03', 'SM_tree_04', 'SM_bush_01']
            tscale = (0.55, 0.8)
        else:
            ntree = max(6, int(area / 95000.0))
            nseat = max(4, int(area / 340000.0))
            bag = _BAG
            tscale = (0.8, 1.1)
        for i in range(ntree):
            lx = spec['x0'] + W*(0.14 + 0.72*rnd.random())
            ly = 62.0 + (D - 62.0)*(0.28 + 0.62*rnd.random())
            wx, wy = _zone_world(blk, lx, ly)
            nm = bag[rnd.randrange(len(bag))]
            if put('Nature', nm, wx, wy, 62.0, rnd.uniform(0, 360),
                   'zone_%s_t%d' % (spec['name'], i), '', native=True,
                   radius=45.0, scale=rnd.uniform(*tscale)):
                n_zone += 1
        for i in range(nseat):
            lx = spec['x0'] + W*(0.2 + 0.6*rnd.random())
            ly = 62.0 + (D - 62.0)*(0.3 + 0.5*rnd.random())
            wx, wy = _zone_world(blk, lx, ly)
            if put('StreetProps', 'SM_bench', wx, wy, 62.0,
                   rnd.uniform(0, 360), 'zone_%s_b%d' % (spec['name'], i),
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
