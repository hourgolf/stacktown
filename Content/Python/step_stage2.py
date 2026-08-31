"""Board and street for two facing blocks.

Block A faces -Y from Y=0; block B faces +Y from Y=-1600. So the road runs
between them and each side needs its own pavement.
"""
import unreal, sys, math
import _path  # repo tool paths; replaces a dead scratchpad path
from city import BLOCKS, STREETS, AVENUES, BOARD_S, BOARD_E, BOARD_N
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
F='/Game/Stacktown/Materials'
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
def M(n): return unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))

X0, X1 = -300.0, BOARD_E
YB, YT = BOARD_S, BOARD_N
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

# board
for lbl, names in (('STAGE_ModelBoard', ('BoardTop', 'BoardPlinth')),):
    for c in acts[lbl].get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() not in names: continue
        s_ = c.get_world_scale(); e = c.static_mesh.get_bounds().box_extent
        loc = c.get_world_location()
        c.set_world_scale3d(unreal.Vector((X1 - X0)/2.0/e.x, (YT - YB)/2.0/e.y, s_.z))
        c.set_world_location(unreal.Vector((X0 + X1)/2.0, (YB + YT)/2.0, loc.z), False, False)
        print('%-12s X %.0f..%.0f  Y %.0f..%.0f' % (c.get_name(), X0, X1, YB, YT))

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('ROAD_'): eas.destroy_actor(a)


def slab(name, x0, x1, y0, y1, z0, z1, mat):
    if x1 - x0 < 1.0 or y1 - y0 < 1.0: return
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector((x0 + x1)/2.0, (y0 + y1)/2.0, (z0 + z1)/2.0), unreal.Rotator(0, 0, 0))
    a.set_actor_label('ROAD_' + name)
    a.static_mesh_component.set_editor_property('static_mesh', cube)
    a.set_actor_scale3d(unreal.Vector((x1 - x0)/100.0, (y1 - y0)/100.0,
                                      max(0.02, (z1 - z0)/100.0)))
    a.static_mesh_component.set_material(0, M(mat))


def spans(lo, hi, gaps):
    """Sub-spans of lo..hi with every gap removed. This is what stops two
    coplanar road slabs meeting at an intersection: the avenue yields, the
    street runs through, and nothing z-fights."""
    out, cur = [], lo
    for g0, g1 in sorted(gaps):
        if g1 <= cur or g0 >= hi: continue
        if g0 > cur: out.append((cur, min(g0, hi)))
        cur = max(cur, g1)
    if cur < hi: out.append((cur, hi))
    return out


ST = [(y_far + w, y_near - w) for y_far, y_near, w in STREETS]      # road Y spans
AV = [(x_w + w, x_e - w) for x_w, x_e, w in AVENUES]                # road X spans

# --- east-west streets: roads run THROUGH the intersections -----------------
for i, (y_far, y_near, walk) in enumerate(STREETS, 1):
    k_far, k_near = y_far + walk, y_near - walk
    slab('S%dRoad' % i, X0, X1, k_far, k_near, -30, -16, 'MI_studio_grey')
    for j, (a, b) in enumerate(spans(X0, X1, AV)):
        slab('S%dWalkFar%d' % (i, j),  a, b, y_far - 40.0, k_far, -16, 0, 'MI_concrete')
        slab('S%dWalkNear%d' % (i, j), a, b, k_near, y_near + 40.0, -16, 0, 'MI_concrete')
        slab('S%dKerbFar%d' % (i, j),  a, b, k_far, k_far + 14.0, -16, -4, 'MI_paint_cream')
        slab('S%dKerbNear%d' % (i, j), a, b, k_near - 14.0, k_near, -16, -4, 'MI_paint_cream')
    print('street %d: road Y %.0f..%.0f, pavements in %d spans'
          % (i, k_far, k_near, len(spans(X0, X1, AV))))

# --- north-south avenues: yield to the streets ------------------------------
for i, (x_w, x_e, walk) in enumerate(AVENUES, 1):
    k_w, k_e = x_w + walk, x_e - walk
    for j, (a, b) in enumerate(spans(YB, YT, ST)):
        slab('A%dRoad%d' % (i, j), k_w, k_e, a, b, -30, -16, 'MI_studio_grey')
        slab('A%dWalkW%d' % (i, j), x_w - 40.0, k_w, a, b, -16, 0, 'MI_concrete')
        slab('A%dWalkE%d' % (i, j), k_e, x_e + 40.0, a, b, -16, 0, 'MI_concrete')
        slab('A%dKerbW%d' % (i, j), k_w, k_w + 14.0, a, b, -16, -4, 'MI_paint_cream')
        slab('A%dKerbE%d' % (i, j), k_e - 14.0, k_e, a, b, -16, -4, 'MI_paint_cream')
    print('avenue %d: road X %.0f..%.0f, in %d spans between streets'
          % (i, k_w, k_e, len(spans(YB, YT, ST))))

# --- crossings: painted bars on the approach to every intersection ----------
BAR, GAPB = 46.0, 62.0
n_cross = 0
for i, (sy0, sy1) in enumerate(ST, 1):
    for j, (ax0, ax1) in enumerate(AV, 1):
        for side, x_at in (('W', ax0 - 120.0), ('E', ax1 + 120.0)):
            y = sy0 + 40.0
            k = 0
            while y < sy1 - 40.0:
                slab('X%d%d%s_%d' % (i, j, side, k), x_at - 55.0, x_at + 55.0,
                     y, y + BAR, -16, -14, 'MI_paint_cream')
                y += BAR + GAPB; k += 1; n_cross += 1
        for side, y_at in (('S', sy0 - 120.0), ('N', sy1 + 120.0)):
            x = ax0 + 40.0
            k = 0
            while x < ax1 - 40.0:
                slab('X%d%d%s_%d' % (i, j, side, k), x, x + BAR,
                     y_at - 55.0, y_at + 55.0, -16, -14, 'MI_paint_cream')
                x += BAR + GAPB; k += 1; n_cross += 1
print('crossings: %d bars over %d intersections' % (n_cross, len(ST)*len(AV)))

# hide the old single-sided street
for a in eas.get_all_level_actors():
    if a.get_actor_label()=='STAGE_Street':
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_visibility(False,True); c.set_hidden_in_game(True,True)
        print('old STAGE_Street hidden')
les.save_current_level()
