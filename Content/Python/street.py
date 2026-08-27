"""One street from the catalogue, for the Stage 2 gate. Sandbox only.

WHY. `Docs/ONE_BUILDING_GATE.md` Stage 2 says the work must read as a model at
BOTH block hero (whole board) and player zoom (one facade filling the frame),
and that "a block that only works at one of these is not a pass". The 194
baked meshes have only ever been judged one at a time on a bench, at a close
camera. Measured against the gate's own richness metrics they carry 13-31
depth planes at player zoom but only 3-5 that survive the gate's 39 uu
block-hero threshold - so from the block camera thirty-two distinct recipes
may collapse toward a handful of silhouettes. That is the F1 finding restated,
and a street is the only way to see whether it is true.

THE REPEATS, AND WHAT MEASURING THEM FOUND. Two pairs repeat the same recipe
so the clone problem stays visible. P6 recorded the cause as the shared seed -
every building of a recipe is built from one seed, so a repeat is an exact
copy. Measured against the recorded part list, that is wrong about the
mechanism: a different seed swaps two rooftop clutter meshes (an air
conditioner becomes an antenna) and moves NO geometry whatsoever - 0 fields on
vernacular3 t4 and deco t5, 3 on the recipes that own a stairhead. Per-parcel
seeds, the fix P6 names, would not have fixed P6.

What does move is the PARCEL. Width 1640 -> 2050 restructures 322 parts and
moves 5 of them past the gate's 39 uu block-hero threshold, up to 410 uu; a
tier step moves 243. So the clone fix is a placement rule, not a generator
change, and it needs no re-bake because the widths are already on disk. See
`vary_repeats` below - the repeats now stand as the demonstration that the
rule works, which is what a real street does anyway: a developer puts the same
building type on two plots of different size.

Stage 2 constraints carried: no people, vehicles or signage; one master
material; work in a sandbox; OneBuildingTest untouched.
"""
import unreal
import _path  # noqa: F401
import recipes
import palette
import stagegeo
import json
import random

# Sandbox_Bench built these first; Stage2_Street is now their own room
# (streetroom.py). Both are allowed: the bench copy stays usable until
# the owner confirms the new map, which was their explicit instruction.
SANDBOX = ('Sandbox_Bench', 'Stage2_Street')
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not any(k in eus.get_editor_world().get_path_name() for k in SANDBOX):
    raise SystemExit('street.py is sandbox only - open /Game/Maps/%s' % SANDBOX)

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
BAKED = '/Game/Stacktown/Baked'

X0 = 3000.0                     # clear of the shelf, south of it
Y_NORTH = -22000.0              # the north row's facade line
STREET_W = 1500.0               # carriageway + both pavements
PAVE = 260.0
GAP = 60.0                      # nominal; varied per parcel below

# THE BUILDING LINE HAS TO MOVE. First street test: every building was a
# flat-fronted prism standing on one continuous line with a uniform 60 uu
# gap, and the row read as a comb. ONE_BUILDING_GATE Stage 2 names exactly
# this first under what carries block-hero range - "setbacks ... silhouette
# variation between buildings, and the gaps between them".
#
# Both numbers are well above the gate's own 39 uu threshold, which is the
# whole point: this is mass-scale variation, the range where it is seen.
# Deterministic per parcel so a street is reproducible.
SETBACK = (0.0, 210.0)          # how far a parcel may sit back off the line
GAPS = (40.0, 300.0)            # and how wide the gap to its neighbour may be
LINE_SEED = 5150
Z = stagegeo.FLOOR_Z

