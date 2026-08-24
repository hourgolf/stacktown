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
import ue, json, math, random

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
