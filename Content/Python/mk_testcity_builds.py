"""Place the test city's 14 lots as interactive, empty BP_Parcel instances.

RUN THROUGH rung.sh - it mutates. TestCity only. Idempotent.

WHY THE FIRST PLACEMENT WAS BOXES. citylayout's block length was 4800,
chosen because it divided by six. The catalogue's widths are 820 / 1230 /
1640 / 2050 / 2460 - all multiples of 410 - so 4800 gave 800 uu lots and
NOTHING IN THE CATALOGUE FITS AN 800 UU LOT. The boxes were not a staging
decision, they were the only thing that could stand there. BLOCK_LEN is now
4920 (410 x 12), lots are 820, and citylayout's LOTS-ARE-CATALOGUE-WIDTHS
test fails if that ever drifts again.

REWRITTEN 2026-09-01 for "play from scratch"
(PARCELIZATION_CONTRACT.md's amendment, A3). Two real changes from the
version this replaces:

1. SPAWNS BP_Parcel, NOT StaticMeshActor. The original §3 design ("the
   builder emits BP_Parcel directly") was declared but never actually
   wired - this file still spawned plain StaticMeshActors right up until
   this rewrite, confirmed by reading the file rather than trusting an
   earlier summary of it. Only PARCEL_Demo0 was ever a real BP_Parcel.
2. SETS IDENTITY, NOT THE MESH. RecipeId/WidthUU/CornerSide are the
   parcel's own immutable identity (set once, here, at spawn - matches
   the original §3 reasoning, unchanged). Tier=0 and Owned=False ALWAYS,
   never the pin's declared tier - a fresh purchase starts small and
   grows via the tick (A2). The static mesh itself is never touched here;
   BP_Parcel.ResolveMesh (called at its own EventBeginPlay, which only
   fires in PIE) resolves an empty-lot placeholder until the driver marks
   it owned. This means the level shows NO buildings in the bare editor
   view now (that's expected - PARCEL_Demo0 already worked this way; the
   city was always meant to be seen through PIE, not the editor viewport).

CONSEQUENCE FOR GAP MEASUREMENT: the existing gap-rhythm logic advances
by each building's MEASURED built extent, not its parcel width (see the
GAPS/SETBACK block below) - originally read from the PLACED ACTOR's
bounds. With no mesh resolved until PIE, that reads back empty/zero now.
Measures the CANDIDATE STATIC MESH ASSET's own local bounding box instead
(`sm.get_bounding_box()`, bare-Python, no MCP call - this script runs
inside the editor process via rung.sh, and an MCP call from there
deadlocks) - confirmed to match the placed-actor measurement exactly
(cross-checked 2026-09-01: both give SM_Bld_vernacular_t0_w1230's true
width as 746.7 uu, and the MCP StaticMeshTools.get_bounds route used only
for that cross-check agrees to the decimal).

DEFERRED, NOT DROPPED: per-parcel repaint (street.py's per-lot colour
variation, `repaint()` below) painted the ACTOR'S ACTUAL MESH's material
slots at spawn time - meaningless now that the mesh isn't assigned until
PIE, and potentially reassigned again as a parcel grows. Repainting a
mesh that changes at runtime needs its own design (most likely: the
driver re-applies it in Python each time it pushes a Tier/Owned change,
mirroring how it already pushes those two fields) - out of scope for this
wiring pass per the owner's own priority order (selection feedback > HUD
completeness > tuning; colour variation is polish, not selection feel).
`repaint()` stays defined, just uncalled, so the working logic is here
for whoever picks this up rather than lost. Until then every building
uses its bake's default materials - a real, visible, explicitly chosen
gap, not a silent one.

PLACEMENT CONVENTIONS ARE street.py's, not new ones:
  - a baked building's origin is its LEFT-FRONT CORNER, so a row facing the
    other way is placed from its far corner (px = x + w at yaw 180)
  - unreal.Rotator is (ROLL, PITCH, YAW). street.py carries a comment about
    getting this wrong and standing a whole row on its head; the citylight
    rig hit the identical trap the same day with a light aimed at the sky.
    Third time it is written down.
"""
import random

