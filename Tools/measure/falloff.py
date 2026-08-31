"""Measure a light's FALLOFF from a street frame, using the road as the probe.

WHY THE ROAD. In a street frame the carriageway is the only surface that runs
continuously from the camera to the vanishing point in ONE material. Its
brightness profile down the image is therefore the light's falloff with albedo
held constant - nothing else in the frame separates light from paint. Facades
cannot do this job: they change colour every parcel.

The camera looks down the corridor at a shallow pitch, so the road recedes to
a vanishing point near the frame's vertical centre. Image BOTTOM is NEAR,
image CENTRE is FAR, and the default window is a centre strip from 56% down to
the bottom edge - clear of the parked cars on both sides at the framings this
project uses.

WHAT THE NUMBER MEANS. near/far > 1 is a light with real falloff over the
subject. near/far < 1 means the road is DARKER toward the camera, which no
light with falloff can produce - it is the signature of a key that cannot
reach the road at all, with the frame carried by ambient and by a fill at the
far end. That is exactly what it found on Sandbox_Bench on 2026-08-31: the
passing frame measured 0.71x, backwards, and the key was standing 9,147 uu
OUTSIDE a 2,096 uu canyon.

CAUTION: the far band is small and dark, so its relative variance is high.
Two converged captures of the same scene have read 3.34x and 3.91x. Treat the
STOPS figure as good to about +/- 0.2 and do not tune against the third digit.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import img

BANDS = 8
X_FRAC = (0.42, 0.58)      # centre strip, clear of kerbside parking
Y_FRAC = (0.56, 1.00)      # vanishing point down to the bottom edge


def profile(path, bands=BANDS, x_frac=X_FRAC, y_frac=Y_FRAC):
    """Mean level in `bands` bands of the road strip, FAR first."""
    im = img.load(path)
    x0, x1 = int(im.w * x_frac[0]), int(im.w * x_frac[1])
    y0, y1 = int(im.h * y_frac[0]), int(im.h * y_frac[1])
    out = []
    for i in range(bands):
        a = y0 + (y1 - y0) * i // bands
        b = y0 + (y1 - y0) * (i + 1) // bands
        out.append(img.mean(img.patch(im, x0, a, x1, b)))
    return out


def ratio(path, **kw):
    """near/far as a linear ratio. > 1 is falloff, < 1 is backwards."""
    v = profile(path, **kw)
    return (v[-1] / v[0]) if v[0] > 0 else 0.0


def stops(path, **kw):
    import math
    r = ratio(path, **kw)
    return math.log(r, 2) if r > 0 else float('-inf')


# known answer: a synthesised gradient must measure the gradient it was built
# with, and a flat field must measure 1.00x. The instrument is checked before
# it is believed - this project has twice drawn a conclusion from a census
# that was enumerating the wrong thing.
if __name__ == '__main__':
    import math
    if len(sys.argv) > 1:
        for p in sys.argv[1:]:
            v = profile(p)
            print('%-34s  far %6.2f -> near %6.2f   %5.2fx (%+5.2f stops)'
                  % (os.path.basename(p), v[0], v[-1],
                     v[-1] / v[0] if v[0] else 0.0,
                     math.log(v[-1] / v[0], 2) if v[0] and v[-1] else 0.0))
            print('   bands far..near: %s' % ' '.join('%6.1f' % x for x in v))
        sys.exit(0)

    class _F:
        pass

    # flat field -> 1.00x
    f = _F(); f.w, f.h = 100, 100
    f.px = bytearray([120]) * (100 * 100)
    # profile() loads from disk, so exercise the banding maths directly
    def _bands(im, bands=BANDS):
        x0, x1 = int(im.w * X_FRAC[0]), int(im.w * X_FRAC[1])
        y0, y1 = int(im.h * Y_FRAC[0]), int(im.h * Y_FRAC[1])
        return [img.mean(img.patch(im, x0, y0 + (y1 - y0) * i // bands,
                                   x1, y0 + (y1 - y0) * (i + 1) // bands))
                for i in range(bands)]
    b = _bands(f)
    assert abs(b[-1] / b[0] - 1.0) < 1e-9, b
    print('falloff flat-field self-check: pass (%.4fx)' % (b[-1] / b[0]))

    # built gradient: level rises linearly toward the bottom by a known factor
    g = _F(); g.w, g.h = 100, 100
    g.px = bytearray(100 * 100)
    for y in range(100):
        for x in range(100):
            g.px[y * 100 + x] = int(round(40 + 120 * (y / 99.0)))
    b = _bands(g)
    y0, y1 = int(100 * Y_FRAC[0]), int(100 * Y_FRAC[1])
    lo_c = (y0 + (y1 - y0) * 0 // BANDS + y0 + (y1 - y0) * 1 // BANDS - 1) / 2.0
    hi_c = (y0 + (y1 - y0) * (BANDS - 1) // BANDS
            + y0 + (y1 - y0) * BANDS // BANDS - 1) / 2.0
    want = (40 + 120 * (hi_c / 99.0)) / (40 + 120 * (lo_c / 99.0))
    assert abs(b[-1] / b[0] - want) < 0.02, (b[-1] / b[0], want)
    print('falloff gradient self-check: pass (%.3fx, expected %.3fx)'
          % (b[-1] / b[0], want))
