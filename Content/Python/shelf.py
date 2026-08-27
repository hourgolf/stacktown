"""Lay the whole baked catalogue out on the sandbox floor, in rows.

One model alone on a large floor is a poor review surface: you have to know
where it is to look at it, and you cannot compare anything. A shelf puts every
tier of every recipe side by side, ordered, so the ladder reads as a ladder
and a regression in tier 3 is visible next to tiers 2 and 4.

Sandbox only - this spawns a lot of actors and must never do it in the city.
"""
import unreal
import _path  # noqa: F401
import recipes
import random
import stagegeo
import palette

SANDBOX = 'Sandbox_Bench'
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
lvl = eus.get_editor_world().get_path_name()
if SANDBOX not in lvl:
    raise SystemExit('refusing to build the shelf in %s - open /Game/Maps/%s'
                     % (lvl, SANDBOX))

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
BAKED = '/Game/Stacktown/Baked'
WIDTH_FOR = {'contemporary': 2050.0,
             'contemporary2': 1640.0,
             'contemporary3': 1640.0,
             'contemporary4': 1640.0,
             'contemporary5': 1640.0,
             'contemporary6': 2050.0,
             'contemporary7': 1640.0,
             'contemporary8': 1640.0,
             'deco': 1640.0,
             'deco2': 2050.0,
             'deco3': 2050.0,
             'deco4': 2050.0,
             'deco5': 1640.0,
             'deco6': 1640.0,
             'deco7': 2460.0,
             'deco8': 1640.0,
             'modern2': 1640.0,
             'modern3': 1640.0,
             'modern4': 2050.0,
             'modern5': 1640.0,
             'modern6': 2050.0,
             'modern7': 1640.0,
             'modern8': 1640.0,
             'tower': 2050.0,
             'vernacular': 1230.0,
             'vernacular2': 1640.0,
             'vernacular3': 1640.0,
             'vernacular4': 2050.0,
             'vernacular5': 1640.0,
             'vernacular6': 2050.0,
             'vernacular7': 1640.0,
             'vernacular8': 1230.0}
# CLEAR OF THE MODEL BOARD. The shelf needs ~9000 uu of run and the board is
# 2900 wide, so it was always going to spill onto the room floor - which is
# 128 uu LOWER. Half on, half off, all spawned at z=0, and everything past the
# board's edge floated. The whole shelf goes on the floor, past the board.
SHELF_X0 = stagegeo.BOARD_X[1] + 700.0
SHELF_Z = stagegeo.FLOOR_Z
GAP = 420.0
ROW_GAP = 1500.0

# A GRID, NOT A LIST. One row per recipe was fine at four recipes and absurd
# at thirty-two: the shelf ran to y = -70,518 while STAGE_Ground stopped near
# -12,000, so five sixths of the catalogue sat unlit in the void and no
# capture of it was usable (P14).
#
# Ladders are laid in COLUMNS. Every column is as wide as the LONGEST ladder
# so the grid stays square-edged and a row of models never runs into the
# column beside it - the same reason the donor sheet needed a grid.
COLS = 4
GUTTER = 900.0

rnd = random.Random(20260826)
ROWS = {}      # row index -> measured extent, for the per-row cameras (P7)


def repaint(actor, sm, rid, scheme):
    """Override a baked model's paint per INSTANCE.

    A baked mesh carries one wall, one trim and one accent, so variety between
    buildings is an instance override - not thirty more baked variants. Slot
    names carry the baked material's name, so each role is found rather than
    assumed, and a role that is not present is reported instead of silently
    skipped.
    """
    base = recipes.RECIPES[rid]['base']
    want = {base.get('wall') or 'MI_dist_buff': scheme['wall'],
            base.get('trim') or 'MI_paint_cream': scheme['trim'],
            'MI_canopy_accent': scheme['accent']}
    # THE SECOND CLADDING takes the scheme's `base` role - the one colour in
    # every scheme that had no job until a style arrived with two wall
    # materials. A contemporary block is a clad volume beside a clad volume,
    # and both have to move together when the building is repainted or the
    # brick half stays brick on every building in the district.
    if base.get('panel_b'):
        want[base['panel_b']] = scheme['base']
    # the curtain wall takes the scheme's glass, so a district reads as teal
    # and bronze and ink towers rather than nine grey ones
    want['MI_glass_b'] = scheme['glass']
    hit = 0
    for si, sl in enumerate(sm.get_editor_property('static_materials')):
        nm = str(sl.material_slot_name)
        if nm in want:
            mi = eal.load_asset('/Game/Stacktown/Materials/%s' % want[nm])
            if mi:
                actor.static_mesh_component.set_material(si, mi)
                hit += 1
    return hit

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('SHELF_'):
        eas.destroy_actor(a)

