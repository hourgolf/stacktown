#!/usr/bin/env python3
"""Generate chamfered-box OBJ meshes for Stage 0 gate line B6.

Geometry Script's bevel library is not exposed to Python in UE 5.8 and the
StaticMeshDescription polygon binding is broken (it crashes the editor), so the
chamfered geometry is authored as OBJ on disk and imported via
StaticMeshTools.import_file instead.

A chamfered box = 6 inset face quads + 12 edge strips + 8 corner triangles.
Faces are flat-shaded (one normal per polygon) so each chamfer facet catches
the key light as a distinct highlight - that highlight is what reads as a
softened edge at the approved camera, where the chamfer itself is sub-pixel.
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'obj')


def _verts(h, c):
    V = {}
    for a in range(3):
        o = [i for i in range(3) if i != a]
        for s in (-1, 1):
            for sb in (-1, 1):
                for sd in (-1, 1):
                    p = [0.0, 0.0, 0.0]
                    p[a] = s * h[a]
                    p[o[0]] = sb * (h[o[0]] - c)
                    p[o[1]] = sd * (h[o[1]] - c)
                    V[(a, s, sb, sd)] = tuple(p)
    return V


def polys(dims, c):
    h = [d / 2.0 for d in dims]
    c = min(c, 0.45 * min(dims))
    V = _verts(h, c)
    out = []
    for a in range(3):
        for s in (-1, 1):
            out.append([V[(a, s, sb, sd)]
                        for sb, sd in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a in range(3):
        for b in range(a + 1, 3):
            d = [i for i in range(3) if i not in (a, b)][0]
            oa = [i for i in range(3) if i != a]
            ob = [i for i in range(3) if i != b]
            for s in (-1, 1):
                for t in (-1, 1):
                    def va(sd):
                        k = [None, None]
                        k[oa.index(b)] = t
                        k[oa.index(d)] = sd
                        return V[(a, s, k[0], k[1])]

                    def vb(sd):
                        k = [None, None]
                        k[ob.index(a)] = s
                        k[ob.index(d)] = sd
                        return V[(b, t, k[0], k[1])]
                    out.append([va(-1), va(1), vb(1), vb(-1)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                sg = (sx, sy, sz)
                tri = []
                for a in range(3):
                    o = [i for i in range(3) if i != a]
                    tri.append(V[(a, sg[a], sg[o[0]], sg[o[1]])])
                out.append(tri)
    return out


def _newell(p):
    n = [0.0, 0.0, 0.0]
    for i in range(len(p)):
        u, v = p[i], p[(i + 1) % len(p)]
        n[0] += (u[1] - v[1]) * (u[2] + v[2])
        n[1] += (u[2] - v[2]) * (u[0] + v[0])
        n[2] += (u[0] - v[0]) * (u[1] + v[1])
    return n


def write_obj(path, dims, chamfer, name='chamfered_box'):
    ps = polys(dims, chamfer)
    vs, ns, fs = [], [], []
    for p in ps:
        n = _newell(p)
        cen = [sum(q[i] for q in p) / len(p) for i in range(3)]
        if sum(n[i] * cen[i] for i in range(3)) < 0:
            p = list(reversed(p))
            n = _newell(p)
        ln = max(1e-12, sum(x * x for x in n) ** 0.5)
        n = [x / ln for x in n]
        ns.append(n)
        idx = []
        for q in p:
            vs.append(q)
            idx.append(len(vs))
        fs.append((idx, len(ns)))
    with open(path, 'w') as f:
        f.write('# %s  dims=%s chamfer=%s\n' % (name, dims, chamfer))
        f.write('o %s\n' % name)
        for v in vs:
            f.write('v %.5f %.5f %.5f\n' % v)
        for n in ns:
            f.write('vn %.6f %.6f %.6f\n' % tuple(n))
        for idx, ni in fs:
            f.write('f ' + ' '.join('%d//%d' % (i, ni) for i in idx) + '\n')
    return len(vs), len(fs)


# boxes whose edges are visible at the approved camera
SIZES = [(5.0, 6.0, 210.0), (60.0, 30.0, 360.0), (240.0, 6.0, 5.0),
         (240.0, 26.0, 90.0), (240.0, 30.0, 60.0), (250.0, 19.5, 6.0),
         (250.0, 27.0, 6.0), (250.0, 37.0, 6.0), (1176.0, 146.0, 20.0),
         (1200.0, 170.0, 10.0)]
CHAMFER = 0.25   # 2.5 mm world, fabrication-plausible


def asset_name(d):
    return 'SM_Cx_%s' % '_'.join(str(x).replace('.', 'p') for x in d)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for d in SIZES:
        nm = asset_name(d)
        nv, nf = write_obj(os.path.join(OUT, nm + '.obj'), d, CHAMFER, nm)
        print('%-34s verts=%-4d faces=%-3d %s' % (nm, nv, nf, d))
    print('wrote %d OBJ files to %s' % (len(SIZES), OUT))
