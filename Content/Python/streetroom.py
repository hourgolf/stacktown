"""Turn the duplicated map into the STREET'S room: purge the workshop
furniture, then give the street a board and a backdrop that actually sit
behind it.

REFUSES TO RUN OUTSIDE Stage2_Street. This is a purge. Pointed at
Sandbox_Bench it would destroy the 203-actor catalogue shelf and the donor
survey, which are the review surfaces the whole project is judged on. The
guard in _guard.py allows several maps; this check is narrower on purpose,
and follows the precedent of bench.py and study_place.py.

WHAT WAS WRONG. The street was sharing Sandbox_Bench with 249 actors of
workshop furniture (POLISH_BACKLOG S5, S8), which forced the block rig's
attenuation down so it would not relight the bench - costing the street's far
end light and drawing a visible circular falloff edge on the ground.

And the backdrop was never behind the street. Measured: STAGE_Backdrop spans
x -12500..12500 at y +-629, centred on the ORIGIN board, while the street runs
x 2600..18703 at y -22700. Every block-hero frame looked past it into black.
That is not a backdrop that needs widening; it is one that is in another room.
"""
import unreal
import _path  # noqa: F401
import stagegeo

ROOM = 'Stage2_Street'
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
_lvl = eus.get_editor_world().get_path_name()
if ROOM not in _lvl:
    raise SystemExit('streetroom.py is %s only - this is %s. It PURGES; '
                     'in Sandbox_Bench it would destroy the shelf.' % (ROOM, _lvl))

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CUBE = eal.load_asset('/Engine/BasicShapes/Cube')
Z = stagegeo.FLOOR_Z

# Furniture that belongs to the bench, not to the street. LIGHT_* and
# STAGE_Ground are KEPT: the board rig is 20,000 uu away and harmless, and
# removing all ambient light before measuring the new room would confound the
# one measurement this script exists to make possible.
# LOOK_ IS NOT FURNITURE. LOOK_Post is the PostProcessVolume that holds the
# whole grade - crucially AEM_Manual, ISO 800, shutter 60. Purging it dropped
# the level to UE's default AUTO exposure, which then compensated upward for a
# newly-emptied frame and blew every capture to white: the same camera that
# read mean 87.71 in Sandbox_Bench read 245.95 here, and no amount of moving
# walls or dimming the rig touched it because none of them was the cause.
# Anything named for the LOOK is part of the instrument, not the subject.
PURGE = ('SHELF_', 'DONOR_', 'SWATCH_', 'BENCH_', 'STAND_', 'BOARD_')
PURGE_EXACT = ('STAGE_Street', 'STAGE_ModelBoard', 'STAGE_Backdrop')

gone = 0
for a in list(eas.get_all_level_actors()):
    l = a.get_actor_label()
    if l.startswith(PURGE) or l in PURGE_EXACT:
        eas.destroy_actor(a)
        gone += 1
print('streetroom: purged %d furniture actors' % gone)

# the street's own extent, measured now rather than assumed
lo = [1e18] * 3
hi = [-1e18] * 3
n = 0
for a in eas.get_all_level_actors():
    if not a.get_actor_label().startswith('ST_'):
        continue
    o, e = a.get_actor_bounds(False)
    for k, ax in enumerate('xyz'):
        lo[k] = min(lo[k], getattr(o, ax) - getattr(e, ax))
        hi[k] = max(hi[k], getattr(o, ax) + getattr(e, ax))
    n += 1
if not n:
    raise SystemExit('no ST_ actors - run street.py first')
print('streetroom: street x %.0f..%.0f  y %.0f..%.0f  top %.0f'
      % (lo[0], hi[0], lo[1], hi[1], hi[2]))

# APRON. THE ROOM MUST CONTAIN ITS OWN LIGHTS. First attempt used 7,000 uu,
# which put the walls BETWEEN the block rig and the street - the rig stands
# 14,000 out (blockrig.REF, derived by inverse square from the board rig). A
# backdrop is built with cast_shadow off so it never casts into the model it
# stands behind, which also means it does not occlude: the key flooded the
# room from outside and every inside face rendered white. Measured mean 254.88
# of 255, sd 0.97 - a blank frame.
#
# So the apron is derived from the rig distance, not chosen. Anything smaller
# builds a lightbox.
import blockrig as _br
APRON = float(getattr(_br, 'RIG_DIST_DEFAULT', 14000.0)) + 2500.0
WALL_H = max(14000.0, (hi[2] - Z) * 2.2)
x0, x1 = lo[0] - APRON, hi[0] + APRON
y0, y1 = lo[1] - APRON, hi[1] + APRON
T = 240.0                                # wall thickness, so it reads as built

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('ROOM_'):
        eas.destroy_actor(a)


def slab(name, ax0, ax1, ay0, ay1, az0, az1, mat):
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector((ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0, (az0 + az1) / 2.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    a.set_actor_label('ROOM_%s' % name)
    a.static_mesh_component.set_editor_property('static_mesh', CUBE)
    a.set_actor_scale3d(unreal.Vector((ax1 - ax0) / 100.0, (ay1 - ay0) / 100.0,
                                      (az1 - az0) / 100.0))
    mi = eal.load_asset('/Game/Stacktown/Materials/%s' % mat)
    if mi:
        a.static_mesh_component.set_material(0, mi)
    # a backdrop must never cast into the model it is standing behind
    if name != 'Board':
        a.static_mesh_component.set_editor_property('cast_shadow', False)
    return a


# the board the model sits on - a visible edge is what tells the eye this is an
# object on a table (studio-director, "what reads as a physical model", 2)
slab('Board', x0, x1, y0, y1, Z - 90.0, Z - 8.0, 'MI_model_board')
# FOUR walls, not one. A single backdrop is what the bench had, and it only
# works from the one camera it was aimed at; every other angle found black.
slab('BackN', x0 - T, x1 + T, y1, y1 + T, Z - 90.0, Z + WALL_H, 'MI_studio_grey')
slab('BackS', x0 - T, x1 + T, y0 - T, y0, Z - 90.0, Z + WALL_H, 'MI_studio_grey')
slab('BackW', x0 - T, x0, y0, y1, Z - 90.0, Z + WALL_H, 'MI_studio_grey')
slab('BackE', x1, x1 + T, y0, y1, Z - 90.0, Z + WALL_H, 'MI_studio_grey')
print('streetroom: board %.0f x %.0f, walls %.0f tall, apron %.0f'
      % (x1 - x0, y1 - y0, WALL_H, APRON))
les.save_current_level()
print('streetroom: saved')