import unreal
import _path  # noqa: F401
import recipes
import citylayout as L
import testcity_pins
import placement

PARCEL_CLASS_PATH = '/Game/Stacktown/Runtime/BP_Parcel.BP_Parcel_C'
# Deep underground, all 30 stacked at one point - collision is off and the
# actor is hidden before this script ever returns, so overlap and
# visibility don't matter, but a real out-of-band position is a second,
# independent guarantee against a stray trace ever landing on a dormant
# one (belt-and-braces, not load-bearing on its own).
_POOL_GRAVEYARD = unreal.Vector(0.0, 0.0, -50000.0)

BAKED = '/Game/Stacktown/Baked'
# PER-LOT WIDTH, not one width. The first version hardcoded 820 because
# every lot was 820 - and only vernacular/vernacular8 are baked at 820, so the
# city came out ONE ERA and half of it brick. citylayout now partitions each
# block across the ladder; this reads each lot's own width.
SEED = 4920                  # deterministic: the same city every run

# TRANSPLANTED VERBATIM FROM street.py, on the project lead's ruling. These
# are PER-PARCEL ABSOLUTES tuned to fix a FRAMING property (the weak block
# hero read), not a property of that street's 14,483 uu run - their scale
# comes from the 0.4% table, where a 40 uu gap is 400 mm against the hero
# threshold's 230 mm, so the smallest gap just reads at hero range.
# The buildings DO NOT FILL THEIR LOTS: the width in an asset name is the
# PARCEL width, and fill means the tier takes a share of it. Placing each
# mesh at its lot's left edge and assuming it spanned the lot left accidental
# gaps up to 382 uu, which exposed neighbours' blank party flanks - the
# "big green building with no windows".
GAPS = (40.0, 300.0)         # gap to the neighbour, varied per parcel
SETBACK = (0.0, 210.0)       # how far a parcel may sit back off the line
Z = 0.0

eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if 'TestCity' not in eus.get_editor_world().get_path_name():
    raise SystemExit('mk_testcity_builds.py runs only in TestCity')

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary


def baked_asset_names():
    """Every asset name actually present under BAKED, queried directly from
    the content browser - not derived from recipes.py's declared space,
    which is far larger than what's baked (testcity_pins.py's own corner
    -bake story: ten exist of what a complete set would need). This is the
    `have` set testcity_pins.require() checks each pin against."""
    names = set()
    for a in eal.list_assets(BAKED, recursive=False, include_folder=False):
        names.add(a.split('.')[0].rsplit('/', 1)[-1])
    return names


def repaint(actor, sm, rid, scheme):
    """street.py's repaint, reused - slot names come from the recipe base.

    NOT CALLED from build() as of the 2026-09-01 rewrite - see the module
    docstring's "DEFERRED, NOT DROPPED" note. Kept working and callable
    (needs `palette.scheme_for(key, rid)` for `scheme` at the call site,
    not imported here since nothing currently calls this) for whoever
    redesigns per-parcel paint against a mesh that's assigned at PIE time
    and can change tier during play, rather than at editor-placement
    time."""
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


