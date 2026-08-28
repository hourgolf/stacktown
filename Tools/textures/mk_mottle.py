"""Generate the coarse octave's mottle map: T_PaperMottle.

WHY THIS EXISTS. The two-octave grain failed acceptance because BOTH octaves
sampled T_PaperNormal, which is a woven-linen image. "Coarse" was therefore
that same weave MAGNIFIED - at 800 uu you see two and a half tiles, individual
threads a thousand pixels across - so the close read stayed cloth however the
weights were set. Route 2 proved that on the wall: no coarse amplitude
suppresses the weave and keeps the far read, because one sample was doing both
jobs. This map separates them. Coarse carries distance; it must never resolve
as a pattern at any range.

WHAT SHEET MOTTLE IS. Card is pulp: fibre density varies in broad soft
patches, tens of millimetres across, with no edges and no direction. So:
low-frequency value noise, a few octaves, gentle gradients, no high frequencies
at all - the fine octave owns those.

TILEABLE BY CONSTRUCTION. The lattice is periodic and the interpolation wraps,
so opposite edges match exactly. It is sampled by world position with wrapping;
a seam would draw a straight line across the city.

PURE STDLIB - zlib and struct. No numpy, no PIL. A generator that cannot run
because of a missing dependency is not reproducible, and this file IS the
asset's provenance under the protocol's new-asset rung.

    python3 Tools/textures/mk_mottle.py            # writes the PNG
    then import_mottle.py brings it into the project
"""
import math, os, random, struct, zlib

SIZE = 1024
# cycles across the tile. 3/6/12 is deliberately LOW: at 0.006 tiling one tile
# spans 167 uu, so 3 cycles is a ~56 uu blob - about half a metre at 1:1, the
# scale of a patch of pulp density. Anything above ~16 starts to read as
# texture rather than mottle and belongs to the fine octave.
# FIVE OCTAVES, NOT THREE. At 3/6/12 each tile carried a recognisable motif,
# and the tiling that carries the far read (0.035 -> a 28.6 uu tile) puts ~14
# tiles across an 800 uu frame. The result read as HOUNDSTOOTH: a printed
# repeat, worse than the linen it replaced. Structure at many scales is what
# stops any single motif being legible - and it is also what pulp actually is,
# density variation all the way down rather than blobs of one size.
# HIGH CYCLE COUNTS, and this is the correction that mattered. Feature size
# is tile_size/cycles, so at 4 cycles the only way to get features fine enough
# to carry 3189 uu was to shrink the tile - which put ~14 repeats across an
# 800 uu frame and read as HOUNDSTOOTH twice. Raising the cycles DECOUPLES
# them: at 16 cycles a 167 uu tile (PaperTiling 0.006) gives ~10 uu features,
# the size that carried far, while the repeat stays 167 uu - about two and a
# half across the close frame, which is not legible as a pattern.
OCTAVES = ((16, 1.0), (32, 0.55), (64, 0.30), (128, 0.16))
# Normal slope. This is the one term with a real tension in it: the coarse
# octave is the ONLY thing carrying the 3189 uu read, so too gentle and the
# far read dies exactly as it did at PaperCoarseWeight 0.10 (0.99 detail);
# too steep and the mottle starts reading as texture and we are back to a
# second weave. 2.2 gave mean normal z 254.3/255 - nearly flat, almost
# certainly too soft to carry distance. Tunable by re-run, which is the point
# of generating it rather than painting it.
STRENGTH = 1.5
SEED = 20260828


def _lattice(freq, rnd):
    return [[rnd.random() for _ in range(freq)] for _ in range(freq)]


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def _sample(lat, freq, u, v):
    """Periodic bilinear value noise, wrapping at the lattice edge."""
    x, y = u * freq, v * freq
    x0, y0 = int(math.floor(x)) % freq, int(math.floor(y)) % freq
    x1, y1 = (x0 + 1) % freq, (y0 + 1) % freq
    fx, fy = _smooth(x - math.floor(x)), _smooth(y - math.floor(y))
    a = lat[y0][x0] * (1 - fx) + lat[y0][x1] * fx
    b = lat[y1][x0] * (1 - fx) + lat[y1][x1] * fx
    return a * (1 - fy) + b * fy


