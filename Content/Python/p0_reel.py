"""P0 demo reel: the boom's motion grammar, rendered as frames.

Runs LOCALLY (drives the editor over MCP like cap2 does). Produces a
numbered frame sequence in the scratchpad demonstrating, on the real
street, judge-mode (no DOF - focus feel arrives with the interactive
rig): an establishing arc at BOARD, snap-racks down the ladder, a
street-axis reach glide, a whip pan, a feed cut, and the arm-flex
settle at MACRO. If ffmpeg exists the frames become p0_reel.mp4.

    python3 p0_reel.py [out_dir]

One writer in the editor: run only when the editor is free.
"""
import os, sys, math, json, base64, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import boomspace as B
import lenskit as L
import ue

E = 'EditorToolset.EditorAppToolset'
FPS = 24

# MEASURED, not authored - the first cut of this reel aimed an authored
# centre at the catalogue shelf and shot the FACADE/MACRO leg at empty
# board (subject-absent frames). These anchors come from enumerating the
# level's SM_Bld actors (measure_street.py): the ST_ street runs along X,
# x 3000..17417, rows at y -23500 / -22000, bases at z -128; the close
# subject is ST_N_3_deco_t5 at (8466, -21901).
CENTRE = (11200.0, -22750.0, -128.0)      # street span midpoint
SUBJECT = (13508.0, -23500.0, -128.0)     # ST_S_5_deco5_t5 FACADE CENTRE
# (bake origins are CORNERS: deco5 origin (14328,-23500) yaw 180, ext
#  1640 -> facade midpoint x 13508, facade plane y -23500. The SOUTH row
#  faces north into the light; the north row's canyon faces sit in shade
#  and read as dark glass - probed, looked at, rejected.)


def capture(pose, focal, path, centre=CENTRE):
    loc = pose.location(centre)
    pitch, yaw, _ = pose.rotation()
    xf = {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]},
          'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0.0},
          'scale': {'x': 1, 'y': 1, 'z': 1}}
    # per-frame FOV = the zoom is real, not cropped
    import cap2
    cap2.set_fov(L.fov_deg(focal))
    r = ue.tool(E, 'CaptureViewport', {
        'captureTransform': xf, 'bShowUI': False,
        'annotations': {'gridSpacing': 0, 'gridExtent': 0, 'gridHeight': 0,
                        'maxLabelDistance': 0, 'classFilter': None,
                        'maxLabels': 0}})
    d = json.loads(r)['returnValue']['image']['data']
    open(path, 'wb').write(base64.b64decode(d))


def shot(frames, out, n0, centre=CENTRE):
    for i, (pose, focal) in enumerate(frames):
        capture(pose, focal, os.path.join(out, 'f%04d.png' % (n0 + i)),
                centre)
    return n0 + len(frames)


def seq(p0, p1, f0, f1, nframes, curve=B.ease):
    """A move: poses interpolated in boom space, focal eased alongside."""
    out = []
    for i in range(nframes):
        t = i / max(1, nframes - 1)
        k = curve(t)
        out.append((B.move(p0, p1, t, curve), f0 + (f1 - f0) * k))
    return out


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.environ.get('TMPDIR', '/tmp'), 'p0_reel')
    os.makedirs(out, exist_ok=True)
    n = 0
    board = L.stop('BOARD'); block = L.stop('BLOCK')
    street = L.stop('STREET'); facade = L.stop('FACADE')
    macro = L.stop('MACRO')

    # South of the street is azimuth 270 from CENTRE; the canyon axis is
    # X, so azimuth 180 at low height threads the canyon looking east.
    # 1. establishing arc at BOARD - 3s from the south, whole board,
    #    shelf skyline as the backdrop, constant radius
    a = B.Pose(250.0, board['standoff'], 9000.0, tilt=-25.0)
    b = B.Pose(280.0, board['standoff'], 9000.0, tilt=-25.0)
    n = shot(seq(a, b, board['focal'], board['focal'], 3 * FPS), out, n)
    # 2. SNAP to BLOCK - 0.5s rack with overshoot, arm reaches in
    c = B.Pose(280.0, block['standoff'], 3400.0, tilt=-10.0)
    n = shot(seq(b, c, board['focal'], block['focal'], FPS // 2,
                 curve=B.snap), out, n)
    # 3. slow arc at BLOCK - the street skyline slides
    d = B.Pose(265.0, block['standoff'], 3400.0, tilt=-10.0)
    n = shot(seq(c, d, block['focal'], block['focal'], 2 * FPS), out, n)
    # 4. SNAP to STREET - reach in on the south row from across
    e = B.Pose(265.0, street['standoff'], 700.0, tilt=-5.0)
    n = shot(seq(d, e, block['focal'], street['focal'], FPS // 2,
                 curve=B.snap), out, n)
    # 5. FEED CUT to the canyon mouth, then the party trick: a reach
    #    glide along the canyon centreline, buildings on both sides
    f0 = B.Pose(180.0, 8200.0, 450.0, tilt=-1.0)
    f1 = B.Pose(180.0, 4500.0, 450.0, tilt=-1.0)
    n = shot(seq(f0, f0, street['focal'], street['focal'], FPS // 2), out, n)
    n = shot(seq(f0, f1, street['focal'], street['focal'], 3 * FPS), out, n)
    # 6. WHIP PAN - head-only, 0.33s, up onto the deco tower's row
    g = B.Pose(180.0, 4500.0, 450.0, pan=20.0, tilt=3.0)
    n = shot(seq(f1, g, street['focal'], street['focal'], FPS // 3), out, n)
    # 7. FEED CUT (hard) to FACADE mid-band on the deco5 tower -
    #    azimuth 90 puts the boom head in the canyon looking south
    h = B.Pose(90.0, facade['standoff'], 1000.0, tilt=-5.0)
    n = shot(seq(h, h, facade['focal'], facade['focal'], FPS // 2), out, n,
             centre=SUBJECT)
    # 8. SNAP to MACRO - the arm pedestals up the facade as the lens
    #    tightens, landing on the sunlit crown cornice + flex settle
    m = B.Pose(90.0, macro['standoff'], 3900.0, tilt=-2.0)
    n = shot(seq(h, m, facade['focal'], macro['focal'], FPS // 2,
                 curve=B.snap), out, n, centre=SUBJECT)
    flexed = []
    for i in range(FPS):
        t = i / FPS
        off = B.flex(t)
        p = B.Pose(m.azimuth + off * 0.01, m.reach, m.height + off * 0.5,
                   m.pan, m.tilt)
        flexed.append((p, macro['focal']))
    n = shot(flexed, out, n, centre=SUBJECT)

    print('reel: %d frames -> %s' % (n, out))
    try:
        subprocess.run(['ffmpeg', '-y', '-framerate', str(FPS), '-i',
                        os.path.join(out, 'f%04d.png'),
                        '-pix_fmt', 'yuv420p',
                        os.path.join(out, 'p0_reel.mp4')],
                       capture_output=True, check=True)
        print('encoded: %s' % os.path.join(out, 'p0_reel.mp4'))
    except Exception as ex:
        print('ffmpeg unavailable (%s) - frames stand alone' % ex)


if __name__ == '__main__':
    main()
