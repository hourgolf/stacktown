"""Rebuild the saved camera set from the city table.

Most of these were placed when there were one or two blocks. There are eight
now, and cam_audit.py found three that stand inside a building or look into a
wall 400 uu away. Rather than nudge them, DERIVE them: every block already
knows its own rectangle, its own height and which way it fronts, and
Tools/measure/framing.py can solve a standoff that contains a box and clears
everything between. A camera should not be a remembered number.

Legacy Stage-1 cameras (CAM_Mark_*, CAM_Judge_*, CAM_View_*) are gate evidence
and are left alone unless the audit says they are broken, in which case they
are re-solved onto the same subject.
"""
import unreal, sys, math
import _path
import citygeom as G
from city import BLOCKS
sys.path.insert(0, '/Users/ben/Documents/Unreal Projects/StacktownAlpha/Tools/measure')
import framing

FOCAL = 70.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def height(sp):
    return (sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0)
            + sp.get('parapet', 0.0))


BLOCKERS = [(r, height(sp)) for _n, sp, r in G.lots(('gen', 'av'))]


def block_rect(blk):
    rs = [G.lot_rect(blk, l) for l in blk['lots']]
    return (min(r[0] for r in rs), min(r[1] for r in rs),
            max(r[2] for r in rs), max(r[3] for r in rs))


def block_height(blk):
    return max([height(l) for l in blk['lots'] if l['kind'] in ('gen', 'av')]
               or [300.0])


BOARD = G.board_rect()
REACH = 3000.0        # how far off the board a camera may stand


def on_board(loc):
    return (BOARD[0] - REACH <= loc['x'] <= BOARD[2] + REACH
            and BOARD[1] - REACH <= loc['y'] <= BOARD[3] + REACH)


def solve(rect, side, blockers, z1):
    """Street-side if it can be had from near the board, otherwise over the top.

    from_street_clear() will happily retreat ten thousand units to find a clear
    line - it did, for every block with another block in front of it - and a
    camera that far out is a compressed telephoto of a backdrop. A diorama is
    looked at from close and above, so when the street view cannot be had from
    near the board, take the overhead instead of a distant one.
    """
    try:
        loc, rot, p = framing.from_street_clear(rect, side, blockers, z1=z1,
                                                margin=1.10)
        if on_board(loc):
            return loc, rot, p
    except ValueError:
        pass
    bearing = {'S': 90.0, 'N': -90.0}[side]
    for pitch in (-58.0, -68.0, -78.0, -86.0):
        loc, rot = framing.frame(rect, bearing, pitch=pitch, z1=z1, margin=1.10)
        cam = (loc['x'], loc['y'], loc['z'])
        tgt = ((rect[0] + rect[2])/2.0, (rect[1] + rect[3])/2.0, z1/2.0)
        if on_board(loc) and not framing.blocked(cam, tgt, blockers):
            return loc, rot, pitch
    return loc, rot, -86.0


def place(name, loc, rot):
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == name:
            eas.destroy_actor(a)
    cam = eas.spawn_actor_from_class(
        unreal.CineCameraActor,
        unreal.Vector(loc['x'], loc['y'], loc['z']),
        unreal.Rotator(0.0, rot['pitch'], rot['yaw']))
    cam.set_actor_label(name)
    try:
        cc = cam.get_cine_camera_component()
        cc.set_editor_property('current_focal_length', FOCAL)
    except Exception:
        pass
    return cam


made = 0
for blk in BLOCKS:
    rect = block_rect(blk)
    side = 'S' if abs(blk['yaw']) < 1.0 else 'N'      # which way the block fronts
    z1 = block_height(blk) + 120.0
    mine = [b for b in BLOCKERS
            if not (rect[0] <= (b[0][0] + b[0][2])/2.0 <= rect[2]
                    and rect[1] <= (b[0][1] + b[0][3])/2.0 <= rect[3])]
    loc, rot, p = solve(rect, side, mine, z1)
    place('CAM_Blk_%s' % blk['name'], loc, rot)
    print('  CAM_Blk_%-3s from %s pitch %-5.0f (%7.0f,%8.0f,%6.0f)'
          % (blk['name'], side, p, loc['x'], loc['y'], loc['z']))
    made += 1

# the open lots are subjects in their own right
for _n, sp, r in G.lots(('plaza', 'green', 'park')):
    loc, rot, p = solve(r, 'N', BLOCKERS, 500.0)
    place('CAM_Lot_%s' % sp['name'], loc, rot)
    print('  CAM_Lot_%-8s pitch %-5.0f (%7.0f,%8.0f,%6.0f)'
          % (sp['name'], p, loc['x'], loc['y'], loc['z']))
    made += 1

# and the whole board, from over the corner it has always been shot from
b = G.board_rect()
loc, rot = framing.frame(b, 132.0, pitch=-32.0, z1=2600.0, margin=1.06)
place('CAM_Blk_Board', loc, rot)
print('  CAM_Blk_Board          (%7.0f,%8.0f,%6.0f)' % (loc['x'], loc['y'], loc['z']))
made += 1

# --- the three legacy cameras cam_audit.py found broken ---------------------
# They are Stage-1 era and the city grew around them: one stands inside block
# B's Hall, two look into a wall a few hundred uu away. Re-solve them onto the
# subject each was named for rather than deleting evidence cameras.
A = next(b for b in BLOCKS if b['name'] == 'A')
a_rect = block_rect(A)
corner = (a_rect[0], a_rect[1], a_rect[0] + 900.0, a_rect[3])
jn = G.junction_rects()[0]
for name, rect, side, z1 in (
        ('CAM_View_Approach', a_rect, 'S', block_height(A) + 120.0),
        ('CAM_Judge_Corner',  corner, 'S', block_height(A) + 120.0),
        ('CAM_Junction',      jn,     'N', 400.0)):
    mine = [b for b in BLOCKERS
            if not (rect[0] <= (b[0][0] + b[0][2])/2.0 <= rect[2]
                    and rect[1] <= (b[0][1] + b[0][3])/2.0 <= rect[3])]
    loc, rot, p = solve(rect, side, mine, z1)
    place(name, loc, rot)
    print('  %-20s re-solved pitch %-5.0f (%7.0f,%8.0f,%6.0f)'
          % (name, p, loc['x'], loc['y'], loc['z']))
    made += 1

print('placed %d derived cameras' % made)
les.save_current_level()