# (recipe, tier, width). Mixed eras, mixed heights, two deliberate repeats.
# A CROWN-RICH MIX. The first street used almost no recipe that carries a
# crown, and at tiers where the crowns do not appear - so every silhouette was
# a flat parapet and the row read as a comb of prisms. That was a composition
# failure, not a catalogue one: the catalogue holds ziggurats, masts, stacks,
# blade signs, cupolas, gables, pediments, chimney stacks and mech penthouses,
# all of them well above the gate's 39 uu block threshold.
#
# This mix is chosen so that no two neighbours share a crown TYPE, which is
# the actual variable the gate asks about at block-hero range. Two repeats are
# still deliberate so P6 stays visible.
NORTH = [
    ('vernacular5',   3, 1640.0),   # cupola
    ('deco3',         4, 2050.0),   # brick stack
    ('vernacular',    3, 1230.0),   # flat, cornice - the quiet one
    ('deco',          5, 1640.0),   # ziggurat + mast
    ('contemporary',  5, 1640.0),   # mech penthouse
    ('vernacular7',   3, 1640.0),   # stepped gable
    ('vernacular5',   3, 1640.0),   # REPEAT - P6 made visible
    ('modern6',       4, 2050.0),   # constant-setback podium
]
SOUTH = [
    ('deco4',         4, 2050.0),   # blade sign + marquee
    ('vernacular3',   4, 1640.0),   # chimney stacks
    ('tower',         5, 1640.0),   # stepped tower
    ('vernacular4',   3, 2050.0),   # pediment
    ('contemporary8', 4, 1640.0),   # slender + mech
    ('deco5',         5, 1640.0),   # zigzag + mast
    ('vernacular3',   4, 1640.0),   # REPEAT - P6 made visible
    ('modern2',       4, 1640.0),   # precast + service shaft
]


# NO TWO PARCELS ON THE BLOCK MAY SHARE (recipe, tier, width).
#
# That triple IS the baked asset name, so sharing it means placing the same
# mesh twice - the same building, down to the rooftop clutter. The rule spans
# BOTH rows because block hero sees both at once; per-row would let a clone
# sit directly across the street from its twin, which is worse.
#
# Width is tried before tier: it restructures more parts (322 vs 243 measured
# on vernacular3 t4) and it keeps the building's story - same type, bigger
# plot - whereas a tier step says the owner rebuilt. Widest change first, so
# a forced variation is one that reads at block range rather than the nearest
# width that merely clears the rule.
def vary_repeats(rows):
    used = set()
    changed = []
    for tag, row in rows:
        for i, (rid, t, w) in enumerate(row):
            if (rid, t, w) not in used:
                used.add((rid, t, w))
                continue
            alts = sorted(recipes.widths(rid), key=lambda v: -abs(v - w))
            pick = None
            for aw in alts:
                if (rid, t, aw) in used:
                    continue
                if eal.does_asset_exist('%s/%s' % (BAKED, recipes.asset_name(rid, t, aw))):
                    pick = (rid, t, aw)
                    break
            if pick is None:
                for at in (t + 1, t - 1):
                    if at < 0 or (rid, at, w) in used:
                        continue
                    if eal.does_asset_exist('%s/%s' % (BAKED, recipes.asset_name(rid, at, w))):
                        pick = (rid, at, w)
                        break
            if pick is None:
                changed.append('%s%d %s t%d w%d KEPT - no distinct variant baked'
                               % (tag, i, rid, t, int(w)))
                used.add((rid, t, w))
                continue
            row[i] = (pick[0], pick[1], pick[2])
            used.add(pick)
            changed.append('%s%d %s t%d w%d -> t%d w%d'
                           % (tag, i, rid, t, int(w), pick[1], int(pick[2])))
    return changed


for _line in vary_repeats((('N', NORTH), ('S', SOUTH))):
    print('  vary: %s' % _line)


def repaint(actor, sm, rid, scheme):
    base = recipes.RECIPES[rid]['base']
    want = {base.get('wall') or 'MI_dist_buff': scheme['wall'],
            base.get('trim') or 'MI_paint_cream': scheme['trim'],
            'MI_canopy_accent': scheme['accent'],
            'MI_glass_b': scheme['glass']}
    if base.get('panel_b'):
        want[base['panel_b']] = scheme['base']
    n = 0
    for si, sl in enumerate(sm.get_editor_property('static_materials')):
        nm = str(sl.material_slot_name)
        if nm in want:
            mi = eal.load_asset('/Game/Stacktown/Materials/%s' % want[nm])
            if mi:
                actor.static_mesh_component.set_material(si, mi)
                n += 1
    return n


