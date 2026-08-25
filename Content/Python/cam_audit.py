"""Which saved cameras still work?

Eight blocks have been built since most of these were placed. A camera that
framed open board in Stage 2 may now stand inside a building, or look straight
into one 40 uu away. Rather than open each one by eye, ask two questions that
can be answered from the table: is the camera INSIDE a lot, and how far can it
see before a building stops it?
"""
import math, sys
import _path
import snapshot, labels
import citygeom as G
sys.path.insert(0, '/Users/ben/Documents/Unreal Projects/StacktownAlpha/Tools/measure')

def height(sp):
    return (sp.get('gf_h', 300.0) + sp.get('floors', 4)*sp.get('fl_h', 260.0)
            + sp.get('parapet', 0.0))

# ONE pass. Building the rects and the names from two separate G.lots() calls
# gave two sets of tuples with different identities, so id(r) missed and the
# audit died on the first camera that actually was inside something.
BLOCKERS = [(r, height(sp), sp['name']) for _n, sp, r in G.lots(('gen', 'av'))]

snap = snapshot.take()
cams = [a for a in snap['actors'] if labels.family(a['label']) == 'CAM']
print('%d cameras' % len(cams))
bad = 0
for a in sorted(cams, key=lambda c: c['label']):
    x, y, z = a['loc']
    pitch, yaw = a['rot'][0], a['rot'][1]
    inside = None
    for r, h, nm in BLOCKERS:
        if r[0] <= x <= r[2] and r[1] <= y <= r[3] and z < h:
            inside = nm
            break
    # how far forward before a building stops the view
    fx = math.cos(math.radians(pitch))*math.cos(math.radians(yaw))
    fy = math.cos(math.radians(pitch))*math.sin(math.radians(yaw))
    fz = math.sin(math.radians(pitch))
    reach = 40000.0
    step = 50.0
    for i in range(1, int(reach/step)):
        px, py, pz = x + fx*step*i, y + fy*step*i, z + fz*step*i
        if pz < 0.0:
            reach = step*i; break
        hit = False
        for r, h, _nm in BLOCKERS:
            if r[0] <= px <= r[2] and r[1] <= py <= r[3] and pz < h:
                reach = step*i; hit = True; break
        if hit:
            break
    verdict = 'INSIDE %s' % inside if inside else ('BLOCKED at %.0f' % reach
                                                   if reach < 900.0 else 'ok')
    if verdict != 'ok':
        bad += 1
    print('  %-22s (%7.0f,%8.0f,%6.0f) p%+4.0f y%+5.0f  %s'
          % (a['label'], x, y, z, pitch, yaw, verdict))
print('%d of %d cameras need replacing' % (bad, len(cams)))
