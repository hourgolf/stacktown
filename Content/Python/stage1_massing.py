"""Stage 1 - one building. Massing + stacked paper bands + facade.

Design basis (measured, not guessed): at Stage 1 framing the camera sits ~95 m
back (0.671 px/uu vs Stage 0's 2.616). A 250 mm window recess reads only 3.5 px
there, so per-window recess CANNOT carry the reveal at building scale. Depth is
carried by metre-scale features instead - stacked floor bands proud 600-700 mm
(8-10 px) and a 1.5 m canopy (21 px) - which is exactly how the paper-model
reference works. Windows are still real openings with glazing set behind, so
gate A1 stays honest.

Scale 1 uu = 1 cm. Street face is -Y. Bays reuse the Stage 0 3600 mm module.
"""
import ue, json

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
OWNED = ('BLD_', 'STAGE_', 'LIGHT_', 'CAM_', 'LOOK_', 'PROP_')

W, D = 1080.0, 800.0          # street width (3 x 360 bays), depth
GF_H = 420.0                  # ground floor 4.2 m
FL_H = 360.0                  # upper floor 3.6 m
N_FL = 4
PARAPET = 90.0
TOTAL = GF_H + N_FL * FL_H + PARAPET      # 1950 uu = 19.5 m

# per-floor band projection and lateral overhang, deliberately uneven (gate C3)
BAND_P = [62.0, 55.0, 68.0, 58.0]
BAND_S = [5.0, 2.0, 7.0, 3.0]
BAND_COURSE = 44.0            # height of the proud "paper edge" course
RECESS = 25.0                 # 250 mm window recess - secondary cue
BAYS = [(60.0, 300.0), (420.0, 660.0), (780.0, 1020.0)]
PIERS = [(0.0, 60.0), (300.0, 420.0), (660.0, 780.0), (1020.0, 1080.0)]


def label(ref):
    try:
        return json.loads(ue.tool(A, 'get_label', {'actor': ref}))['returnValue']
    except Exception:
        return ''


def wipe():
    acts = json.loads(ue.tool(S, 'find_actors',
                              {'name': '', 'tag': '', 'collision_channels': []}))['returnValue']
    n = 0
    for a in acts:
        ref = a if isinstance(a, dict) else {'refPath': a}
        if label(ref).startswith(OWNED):
            ue.tool(S, 'remove_from_scene', {'actor': ref})
            n += 1
    print('  removed %d pre-existing owned actors' % n)


def mkactor(name, loc=(0, 0, 0), cls='/Script/Engine.Actor', rot=None):
    x = {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]}}
    if rot:
        x['rotation'] = {'pitch': rot[0], 'yaw': rot[1], 'roll': rot[2]}
    r = ue.tool(S, 'add_to_scene_from_class',
                {'actor_type': {'refPath': cls}, 'name': name, 'xform': x})
    ref = json.loads(r)['returnValue']
    ue.tool(A, 'set_label', {'actor': ref, 'label': name})
    return ref


def box(actor, name, x0, x1, y0, y1, z0, z1):
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': abs(x1 - x0), 'y': abs(y1 - y0), 'z': abs(z1 - z0)},
        'local_transform': {'location': {'x': (x0 + x1) / 2.0,
                                         'y': (y0 + y1) / 2.0,
                                         'z': (z0 + z1) / 2.0}}})


def main():
    print('=== wipe ===')
    wipe()

    print('=== core mass ===')
    core = mkactor('BLD_Core')
    # Core must start BEHIND the facade plane (which occupies Y 0..60) or it
    # fills every window opening from behind and the facade renders blank.
    box(core, 'Core', 0, W, 60, D, 0, TOTAL - PARAPET)
    box(core, 'RearWall', 0, W, D - 20, D, 0, TOTAL)

    print('=== upper floors (stacked paper bands) ===')
    for n in range(N_FL):
        z0 = GF_H + n * FL_H
        z1 = z0 + FL_H
        p, s = BAND_P[n], BAND_S[n]
        f = mkactor('BLD_Floor_%d' % (n + 1))
        # proud band course - the visible stacked-paper edge, the main depth cue
        box(f, 'BandCourse', -s, W + s, -p, 60, z0, z0 + BAND_COURSE)
        # wall plane with window openings
        for i, (px0, px1) in enumerate(PIERS):
            box(f, 'Pier%d' % i, px0, px1, 0, 60, z0 + BAND_COURSE, z1)
        box(f, 'Header', 0, W, 0, 60, z1 - 55, z1)
        for i, (bx0, bx1) in enumerate(BAYS):
            wz0, wz1 = z0 + BAND_COURSE, z1 - 55
            # glazing card set behind the opening - real recess, gate A1
            box(f, 'Glass%d' % i, bx0, bx1, RECESS, RECESS + 2, wz0, wz1)
            box(f, 'Reveal%d' % i, bx0 - 3, bx1 + 3, RECESS + 2, 60, wz0, wz1)
            # window frame + mullion grid, standing proud of the glass.
            # At 0.671 px/uu a 60 mm member is ~4 px - enough to read as the
            # printed grid the paper reference relies on.
            fy0, fy1 = RECESS - 6.0, RECESS + 1.0
            box(f, 'FrmL%d' % i, bx0, bx0 + 6, fy0, fy1, wz0, wz1)
            box(f, 'FrmR%d' % i, bx1 - 6, bx1, fy0, fy1, wz0, wz1)
            box(f, 'FrmB%d' % i, bx0, bx1, fy0, fy1, wz0, wz0 + 6)
            box(f, 'FrmT%d' % i, bx0, bx1, fy0, fy1, wz1 - 6, wz1)
            span = bx1 - bx0
            for k in (1, 2):
                mx = bx0 + span * k / 3.0
                box(f, 'MulV%d_%d' % (i, k), mx - 2.5, mx + 2.5, fy0, fy1, wz0, wz1)
            tz = wz0 + (wz1 - wz0) * 0.62
            box(f, 'MulH%d' % i, bx0, bx1, fy0, fy1, tz - 2.5, tz + 2.5)
        print('   floor %d  z %.0f..%.0f  proud %.0f mm' % (n + 1, z0, z1, p * 10))

    print('=== roof condition ===')
    r = mkactor('BLD_Roof')
    zt = GF_H + N_FL * FL_H
    box(r, 'ParapetFront', -6, W + 6, -14, 20, zt, zt + PARAPET)
    box(r, 'ParapetCap', -10, W + 10, -20, 26, zt + PARAPET - 12, zt + PARAPET)
    box(r, 'ParapetL', -6, 20, -14, D, zt, zt + PARAPET - 18)
    box(r, 'ParapetR', W - 20, W + 6, -14, D, zt, zt + PARAPET - 18)
    box(r, 'RoofDeck', 0, W, 0, D, zt - 8, zt)
    # rooftop unit - one of the three A6 silhouette projections
    box(r, 'RooftopUnit', 300, 620, 210, 470, zt + PARAPET - 12, zt + PARAPET + 95)
    box(r, 'RooftopVent', 700, 800, 260, 360, zt + PARAPET - 12, zt + PARAPET + 60)
    print('   parapet + cap + rooftop unit at z %.0f' % zt)

    print('=== done: massing, %d floors, total height %.0f uu (%.1f m) ==='
          % (N_FL, TOTAL, TOTAL / 100))


if __name__ == '__main__':
    main()