lo = [1e18]*3
hi = [-1e18]*3
n = 0
RIDS = sorted(recipes.RECIPES)
# the widest cell any ladder needs, measured rather than guessed
CELL_W = max(recipes.tier_count(r) * (WIDTH_FOR.get(r, recipes.widths(r)[0])
                                      + GAP) for r in RIDS) + GUTTER
print('  grid: %d recipes, %d columns, cell %.0f uu wide' % (len(RIDS), COLS, CELL_W))

for idx, rid in enumerate(RIDS):
    w = WIDTH_FOR.get(rid, recipes.widths(rid)[0])
    col, row = idx % COLS, idx // COLS
    x = SHELF_X0 + col * CELL_W
    y = -row * ROW_GAP
    for t in range(recipes.tier_count(rid)):
        asset = recipes.asset_name(rid, t, w)
        sm = eal.load_asset('%s/%s' % (BAKED, asset))
        if not sm:
            print('  missing %s' % asset)
            continue
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                       unreal.Vector(x, y, SHELF_Z),
                                       unreal.Rotator(0, 0, 0))
        a.set_actor_label('SHELF_%s_t%d' % (rid, t))
        a.static_mesh_component.set_editor_property('static_mesh', sm)
        ROWS.setdefault(row, {'x0': 1e18, 'x1': -1e18, 'top': -1e18, 'y': y})
        # ONE SCHEME PER BUILDING, HELD ACROSS EVERY TIER. This used to
        # pick a colour per MODEL, so vernacular t0..t5 - the same building
        # growing - came out in six unrelated colours. A building does not
        # repaint itself when it gains a storey. The scheme is keyed on the
        # recipe, so the whole ladder wears one palette.
        if repaint(a, sm, rid, palette.scheme_for(rid)) == 0:
            print('  %s: no scheme slots matched - paint not applied' % asset)
        o, e = a.get_actor_bounds(False)
        _r = ROWS[row]
        _r['x0'] = min(_r['x0'], o.x - e.x)
        _r['x1'] = max(_r['x1'], o.x + e.x)
        _r['top'] = max(_r['top'], o.z + e.z)
        for i, (oo, ee) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            lo[i] = min(lo[i], oo - ee)
            hi[i] = max(hi[i], oo + ee)
        x += w + GAP
        n += 1
    print('  %-11s %d tiers at w%.0f' % (rid, recipes.tier_count(rid), w))

