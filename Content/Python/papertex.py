#!/usr/bin/env python3
"""Generate tileable paper/card textures with no external assets.

MASTER_MATERIAL_SPEC asks for a micro-normal at ~0.5 mm feature size, low
intensity 0.05-0.10, plus fine surface noise - "the tooth of paint or print".
I built the master without them because they are sub-pixel at the 95 m hero
camera. The 9 m close-up showed the cost: the surfaces have nothing to resolve
as a player approaches, so they read as untextured greybox.

Two maps, both tileable so world-aligned projection has no visible seams:
  paper_normal  - fibre tooth. Directional streaks plus fine grain.
  paper_detail  - greyscale, drives small roughness variation.
"""
import math, random, struct, zlib, os

SIZE = 512
OUT = os.path.dirname(os.path.abspath(__file__))


def write_png(path, w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 6))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)


def value_noise(size, cells, seed, ax=1.0, ay=1.0):
    """Tileable value noise. ax/ay stretch the cell grid to make fibres."""
    rnd = random.Random(seed)
    cx, cy = max(1, int(cells * ax)), max(1, int(cells * ay))
    grid = [[rnd.random() for _ in range(cx)] for _ in range(cy)]
    out = [0.0] * (size * size)
    for y in range(size):
        fy = y / size * cy
        y0 = int(fy) % cy
        y1 = (y0 + 1) % cy
        ty = fy - int(fy)
        ty = ty * ty * (3 - 2 * ty)
        for x in range(size):
            fx = x / size * cx
            x0 = int(fx) % cx
            x1 = (x0 + 1) % cx
            tx = fx - int(fx)
            tx = tx * tx * (3 - 2 * tx)
            a = grid[y0][x0] * (1 - tx) + grid[y0][x1] * tx
            b = grid[y1][x0] * (1 - tx) + grid[y1][x1] * tx
            out[y * size + x] = a * (1 - ty) + b * ty
    return out


def build_height():
    h = [0.0] * (SIZE * SIZE)
    # fibres: strongly stretched cells in two directions, as pulp lies
    for seed, cells, ax, ay, amp in ((11, 26, 6.0, 0.35, 0.42),
                                     (23, 22, 0.35, 6.0, 0.26),
                                     (37, 64, 1.0, 1.0, 0.22),
                                     (51, 150, 1.0, 1.0, 0.10)):
        n = value_noise(SIZE, cells, seed, ax, ay)
        for i in range(SIZE * SIZE):
            h[i] += n[i] * amp
    lo, hi = min(h), max(h)
    rng = (hi - lo) or 1.0
    return [(v - lo) / rng for v in h]


def height_to_normal(h, strength):
    px = bytearray(SIZE * SIZE * 3)
    for y in range(SIZE):
        yn, yp = (y - 1) % SIZE, (y + 1) % SIZE
        for x in range(SIZE):
            xn, xp = (x - 1) % SIZE, (x + 1) % SIZE
            dx = (h[y * SIZE + xp] - h[y * SIZE + xn]) * strength
            dy = (h[yp * SIZE + x] - h[yn * SIZE + x]) * strength
            nx, ny, nz = -dx, -dy, 1.0
            L = math.sqrt(nx * nx + ny * ny + nz * nz)
            i = (y * SIZE + x) * 3
            px[i] = int((nx / L * 0.5 + 0.5) * 255)
            px[i + 1] = int((ny / L * 0.5 + 0.5) * 255)
            px[i + 2] = int((nz / L * 0.5 + 0.5) * 255)
    return px


def height_to_grey(h):
    px = bytearray(SIZE * SIZE * 3)
    for i, v in enumerate(h):
        # keep it tight - this drives roughness, not albedo
        g = int((0.42 + v * 0.16) * 255)
        px[i * 3] = px[i * 3 + 1] = px[i * 3 + 2] = g
    return px


if __name__ == '__main__':
    print('building height field %dx%d ...' % (SIZE, SIZE))
    h = build_height()
    write_png(os.path.join(OUT, 'T_PaperNormal.png'), SIZE, SIZE,
              height_to_normal(h, 2.6))
    write_png(os.path.join(OUT, 'T_PaperDetail.png'), SIZE, SIZE,
              height_to_grey(h))
    for f in ('T_PaperNormal.png', 'T_PaperDetail.png'):
        p = os.path.join(OUT, f)
        print('%-22s %6.0f KB' % (f, os.path.getsize(p) / 1024))
