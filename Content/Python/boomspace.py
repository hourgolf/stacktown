"""Boom-space: the camera pose model for the Impossible Boom (P0).

The design contract (Docs/CAMERA_DESIGN.md): camera pose is authored in
BOOM SPACE - azimuth around the board, reach, height, head pan/tilt -
so boom-legal motion (arcs, reaches, pedestals) falls out by
construction and drone-like strafing is unrepresentable.

Pure module, no `unreal`, self-tested with known answers - same rules as
citygeom and modelgate, for the same reason: a pose model that cannot be
proven against a hand-computed answer will lie eventually.

Angles in degrees. World frame matches the project's: X east, Y north,
Z up, yaw about Z (UE convention, pitch positive = up).
"""
import math


class Pose:
    """One boom pose: where the head is and where it looks.

    azimuth: degrees around the board centre (0 = +X, CCW positive)
    reach:   horizontal distance from centre, uu
    height:  Z above the board plane, uu
    pan:     head yaw OFFSET from 'aimed at centre', degrees
    tilt:    head pitch, degrees (negative looks down)
    """
    def __init__(self, azimuth, reach, height, pan=0.0, tilt=0.0):
        self.azimuth = float(azimuth) % 360.0
        self.reach = float(reach)
        self.height = float(height)
        self.pan = float(pan)
        self.tilt = float(tilt)

    def location(self, centre=(0.0, 0.0, 0.0)):
        a = math.radians(self.azimuth)
        return (centre[0] + self.reach * math.cos(a),
                centre[1] + self.reach * math.sin(a),
                centre[2] + self.height)

    def rotation(self):
        """(pitch, yaw, roll) - the head aims back at the centre azimuth,
        plus the pan offset. Roll is always 0: a boom head does not roll."""
        yaw_to_centre = (self.azimuth + 180.0) % 360.0
        return (self.tilt, (yaw_to_centre + self.pan) % 360.0, 0.0)


def look_at(pose, subject, centre=(0.0, 0.0, 0.0)):
    """Head angles (pan, tilt) that aim this pose's head at a world point.
    Returns a NEW pose; the arm does not move, only the head."""
    loc = pose.location(centre)
    dx, dy, dz = (subject[0] - loc[0], subject[1] - loc[1], subject[2] - loc[2])
    flat = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx))
    tilt = math.degrees(math.atan2(dz, flat))
    yaw_to_centre = (pose.azimuth + 180.0) % 360.0
    pan = ((yaw - yaw_to_centre + 180.0) % 360.0) - 180.0
    return Pose(pose.azimuth, pose.reach, pose.height, pan, tilt)


# --- ease curves: boom moves have mass -------------------------------------
def ease(t):
    """Smoothstep - zero velocity at both ends. The default boom ease."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def snap(t, overshoot=0.04):
    """The snap-zoom curve: fast in, small overshoot, settle to 1.
    overshoot is the fraction past the target at the peak."""
    t = max(0.0, min(1.0, t))
    # ease to (1+overshoot) in the first 70%, settle back in the last 30%
    if t < 0.7:
        return ease(t / 0.7) * (1.0 + overshoot)
    return (1.0 + overshoot) - ease((t - 0.7) / 0.3) * overshoot


def _lerp_angle(a, b, t):
    """Shortest-path angular interpolation, degrees."""
    d = ((b - a + 180.0) % 360.0) - 180.0
    return (a + d * t) % 360.0


def move(p0, p1, t, curve=ease):
    """Interpolate two poses in BOOM SPACE. Because azimuth, reach and
    height interpolate independently, a pure-azimuth move IS an arc at
    constant radius, a pure-reach move IS a straight reach along the
    arm, and a mixed move is the graceful compound curve a real operator
    swings. Interpolating world positions instead would cut the chord -
    the exact drone-flavoured shortcut this module exists to forbid."""
    k = curve(t)
    return Pose(_lerp_angle(p0.azimuth, p1.azimuth, k),
                p0.reach + (p1.reach - p0.reach) * k,
                p0.height + (p1.height - p0.height) * k,
                p0.pan + (p1.pan - p0.pan) * k,
                p0.tilt + (p1.tilt - p0.tilt) * k)


def flex(t_since_stop, amplitude=1.5, freq=3.2, damp=4.0):
    """Arm flex on a hard stop: a damped sway, uu of lateral offset.
    Gone in ~half a second at the defaults. Apply at MACRO reach only."""
    if t_since_stop < 0.0:
        return 0.0
    return (amplitude * math.exp(-damp * t_since_stop)
            * math.sin(2.0 * math.pi * freq * t_since_stop))


if __name__ == '__main__':
    # KNOWN ANSWERS - hand-computed, not printed-and-pasted.
    # 1. Pose at azimuth 0, reach 100: location is exactly (+100, 0, h),
    #    and the head aims back along -X (yaw 180).
    p = Pose(0.0, 100.0, 50.0)
    assert [round(v, 6) for v in p.location()] == [100.0, 0.0, 50.0]
    assert p.rotation() == (0.0, 180.0, 0.0)
    # 2. Azimuth 90 puts the camera at +Y, aiming yaw 270.
    p = Pose(90.0, 100.0, 0.0)
    loc = p.location()
    assert abs(loc[0]) < 1e-9 and round(loc[1], 6) == 100.0
    assert p.rotation()[1] == 270.0
    # 3. AN ARC IS AN ARC: a pure-azimuth move holds radius at every t.
    a, b = Pose(0.0, 500.0, 100.0), Pose(90.0, 500.0, 100.0)
    for i in range(11):
        m = move(a, b, i / 10.0)
        x, y, _ = m.location()
        assert abs(math.hypot(x, y) - 500.0) < 1e-6, 'chord-cutting!'
    # 4. Shortest-path azimuth: 350 -> 10 goes through 0, not 180.
    m = move(Pose(350.0, 100.0, 0.0), Pose(10.0, 100.0, 0.0), 0.5)
    assert abs(m.azimuth - 0.0) < 1e-9, m.azimuth
    # 5. look_at aims the head: from azimuth 0/reach 100/height 0 at a
    #    subject at the centre, tilt 0 pan 0; at a subject 100 up, tilt 45.
    p = Pose(0.0, 100.0, 0.0)
    q = look_at(p, (0.0, 0.0, 0.0))
    assert abs(q.pan) < 1e-9 and abs(q.tilt) < 1e-9
    q = look_at(p, (0.0, 0.0, 100.0))
    assert abs(q.tilt - 45.0) < 1e-9
    # 6. Ease endpoints exact; snap ends exactly at 1.0 and peaks over it.
    assert ease(0.0) == 0.0 and ease(1.0) == 1.0
    assert abs(snap(1.0) - 1.0) < 1e-9
    assert max(snap(i / 100.0) for i in range(101)) > 1.0
    # 7. Flex decays: amplitude at 0.5s under 15% of initial.
    assert abs(flex(0.5)) < 0.15 * 1.5
    print('boomspace self-check: pass')
