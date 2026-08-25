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



def _bx(a, nm, axis, p0, p1, u0, u1, z0, z1):
    """box() with the wall's plane axis abstracted, so one window routine can
    serve a front wall and a flank."""
    if axis == 'y':
        box(a, nm, u0, u1, min(p0, p1), max(p0, p1), z0, z1)
    else:
        box(a, nm, min(p0, p1), max(p0, p1), u0, u1, z0, z1)


def window(a, tag, axis, plane, outward, u0, u1, z0, z1, bars=(1, 1)):
    """A recessed window with a frame, a sill and glazing bars.

    The houses and walk-ups were built with a flat pane sitting ON the wall
    plane and a sill under it - three parts - while block A gives every opening
    eight: glass set back 250 mm (the Stage 0 finding), an interior behind it,
    a frame standing 8 uu proud of the glass on three sides, a sill proud
    again, and glazing bars. That difference is the whole of "they don't look
    as finished". Gate A1 wants the recess to read as a shadow line and A2
    wants the sill to have real thickness; a flat pane has neither.

    `outward` is +1 if the exterior face looks along +axis, -1 if it looks back.
    """
    d = -outward                        # into the wall
    g = plane + d*24.0                  # the glass plane
    _bx(a, 'Glass_%s' % tag, axis, g, g + d*2, u0 + 6, u1 - 6, z0 + 6, z1 - 6)
    _bx(a, 'Interior_%s' % tag, axis, g + d*18, g + d*24, u0, u1, z0, z1)
    _bx(a, 'Frame_%sL' % tag, axis, g - d*8, g + d*2, u0, u0 + 6, z0, z1)
    _bx(a, 'Frame_%sR' % tag, axis, g - d*8, g + d*2, u1 - 6, u1, z0, z1)
    _bx(a, 'Frame_%sT' % tag, axis, g - d*8, g + d*2, u0, u1, z1 - 6, z1)
    _bx(a, 'Frame_%sS' % tag, axis, g - d*16, g + d*2, u0 - 5, u1 + 5, z0 - 9, z0)
    n = 6
    for k in range(1, bars[0] + 1):
        m = u0 + (u1 - u0)*k/(bars[0] + 1.0)
        _bx(a, 'Mullion_%sV%d' % (tag, k), axis, g - d*6, g + d*1,
            m - 3, m + 3, z0, z1); n += 1
    for k in range(1, bars[1] + 1):
        mz = z0 + (z1 - z0)*k/(bars[1] + 1.0)
        _bx(a, 'Mullion_%sH%d' % (tag, k), axis, g - d*6, g + d*1,
            u0, u1, mz - 3, mz + 3); n += 1
    return n