# ---- the district row ---------------------------------------------------
# One tier of one recipe, once per scheme. The ladders above are honest about
# growth (a building keeps its paint as it climbs) and that costs the shelf
# its colour range, so the range gets its own row instead of being faked by
# repainting the ladder. This is what a street of neighbours looks like.
DIST_RID, DIST_TIER = 'vernacular', 3
dw = WIDTH_FOR[DIST_RID]
dy = -(((len(RIDS) + COLS - 1) // COLS) + 1) * ROW_GAP
dasset = recipes.asset_name(DIST_RID, DIST_TIER, dw)
dsm = eal.load_asset('%s/%s' % (BAKED, dasset))
if dsm:
    dx = SHELF_X0
    for si, sname in enumerate(palette.ORDER):
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                       unreal.Vector(dx, dy, SHELF_Z),
                                       unreal.Rotator(0, 0, 0))
        a.set_actor_label('SHELF_district_%s' % sname)
        a.static_mesh_component.set_editor_property('static_mesh', dsm)
        if repaint(a, dsm, DIST_RID, palette.scheme(sname)) == 0:
            print('  district %s: no scheme slots matched' % sname)
        o, e = a.get_actor_bounds(False)
        for i, (oo, ee) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            lo[i] = min(lo[i], oo - ee)
            hi[i] = max(hi[i], oo + ee)
        dx += dw + GAP
        n += 1
    print('  district   %d schemes at w%.0f' % (len(palette.ORDER), dw))
else:
    print('  missing %s for the district row' % dasset)

import json
# SIZE THE GROUND TO THE SHELF. The bench is only usable if the models are
# standing on something lit; leaving that to be remembered by hand is how the
# catalogue ended up floating in the dark in the first place.
import os, tempfile
json.dump({'x0': lo[0], 'y0': lo[1], 'x1': hi[0], 'y1': hi[1], 'margin': 2600.0},
          open(os.path.join(tempfile.gettempdir(), 'stacktown_ground.json'), 'w'))
print('  ground wanted: x %.0f..%.0f  y %.0f..%.0f  (run groundfit.py)'
      % (lo[0], hi[0], lo[1], hi[1]))
print('SHELFBOUNDS ' + json.dumps(dict(lo=lo, hi=hi, n=n)))
# ---- one camera per row (P7) --------------------------------------------
# Rows used to be shot from a single hand-placed camera, so every row capture
# needed its viewpoint nudged by hand - which is how a run gets spent chasing
# framing instead of defects.
#
# Two things make a row camera non-trivial and both are DERIVED, not guessed:
#
#   FRAMING. The project's camera is 70 mm on a 36x24 back, hFOV 28.84 deg
#   (cap2.FOV). To hold a row of width Wr the camera must stand back
#   (Wr/2) / tan(hFOV/2).
#
#   OCCLUSION. Rows march away in -y at ROW_GAP, so at ground level every row
#   sits behind the ones in front of it. The camera rises until its sight line
#   to this row's BASE clears the measured top of every intervening row -
#   computed from what was actually placed, not from an assumed height.
import math as _math

CAM_FOV = 28.84                  # keep in step with cap2.FOV
CAM_CLEAR = 260.0                # uu of daylight over an intervening row
_cams = {}
_skipped = []
for _ri in sorted(ROWS):
    _r = ROWS[_ri]
    if _r['x1'] <= _r['x0']:
        continue
    _wide = (_r['x1'] - _r['x0']) * 1.06
    _back = (_wide / 2.0) / _math.tan(_math.radians(CAM_FOV / 2.0))
    _cx = (_r['x0'] + _r['x1']) / 2.0
    _cy = _r['y'] - _back
    _z = SHELF_Z + _r['top'] * 0.55
    for _oi in sorted(ROWS):
        if _oi == _ri:
            continue
        _o = ROWS[_oi]
        _d_row = _r['y'] - _cy
        _d_obst = _o['y'] - _cy
        # WHICH ROWS ARE ACTUALLY IN THE WAY is a geometric question, not an
        # index one. Rows march away in -y and the camera stands further -y
        # still, so the rows BETWEEN camera and subject are the ones with a
        # HIGHER index - the opposite of what an index test suggests. Filtering
        # on `_oi < _ri` checked the rows beyond the subject and left every
        # real obstruction unconsidered; the offline clearance check caught it
        # because it verified the property instead of trusting the loop.
        if _d_obst <= 0 or _d_row <= 0 or _d_obst >= _d_row:
            continue
        _f = _d_obst / _d_row
        _need = SHELF_Z + _o['top'] + CAM_CLEAR
        _z = max(_z, (_need - SHELF_Z * _f) / (1.0 - _f))
    # HONEST REFUSAL. If clearing the rows in front demands a camera far
    # above the models, the shot is a plan view of a shelf, not a review of a
    # ladder - and emitting it anyway would hand the next person a camera that
    # looks placed but is useless. Measured: ROW_GAP is 1500 uu, so a camera
    # standing in the gap frames 617 uu of row, while the NARROWEST building
    # in the catalogue is 1230 uu. Per-row cameras are not placeable at this
    # spacing with the project's 70 mm lens; the layout has to change. See
    # POLISH_BACKLOG P7.
    _ceiling = SHELF_Z + _r['top'] * 3.0
    if _z > _ceiling:
        _skipped.append((_ri, round(_z, 0), round(_ceiling, 0)))
        continue
    _aim = SHELF_Z + _r['top'] * 0.45
    _pitch = -_math.degrees(_math.atan2(_z - _aim, _back))
    _a = eas.spawn_actor_from_class(unreal.CameraActor,
                                    unreal.Vector(_cx, _cy, _z),
                                    unreal.Rotator(0.0, _pitch, 90.0))
    _a.set_actor_label('SHELF_CAM_r%d' % _ri)
    _cams['r%d' % _ri] = {'loc': [round(_cx, 1), round(_cy, 1), round(_z, 1)],
                          'rot': {'pitch': round(_pitch, 2), 'yaw': 90.0,
                                  'roll': 0.0},
                          'row_width': round(_wide, 1),
                          'standback': round(_back, 1)}
if _cams:
    print('  cameras: %d rows, standback %.0f..%.0f uu, height %.0f..%.0f uu'
          % (len(_cams),
             min(c['standback'] for c in _cams.values()),
             max(c['standback'] for c in _cams.values()),
             min(c['loc'][2] for c in _cams.values()),
             max(c['loc'][2] for c in _cams.values())))
if _skipped:
    print('  CAMERAS NOT PLACEABLE for %d row(s): clearing the rows in front '
          'needs a camera above 3x the model height.' % len(_skipped))
    for _ri, _zz, _cc in _skipped[:3]:
        print('    row %d wanted z %.0f, ceiling %.0f' % (_ri, _zz, _cc))
    print('    ROW_GAP %.0f frames %.0f uu of row; narrowest building is 1230.'
          % (ROW_GAP, 2 * (ROW_GAP - 200) * _math.tan(_math.radians(CAM_FOV / 2))))
    print('    This is a LAYOUT constraint, not a camera bug - see P7.')
import os as _os
_camf = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.abspath(__file__)))), 'Tools', 'measure', 'shelf_cams.json')
json.dump(_cams, open(_camf, 'w'), indent=1, sort_keys=True)
print('  camera transforms -> Tools/measure/shelf_cams.json')

les.save_current_level()
print('shelf: %d models' % n)
