#!/usr/bin/env python3
"""Derive the species GRAIN MASKS from their CC0 diffuse maps.

    python3 Tools/textures/mk_grain_masks.py

WHY THIS SCRIPT EXISTS AND IS COMMITTED. The fix-class ladder requires that a
new asset ships with its generation script alongside - reproducible, never a
hand-painted orphan. These masks are generated, so this is that script, and
re-running it must reproduce them byte-for-byte from the sources in
source/polyhaven/.

WHAT A GRAIN MASK IS, AND THE RULE IT ENFORCES. Direction B's extension of the
donor-texture rule is "THEIR PATTERN, OUR PALETTE" (owner, 2026-08-31, see
Docs/DIRECTION_B_DECLARATIONS.md D8): a donor wood map may lend its normal AND
a LUMINANCE-ONLY grain mask from its diffuse. No hue, no saturation, no
absolute brightness may cross over.

THE CONVERSION IS THE ENFORCEMENT. Importing the colour diffuse and taking
luminance in the shader would put a donor's brown inside the project, one
wiring mistake away from the frame. Converting to single-channel HERE means
the donor's colour never enters Content/ at all - the rule becomes a property
of the asset instead of a promise about the graph.

GRAIN DIRECTION IS NORMALISED, and this is the fix for the first thing an
eye caught on the board: "the grain of the wood is not consistent like a block
of carved wood would be... vertically and then it goes horizontally on other
building faces."

The master's triplanar samples V=z on BOTH side planes, so the direction grain
runs on a wall is decided entirely by which way it runs IN THE SOURCE IMAGE.
Measured across the seven admitted maps, FIVE run horizontally and TWO run
vertically - so two species showed vertical grain on a wall and five showed
horizontal, on identical geometry. Mixed stock, not one workshop.

Each mask is therefore measured and rotated to a canonical direction: grain
along the image's V axis, which lands as VERTICAL grain on a standing wall -
the common way to cut a tall block. The measurement is anisotropy on the
mask itself, so the check and the asset agree by construction, and the
assertion at the end means a future map that arrives the wrong way round
cannot ship quietly.

REC.709 LUMA, not a colourspace convert. sips' grey profile does its own
thing; this uses the same integer weights as Tools/measure/img.py so a mask
and a measurement of it agree by construction.

THE MEAN IS DATA, NOT A BAKED CORRECTION. A mask is emitted as plain
luminance and its MEAN is printed for the stock table to record. Centring is
done in the material against that scalar, so the asset stays a faithful
greyscale of the source rather than a lossily re-levelled one - and a mask
whose mean drifts on re-run is a signal the source changed, which a
pre-levelled asset would hide.

AND THE SD IS DATA TOO, FOR A REASON MEASURED RATHER THAN ASSUMED. Figure
strength varies TENFOLD across these seven sources: sd/mean runs 0.176 for
pine down to 0.018 for maple. Under one shared gain, pine would scream and
maple would be invisible, and the species would stop reading as one family -
which is the property the master material exists to protect. So the material
normalises by sd, and a single gain then gives every species comparable
amplitude, with any per-species trim being a deliberate override instead of
an accident of how a photograph was exposed.

This is the same fault the fabrication table already fixed once: card_heavy
pushed brick, concrete and skimmed render at an identical amplitude of 2.0
"regardless of what their relief actually is". Caught here before it shipped,
because the numbers were looked at before the geometry.
"""
import os, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'source', 'polyhaven')
OUT = os.path.join(HERE, 'grain_masks')

# species -> the CC0 diffuse it derives from. One entry per stock; a species
# absent here has no mask and must not claim one.
SPECIES = {
    'pine':   'coated_pine',
    'maple':  'white_maple_veneer',
    'ash':    'ash_veneer',
    'oak':    'white_oak_veneer',
    'cherry': 'cherry_veneer',
    'sapele': 'sapele_veneer',
    'walnut': 'american_walnut_veneer',
}

KR, KG, KB = 218, 732, 74          # Rec.709 /1024, identical to img.py


