"""Emit a whole building as ONE OBJ with per-role material groups.

Same geometry as genbuild.py, different backend. genbuild makes one MCP
add_cube round trip per box - measured at 0.75 s each, which is 9 hours for a
hundred blocks and 43,000 components that would not render. This writes the
identical boxes into a single mesh with a `usemtl` group per material role, so
a building costs ONE import instead of ~140 round trips and ONE component
instead of ~140.

Per-floor hand-made tolerance is baked into the vertices here rather than
applied to an actor afterwards, because there is no per-floor actor any more.
Same seed and same draw order as genbuild so the two versions are comparable.
"""
import math, os, random
from objgen import polys

CHAMFER = 4.0            # 40 mm, the card-edge value from MINIATURE_RECIPE


def _xf(p, dx, dy, yaw, roll, pivot):
    """Apply a floor's offset and small yaw/roll about its own pivot."""
    x, y, z = p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    x, y = x * cy - y * sy, x * sy + y * cy
    cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    y, z = y * cr - z * sr, y * sr + z * cr
    return (x + pivot[0] + dx, y + pivot[1] + dy, z + pivot[2])


def _newell(p):
    n = [0.0, 0.0, 0.0]
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    return n


class Bake:
    def __init__(self):
        self.groups = {}
        self.xf = None

    def box(self, role, x0, x1, y0, y1, z0, z1):
        dims = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        c = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
        for poly in polys(dims, CHAMFER):
            # objgen.polys returns unoriented polygons - objgen.write_obj is
            # what flips the inward-facing ones, and it can only do that while
            # they are still centred on the origin. Reusing polys() without
            # that step renders the building inside-out: backface culling eats
            # every wall and leaves a skeleton of frames and mullions.
            n = _newell(poly)
            cen = [sum(q[i] for q in poly) / len(poly) for i in range(3)]
            if sum(n[i] * cen[i] for i in range(3)) < 0:
                poly = list(reversed(poly))
            pts = [(p[0] + c[0], p[1] + c[1], p[2] + c[2]) for p in poly]
            if self.xf:
                pts = [self.xf(p) for p in pts]
            self.groups.setdefault(role, []).append(pts)

    def write(self, path, name):
        vs, out = [], []
        ns, faces = [], []
        for role in sorted(self.groups):
            f0 = len(faces)
            for p in self.groups[role]:
                n = _newell(p)
                ln = max(1e-12, sum(v * v for v in n) ** 0.5)
                ns.append([v / ln for v in n])
                idx = []
                for q in p:
                    vs.append(q)
                    idx.append(len(vs))
                faces.append((idx, len(ns)))
            out.append((role, f0, len(faces)))
        with open(path, 'w') as f:
            f.write('# %s  %d groups\n' % (name, len(out)))
            f.write('mtllib %s.mtl\n' % name)
            f.write('o %s\n' % name)
            for v in vs:
                f.write('v %.4f %.4f %.4f\n' % v)
            for n in ns:
                f.write('vn %.5f %.5f %.5f\n' % tuple(n))
            for role, a, b in out:
                f.write('g %s\nusemtl %s\n' % (role, role))
                for idx, ni in faces[a:b]:
                    f.write('f ' + ' '.join('%d//%d' % (i, ni) for i in idx) + '\n')
        # a minimal mtl so the importer creates one slot per role
        with open(os.path.join(os.path.dirname(path), name + '.mtl'), 'w') as f:
            for role, _, _ in out:
                f.write('newmtl %s\nKd 0.8 0.8 0.8\n\n' % role)
        return len(vs), len(faces), [r for r, _, _ in out]


