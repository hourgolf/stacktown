"""Parameterised card-model building generator.

Stage 1 was hand-placed. That does not scale to a metropolis, so every building
from here is a PARAMETER SET, not a drawing. Component names carry their
material role as a prefix (Wall_, Glass_, Frame_, ...) so material assignment is
one sweep over the whole level rather than a per-building wiring job - the
pattern the Portland build got right and Stage 1 did not.

Sized against Saved/Stage2/STAGE2_BUDGET.md: at the block hero the 0.4%
threshold is 230 mm, so what earns its place here is MASS - height, plane
breaks, band offsets, canopies. Window furniture is built because it has to
hold at the 19 mm player-zoom threshold, not because it reads from 112 m.
"""
import _path  # noqa: F401 - puts Tools/measure (ue.py) on sys.path
import ue, json, math, random
import paths

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'


def mkactor(name, loc=(0, 0, 0), rot=None):
    x = {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]}}
    if rot:
        x['rotation'] = {'pitch': rot[0], 'yaw': rot[1], 'roll': rot[2]}
    ref = json.loads(ue.tool(S, 'add_to_scene_from_class',
                             {'actor_type': {'refPath': '/Script/Engine.Actor'},
                              'name': name, 'xform': x}))['returnValue']
    ue.tool(A, 'set_label', {'actor': ref, 'label': name})
    return ref


def box(actor, name, x0, x1, y0, y1, z0, z1):
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': abs(x1 - x0), 'y': abs(y1 - y0), 'z': abs(z1 - z0)},
        'local_transform': {'location': {'x': (x0 + x1) / 2.0,
                                         'y': (y0 + y1) / 2.0,
                                         'z': (z0 + z1) / 2.0}}})