def read_bmp(path):
    d = open(path, 'rb').read()
    if d[:2] != b'BM':
        raise ValueError('not a BMP: %s' % path)
    off = struct.unpack('<I', d[10:14])[0]
    w, h = struct.unpack('<ii', d[18:26])
    bpp = struct.unpack('<H', d[28:30])[0]
    if bpp not in (24, 32):
        raise ValueError('expected 24/32bpp, got %d' % bpp)
    n = bpp // 8
    topdown = h < 0
    h = abs(h)
    stride = ((w * n + 3) // 4) * 4
    px = bytearray(w * h)
    for y in range(h):
        s = off + (y if topdown else (h - 1 - y)) * stride
        row = d[s:s + stride]
        base = y * w
        for x in range(w):
            i = x * n
            px[base + x] = (row[i + 2] * KR + row[i + 1] * KG + row[i] * KB) >> 10
    return w, h, px


def write_grey_bmp(path, w, h, px):
    """24bpp BMP with R=G=B. Written as 24bpp rather than 8bpp+palette because
    sips reads it without argument and the file is a build intermediate."""
    stride = ((w * 3 + 3) // 4) * 4
    pad = stride - w * 3
    rows = []
    for y in range(h - 1, -1, -1):
        r = bytearray()
        base = y * w
        for x in range(w):
            v = px[base + x]
            r += bytes((v, v, v))
        r += b'\0' * pad
        rows.append(bytes(r))
    data = b''.join(rows)
    hdr = b'BM' + struct.pack('<IHHI', 14 + 40 + len(data), 0, 0, 14 + 40)
    hdr += struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, len(data),
                       2835, 2835, 0, 0)
    open(path, 'wb').write(hdr + data)


def _direction(px, w, h):
    """(|dx|, |dy|) of the high-pass residual. |dy| larger means variation
    runs ACROSS rows, i.e. the features lie HORIZONTALLY."""
    dx = dy = 0.0
    n = 0
    for y in range(2, h - 2, 3):
        b = y * w
        for x in range(2, w - 2, 3):
            dx += abs(px[b + x + 1] - px[b + x - 1])
            dy += abs(px[b + w + x] - px[b - w + x])
            n += 1
    return (dx / n, dy / n) if n else (0.0, 0.0)


def _rot90(px, w, h):
    """Rotate the luminance plane 90 degrees. Returns (px, w, h)."""
    out = bytearray(w * h)
    for y in range(h):
        b = y * w
        for x in range(w):
            out[x * h + (h - 1 - y)] = px[b + x]
    return out, h, w


def main():
    if not os.path.isdir(SRC):
        raise SystemExit('no source dir: %s' % SRC)
    os.makedirs(OUT, exist_ok=True)
    print('%-9s %-26s %11s %7s %6s %7s'
          % ('stock', 'source diffuse', 'size', 'mean', 'sd', 'sd/mean'))
    means = {}
    for stock in sorted(SPECIES):
        asset = SPECIES[stock]
        jpg = os.path.join(SRC, '%s_diffuse_2k.jpg' % asset)
        if not os.path.exists(jpg):
            print('%-9s %-26s MISSING - run the download step first'
                  % (stock, asset))
            continue
        tmp = os.path.join(OUT, '_%s.bmp' % stock)
        subprocess.run(['sips', '-s', 'format', 'bmp', jpg, '--out', tmp],
                       check=True, capture_output=True)
        w, h, px = read_bmp(tmp)
        os.remove(tmp)
        # NORMALISE THE GRAIN DIRECTION. Canonical is grain along V, which
        # the master's triplanar puts VERTICALLY on a standing wall.
        ddx, ddy = _direction(px, w, h)
        turned = ''
        if ddy > ddx:                      # runs horizontally -> turn it
            px, w, h = _rot90(px, w, h)
            ddx, ddy = _direction(px, w, h)
            turned = ' rotated 90'
        assert ddx >= ddy, (
            '%s grain still runs horizontally after rotation (%.2f vs %.2f) - '
            'it is not directional enough to normalise, and a map with no '
            'direction is not depicting wood' % (stock, ddx, ddy))
        grey = os.path.join(OUT, '_grey_%s.bmp' % stock)
        write_grey_bmp(grey, w, h, px)
        png = os.path.join(OUT, 'T_grain_%s.png' % stock)
        subprocess.run(['sips', '-s', 'format', 'png', grey, '--out', png],
                       check=True, capture_output=True)
        os.remove(grey)
        n = len(px)
        m = sum(px) / float(n)
        sd = (sum((v - m) * (v - m) for v in px) / float(n)) ** 0.5
        means[stock] = (m, sd)
        print('%-9s %-26s %5dx%-5d %7.1f %6.1f %7.3f%s'
              % (stock, asset, w, h, m, sd, sd / m, turned))
    if means:
        print('\nfor the stock table - the material centres on mean and '
              'normalises by sd:')
        for s in sorted(means):
            m, sd = means[s]
            print('    %-9s figure_mean=%.1f, figure_sd=%.1f' % (s, m, sd))
    return 0


if __name__ == '__main__':
    sys.exit(main())
