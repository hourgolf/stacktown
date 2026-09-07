#!/usr/bin/env python3
"""The arrival view against the camera model, without an engine.

The design lane's acceptance rule for the arrival (BOARD 2026-09-07 05:32): all
four plate corners inside the frame with backdrop past each, and no margin more
than twice another. This projects the plate's corners through the C++ camera
model (StacktownCameraModel.h: pitch/yaw/reach about a focus, the focal ramp
24 mm at the wide stop to 200 mm at the close stop on a 36 mm sensor, 16:9
frame, the HUD bar's 65 px counted as no backdrop) and prints each corner's
distance to the nearest frame edge. Checked against a real frame at reach
19,000 on 2026-09-07 (left corner predicted (259,350), seen (260,350)).

  python3 Tools/measure/arrival_margins.py                 # the shipped arrival
  python3 Tools/measure/arrival_margins.py --search        # sweep yaw/pitch/reach/aim
  python3 Tools/measure/arrival_margins.py --yaw 45 --pitch -40 --reach 19000 --aim 0
"""
import argparse, math

W, H, BAR = 1600, 900, 65
MIN_D, MAX_D, F_CLOSE, F_WIDE = 1200.0, 21024.0, 200.0, 24.0
PLATE = [(-7650, -4230), (7650, -4230), (7650, 4230), (-7650, 4230)]


def focal(d):
    d = min(max(d, MIN_D), MAX_D)
    t = (math.log(d) - math.log(MIN_D)) / (math.log(MAX_D) - math.log(MIN_D))
    return F_CLOSE + (F_WIDE - F_CLOSE) * t


def project(focus, yaw, pitch, d, p):
    y, q = math.radians(yaw), math.radians(pitch)
    fwd = (math.cos(q) * math.cos(y), math.cos(q) * math.sin(y), math.sin(q))
    right = (-math.sin(y), math.cos(y), 0.0)
    up = (-math.sin(q) * math.cos(y), -math.sin(q) * math.sin(y), math.cos(q))
    cam = tuple(focus[i] - fwd[i] * d for i in range(3))
    v = (p[0] - cam[0], p[1] - cam[1], 0.0 - cam[2])
    z = sum(v[i] * fwd[i] for i in range(3))
    xv = sum(v[i] * right[i] for i in range(3))
    yv = sum(v[i] * up[i] for i in range(3))
    hfov = 2.0 * math.atan(18.0 / focal(d))
    k = (W / 2) / math.tan(hfov / 2)
    return (W / 2 + xv / z * k, H / 2 - yv / z * k)


def margins(yaw, pitch, reach, aim):
    """aim: uu the focus sits short of the plate's centre, toward the camera."""
    y = math.radians(yaw)
    focus = (-aim * math.cos(y), -aim * math.sin(y), 0.0)
    pts = [project(focus, yaw, pitch, reach, c) for c in PLATE]
    m = [min(x, W - x, yy - BAR, H - yy) for x, yy in pts]
    return pts, m


def area_fraction(pts):
    """The plate's projected area as a fraction of the frame (shoelace)."""
    a = 0.0
    for i in range(4):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % 4]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0 / (W * H)


def look_rule(pts):
    """The design lane's rule (BOARD 2026-09-07 06:40, floor dropped 06:58): all
    four corners inside the frame, no corner within 5 percent of an edge (the
    HUD bar's bottom is the top edge); the plate then as large as that allows.
    The third-of-frame floor was dropped once measured unreachable (28.5 percent
    is the ceiling at pitch -38). Returns (corners_ok, area_ok, area) - area_ok
    is informational only now."""
    left, right = 0.05 * W, 0.95 * W
    top, bottom = BAR + 0.05 * H, 0.95 * H
    corners_ok = all(left <= x <= right and top <= y <= bottom for x, y in pts)
    area = area_fraction(pts)
    return corners_ok, area >= 1.0 / 3.0, area


def report(yaw, pitch, reach, aim):
    pts, m = margins(yaw, pitch, reach, aim)
    ok = min(m) > 0
    ratio = (max(m) / min(m)) if ok else float('inf')
    c_ok, a_ok, area = look_rule(pts)
    print('yaw %g pitch %g reach %g aim %g (focal %.1f mm): corners %s margins %s -> %s, %.2fx; plate %.1f%% of the frame; 5%%-edge rule %s, third-of-frame %s' % (
        yaw, pitch, reach, aim, focal(reach), [(round(x), round(y)) for x, y in pts],
        [round(v) for v in m], 'all four in' if ok else 'A CORNER IS OUT', ratio, 100 * area,
        'met' if c_ok else 'FAILED', 'met' if a_ok else 'not met (informational since 06:58)'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--yaw', type=float, default=45.0)
    ap.add_argument('--pitch', type=float, default=-38.0)
    ap.add_argument('--reach', type=float, default=21000.0)
    ap.add_argument('--aim', type=float, default=1500.0)
    ap.add_argument('--search', action='store_true')
    ap.add_argument('--look', action='store_true', help='largest plate that meets the 5%%-edge rule at pitch -38 on the diagonal')
    a = ap.parse_args()
    if a.look:
        best = None
        for yaw in (41, 45, 49):
            for reach in range(15000, 21025, 250):
                for aim in range(0, 4001, 250):
                    pts, _ = margins(yaw, -38, reach, aim)
                    c_ok, _, area = look_rule(pts)
                    if c_ok and (best is None or area > best[0]):
                        best = (area, yaw, reach, aim)
        print('largest plate under the 5%%-edge rule at pitch -38: %.1f%% of the frame at yaw %d reach %d aim %d' % (100 * best[0], best[1], best[2], best[3]))
        report(best[1], -38, best[2], best[3])
    elif not a.search:
        report(a.yaw, a.pitch, a.reach, a.aim)
    else:
        rows = []
        for yaw in (38, 41, 45, 49):
            for pitch in (-38, -40, -42, -45):
                for reach in range(17000, 21025, 250):
                    for aim in range(0, 3001, 250):
                        _, m = margins(yaw, pitch, reach, aim)
                        if min(m) > 0:
                            rows.append((max(m) / min(m), yaw, pitch, reach, aim))
        rows.sort()
        print('best twelve by margin ratio (rule: <= 2x):')
        for r in rows[:12]:
            print('  %.2fx  yaw %d pitch %d reach %d aim %d' % r)
