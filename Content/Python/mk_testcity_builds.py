"""Replace the test city's placeholder masses with REAL baked buildings.

RUN THROUGH rung.sh - it mutates. TestCity only. Idempotent.

WHY THE FIRST PLACEMENT WAS BOXES. citylayout's block length was 4800,
chosen because it divided by six. The catalogue's widths are 820 / 1230 /
1640 / 2050 / 2460 - all multiples of 410 - so 4800 gave 800 uu lots and
NOTHING IN THE CATALOGUE FITS AN 800 UU LOT. The boxes were not a staging
decision, they were the only thing that could stand there. BLOCK_LEN is now
4920 (410 x 12), lots are 820, and citylayout's LOTS-ARE-CATALOGUE-WIDTHS
test fails if that ever drifts again.

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
import palette
import recipes
import citylayout as L

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


def catalogue_at(width):
    """Every (recipe, tier) whose baked mesh exists at this width."""
    out = []
    for rid in sorted(recipes.RECIPES):
        if width not in [round(w) for w in recipes.widths(rid)]:
            continue
        for t in range(recipes.tier_count(rid)):
            if eal.does_asset_exist('%s/%s'
                                    % (BAKED, recipes.asset_name(rid, t, width))):
                out.append((rid, t))
    return out


def repaint(actor, sm, rid, scheme):
    """street.py's repaint, reused - slot names come from the recipe base."""
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
    if not (L.parcelmeta.selftests(verbose=False) and L.selftests(verbose=False)):
        raise SystemExit('layout self-tests failed - placing nothing')
    stock = {}
    for b in L.blocks():
        for _k, lx0, lx1, _c in L.lots(b):
            w = round(lx1 - lx0)
            if w not in stock:
                stock[w] = catalogue_at(w)
                if not stock[w]:
                    raise SystemExit('no baked catalogue at width %d' % w)
    print('catalogue: %s'
          % ', '.join('w%d:%d' % (w, len(v)) for w, v in sorted(stock.items())))

    killed = 0
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith(('TC_Mass', 'TC_Bld')):
            eas.destroy_actor(a)
            killed += 1

    rnd = random.Random(SEED)
    made, missing = 0, []
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
            rid, t = rnd.choice(stock[w])
            # A CORNER PARCEL ASKS FOR THE CORNER ASSET. Handed by which side
            # of the block meets the crossing, and deep so the flank is a full
            # elevation on the cross street rather than a stub two thirds of
            # the way along it. Every draw is made from the SAME rnd sequence
            # whether or not the lot is a corner, so adding corners does not
            # reshuffle the rest of the city.
            if corner:
                asset = recipes.asset_name(rid, t, w,
                                           depth=recipes.DEPTH_CORNER,
                                           corner=turn_side)
            else:
                asset = recipes.asset_name(rid, t, w)
            sm = eal.load_asset('%s/%s' % (BAKED, asset))
            # DRAW EVERYTHING BEFORE THE EXISTENCE CHECK. These two draws
            # sat AFTER it, so a `continue` on a missing asset consumed
            # fewer random numbers and shifted every later lot - meaning the
            # city depended on WHICH ASSETS HAPPENED TO BE BAKED. Each
            # on-demand bake changed the draws for everything after it, so
            # the missing list moved every run and never converged. SEED
            # promises the same city every time, not the same city per bake
            # state.
            gap_draw = rnd.uniform(*GAPS)
            back = rnd.choice((0.0, 0.0, rnd.uniform(*SETBACK),
                               rnd.uniform(*SETBACK)))
            if not sm:
                missing.append(asset)
                continue
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
            # intent the ranges encode.
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
                unreal.StaticMeshActor, unreal.Vector(px, face, Z),
                unreal.Rotator(0.0, 0.0, yaw))       # ROLL, PITCH, YAW
            a.set_actor_label('TC_Bld_%s_%s_t%d' % (key, rid, t))
            a.static_mesh_component.set_editor_property('static_mesh', sm)
            # PER-PARCEL PAINT, street.py's rule. The palette is keyed on the
            # PARCEL, not the recipe, so two of the same building are
            # different colours. Without this every mesh takes its bake
            # defaults and a street of 24 buildings comes out one flat brown -
            # which is exactly how the first placement looked.
            if corner:
                corners_placed += 1
            repaint(a, sm, rid, palette.scheme_for(key, rid))
            o, e = a.get_actor_bounds(False)
            prev_end = o.x + e.x
            made += 1
    print('cleared %d placeholder(s); placed %d real buildings (%d corner)'
          % (killed, made, corners_placed))
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
    if missing:
        print('MISSING %d: %s' % (len(missing), sorted(set(missing))[:4]))
    return made


build()