def build():
    if not (L.parcelmeta.selftests(verbose=False) and L.selftests(verbose=False)
            and testcity_pins._selftest()):
        raise SystemExit('layout/pin self-tests failed - placing nothing')
    have = baked_asset_names()
    print('catalogue: %d baked assets under %s' % (len(have), BAKED))
    parcel_class = unreal.load_class(None, PARCEL_CLASS_PATH)

    killed = 0
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith(('TC_Mass', 'TC_Bld', 'POOL_')):
            eas.destroy_actor(a)
            killed += 1

    rnd = random.Random(SEED)
    made = 0
    gaps_used, setbacks_used, prev_end = [], [], None
    corners_placed = 0
    for bname in sorted(L.blocks()):
        b = L.blocks()[bname]
        _, y0, _, y1 = b['env']
        # blocks NORTH of the arterial face SOUTH (yaw 0, front toward -y);
        # blocks SOUTH of it face NORTH (yaw 180). 'faces' is carried by the
        # layout rather than re-derived from the sign here.
        _end, turn_side = L.cross_street_end(bname)
        north = b['faces'] == 'south'
        yaw = 0.0 if north else 180.0
        face_y = y0 if north else y1
        # per BLOCK: cursor and prev_end both reset, or the first lot of
        # each block records a 'gap' that spans the cross street.
        cursor, prev_end = None, None
        for i, (key, lx0, lx1, corner) in enumerate(L.lots(bname)):
            w = round(lx1 - lx0)
            # PINNED, NOT DRAWN (Docs/BETA_TWIN_PLAN.md, testcity_pins.py):
            # each lot names a fixed (recipe, tier) identity so the same
            # city renders under any catalogue - a draw from `stock[w]`
            # dealt a DIFFERENT city per bake set (measured: removing one
            # asset changed 7 of 14 buildings), which the wooden twin
            # cannot demonstrate anything against. require() raises loudly
            # (PinNotBaked) rather than falling back to a draw - the whole
            # point of pinning is that this never silently happens.
            rid, t = testcity_pins.identity(key)
            asset = testcity_pins.require(
                key, have, corner_side=turn_side if corner else None)
            sm = eal.load_asset('%s/%s' % (BAKED, asset))
            # gap/setback are positioning, not identity - still drawn from
            # the SAME rnd sequence as before pinning, so the street's
            # rhythm is unchanged by this change.
            gap_draw = rnd.uniform(*GAPS)
            back = rnd.choice((0.0, 0.0, rnd.uniform(*SETBACK),
                               rnd.uniform(*SETBACK)))
            if not sm:
                # require() already proved `asset` is in `have`, the exact
                # set list_assets() just reported - load_asset failing
                # anyway means the content browser disagreed with itself
                # between those two calls, not a missing bake.
                raise SystemExit(
                    'INTERNAL: %s required %s but load_asset failed - '
                    'have-set and content browser disagree' % (key, asset))
            # street.py's rhythm: advance by the parcel width and a VARIED
            # gap, and let some parcels sit back off the building line. The
            # gap is deliberate and legible rather than an artefact of fill.
            # ADVANCE BY THE BUILT EXTENT, NOT THE PARCEL WIDTH. street.py
            # writes x += w + GAP, where w is the parcel; because buildings
            # take only a SHARE of their parcel, the leftover silently adds
            # itself to every gap. Measured that way the transplant landed at
            # 61..1926 uu against a 40..300 range - so the rhythm was not
            # transplanted at all, it was buried under fill slack. Advancing
            # by the measured right edge is what actually reproduces the
            # intent the ranges encode. Measured off the CANDIDATE ASSET's
            # own local bounds now (built_w), not the placed actor's world
            # bounds - see the module docstring's "CONSEQUENCE FOR GAP
            # MEASUREMENT" note.
            built_w = sm.get_bounding_box().max.x - sm.get_bounding_box().min.x
            if cursor is None:
                cursor = lx0
            else:
                cursor = prev_end + gap_draw
            sign = 1.0 if yaw == 0.0 else -1.0
            if prev_end is not None:
                gaps_used.append(cursor - prev_end)
            setbacks_used.append(back)
            px = cursor if yaw == 0.0 else cursor + w
            face = face_y + sign * back
            a = eas.spawn_actor_from_class(
                parcel_class, unreal.Vector(px, face, Z),
                unreal.Rotator(0.0, 0.0, yaw))       # ROLL, PITCH, YAW
            # DORMANT, not active - empty-mode's unified pool (2026-09-02,
            # PARCELIZATION_CONTRACT.md's pool doctrine, extended to
            # pins): this actor's real identity (RecipeId/WidthUU/Tier/
            # Owned/CornerSide) is set by init_unreal.py's pin-
            # reactivation pass at PIE start, reading testcity_pins
            # directly - never here, and never TC_Bld_ labelled anymore.
            # What DOES have to happen here, and only here: the gap/
            # setback rhythm above needs the real baked asset's bounding
            # box (built_w), an editor-only read the driver doesn't have
            # and shouldn't need - so this actor is pre-positioned at its
            # final, rhythm-adjusted transform right now and left hidden/
            # non-colliding until the driver decides, via EmptyStart,
            # whether to ever show it. Label carries the pin key so
            # reactivation can find it by name, same discipline as the
            # placement pool's own POOL_NN -> pid relabel on activation.
            a.set_actor_label('POOL_PIN_%s' % key)
            a.set_actor_hidden_in_game(True)
            a.set_actor_enable_collision(False)
            if corner:
                corners_placed += 1
            prev_end = px + built_w if yaw == 0.0 else px
            made += 1

    # DORMANT POOL (PARCELIZATION_CONTRACT.md: "a parcel actor is a
    # pooled, pre-placed object; placement activates, reset deactivates").
    # No Python API in this build spawns an actor into the GAME/PIE world
    # (confirmed 2026-09-02 by exhausting every candidate: World has no
    # spawn method at all, GameplayStatics has none for generic actors,
    # and the only spawn_actor_from_class in the whole `unreal` module
    # lives on the two editor-world-only subsystems) - so a placement-
    # time click can only ACTIVATE an actor that already exists, never
    # create one. These 30 are that inventory: no identity (BP_Parcel's
    # own class defaults - Owned=False - already read as an empty-lot
    # placeholder, same as a fresh pinned lot), hidden, non-colliding,
    # labelled POOL_00.. so the driver can find them by prefix and so a
    # half-activated one is never mistaken for real city content.
    pooled = 0
    for i in range(placement.POOL_SIZE):
        a = eas.spawn_actor_from_class(
            parcel_class, _POOL_GRAVEYARD, unreal.Rotator(0.0, 0.0, 0.0))
        a.set_actor_label('POOL_%02d' % i)
        a.set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)
        pooled += 1

    print('cleared %d placeholder(s); pre-positioned %d dormant pin slots '
          '(%d corner) at their rhythm-adjusted transforms, all %d lots '
          'pinned, require() green - identity/visibility land at PIE '
          'start via init_unreal.py\'s pin-reactivation pass, gated on '
          'EmptyStart; %d dormant placement-pool actors staged '
          '(placement.POOL_SIZE)'
          % (killed, made, corners_placed, len(testcity_pins.PINS), pooled))
    # VERIFY THE DISTRIBUTION LANDED - the known-answer discipline applied to
    # placement. A transplant that silently misses its ranges is not one.
    g = [v for v in gaps_used if v > 0]
    if g:
        print('gaps: n=%d min %.0f max %.0f mean %.0f   (street.py %g..%g)'
              % (len(g), min(g), max(g), sum(g)/len(g), GAPS[0], GAPS[1]))
    sb = [v for v in setbacks_used if v > 0]
    print('setbacks: %d of %d set back, max %.0f   (street.py %g..%g)'
          % (len(sb), len(setbacks_used), max(sb) if sb else 0.0,
             SETBACK[0], SETBACK[1]))
    return made