def slab(actor, name, cx, cy, cz, sx, sy, sz, pitch=0.0, roll=0.0, yaw=0.0):
    """A box with a ROTATION. add_cube honours a rotation in its local
    transform - measured, the component reads back what it was given - which
    box() never passed, so every roof in this project was a stack of treads.
    Eleven risers over a 168 uu rise reads as terracing from the pavement."""
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': sx, 'y': sy, 'z': sz},
        'local_transform': {'location': {'x': cx, 'y': cy, 'z': cz},
                            'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': roll}}})


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
    if st == 'walkup':
        return build_walkup(spec, origin, yaw)
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

    # VARIANTS. Five houses from one generator were five colours of the same
    # house, which is the thing "buildings are parameter sets" is supposed to
    # avoid. These are the differences that actually read from the street: what
    # the roof does at the top, what the front door does at the bottom, and
    # whether the elevation is flat or broken.
    roof_kind = spec.get('roof', rnd.choice(('gable', 'crossgable', 'gable')))
    entry = spec.get('entry', rnd.choice(('porch', 'stoop')))
    dormers = spec.get('dormers', rnd.choice((0, 0, 2)))
    bay = spec.get('bay', rnd.random() < 0.45)
    garage = spec.get('garage', rnd.random() < 0.4)

    GARDEN = 250.0 + rnd.uniform(-20, 20)  # street line to the front wall
    SIDE = 100.0                           # gap to the lot edge, each side
    hx0, hx1 = x0 + SIDE, x0 + W - SIDE
    hy0 = GARDEN
    hy1 = min(D - 60.0, GARDEN + 430.0)
    HW, HD = hx1 - hx0, hy1 - hy0
    eaves = GF + F*FH
    made = 0

    a = mkactor('BLD2_%s_H' % n, origin, (0.0, yaw, 0.0))

    # ---- gardens, fences, front walk, drive ---------------------------------
    # which side the drive takes is decided first, because the shed goes in the
    # back corner the drive does not use
    dside = 1 if rnd.random() < 0.5 else -1
    dx = x0 + (W - 150.0) if dside > 0 else x0 + 26.0
    box(a, 'Grass_Yard', x0 + 12, x0 + W - 12, 8, GARDEN - 4, 0, 10); made += 1
    # THE BACK GARDEN. A house with nothing behind it is a facade with a roof;
    # from any camera that is not square to the street the rear reads, and
    # these had bare walls and bare ground.
    by0, by1 = hy1 + 10.0, D - 12.0
    if by1 - by0 > 200.0:
        box(a, 'Grass_Back', x0 + 12, x0 + W - 12, by0, by1, 0, 10); made += 1
        box(a, 'Ground_Patio', hx0 + 30, hx1 - 30, by0, by0 + 130, 0, 13); made += 1
        for sgn, fx in ((-1.0, x0 + 8), (1.0, x0 + W - 8)):
            box(a, 'Kerbing_SideFence%d' % (int(sgn) + 1), fx - 7, fx + 7,
                GARDEN - 20, by1, 8, 78); made += 1
        box(a, 'Kerbing_BackFence', x0 + 8, x0 + W - 8, by1 - 10, by1, 8, 84)
        made += 2
        # THINGS PEOPLE PUT IN A GARDEN. An empty fenced rectangle of grass
        # reads as a site, not a home. None of this is large; all of it is what
        # the eye uses to tell one back garden from the next.
        gcx = (x0 + W)/2.0
        if rnd.random() < 0.62:                       # a swing set
            sw = x0 + 120.0 if dside > 0 else x0 + W - 320.0
            for k in (0, 1):
                for sgn2 in (-1, 1):
                    box(a, 'Frame_SwingLeg%d%d' % (k, sgn2 + 1),
                        sw + k*190 - 8, sw + k*190 + 8,
                        by0 + 150 + sgn2*54, by0 + 150 + sgn2*54 + 12, 0, 150)
            box(a, 'Frame_SwingBar', sw - 14, sw + 204, by0 + 144, by0 + 156, 142, 154)
            for k in (0, 1):
                box(a, 'Frame_SwingSeat%d' % k, sw + 40 + k*90, sw + 96 + k*90,
                    by0 + 140, by0 + 160, 52, 60)
            made += 7
        elif rnd.random() < 0.5:                      # a putting green
            box(a, 'Grass_Putt', gcx - 170, gcx + 170, by0 + 120, by0 + 380, 10, 16)
            box(a, 'Frame_PuttFlag', gcx + 96, gcx + 104, by0 + 244, by0 + 252, 16, 120)
            box(a, 'Accent_PuttFlag', gcx + 104, gcx + 160, by0 + 246, by0 + 250, 96, 120)
            made += 3
        # a raised bed along one fence, always
        bs = x0 + 30.0 if dside > 0 else x0 + W - 250.0
        box(a, 'Kerbing_Bed', bs, bs + 220, by0 + 60, by1 - 240, 10, 46)
        box(a, 'Grass_Bed', bs + 14, bs + 206, by0 + 74, by1 - 254, 10, 54)
        # a washing line
        for sgn2 in (-1, 1):
            px2 = gcx + sgn2*200.0
            box(a, 'Frame_LinePost%d' % (sgn2 + 1), px2 - 7, px2 + 7,
                by1 - 300, by1 - 286, 10, 170)
        box(a, 'Frame_Line', gcx - 200, gcx + 200, by1 - 295, by1 - 291, 160, 164)
        made += 5

        # a shed in the corner the drive does not use
        sx_ = x0 + W - 250.0 if dside < 0 else x0 + 60.0
        box(a, 'Wall_Shed', sx_, sx_ + 190, by1 - 190, by1 - 24, 0, 150); made += 1
        box(a, 'Tile_Shed', sx_ - 12, sx_ + 202, by1 - 202, by1 - 12, 150, 166)
        box(a, 'Frame_ShedDoor', sx_ + 40, sx_ + 150, by1 - 196, by1 - 188, 8, 128)
        made += 2
        for k in range(3):
            px = x0 + 120.0 + (W - 240.0)*k/2.0
            box(a, 'Frame_BackPost%d' % k, px - 6, px + 6, by1 - 12, by1 + 2,
                8, 96); made += 1
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
    box(a, 'Ground_Drive', dx, dx + 124, 0, GARDEN + 40, 0, 11); made += 1

    # ---- body ---------------------------------------------------------------
    box(a, 'Wall_Plinth', hx0 - 10, hx1 + 10, hy0 - 10, hy1 + 10, 0, 26); made += 1
    box(a, 'Wall_Body', hx0, hx1, hy0, hy1, 26, eaves); made += 1

    # ---- the way the front door meets the ground ----------------------------
    if entry == 'porch':
        pw = 210.0
        box(a, 'Roof_Porch', cx - pw/2 - 20, cx + pw/2 + 20, hy0 - 96, hy0 + 6,
            GF - 34, GF - 16); made += 1
        for sgn in (-1, 1):
            px = cx + sgn*(pw/2 - 8)
            box(a, 'Frame_PorchPost%d' % (sgn + 1), px - 9, px + 9,
                hy0 - 88, hy0 - 70, 26, GF - 34); made += 1
        box(a, 'Ground_PorchDeck', cx - pw/2 - 14, cx + pw/2 + 14,
            hy0 - 92, hy0, 14, 26); made += 1
    else:
        # a stoop: three steps up to the door and a small hood over it
        for i in range(3):
            box(a, 'Ground_Stoop%d' % i, cx - 78 + i*6, cx + 78 - i*6,
                hy0 - 72 + i*22, hy0, 0, 10 + i*8); made += 1
        box(a, 'Roof_Hood', cx - 76, cx + 76, hy0 - 54, hy0 + 4,
            26 + 158, 26 + 178); made += 1
    box(a, 'Frame_Door', cx - 44, cx + 44, hy0 - 4, hy0 + 5, 26, 26 + 150); made += 1
    box(a, 'Interior_Hall', cx - 38, cx + 38, hy0 + 5, hy0 + 12, 30, 26 + 140); made += 1

    # ---- windows: front, and both flanks, because a house is seen from three
    # sides at once and a blank gable is what gave the first block away -------
    # front elevation: door bay in the middle, windows either side
    for b in range(BAYS):
        bx = hx0 + 40 + (HW - 80)*(b + 0.5)/BAYS
        if abs(bx - cx) > 70:
            made += window(a, 'GF%d' % b, 'y', hy0, -1.0, bx - 62, bx + 62,
                           26 + 62, GF - 34, bars=(1, 1))
        for f in range(F):
            z0 = GF + f*FH + 44
            made += window(a, 'U%d_%d' % (f, b), 'y', hy0, -1.0,
                           bx - 56, bx + 56, z0, z0 + FH - 96, bars=(1, 1))
    # flanks
    for sgn, side in ((-1.0, hx0), (1.0, hx1)):
        for k in range(2):
            wy = hy0 + HD*(0.3 + 0.4*k)
            made += window(a, 'S%d_%d' % (int(sgn) + 1, k), 'x', side, sgn,
                           wy - 58, wy + 58, GF + 44, GF + FH - 52, bars=(1, 0))

    # ---- rear elevation ------------------------------------------------------
    for b in range(2):
        rx = hx0 + 40 + (HW - 80)*(b + 0.5)/2.0
        made += window(a, 'R0_%d' % b, 'y', hy1, 1.0, rx - 58, rx + 58,
                       26 + 66, GF - 40, bars=(1, 1))
        for f in range(F):
            z0 = GF + f*FH + 44
            made += window(a, 'R%d_%d' % (f + 1, b), 'y', hy1, 1.0,
                           rx - 52, rx + 52, z0, z0 + FH - 96, bars=(1, 1))
    bd = (hx0 + hx1)/2.0
    box(a, 'Frame_BackDoor', bd - 40, bd + 40, hy1 - 5, hy1 + 4, 26, 26 + 146)
    box(a, 'Roof_BackHood', bd - 62, bd + 62, hy1 - 4, hy1 + 54,
        26 + 150, 26 + 166)
    made += 2

    # ---- trim: the small parts that separate a model from a massing study ---
    # A fascia is a BAND round the eaves. This was a solid box spanning the
    # whole plan at eaves height - a flat slab under the pitched roof, which is
    # what made the roofs read as inverted and as "a flat roof laid on top of a
    # pitched one". Four thin bands, not a lid.
    for tag, fx0, fy0, fx1, fy1 in (
            ('F', hx0 - 30, hy0 - 30, hx1 + 30, hy0 - 12),
            ('B', hx0 - 30, hy1 + 12, hx1 + 30, hy1 + 30),
            ('L', hx0 - 30, hy0 - 30, hx0 - 12, hy1 + 30),
            ('R', hx1 + 12, hy0 - 30, hx1 + 30, hy1 + 30)):
        box(a, 'Frame_Fascia%s' % tag, fx0, fx1, fy0, fy1,
            eaves - 16, eaves + 4); made += 1
    box(a, 'Frame_Gutter', hx0 - 34, hx1 + 34, hy0 - 34, hy0 - 22,
        eaves - 14, eaves - 2); made += 1
    box(a, 'Frame_Downpipe', hx1 - 22, hx1 - 8, hy0 - 20, hy0 - 6,
        26, eaves - 12); made += 1
    for cxn, cx_ in (('L', hx0), ('R', hx1)):
        box(a, 'Frame_Corner%sF' % cxn, cx_ - 9, cx_ + 9, hy0 - 6, hy0 + 4,
            26, eaves); made += 1
        box(a, 'Frame_Corner%sB' % cxn, cx_ - 9, cx_ + 9, hy1 - 4, hy1 + 6,
            26, eaves); made += 1
    box(a, 'Frame_Threshold', cx - 52, cx + 52, hy0 - 16, hy0 + 4, 20, 30); made += 1
    box(a, 'Glass_Fanlight', cx - 36, cx + 36, hy0 + 2, hy0 + 6,
        26 + 152, 26 + 172); made += 1
    made += 4

    # ---- a bay window, which is what breaks a flat cottage elevation --------
    if bay:
        bside = -1 if entry == 'porch' else 1
        bx = cx + bside*(HW*0.28)
        box(a, 'Wall_Bay', bx - 96, bx + 96, hy0 - 86, hy0 + 6, 20, GF - 30); made += 1
        box(a, 'Glass_Bay', bx - 82, bx + 82, hy0 - 90, hy0 - 84, 26 + 60, GF - 52); made += 1
        for sgn in (-1, 1):
            box(a, 'Glass_BayS%d' % (sgn + 1), bx + sgn*90, bx + sgn*96,
                hy0 - 80, hy0 - 10, 26 + 60, GF - 52); made += 1
        box(a, 'Roof_Bay', bx - 104, bx + 104, hy0 - 94, hy0 + 6,
            GF - 30, GF - 14); made += 1
        made += 4

    # ---- a garage, set back from the house front so it does not lead --------
    if garage:
        gw = 190.0
        gx = dx + 62.0 - gw/2.0
        box(a, 'Wall_Garage', gx, gx + gw, hy0 + 40, hy0 + 230, 0, 190); made += 1
        box(a, 'Frame_GarageDoor', gx + 14, gx + gw - 14, hy0 + 34, hy0 + 42,
            8, 168); made += 1
        box(a, 'Roof_Garage', gx - 16, gx + gw + 16, hy0 + 26, hy0 + 240,
            190, 210); made += 1

    # ---- pitched roof, actually pitched --------------------------------------
    # Two rotated slabs meeting at a ridge. The HIP that used to live here was
    # wrong: a hip's main slopes are trapezoids and its ends are triangles, and
    # a box is neither, so it came out as four full-size slabs overlapping in
    # the middle - which is the "flat roof laid on top of a pitched roof" in
    # the frames. Variety comes from which way the RIDGE runs instead, which is
    # a real difference a street reads: gable to the side, or gable to the
    # street.
    OV = 34.0
    rise = 168.0 + rnd.uniform(-16, 16)
    ey0, ey1 = hy0 - OV, hy1 + OV
    ex0, ex1 = hx0 - OV, hx1 + OV
    street_gable = (roof_kind == 'crossgable')

    if street_gable:
        ridge = (ex0 + ex1)/2.0
        run = ridge - ex0
        ang = math.degrees(math.atan2(rise, run))
        for sgn in (-1.0, 1.0):
            slab(a, 'Tile_Slope%d' % (int(sgn) + 1), ridge + sgn*run/2.0,
                 (ey0 + ey1)/2.0, eaves + rise/2.0,
                 # sign mirrors the roll used for a ridge along X; the first
                 # version had it the other way and the roof came out as a
                 # valley - two slopes meeting in a V instead of at a ridge
                 math.hypot(run, rise), ey1 - ey0, 18.0, pitch=-sgn*ang)
            made += 1
        for sgn, ey_ in ((-1.0, hy0), (1.0, hy1)):
            for i in range(7):
                t0, t1 = i/7.0, (i + 1)/7.0
                box(a, 'Wall_Gable%d_%d' % (int(sgn) + 1, i),
                    ex0 + run*t1, ex1 - run*t1, ey_ - 10, ey_ + 10,
                    eaves + rise*t0, eaves + rise*t1)
                made += 1
    else:
        ridge = (ey0 + ey1)/2.0
        run = ridge - ey0
        ang = math.degrees(math.atan2(rise, run))
        for sgn, tag in ((-1.0, 'F'), (1.0, 'B')):
            slab(a, 'Tile_Slope%s' % tag, (hx0 + hx1)/2.0, ridge + sgn*run/2.0,
                 eaves + rise/2.0, (hx1 - hx0) + 2*OV,
                 # MEASURED, not reasoned: a positive roll takes +Y DOWN, so
                 # the slope whose +Y end is the ridge needs a NEGATIVE roll.
                 # This was -sgn*ang and every side-gabled roof was a valley.
                 math.hypot(run, rise), 18.0, roll=sgn*ang)
            made += 1
        for sgn, hx_ in ((-1.0, hx0), (1.0, hx1)):
            for i in range(7):
                t0, t1 = i/7.0, (i + 1)/7.0
                # the step's top must land ON the slope, not above it: take
                # the NEXT station's footprint, or each corner pokes through
                # and the ridge shows as a dashed line
                box(a, 'Wall_Gable%d_%d' % (int(sgn) + 1, i),
                    hx_ - 10, hx_ + 10, ey0 + run*t1, ey1 - run*t1,
                    eaves + rise*t0, eaves + rise*t1)
                made += 1

    # Dormers: SHED dormers, with their own sloped cap. The old ones were a
    # box with a flat plate on top, sitting on a pitched slope - which is
    # exactly the "flat roof on a pitched roof" that reads as broken. Only on a
    # side-gabled roof: a street-facing gable has no front slope to sit in.
    if dormers and not street_gable:
        dh = rise*0.52
        dd = run*0.46
        dang = math.degrees(math.atan2(dh*0.34, dd))
        for d in range(dormers):
            dxc = hx0 + HW*(0.3 + 0.4*d)
            dz = eaves + rise*0.10
            box(a, 'Wall_DormerC%dL' % d, dxc - 66, dxc - 52,
                hy0 - 8, hy0 - 8 + dd, dz, dz + dh); made += 1
            box(a, 'Wall_DormerC%dR' % d, dxc + 52, dxc + 66,
                hy0 - 8, hy0 - 8 + dd, dz, dz + dh); made += 1
            box(a, 'Wall_DormerF%d' % d, dxc - 66, dxc + 66,
                hy0 - 12, hy0 - 4, dz, dz + dh); made += 1
            made += window(a, 'Dm%d' % d, 'y', hy0 - 8, -1.0,
                           dxc - 48, dxc + 48, dz + 26, dz + dh - 22, bars=(1, 0))
            slab(a, 'Tile_Dormer%d' % d, dxc, hy0 - 14 + dd/2.0,
                 dz + dh + dh*0.17, 148.0, math.hypot(dd, dh*0.34), 12.0,
                 roll=-dang)
            made += 1

    box(a, 'Wall_Chimney', hx1 - 120, hx1 - 62, hy0 + HD*0.62, hy0 + HD*0.62 + 58,
        eaves, eaves + rise + 86); made += 1

    print('%s [house %s/%s%s%s%s]: %d boxes'
          % (n, roof_kind, entry, ' bay' if bay else '',
             ' %ddormer' % dormers if dormers else '',
             ' garage' if garage else '', made))
    return made


