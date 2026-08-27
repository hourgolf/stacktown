"""Every donor mesh in the kit, spawned in a labelled row, so it can be LOOKED AT.

This exists because I enlisted `SM_roofStand_donut` as rooftop equipment on the
strength of its name and shipped a car tyre on the crown of every tower. That
is the same defect as picking `MI_precast_buff` for gravel because the word
"precast" sounded right: a name is not a measurement, and a triangle count is
not a picture. The survey measured these pieces and never rendered them.

So: one row, one piece per column, each on a 200 uu reference plinth that is
our own geometry at our own detail tier. If a piece does not read as the thing
its key claims, that is visible here before it reaches a building.

Sandbox only.
"""
import unreal
import _path  # noqa: F401
import avkit
import stagegeo
import json

SANDBOX = 'Sandbox_Bench'
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
lvl = eus.get_editor_world().get_path_name()
if SANDBOX not in lvl:
    raise SystemExit('refusing to build the donor sheet in %s - open /Game/Maps/%s'
                     % (lvl, SANDBOX))

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CUBE = eal.load_asset('/Engine/BasicShapes/Cube')
PLINTH = 200.0
GAP = 360.0
# Clear of the shelf rows, which start at y=0 and march negative. The first
# capture framed the shelf instead of the donors because the two occupied the
# same ground.
X0 = -5200.0
Y_ROW = -1200.0
# The donor grid is off the board, so it rests on the room floor. It used to
# spawn at z=0 and float 128 uu like everything else out here.
Z0 = stagegeo.FLOOR_Z
# A grid, not a row. Fourteen pieces in a line spans 8,000 uu, which forces the
# camera so far back that a 100 uu plant is four pixels - the sheet renders but
# answers nothing. Five columns keeps the span under 2,500 so a piece is big
# enough on screen to judge.
COLS = 5
# Rows march AWAY from the backdrop. STAGE_Backdrop is a volume spanning
# y -128..1130; a row placed at +600 would have been inside it. And the whole
# grid sits at x -5200, on lit STAGE_Ground and clear of the shelf at x >= 0 -
# the first attempt put it at y 4000, past the edge of the ground, which is
# why every piece came back nearly black.
ROW_PITCH = -900.0

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('DONOR_'):
        eas.destroy_actor(a)

keys = sorted(avkit.PIECES)
lo = [1e18] * 3
hi = [-1e18] * 3
missing = []
placed = {}
x = X0
col = 0
row = 0
for k in keys:
    p = avkit.path(k)
    sm = eal.load_asset(p)
    if not sm:
        missing.append(k)
        continue
    sx, sy, sz = avkit.size(k)
    # plinth: our own box, so the donor is always judged next to our tier
    pl = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                    unreal.Vector(x, Y_ROW + row * ROW_PITCH, Z0 - 10.0),
                                    unreal.Rotator(0, 0, 0))
    pl.set_actor_label('DONOR_plinth_%s' % k)
    pl.static_mesh_component.set_editor_property('static_mesh', CUBE)
    pl.set_actor_scale3d(unreal.Vector(PLINTH / 100.0, PLINTH / 100.0, 0.20))
    grey = eal.load_asset('/Game/Stacktown/Materials/MI_model_board')
    if grey:
        pl.static_mesh_component.set_material(0, grey)

    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(x, Y_ROW + row * ROW_PITCH, Z0),
                                   unreal.Rotator(0, 0, 0))
    a.set_actor_label('DONOR_%s' % k)
    a.static_mesh_component.set_editor_property('static_mesh', sm)
    mi = eal.load_asset('/Game/Stacktown/Materials/%s' % avkit.mat(k))
    if mi:
        for si in range(len(sm.get_editor_property('static_materials'))):
            a.static_mesh_component.set_material(si, mi)
    o, e = a.get_actor_bounds(False)
    for i, ax in enumerate('xyz'):
        lo[i] = min(lo[i], getattr(o, ax) - getattr(e, ax))
        hi[i] = max(hi[i], getattr(o, ax) + getattr(e, ax))
    # measured vs declared, so the sheet also polices avkit's own numbers
    md = (round(getattr(e, 'x') * 2), round(getattr(e, 'y') * 2),
          round(getattr(e, 'z') * 2))
    flag = '' if all(abs(md[i] - (sx, sy, sz)[i]) <= 3 for i in range(3)) \
        else '   DECLARED %s MEASURED %s' % ((sx, sy, sz), md)
    print('  %-16s %-52s%s' % (k, p.split('/')[-1], flag))
    placed[k] = {'at': [getattr(o, 'x'), getattr(o, 'y'), getattr(o, 'z')],
                 'size': [sx, sy, sz], 'tris': avkit.PIECES[k][2],
                 'mesh': p.split('/')[-1], 'mat': avkit.mat(k)}
    col += 1
    if col >= COLS:
        col = 0
        row += 1
        x = X0
    else:
        x += max(PLINTH, sx) + GAP

if missing:
    print('  MISSING ON DISK: %s' % ', '.join(missing))
les.save_current_level()
print('donorsheet: %d pieces' % (len(keys) - len(missing)))
print('DONORBOUNDS ' + json.dumps({'lo': lo, 'hi': hi, 'placed': placed}))
