"""The lens kit: the stop ladder for the Impossible Boom (P0).

The 0.4% table made playable (Docs/CAMERA_DESIGN.md): each optical stop
is a prime-lens character matched to a gate framing. Pure module,
self-tested against the project's one hand-verified optic: cap2.py's
70 mm on a 36x24 back = 28.84 degrees.

Aperture anchor: the owner LOCKED f/2.8 at facade range (2026-08-29,
DESIGN's exposure-held sweep - ISO scaled by (N/N0)^2 so the ladder
measured defocus, not brightness). FACADE and MACRO carry that lock;
the wider stops' apertures remain design placeholders until show-mode
DOF exists (P1) - deep focus at survey range is the intent either way.
"""
import math

SENSOR_W = 36.0          # mm, the project's 36x24 back (cap2.py)


def fov_deg(focal_mm):
    """Horizontal field of view for a focal length on the 36mm back."""
    return math.degrees(2.0 * math.atan(SENSOR_W / (2.0 * focal_mm)))


def focal_mm(fov):
    return SENSOR_W / (2.0 * math.tan(math.radians(fov) / 2.0))


# stop      focal  aperture  standoff(uu)  what it judges / shows
LADDER = [
    dict(name='BOARD',  focal=24.0,  fstop=11.0, standoff=19000.0,
         note='the whole model on its table; districts and markets read'),
    dict(name='BLOCK',  focal=50.0,  fstop=8.0,  standoff=11168.0,
         note='the gate block-hero framing; the skyline-as-chart'),
    dict(name='STREET', focal=85.0,  fstop=5.6,  standoff=3500.0,
         note='the approach framing; one facade fills the frame'),
    # The close standoffs are derived from FRAME WIDTH, not carried over
    # from the gate's 70 mm framings: the first reel kept the gate's
    # 900 uu standoff while doubling the focal, which halved the frame to
    # a single glazing pane (probed, looked at, unusable). The canyon is
    # 1500 uu wide, which caps FACADE's standoff below the frame-width-
    # preserving 1739 uu - 1350 keeps the camera out of the far row.
    dict(name='FACADE', focal=135.0, fstop=2.8,  standoff=1350.0,
         note='player-zoom subject size, canyon-constrained; f/2.8 LOCKED'),
    dict(name='MACRO',  focal=200.0, fstop=2.8,  standoff=800.0,
         note='fabrication delight, one bay + cornice; f/2.8 LOCKED'),
]
DIGITAL_MAX = 1.4        # crop factor before the next optical snap


def stop(name):
    for s in LADDER:
        if s['name'] == name:
            return s
    raise KeyError(name)


def neighbours(name):
    """(wider, tighter) stop names, None at the ladder's ends."""
    i = next(i for i, s in enumerate(LADDER) if s['name'] == name)
    return (LADDER[i - 1]['name'] if i > 0 else None,
            LADDER[i + 1]['name'] if i < len(LADDER) - 1 else None)


def frame_width_uu(name):
    """World width the frame covers at the stop's standoff - the number
    the 0.4% rule divides. width = 2 * standoff * tan(fov/2)."""
    s = stop(name)
    return 2.0 * s['standoff'] * math.tan(math.radians(fov_deg(s['focal'])) / 2.0)


def threshold_mm(name):
    """The 0.4% legibility threshold at this stop, in MILLIMETRES.
    1 uu = 1 cm = 10 mm - the first self-check run caught this module
    conflating the two (7.2 uu reported against the gate's 72 mm), which
    is exactly what a known-answer cell is for."""
    return 0.004 * frame_width_uu(name) * 10.0


if __name__ == '__main__':
    # KNOWN ANSWER: cap2.py's hand-verified optic - 70mm = 28.84 deg.
    assert abs(fov_deg(70.0) - 28.84) < 0.05, fov_deg(70.0)
    # Round trip.
    for f in (24.0, 50.0, 85.0, 135.0, 200.0):
        assert abs(focal_mm(fov_deg(f)) - f) < 1e-9
    # The ladder tightens monotonically: each stop longer focal, nearer
    # standoff, narrower frame.
    for a, b in zip(LADDER, LADDER[1:]):
        assert b['focal'] > a['focal'] and b['standoff'] < a['standoff']
        assert frame_width_uu(b['name']) < frame_width_uu(a['name'])
    # HANDOFF's own 0.4% table, reproduced within tolerance: the gate
    # says approach (3500 uu) threshold is 72mm and block hero
    # (11168 uu) is 230mm. Those used the 70mm optic; check with it.
    for standoff, expect_mm in ((3500.0, 72.0), (11168.0, 230.0)):
        w = 2.0 * standoff * math.tan(math.radians(fov_deg(70.0)) / 2.0)
        assert abs(0.004 * w * 10.0 - expect_mm) < 5.0, (standoff, 0.004 * w * 10.0)
    # neighbours() walks the ladder.
    assert neighbours('BOARD') == (None, 'BLOCK')
    assert neighbours('MACRO') == ('FACADE', None)
    print('lenskit self-check: pass')
    for s in LADDER:
        print('  %-6s %5.0fmm f/%-4.1f  frame %6.0f uu  0.4%% = %5.1f mm'
              % (s['name'], s['focal'], s['fstop'],
                 frame_width_uu(s['name']), threshold_mm(s['name'])))
