"""A peeling sheet corner — the one shape a chamfered box cannot be.

Fibre lifting reads because of its OUTLINE and its TAPER: it is attached along
one edge, narrows as it lifts, and goes to nothing where it is still stuck
down. A rectangular slab of any thickness reads as a tab glued to the wall,
which is exactly what the 4 uu and the 1.6 uu box versions both did.

Two baked orientations rather than one plus rotation, because getting the
lift direction wrong by 90 degrees is invisible in a transform table and
obvious in a render:

  SM_Peel_V  lies in XZ, thin in Y, attached along its low-Z edge,
             lifting toward -Y   (for a wall face whose normal is -Y)
  SM_Peel_H  lies in XY, thin in Z, attached along its low-Y edge,
             lifting toward +Z   (for a top surface)
"""
import os


def _newell(p):
    n = [0.0, 0.0, 0.0]
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    return n


def _write(path, polys, name):
    vs, ns, fs = [], [], []
    for p in polys:
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
        f.write('o %s\n' % name)
        for v in vs:
            f.write('v %.5f %.5f %.5f\n' % tuple(v))
        for n in ns:
            f.write('vn %.5f %.5f %.5f\n' % tuple(n))
        for idx, ni in fs:
            f.write('f ' + ' '.join('%d//%d' % (i, ni) for i in idx) + '\n')


def peel(path, name, w, d, lift, t, taper=0.42, orient='V'):
    """w across the attached edge, d out to the free edge, lift at the free
    edge, t thickness there. Thickness at the attached edge is 0.18*t so the
    sheet disappears into the surface instead of ending in a step."""
    w2, fw2, t0 = w / 2.0, w * taper / 2.0, t * 0.18

    def pt(u, v, off):
        """u across, v out (0..1), off along the surface normal."""
        x = u
        z = lift * v * v                      # eased, so it curls rather than tilts
        if orient == 'V':
            return [x, -(off), v * d + z * 0.0 + (v * d) * 0.0 + z * 0 + 0.0 + v * 0 + (0.0), ]
        return [x, v * d, off]

    # build explicitly per orientation - clearer than one clever expression
    quads = []
    if orient == 'V':                          # thin in Y, lifts toward -Y
        def P(u, v, off):
            return [u, -off, v * d]
        curl = lambda v: lift * v * v
        A = [P(-w2, 0, t0), P(w2, 0, t0), P(fw2, 1, curl(1) + t), P(-fw2, 1, curl(1) + t)]
        B = [P(-w2, 0, -t0), P(w2, 0, -t0), P(fw2, 1, curl(1)), P(-fw2, 1, curl(1))]
    else:                                      # thin in Z, lifts toward +Z
        def P(u, v, off):
            return [u, v * d, off]
        curl = lambda v: lift * v * v
        A = [P(-w2, 0, t0), P(w2, 0, t0), P(fw2, 1, curl(1) + t), P(-fw2, 1, curl(1) + t)]
        B = [P(-w2, 0, -t0), P(w2, 0, -t0), P(fw2, 1, curl(1)), P(-fw2, 1, curl(1))]

    quads.append(A)                            # top
    quads.append(list(reversed(B)))            # bottom
    for i in range(4):                         # sides
        j = (i + 1) % 4
        quads.append([A[i], A[j], B[j], B[i]])
    _write(path, quads, name)
    return path