def build_walkup(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A small walk-up apartment block: the step between a house and a block.

    It is not a short office block and it is not a wide house. What makes it
    read as apartments is REPETITION with a single front door - the same window
    and the same balcony stacked three high, one stoop on the street, and a
    forecourt too small to be a garden. Setback is shallower than a house's,
    because a walk-up sits closer to the pavement than a cottage does.

    Detached like the houses, so it builds all four of its own walls.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    GF, FH, PAR = spec['gf_h'], spec['fl_h'], spec['parapet']
    F = spec['floors']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))

    FORE = 130.0 + rnd.uniform(-14, 14)
    SIDE = 70.0
    hx0, hx1 = x0 + SIDE, x0 + W - SIDE
    hy0 = FORE
    hy1 = min(D - 60.0, FORE + 520.0)
    HW = hx1 - hx0
    top = GF + F*FH
    made = 0

    a = mkactor('BLD2_%s_A' % n, origin, (0.0, yaw, 0.0))
    cx = (hx0 + hx1)/2.0

    # ---- forecourt: a low wall and a path, not a garden ---------------------
    box(a, 'Ground_Fore', x0 + 10, x0 + W - 10, 8, FORE - 4, 0, 12); made += 1
    box(a, 'Kerbing_Wall', x0 + 8, x0 + W - 8, 0, 16, 12, 62); made += 1
    walk = paths.Path((cx, 0.0), (cx, FORE + 6.0), 130.0, 'walk')
    wr = walk.rect()
    box(a, 'Ground_Walk', wr[0], wr[2], wr[1], wr[3], 0, 14); made += 1

    # ---- body ---------------------------------------------------------------
    box(a, 'Wall_Plinth', hx0 - 12, hx1 + 12, hy0 - 12, hy1 + 12, 0, 34); made += 1
    box(a, 'Wall_Body', hx0, hx1, hy0, hy1, 34, top); made += 1
    box(a, 'Wall_Parapet', hx0 - 10, hx1 + 10, hy0 - 10, hy1 + 10,
        top, top + PAR); made += 1
    box(a, 'Roof_Cap', hx0 - 14, hx1 + 14, hy0 - 14, hy1 + 14,
        top + PAR, top + PAR + 10); made += 1

    # ---- one front door, on a stoop -----------------------------------------
    for i in range(3):
        box(a, 'Ground_Stoop%d' % i, cx - 96 + i*8, cx + 96 - i*8,
            hy0 - 78 + i*24, hy0, 0, 12 + i*8); made += 1
    box(a, 'Frame_Door', cx - 62, cx + 62, hy0 - 6, hy0 + 6, 34, 34 + 170); made += 1
    box(a, 'Interior_Lobby', cx - 54, cx + 54, hy0 + 6, hy0 + 14, 40, 34 + 158); made += 1
    box(a, 'Roof_Canopy', cx - 108, cx + 108, hy0 - 84, hy0 + 6,
        34 + 178, 34 + 200); made += 1

    # ---- the stack: same window, same balcony, three high -------------------
    for f in range(F + 1):
        z0 = 34 + (GF - 34 if f else 0) + max(0, f - 1)*FH
        z0 = GF + (f - 1)*FH if f else 34
        h = (GF - 34) if f == 0 else FH
        for b in range(BAYS):
            bx = hx0 + 44 + (HW - 88)*(b + 0.5)/BAYS
            if f == 0 and abs(bx - cx) < 96:
                continue                       # the door takes the middle bay
            wz0 = z0 + (54 if f else 62)
            wz1 = z0 + h - (46 if f else 40)
            made += window(a, 'W%d_%d' % (f, b), 'y', hy0, -1.0,
                           bx - 62, bx + 62, wz0, wz1, bars=(1, 1))
            if f > 0 and b % 2 == 0:
                # A BALCONY, not a shelf. The old one was a slab with a solid
                # panel in front of it, which from any distance reads as a
                # canopy. What says balcony is the RAILING: a top rail with
                # light showing between uprights, and a door behind it.
                bw2, bp = 96.0, 104.0
                box(a, 'Ground_Balc%d_%d' % (f, b), bx - bw2, bx + bw2,
                    hy0 - bp, hy0 + 2, wz0 - 26, wz0 - 12); made += 1
                for e2, ex2 in (('L', bx - bw2), ('R', bx + bw2)):
                    box(a, 'Frame_BalcEnd%d_%d%s' % (f, b, e2), ex2 - 7, ex2 + 7,
                        hy0 - bp, hy0 + 2, wz0 - 12, wz0 + 84); made += 1
                box(a, 'Frame_BalcRail%d_%d' % (f, b), bx - bw2 - 4, bx + bw2 + 4,
                    hy0 - bp - 4, hy0 - bp + 8, wz0 + 72, wz0 + 84); made += 1
                for u in range(5):
                    ux = bx - bw2 + 2*bw2*(u + 0.5)/5.0
                    box(a, 'Mullion_Balust%d_%d_%d' % (f, b, u), ux - 4, ux + 4,
                        hy0 - bp - 1, hy0 - bp + 6, wz0 - 12, wz0 + 74); made += 1
                box(a, 'Frame_BalcDoor%d_%d' % (f, b), bx - 40, bx + 40,
                    hy0 - 6, hy0 + 3, wz0 - 12, wz0 + 118); made += 1
    # flank windows, because a detached block is seen from three sides
    for sgn, side in ((-1, hx0), (1, hx1)):
        for f in range(F + 1):
            z0 = GF + (f - 1)*FH if f else 34
            h = (GF - 34) if f == 0 else FH
            for k in range(2):
                wy = hy0 + (hy1 - hy0)*(0.32 + 0.36*k)
                made += window(a, 'S%d_%d_%d' % (sgn + 1, f, k), 'x', side,
                               float(sgn), wy - 54, wy + 54,
                               z0 + 58, z0 + h - 46, bars=(1, 0))

    # ---- trim: a cornice, a string course at each floor, a downpipe ---------
    box(a, 'Band_Cornice', hx0 - 16, hx1 + 16, hy0 - 16, hy1 + 16,
        top - 26, top); made += 1
    for f in range(1, F + 1):
        zc = GF + (f - 1)*FH
        box(a, 'Band_String%d' % f, hx0 - 9, hx1 + 9, hy0 - 9, hy0 + 4,
            zc - 12, zc); made += 1
    box(a, 'Frame_Downpipe', hx1 - 26, hx1 - 10, hy0 - 22, hy0 - 6,
        34, top - 20); made += 1
    for cxn, cx_ in (('L', hx0), ('R', hx1)):
        box(a, 'Frame_Corner%s' % cxn, cx_ - 10, cx_ + 10, hy0 - 6, hy0 + 4,
            34, top); made += 1
    box(a, 'Frame_Threshold', cx - 70, cx + 70, hy0 - 18, hy0 + 4, 26, 38); made += 1
    made += 3

    # ---- rear yard and rear elevation ---------------------------------------
    by0, by1 = hy1 + 10.0, D - 12.0
    if by1 - by0 > 200.0:
        box(a, 'Ground_Yard', x0 + 10, x0 + W - 10, by0, by1, 0, 12); made += 1
        box(a, 'Kerbing_YardWall', x0 + 8, x0 + W - 8, by1 - 12, by1, 12, 96)
        for sgn, fx in ((-1.0, x0 + 8), (1.0, x0 + W - 8)):
            box(a, 'Kerbing_YardSide%d' % (int(sgn) + 1), fx - 7, fx + 7,
                by0 - 40, by1, 12, 96); made += 1
        # bin store: every block of flats has one and it is always by the back
        box(a, 'Wall_BinStore', x0 + 70, x0 + 350, by1 - 200, by1 - 30, 0, 130)
        box(a, 'Roof_BinStore', x0 + 58, x0 + 362, by1 - 212, by1 - 18, 130, 144)
        box(a, 'Ground_Bins', x0 + 400, x0 + 640, by1 - 150, by1 - 40, 0, 96)
        # a yard people use: a drying area, a bench, a strip of planting and a
        # couple of parking bays off the back lane
        for sgn2 in (-1, 1):
            px2 = (x0 + W)/2.0 + sgn2*220.0
            box(a, 'Frame_LinePost%d' % (sgn2 + 1), px2 - 7, px2 + 7,
                by0 + 150, by0 + 164, 12, 180); made += 1
        box(a, 'Frame_Line', (x0 + W)/2.0 - 220, (x0 + W)/2.0 + 220,
            by0 + 155, by0 + 159, 170, 174)
        box(a, 'Kerbing_YardBed', x0 + W - 330, x0 + W - 40, by0 + 40, by1 - 260, 12, 48)
        box(a, 'Grass_YardBed', x0 + W - 316, x0 + W - 54, by0 + 54, by1 - 274, 12, 56)
        for k in range(2):
            bxp = x0 + 700.0 + k*260.0
            box(a, 'Ground_Bay%d' % k, bxp, bxp + 230, by1 - 300, by1 - 40, 12, 15)
            made += 1
        made += 7
    for f in range(F + 1):
        z0 = GF + (f - 1)*FH if f else 34
        h = (GF - 34) if f == 0 else FH
        for b in range(2):
            rx = hx0 + 60 + (HW - 120)*(b + 0.5)/2.0
            made += window(a, 'RR%d_%d' % (f, b), 'y', hy1, 1.0,
                           rx - 58, rx + 58, z0 + 58, z0 + h - 46, bars=(1, 1))
    box(a, 'Frame_RearStair', hx1 - 150, hx1 - 30, hy1 - 4, hy1 + 120, 34, top)
    box(a, 'Frame_BackDoor', cx - 44, cx + 44, hy1 - 5, hy1 + 5, 34, 34 + 160)
    made += 2

    box(a, 'Roof_Stair', cx - 110, cx + 110, hy1 - 210, hy1 - 40,
        top + PAR, top + PAR + 120); made += 1

    print('%s [walkup %dst]: %d boxes' % (n, F + 1, made))
    return made