for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('ST_'):
        eas.destroy_actor(a)

lo = [1e18] * 3
hi = [-1e18] * 3
made = 0
missing = []


def place(row, y, yaw, tag):
    global made
    rnd = random.Random(LINE_SEED + (0 if tag == 'N' else 977))
    x = X0
    for i, (rid, t, w) in enumerate(row):
        # a forecourt on some parcels, flush on others. `sign` pushes the
        # building AWAY from the carriageway whichever side it is on.
        back = rnd.choice((0.0, 0.0, rnd.uniform(*SETBACK), rnd.uniform(*SETBACK)))
        sign = 1.0 if yaw == 0.0 else -1.0
        asset = recipes.asset_name(rid, t, w)
        sm = eal.load_asset('%s/%s' % (BAKED, asset))
        if not sm:
            missing.append(asset)
            x += w + GAP
            continue
        # a building's own origin is its left-front corner, so a row facing
        # the other way has to be placed from its far corner
        px = x if yaw == 0.0 else (x + w)
        a = eas.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(px, y + sign * back, Z),
            # Rotator(ROLL, PITCH, YAW) - not (pitch, yaw, roll). Passing
            # yaw in the second slot set PITCH 180 and stood the whole south
            # row on its head, every building hanging below the floor. The
            # bake path documents this same argument order and I still got it
            # the wrong way round here.
            unreal.Rotator(0.0, 0.0, yaw))
        a.set_actor_label('ST_%s_%d_%s_t%d' % (tag, i, rid, t))
        a.static_mesh_component.set_editor_property('static_mesh', sm)
        # PER-PARCEL PAINT. The palette is keyed on the parcel, not the
        # recipe, so two of the same building are different colours - which
        # is what a real street does and what the shelf could not show.
        repaint(a, sm, rid, palette.scheme_for('%s%d' % (tag, i)))
        o, e = a.get_actor_bounds(False)
        for k, ax in enumerate('xyz'):
            lo[k] = min(lo[k], getattr(o, ax) - getattr(e, ax))
            hi[k] = max(hi[k], getattr(o, ax) + getattr(e, ax))
        made += 1
        x += w + rnd.uniform(*GAPS)
    return x


xn = place(NORTH, Y_NORTH, 0.0, 'N')
xs = place(SOUTH, Y_NORTH - STREET_W, 180.0, 'S')

# the street itself: carriageway between the two pavement strips
CUBE = eal.load_asset('/Engine/BasicShapes/Cube')
run = max(xn, xs) - X0


def slab(name, x0, x1, y0, y1, z0, z1, mat):
    global made
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
        unreal.Rotator(0, 0, 0))
    a.set_actor_label('ST_%s' % name)
    a.static_mesh_component.set_editor_property('static_mesh', CUBE)
    a.set_actor_scale3d(unreal.Vector((x1 - x0) / 100.0, (y1 - y0) / 100.0,
                                      (z1 - z0) / 100.0))
    mi = eal.load_asset('/Game/Stacktown/Materials/%s' % mat)
    if mi:
        a.static_mesh_component.set_material(0, mi)
    made += 1


ya, yb = Y_NORTH - STREET_W, Y_NORTH
slab('Road', X0 - 400, X0 + run + 400, ya + PAVE, yb - PAVE, Z - 6, Z + 4,
     'MI_dark_metal')
slab('PaveN', X0 - 400, X0 + run + 400, yb - PAVE, yb, Z - 6, Z + 26,
     'MI_precast_grey')
slab('PaveS', X0 - 400, X0 + run + 400, ya, ya + PAVE, Z - 6, Z + 26,
     'MI_precast_grey')

if missing:
    print('  MISSING: %s' % ', '.join(missing[:6]))
print('street: %d buildings + road, run %.0f uu' % (made - 3, run))
print('STREETBOUNDS ' + json.dumps({'lo': lo, 'hi': hi}))
les.save_current_level()