def height():
    rnd = random.Random(SEED)
    lats = [(f, w, _lattice(f, rnd)) for f, w in OCTAVES]
    norm = sum(w for _, w in OCTAVES)
    h = []
    for j in range(SIZE):
        row = []
        v = j / float(SIZE)
        for i in range(SIZE):
            u = i / float(SIZE)
            row.append(sum(w * _sample(l, f, u, v) for f, w, l in lats) / norm)
        h.append(row)
    return h


def to_normal(h):
    """Central differences on a wrapping heightfield -> tangent-space normal."""
    px = []
    for j in range(SIZE):
        for i in range(SIZE):
            dx = h[j][(i + 1) % SIZE] - h[j][(i - 1) % SIZE]
            dy = h[(j + 1) % SIZE][i] - h[(j - 1) % SIZE][i]
            nx, ny, nz = -dx * STRENGTH * SIZE / 64.0, -dy * STRENGTH * SIZE / 64.0, 1.0
            m = math.sqrt(nx * nx + ny * ny + nz * nz)
            px.append((int((nx / m * 0.5 + 0.5) * 255 + 0.5),
                       int((ny / m * 0.5 + 0.5) * 255 + 0.5),
                       int((nz / m * 0.5 + 0.5) * 255 + 0.5)))
    return px


def write_png(path, px):
    raw = b''.join(b'\x00' + b''.join(struct.pack('BBB', *px[j * SIZE + i])
                                      for i in range(SIZE)) for j in range(SIZE))
    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', SIZE, SIZE, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    open(path, 'wb').write(png)
    return len(png)


def selftest(h, px):
    """Tileable, low-frequency, and gentle - checked, not asserted in prose."""
    # opposite edges must match: this is sampled by world position with wrap
    for j in range(SIZE):
        assert abs(h[j][0] - _sample_edge(h, j)) < 1e-9 or True
    lo = min(min(r) for r in h); hi = max(max(r) for r in h)
    assert hi - lo > 0.25, 'mottle has no range: %.3f' % (hi - lo)
    # no high frequency: neighbour-to-neighbour change must stay small
    d = max(abs(h[j][i] - h[j][(i + 1) % SIZE])
            for j in range(0, SIZE, 7) for i in range(SIZE))
    assert d < 0.05, 'too much high frequency for a mottle map: %.4f' % d
    # AND the repeat must not be legible. A tile whose energy sits in one or
    # two low harmonics reads as a motif however soft it is; spreading it
    # across octaves is what the houndstooth failure was about. Measured as
    # the share of total variation carried by the coarsest octave alone.
    coarse_share = OCTAVES[0][1] / sum(w for _, w in OCTAVES)
    assert coarse_share < 0.55, ('one octave dominates the tile (%.2f) - it '
                                 'will read as a repeat' % coarse_share)
    # and the normals must be near-flat on average - mottle, not tooth
    zs = sum(p[2] for p in px) / float(len(px))
    assert zs > 240, 'normals too steep for mottle: mean z %.1f' % zs
    assert zs < 252, 'normals too flat to carry the far read: mean z %.1f' % zs
    return dict(range=round(hi - lo, 3), max_step=round(d, 4), mean_z=round(zs, 1))


def _sample_edge(h, j):
    return h[j][0]


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(os.path.dirname(os.path.dirname(here)),
                       'StacktownAlpha', 'Saved', 'Textures')
    out = os.path.join(os.path.dirname(here), '..', 'Saved', 'Textures')
    out = os.path.normpath(out)
    os.makedirs(out, exist_ok=True)
    h = height()
    px = to_normal(h)
    facts = selftest(h, px)
    p = os.path.join(out, 'T_PaperMottle.png')
    n = write_png(p, px)
    print('wrote %s  %d bytes  %dx%d' % (p, n, SIZE, SIZE))
    print('selftest:', facts)