def build(spec, path, name):
    b = Bake()
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    pier_w = 52.0

    b.box('Wall', x0 - 6, x0 + W + 6, -12, D * 0.08, 0, 30)
    b.box('Wall', x0, x0 + pier_w, 0, 60, 30, GF - 40)
    b.box('Wall', x0 + W - pier_w, x0 + W, 0, 60, 30, GF - 40)
    b.box('Wall', x0 - 4, x0 + W + 4, -8, 60, GF - 40, GF)
    sx0, sx1 = x0 + pier_w, x0 + W - pier_w
    b.box('Glass', sx0, sx1, 40, 43, 40, GF - 48)
    b.box('Interior', sx0 - 6, sx1 + 6, 52, 58, 30, GF - 44)
    for k in range(1, 4):
        mx = sx0 + (sx1 - sx0) * k / 4.0
        b.box('Mullion', mx - 3, mx + 3, 34, 41, 40, GF - 48)
    b.box('Frame', sx0, sx1, 34, 44, 30, 40)

    for f in range(F):
        z0, z1 = GF + f * FH, GF + (f + 1) * FH
        back = spec.get('setback') if (spec.get('setback') and f == F - 1) else 0
        fy = back
        bw = (W - pier_w) / float(BAYS)
        boxes = []
        for k in range(BAYS + 1):
            px = x0 + k * bw
            boxes.append(('Wall', px, px + pier_w, fy, fy + 60, z0, z1 - 34))
        boxes.append(('Band', x0 - 8, x0 + W + 8, fy - 8, fy + 58, z1 - 34, z1))
        for k in range(BAYS):
            wx0, wx1 = x0 + k * bw + pier_w, x0 + (k + 1) * bw
            wz0, wz1 = z0 + 62, z1 - 66
            gy = fy + 27
            boxes += [('Glass', wx0 + 6, wx1 - 6, gy, gy + 2, wz0 + 6, wz1 - 6),
                      ('Interior', wx0, wx1, gy + 20, gy + 26, wz0, wz1),
                      ('Frame', wx0, wx0 + 6, gy - 8, gy + 2, wz0, wz1),
                      ('Frame', wx1 - 6, wx1, gy - 8, gy + 2, wz0, wz1),
                      ('Frame', wx0, wx1, gy - 8, gy + 2, wz1 - 6, wz1),
                      ('Frame', wx0 - 4, wx1 + 4, gy - 14, gy + 2, wz0 - 6, wz0)]
            mx = (wx0 + wx1) / 2.0
            boxes.append(('Mullion', mx - 3, mx + 3, gy - 6, gy + 1, wz0, wz1))
            mz = wz0 + (wz1 - wz0) * 0.62
            boxes.append(('Mullion', wx0, wx1, gy - 6, gy + 1, mz - 3, mz + 3))
        # same rnd draw order as genbuild so the two builds are comparable
        dx = rnd.uniform(-2.2, 2.2) * (W / 100.0)
        dy = rnd.uniform(-1.6, 1.6)
        yaw = rnd.uniform(-0.9, 0.9)
        roll = rnd.uniform(-0.7, 0.7)
        # genbuild creates each floor as an actor AT THE ORIGIN and sets
        # RelativeRotation, so its yaw/roll pivot is world (0,0,0) - not the
        # building centre. Rotating about the centre instead displaced every
        # floor by up to 24 uu in Y, which silently broke the practicals that
        # had been positioned from the component geometry.
        pivot = (0.0, 0.0, 0.0)
        b.xf = lambda p, dx=dx, dy=dy, yaw=yaw, roll=roll, pv=pivot: _xf(p, dx, dy, yaw, roll, pv)
        for r, a1, a2, a3, a4, a5, a6 in boxes:
            b.box(r, a1, a2, a3, a4, a5, a6)
        b.xf = None

    ztop = GF + F * FH
    b.box('Wall', x0, x0 + W, -4, 30, ztop, ztop + PAR)
    b.box('Band', x0 - 8, x0 + W + 8, -14, 40, ztop + PAR, ztop + PAR + 14)
    b.box('Wall', x0, x0 + 26, 30, D, ztop, ztop + PAR - 20)
    b.box('Wall', x0 + W - 26, x0 + W, 30, D, ztop, ztop + PAR - 20)
    b.box('Roof', x0, x0 + W, 20, D, ztop - 8, ztop)
    for u in range(spec.get('roof_units', 1)):
        ux = x0 + W * (0.28 + 0.42 * u)
        uw = 150 + rnd.random() * 130
        b.box('Roof', ux, ux + uw, 180 + u * 90, 180 + u * 90 + uw * 0.8,
              ztop, ztop + 60 + rnd.random() * 50)
    if spec.get('canopy'):
        pr = spec['canopy']
        b.box('Wall', x0 - 10, x0 + W + 10, -pr, 8, GF - 26, GF - 10)
        b.box('Accent', x0 - 10, x0 + W + 10, -pr - 8, -pr, GF - 40, GF - 4)
    return b.write(path, name)