# ROAD POOL (2026-09-04, Docs/ROAD_BUILD_CONTRACT.md section 5). The
# road-drawing verb's own counterpart to the parcel pool above: no
# Python API in this build spawns an actor into the GAME/PIE world (the
# same wall the parcel pool's own comment already names, exhausted
# 2026-09-02), so a drawn road can only ever ACTIVATE one of these,
# never create one fresh.
ROAD_POOL_SIZE = 10

# NOT `import mk_testcity` for these two, though that file is what
# actually built TC_Road_Arterial/TC_Road_Cross and is the real source
# of truth for them - mk_testcity.py ends with its OWN unconditional
# `build()` call at module scope, exactly like this file's own tail
# below, and it destroys/rebuilds the ENTIRE road/board/mass layout on
# every import. Importing it here to read two string constants would
# have silently rebuilt the whole city as a side effect of adding a
# road pool - found by reading that file's own tail before importing
# it, not after. Copied by hand instead, cited to their real origin:
# mk_testcity.py's own CUBE and M_ROAD, confirmed there as the literal
# arguments TC_Road_Arterial/TC_Road_Cross were built with (its own
# `_box(eas, cube, mats['road'], 'TC_Road_Arterial', ...)` call) - not
# queried from the live actor, since this was written with no editor
# access at all. If mk_testcity.py's own M_ROAD is ever retuned, this
# copy needs updating by hand; there is no automatic check standing in
# for that, the same accepted gap PLATE_X_MIN/MAX already lives with.
_ROAD_CUBE = '/Engine/BasicShapes/Cube.Cube'
_ROAD_MATERIAL = '/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey'