def build(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Dispatch on style. ONE generator with more parameters, never a second
    generator - "buildings are parameter sets" is the property HANDOFF.md 4.2
    calls the most important scaling behaviour in this codebase, and a
    genbuild2.py is how you lose it."""
    st = spec.get('style')
    if st == 'modern':
        return build_modern(spec, origin, yaw)
    if st == 'deco':
        return build_deco(spec, origin, yaw)
    if st == 'house':
        return build_house(spec, origin, yaw)
    return build_vernacular(spec, origin, yaw)


def build_vernacular(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """spec x0/width are BLOCK-LOCAL. The block's world placement lives on the
    actor transform, so a block can be dropped anywhere and rotated - which is
    what lets a second block face the first across a street without every
    coordinate being rewritten."""
    """spec keys: name x0 width depth floors gf_h fl_h parapet bays wall
                  canopy(None|projection) setback(None|uu) roof_units seed"""
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    total = GF + F * FH + PAR
    made = 0

    # ---- ground floor -------------------------------------------------------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 6, x0 + W + 6, -12, D * 0.08, 0, 30); made += 1
    pier_w = 52.0
    box(g, 'Wall_PierL', x0, x0 + pier_w, 0, 60, 30, GF - 40); made += 1
    box(g, 'Wall_PierR', x0 + W - pier_w, x0 + W, 0, 60, 30, GF - 40); made += 1
    box(g, 'Wall_Bulkhead', x0 - 4, x0 + W + 4, -8, 60, GF - 40, GF); made += 1
    sx0, sx1 = x0 + pier_w, x0 + W - pier_w
    box(g, 'Glass_Shop', sx0, sx1, 40, 43, 40, GF - 48); made += 1
    box(g, 'Interior_Shop', sx0 - 6, sx1 + 6, 52, 58, 30, GF - 44); made += 1
    for k in range(1, 4):
        mx = sx0 + (sx1 - sx0) * k / 4.0
        box(g, 'Mullion_Shop%d' % k, mx - 3, mx + 3, 34, 41, 40, GF - 48); made += 1
    box(g, 'Frame_ShopSill', sx0, sx1, 34, 44, 30, 40); made += 1

    # ---- upper floors -------------------------------------------------------
    for f in range(F):
        z0 = GF + f * FH
        z1 = z0 + FH
        # upper-floor setback: a plane break, 900 mm, well over the 230 mm bar
        back = spec.get('setback') if (spec.get('setback') and f == F - 1) else 0
        fy = back
        a = mkactor('BLD2_%s_F%d' % (n, f), origin, (0.0, yaw, 0.0))
        bw = (W - pier_w) / float(BAYS)
        for b in range(BAYS + 1):
            px = x0 + b * bw
            box(a, 'Wall_Pier%d' % b, px, px + pier_w, fy, fy + 60, z0, z1 - 34); made += 1
        # band course - primary depth carrier at range, 60 uu proud
        box(a, 'Band_Course', x0 - 8, x0 + W + 8, fy - 8, fy + 58, z1 - 34, z1); made += 1
        for b in range(BAYS):
            wx0 = x0 + b * bw + pier_w
            wx1 = x0 + (b + 1) * bw
            wz0, wz1 = z0 + 62, z1 - 66
            gy = fy + 27                      # 250 mm recess (Stage 0 finding)
            box(a, 'Glass_B%d' % b, wx0 + 6, wx1 - 6, gy, gy + 2, wz0 + 6, wz1 - 6); made += 1
            box(a, 'Interior_B%d' % b, wx0, wx1, gy + 20, gy + 26, wz0, wz1); made += 1
            box(a, 'Frame_B%dL' % b, wx0, wx0 + 6, gy - 8, gy + 2, wz0, wz1); made += 1
            box(a, 'Frame_B%dR' % b, wx1 - 6, wx1, gy - 8, gy + 2, wz0, wz1); made += 1
            box(a, 'Frame_B%dT' % b, wx0, wx1, gy - 8, gy + 2, wz1 - 6, wz1); made += 1
            box(a, 'Frame_B%dS' % b, wx0 - 4, wx1 + 4, gy - 14, gy + 2, wz0 - 6, wz0); made += 1
            made += 0
            mx = (wx0 + wx1) / 2.0
            box(a, 'Mullion_B%dV' % b, mx - 3, mx + 3, gy - 6, gy + 1, wz0, wz1); made += 1
            mz = wz0 + (wz1 - wz0) * 0.62
            box(a, 'Mullion_B%dH' % b, wx0, wx1, gy - 6, gy + 1, mz - 3, mz + 3); made += 1
        # hand-made tolerance: model tolerances, 1-2% of width, not 0.15%
        ue.tool('editor_toolset.toolsets.object.ObjectTools', 'set_properties', {
            'instance': a, 'values': json.dumps({
                'RelativeLocation': {'x': rnd.uniform(-2.2, 2.2) * (W / 100.0),
                                     'y': rnd.uniform(-1.6, 1.6), 'z': 0.0},
                'RelativeRotation': {'pitch': 0.0, 'yaw': rnd.uniform(-0.9, 0.9),
                                     'roll': rnd.uniform(-0.7, 0.7)}})})

    # ---- roof ---------------------------------------------------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    ztop = GF + F * FH
    box(r, 'Wall_ParapetF', x0, x0 + W, -4, 30, ztop, ztop + PAR); made += 1
    box(r, 'Band_ParapetCap', x0 - 8, x0 + W + 8, -14, 40, ztop + PAR, ztop + PAR + 14); made += 1
    box(r, 'Wall_ParapetL', x0, x0 + 26, 30, D, ztop, ztop + PAR - 20); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 26, x0 + W, 30, D, ztop, ztop + PAR - 20); made += 1
    box(r, 'Roof_Deck', x0, x0 + W, 20, D, ztop - 8, ztop); made += 1
    for u in range(spec.get('roof_units', 1)):
        ux = x0 + W * (0.28 + 0.42 * u)
        uw = 150 + rnd.random() * 130          # >= 230 mm, reads at block hero
        box(r, 'Roof_Unit%d' % u, ux, ux + uw, 180 + u * 90, 180 + u * 90 + uw * 0.8,
            ztop, ztop + 60 + rnd.random() * 50); made += 1

    # ---- canopy -------------------------------------------------------------
    if spec.get('canopy'):
        proj = spec['canopy']
        c = mkactor('BLD2_%s_Canopy' % n, origin, (0.0, yaw, 0.0))
        box(c, 'Wall_CanopySlab', x0 - 10, x0 + W + 10, -proj, 8, GF - 26, GF - 10); made += 1
        box(c, 'Accent_CanopyFascia', x0 - 10, x0 + W + 10, -proj - 8, -proj, GF - 40, GF - 4); made += 1
        made += 1
    print('%s: %d boxes, height %d uu' % (n, made, total))
    return total


# ---------------------------------------------------------------------------
# Late-60s / 70s late-modern.
#
# The difference from the vernacular style is RHYTHM AND PROPORTION, not more
# detail. Card wants flat planes and crisp cut edges, which is why this era is
# easier to fake convincingly in card than Main Street is: there is no
# ornament to approximate, only planes to place accurately.
#
#   vertical bay rhythm  ->  continuous horizontal ribbon
#   punched window       ->  glazing set 880 mm behind a proud spandrel band
#   masonry pier         ->  precast fin
#   projecting cornice   ->  flat coping over a shadow gap
#   shopfront in a frame ->  recessed arcade under an overhanging mass
#
# Everything still lands in y 0..60 with the core starting at 62, exactly as
# the vernacular style does, because step_cores3.py depends on that and a
# facade that drifts off it goes hollow.
# ---------------------------------------------------------------------------
ARCADE = 78.0        # ground floor set back under the overhang
SPAND_F = 0.34       # spandrel band as a fraction of floor height
BAND_PROUD = 40.0    # how far the spandrel stands off the facade line
GLAZE_Y = 44.0       # glazing plane: 84 uu / 840 mm of shadow behind the band
# THE DEPTH BUDGET IS 0..60. The core front is at FACADE_BACK+CLEAR = 62, so
# anything past it is inside solid mass: invisible if fully behind, z-FIGHTING
# if it straddles the face. Measured on Tower before this was fixed:
#   Glass_Shop      Y  78..80   INSIDE CORE      -> storefronts read blank
#   Interior_Shop   Y  94..100  INSIDE CORE
#   Interior_Ribbon Y  60..66   STRADDLES FACE   -> windows clipped at range
# The arcade is the one thing allowed past it, and only because step_cores3.py
# now steps the ground band back by ARCADE to make the recess real.
FIN_W = 34.0         # a precast fin, not a mullion: it has to be deep enough
FIN_PROUD = 46.0     # to cast a real shadow across the glass beside it


def build_modern(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    made = 0

    # ---- ground floor: an arcade, not a shopfront -------------------------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 4, x0 + W + 4, ARCADE - 10, D * 0.08, 0, 22); made += 1
    col_w = 64.0
    for b in range(BAYS + 1):
        px = min(x0 + b * (W / float(BAYS)), x0 + W - col_w)
        box(g, 'Wall_Col%d' % b, px, px + col_w, 0, 62, 0, GF); made += 1
    # the soffit is the whole point of an arcade - it is what casts the shadow
    box(g, 'Wall_Soffit', x0 - 4, x0 + W + 4, 0, ARCADE, GF - 14, GF); made += 1
    sx0, sx1 = x0 + col_w, x0 + W - col_w
    box(g, 'Glass_Shop', sx0, sx1, ARCADE, ARCADE + 2, 26, GF - 20); made += 1
    box(g, 'Interior_Shop', sx0 - 6, sx1 + 6, ARCADE + 16, ARCADE + 22, 22, GF - 16); made += 1
    for k in range(1, BAYS * 2):
        mx = sx0 + (sx1 - sx0) * k / float(BAYS * 2)
        box(g, 'Mullion_Shop%d' % k, mx - 3, mx + 3, ARCADE - 5, ARCADE + 1, 26, GF - 20); made += 1

    # ---- upper floors: ribbon behind a proud band -------------------------
    for f in range(F):
        z0 = GF + f * FH
        z1 = z0 + FH
        sp = FH * SPAND_F
        # Only the TOP floor sets back, which is the rule step_cores3.py bands
        # the core on. build_modern ignored `setback` entirely at first, so the
        # core stepped back 140 uu and the facade did not: gap_check2 measured
        # a 142 uu void behind Tower F6. The spec said setback; the geometry
        # has to agree with it.
        fy = (spec.get('setback') or 0.0) if f == F - 1 else 0.0
        a = mkactor('BLD2_%s_F%d' % (n, f), origin, (0.0, yaw, 0.0))
        # spandrel: full width, standing proud. The primary horizontal.
        box(a, 'Band_Spandrel', x0 - 10, x0 + W + 10, fy - BAND_PROUD, fy + 20, z0, z0 + sp); made += 1
        # returns at each end so the band does not read as a floating slab
        box(a, 'Wall_EndL', x0 - 10, x0 + 16, fy - BAND_PROUD, fy + 60, z0, z1); made += 1
        box(a, 'Wall_EndR', x0 + W - 16, x0 + W + 10, fy - BAND_PROUD, fy + 60, z0, z1); made += 1
        gz0, gz1 = z0 + sp, z1
        gx0, gx1 = x0 + 16, x0 + W - 16
        box(a, 'Glass_Ribbon', gx0, gx1, fy + GLAZE_Y, fy + GLAZE_Y + 2, gz0 + 4, gz1 - 4); made += 1
        box(a, 'Interior_Ribbon', gx0, gx1, fy + GLAZE_Y + 8, fy + GLAZE_Y + 14, gz0, gz1); made += 1
        box(a, 'Frame_RibbonS', gx0 - 4, gx1 + 4, fy + GLAZE_Y - 8, fy + GLAZE_Y + 2, gz0, gz0 + 6); made += 1
        box(a, 'Frame_RibbonT', gx0 - 4, gx1 + 4, fy + GLAZE_Y - 8, fy + GLAZE_Y + 2, gz1 - 6, gz1); made += 1
        # precast fins: the vertical rhythm, standing off the glass
        # FEWER fins, standing further off. At BAYS*2 they subdivided the
        # ribbon into six panes and read as window mullions - which is the
        # vernacular rhythm, the exact thing this style is not.
        fins = max(2, BAYS)
        for k in range(1, fins):
            fx = gx0 + (gx1 - gx0) * k / float(fins)
            box(a, 'Wall_Fin%d' % k, fx - FIN_W / 2, fx + FIN_W / 2,
                fy - FIN_PROUD, fy + GLAZE_Y + 2, gz0, gz1); made += 1
        mz = gz0 + (gz1 - gz0) * 0.58
        box(a, 'Mullion_RibbonH', gx0, gx1, fy + GLAZE_Y - 5, fy + GLAZE_Y + 1, mz - 3, mz + 3); made += 1
        # hand tolerance: MODEL tolerances, 1-2%, not building tolerances
        ue.tool('editor_toolset.toolsets.object.ObjectTools', 'set_properties', {
            'instance': a, 'values': json.dumps({
                'RelativeLocation': {'x': rnd.uniform(-2.0, 2.0) * (W / 100.0),
                                     'y': rnd.uniform(-1.4, 1.4), 'z': 0.0},
                'RelativeRotation': {'pitch': 0.0, 'yaw': rnd.uniform(-0.8, 0.8),
                                     'roll': rnd.uniform(-0.6, 0.6)}})})

    # ---- roof: flat coping over a shadow gap, no cornice ------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    ztop = GF + F * FH
    # the gap is recessed BEHIND the facade line, so the coping reads as a
    # separate cut piece rather than a moulding
    box(r, 'Wall_ParapetF', x0, x0 + W, 12, 40, ztop, ztop + PAR - 12); made += 1
    box(r, 'Band_Coping', x0 - 6, x0 + W + 6, -6, 44, ztop + PAR - 12, ztop + PAR); made += 1
    box(r, 'Wall_ParapetL', x0, x0 + 24, 30, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 24, x0 + W, 30, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Roof_Deck', x0, x0 + W, 20, D, ztop - 8, ztop); made += 1
    for u in range(spec.get('roof_units', 1)):
        ux = x0 + W * (0.3 + 0.4 * u)
        uw = 160 + rnd.random() * 120
        box(r, 'Roof_Unit%d' % u, ux, ux + uw, 200 + u * 100, 200 + u * 100 + uw * 0.8,
            ztop, ztop + 55 + rnd.random() * 45); made += 1

    print('%s [modern]: %d boxes, height %d uu' % (n, made, GF + F * FH + PAR))
    return GF + F * FH + PAR


# ---------------------------------------------------------------------------
# Art Deco / 1930s.
#
# Chosen because it is the OPPOSITE of the late-modern block, not a variation
# on it. Modern is horizontal - ribbon glazing behind a proud spandrel band.
# Deco is vertical: unbroken pilasters running from the base to the parapet,
# with the windows recessed into continuous channels between them, so the eye
# is pulled up rather than along. Set beside the vernacular bay rhythm the
# three read as three eras.
#
# It is also flat. Deco ornament is fluting, setbacks and stepped parapets -
# geometry, not moulding - which is exactly what cut card can do.
#
# Same depth budget as every other style: 0..60, core front at 62.
# ---------------------------------------------------------------------------
DECO_PIL_W = 76.0        # pilaster width
DECO_PROUD = 50.0        # how far it stands off the window plane
DECO_GLAZE = 40.0
DECO_FLUTE = 11.0


def build_deco(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    ztop = GF + F * FH
    bw = W / float(BAYS)
    made = 0
    # ONE jitter for the whole building. The other styles jitter each floor
    # independently, which is fine when every floor is a separate plane - but
    # a deco pilaster is a single piece running the full height, and floors
    # sliding under it would tear the shaft apart.
    jx, jy, jr = (rnd.uniform(-2.0, 2.0) * (W / 100.0),
                  rnd.uniform(-1.4, 1.4), rnd.uniform(-0.8, 0.8))

    def jitter(act):
        ue.tool('editor_toolset.toolsets.object.ObjectTools', 'set_properties', {
            'instance': act, 'values': json.dumps({
                'RelativeLocation': {'x': jx, 'y': jy, 'z': 0.0},
                'RelativeRotation': {'pitch': 0.0, 'yaw': jr, 'roll': 0.0}})})

    # ---- base: a heavy horizontal storefront the shaft stands on ----------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 8, x0 + W + 8, -22, D * 0.08, 0, 46); made += 1
    for b in range(BAYS + 1):
        px = min(x0 + b * bw, x0 + W - DECO_PIL_W)
        box(g, 'Wall_BasePier%d' % b, px - 8, px + DECO_PIL_W + 8,
            -DECO_PROUD - 8, 62, 46, GF - 46); made += 1
    box(g, 'Band_BaseCap', x0 - 16, x0 + W + 16, -DECO_PROUD - 16, 62,
        GF - 46, GF - 12); made += 1
    for b in range(BAYS):
        sx0, sx1 = x0 + b * bw + DECO_PIL_W, x0 + (b + 1) * bw
        if sx1 - sx0 < 80: continue
        box(g, 'Glass_Shop%d' % b, sx0, sx1, 34, 36, 58, GF - 52); made += 1
        box(g, 'Interior_Shop%d' % b, sx0 - 6, sx1 + 6, 48, 54, 50, GF - 48); made += 1
        for k in range(1, 3):
            mx = sx0 + (sx1 - sx0) * k / 3.0
            box(g, 'Mullion_Shop%d_%d' % (b, k), mx - 3, mx + 3, 28, 35,
                58, GF - 52); made += 1
    jitter(g)

    # ---- shaft: unbroken pilasters, fluted -------------------------------
    sh = mkactor('BLD2_%s_Shaft' % n, origin, (0.0, yaw, 0.0))
    for b in range(BAYS + 1):
        px = min(x0 + b * bw, x0 + W - DECO_PIL_W)
        box(sh, 'Wall_Pilaster%d' % b, px, px + DECO_PIL_W,
            -DECO_PROUD, 60, GF - 12, ztop + PAR - 26); made += 1
        # Fluting reads as CARVED STONE, so it takes the wall colour (Band_)
        # rather than the saturated Accent_ role. Spandrels take Frame_, the
        # dark metal, which is what sat between deco windows.
        for k in (1, 2):
            fx = px + DECO_PIL_W * k / 3.0
            box(sh, 'Band_Flute%d_%d' % (b, k), fx - DECO_FLUTE/2, fx + DECO_FLUTE/2,
                -DECO_PROUD - 9, -DECO_PROUD + 4, GF - 4, ztop + PAR - 40); made += 1
    jitter(sh)

    # ---- floors: glazing recessed into the channels -----------------------
    for f in range(F):
        z0, z1 = GF + f * FH, GF + (f + 1) * FH
        a = mkactor('BLD2_%s_F%d' % (n, f), origin, (0.0, yaw, 0.0))
        for b in range(BAYS):
            wx0, wx1 = x0 + b * bw + DECO_PIL_W, x0 + (b + 1) * bw
            if wx1 - wx0 < 80: continue
            # spandrel panel between floors, set BACK from the pilaster face
            box(a, 'Frame_Spandrel%d' % b, wx0, wx1, 18, 30, z0, z0 + FH * 0.24); made += 1
            wz0, wz1 = z0 + FH * 0.24, z1
            box(a, 'Glass_B%d' % b, wx0 + 5, wx1 - 5, DECO_GLAZE, DECO_GLAZE + 2,
                wz0 + 5, wz1 - 5); made += 1
            box(a, 'Interior_B%d' % b, wx0, wx1, DECO_GLAZE + 10, DECO_GLAZE + 16,
                wz0, wz1); made += 1
            box(a, 'Frame_B%dL' % b, wx0, wx0 + 5, DECO_GLAZE - 6, DECO_GLAZE + 2,
                wz0, wz1); made += 1
            box(a, 'Frame_B%dR' % b, wx1 - 5, wx1, DECO_GLAZE - 6, DECO_GLAZE + 2,
                wz0, wz1); made += 1
            mx = (wx0 + wx1) / 2.0
            box(a, 'Mullion_B%dV' % b, mx - 3, mx + 3, DECO_GLAZE - 5, DECO_GLAZE + 1,
                wz0, wz1); made += 1
        jitter(a)

    # ---- roof: STEPPED parapet, the deco silhouette -----------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    mid = BAYS // 2
    for b in range(BAYS):
        px0, px1 = x0 + b * bw, x0 + (b + 1) * bw
        step = PAR * (1.9 if b == mid else (1.35 if abs(b - mid) == 1 else 1.0))
        box(r, 'Wall_Parapet%d' % b, px0, px1, -18, 34, ztop, ztop + step); made += 1
        box(r, 'Band_Cap%d' % b, px0 - 8, px1 + 8, -28, 42,
            ztop + step, ztop + step + 16); made += 1
    box(r, 'Wall_ParapetL', x0, x0 + 26, 30, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 26, x0 + W, 30, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Roof_Deck', x0, x0 + W, 20, D, ztop - 8, ztop); made += 1
    for u in range(spec.get('roof_units', 1)):
        ux = x0 + W * (0.3 + 0.4 * u)
        uw = 150 + rnd.random() * 110
        box(r, 'Roof_Unit%d' % u, ux, ux + uw, 210 + u * 95, 210 + u * 95 + uw * 0.8,
            ztop, ztop + 55 + rnd.random() * 40); made += 1
    jitter(r)

    print('%s [deco]: %d boxes, height %d uu' % (n, made, ztop + PAR))
    return ztop + PAR


def build_house(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A house, which is not a small office block.

    Three things make it read as residential rather than as a shrunk commercial
    block, and none of them is the massing. A SETBACK, so the street line is
    garden and fence instead of shopfront. A PITCHED roof, stepped rather than
    sloped because box() is axis-aligned and a card model folds anyway. And the
    GAP: these are detached, so the lot is wider than the house and the space
    between them is the point.

    Detached also means it is self-contained - all four walls are built here, so
    it needs no core behind it and no flank elevation added later.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    GF, FH = spec['gf_h'], spec['fl_h']
    F = spec['floors']                     # storeys ABOVE the ground floor
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))

    GARDEN = 250.0 + rnd.uniform(-20, 20)  # street line to the front wall
    SIDE = 100.0                           # gap to the lot edge, each side
    hx0, hx1 = x0 + SIDE, x0 + W - SIDE
    hy0 = GARDEN
    hy1 = min(D - 60.0, GARDEN + 430.0)
    HW, HD = hx1 - hx0, hy1 - hy0
    eaves = GF + F*FH
    made = 0

    a = mkactor('BLD2_%s_H' % n, origin, (0.0, yaw, 0.0))

    # ---- garden, fence, front walk, drive -----------------------------------
    box(a, 'Grass_Yard', x0 + 12, x0 + W - 12, 8, GARDEN - 4, 0, 10); made += 1
    box(a, 'Kerbing_FenceL', x0 + 8, x0 + W*0.34, 0, 10, 10, 76); made += 1
    box(a, 'Kerbing_FenceR', x0 + W*0.66, x0 + W - 8, 0, 10, 10, 76); made += 1
    for k in range(4):
        px = x0 + 26 + (W - 52)*k/3.0
        box(a, 'Frame_FencePost%d' % k, px - 7, px + 7, -2, 12, 10, 92); made += 1

    # the front walk is a PATH - a centreline and a width - so the porch and the
    # gate are derived from it rather than from three more hand-typed numbers
    cx = (hx0 + hx1)/2.0
    walk = paths.Path((cx, 0.0), (cx, GARDEN + 6.0), 96.0, 'walk')
    wr = walk.rect()
    box(a, 'Ground_Walk', wr[0], wr[2], wr[1], wr[3], 0, 12); made += 1
    dside = 1 if rnd.random() < 0.5 else -1
    dx = x0 + (W - 150.0) if dside > 0 else x0 + 26.0
    box(a, 'Ground_Drive', dx, dx + 124, 0, GARDEN + 40, 0, 11); made += 1

    # ---- body ---------------------------------------------------------------
    box(a, 'Wall_Plinth', hx0 - 10, hx1 + 10, hy0 - 10, hy1 + 10, 0, 26); made += 1
    box(a, 'Wall_Body', hx0, hx1, hy0, hy1, 26, eaves); made += 1

    # ---- porch --------------------------------------------------------------
    pw = 210.0
    box(a, 'Roof_Porch', cx - pw/2 - 20, cx + pw/2 + 20, hy0 - 96, hy0 + 6,
        GF - 34, GF - 16); made += 1
    for sgn in (-1, 1):
        px = cx + sgn*(pw/2 - 8)
        box(a, 'Frame_PorchPost%d' % (sgn + 1), px - 9, px + 9,
            hy0 - 88, hy0 - 70, 26, GF - 34); made += 1
    box(a, 'Frame_Door', cx - 44, cx + 44, hy0 - 4, hy0 + 5, 26, 26 + 150); made += 1
    box(a, 'Interior_Hall', cx - 38, cx + 38, hy0 + 5, hy0 + 12, 30, 26 + 140); made += 1

    # ---- windows: front, and both flanks, because a house is seen from three
    # sides at once and a blank gable is what gave the first block away -------
    def win(tag, ax0, ax1, ay0, ay1, z0, z1, axis):
        """axis 'y' = a window in a wall facing +/-Y; 'x' = facing +/-X."""
        box(a, 'Glass_%s' % tag, ax0, ax1, ay0, ay1, z0, z1)
        if axis == 'y':
            box(a, 'Frame_%sSill' % tag, ax0 - 8, ax1 + 8, ay0 - 6, ay1 + 6, z0 - 10, z0)
            box(a, 'Interior_%s' % tag, ax0 + 4, ax1 - 4,
                ay0 + (7 if ay0 < (hy0 + hy1)/2 else -7),
                ay1 + (7 if ay0 < (hy0 + hy1)/2 else -7), z0 + 4, z1 - 4)
        else:
            box(a, 'Frame_%sSill' % tag, ax0 - 6, ax1 + 6, ay0 - 8, ay1 + 8, z0 - 10, z0)
        return 3 if axis == 'y' else 2

    # front elevation: door bay in the middle, windows either side
    for b in range(BAYS):
        bx = hx0 + 40 + (HW - 80)*(b + 0.5)/BAYS
        if abs(bx - cx) > 70:
            made += win('GF%d' % b, bx - 62, bx + 62, hy0 - 5, hy0 + 3,
                        26 + 62, GF - 34, 'y')
        for f in range(F):
            z0 = GF + f*FH + 44
            made += win('U%d_%d' % (f, b), bx - 56, bx + 56, hy0 - 5, hy0 + 3,
                        z0, z0 + FH - 96, 'y')
    # flanks
    for sgn, side in ((-1, hx0), (1, hx1)):
        for k in range(2):
            wy = hy0 + HD*(0.3 + 0.4*k)
            made += win('S%d_%d' % (sgn + 1, k), side - 4, side + 4,
                        wy - 58, wy + 58, GF + 44, GF + FH - 52, 'x')

    # ---- pitched roof, stepped; the ridge runs along X so the gables show ----
    # 6 steps over a 150 uu rise read as a ziggurat from above rather than as
    # a pitch. 11 steps put each riser under 15 uu, which is below the 0.4%
    # bar at the board camera and reads as a slope.
    steps = 11
    rise = 168.0 + rnd.uniform(-16, 16)
    for i in range(steps):
        t0, t1 = i/float(steps), (i + 1)/float(steps)
        ins = (HD/2.0 - 24.0)*t0
        box(a, 'Roof_Slope%d' % i, hx0 - 34, hx1 + 34,
            hy0 + ins - 34, hy1 - ins + 34,
            eaves + rise*t0, eaves + rise*t1 + 2); made += 1
    box(a, 'Wall_Chimney', hx1 - 120, hx1 - 62, hy0 + HD*0.62, hy0 + HD*0.62 + 58,
        eaves, eaves + rise + 86); made += 1

    print('%s [house]: %d boxes' % (n, made))
    return made