def build_road_pool():
    """Place ROAD_POOL_SIZE dormant road-segment actors, labelled
    POOL_ROAD_00..09 - the driver claims one on a successful draw_road,
    sets its transform from ROAD_BUILD_CONTRACT.md section 5's own
    math, and relabels it with the road's own id, the identical shape
    the parcel pool above already uses for a placed lot.

    STANDALONE - NOT called from build() and NOT called at this file's
    own bottom-of-file line, deliberately. build() already runs
    unconditionally on any import of this module (this file's own
    long-standing convention: "RUN THROUGH rung.sh - it mutates").
    Folding this in there too would mean a fresh import either
    duplicates the road pool (if not idempotent) or destroys/rebuilds
    the ENTIRE existing city just to add ten actors (if swept into
    build()'s own destroy-then-rebuild pass). Call this explicitly,
    once, from a live reflected call against an already-imported
    module. NAMED PLAINLY, not silently worked around: re-importing
    this FILE fresh (a rung.sh run purges and reloads every project
    module) still re-runs build() at the bottom regardless of whether
    this function is also called - that is this file's own existing
    behaviour, unchanged by this addition.

    IDEMPOTENT on its own: destroys any existing POOL_ROAD_* actors
    first, the same discipline build() already holds for its own OWNED
    prefixes, so re-running this never accumulates duplicates.

    NOT VERIFIED BY EXECUTION - this file requires a loaded TestCity
    editor world just to import (the module-level guard a few lines up
    raises SystemExit otherwise), so it cannot be run headless the way
    econrules.py/citytick.py/placement.py are. Written by close pattern
    match against build()'s own proven parcel-pool loop and mk_testcity
    .py's own proven _box() (get_editor_property('static_mesh') is
    directly proven elsewhere in this project, e.g. init_unreal.py's
    _apply_lot_offset; get_editor_property('override_materials') for
    the material read-back below is standard UE, not personally
    confirmed working in THIS project's own Python binding - the one
    real point of uncertainty in this function, named rather than
    hidden, worth a first look when this actually runs."""
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith('POOL_ROAD_'):
            eas.destroy_actor(a)
    cube = unreal.load_asset(_ROAD_CUBE)
    mat = unreal.load_asset(_ROAD_MATERIAL)
    readback = []
    for i in range(ROAD_POOL_SIZE):
        a = eas.spawn_actor_from_object(
            cube, _POOL_GRAVEYARD, unreal.Rotator(0.0, 0.0, 0.0))
        label = 'POOL_ROAD_%02d' % i
        a.set_actor_label(label)
        a.set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)
        mesh_path = mat_path = None
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_material(0, mat)
            sm = c.get_editor_property('static_mesh')
            mesh_path = sm.get_path_name() if sm else None
            overrides = c.get_editor_property('override_materials')
            mat_path = overrides[0].get_path_name() if overrides else None
        readback.append((label, mesh_path, mat_path))

    for label, mesh_path, mat_path in readback:
        print('%s  mesh=%s  material=%s' % (label, mesh_path, mat_path))
    print('road pool: %d dormant POOL_ROAD_NN actors staged at '
          '_POOL_GRAVEYARD, hidden, non-colliding - activation, '
          'transform and reactivation are the driver\'s own job '
          '(Docs/ROAD_BUILD_CONTRACT.md section 5)' % len(readback))
    return readback


build()
