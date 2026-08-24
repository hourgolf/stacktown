"""A glue bead whose section varies along its length.

The box version failed for the same reason the box peel failed: every segment
was an identical extrusion with a square, chamfered end, so a run read as a row
of little rails with faceted nubs where each one stopped. Squeeze-out is thick
where it was pressed out and dies to nothing at the ends.

Swept K-gon along X. Radius is a smooth taper at both ends multiplied by two
out-of-phase sines, so no two beads in a run share a silhouette. Ends close on
a small cap rather than a point - a true point produces degenerate triangles
that the importer silently drops.
"""
import math
from peelgen import _write


def bead(path, name, length, r0, seed=0, k=8, n=30, taper=0.26, floor=0.10):
    ph1 = (seed * 1.7) % (2 * math.pi)
    ph2 = (seed * 3.1 + 1.1) % (2 * math.pi)
    f1, f2 = 1.6 + 0.4 * ((seed * 7) % 3), 3.3 + 0.5 * ((seed * 5) % 3)

    def smooth(u):
        u = max(0.0, min(1.0, u))
        return u * u * (3.0 - 2.0 * u)

    def radius(t):
        env = smooth(t / taper) * smooth((1.0 - t) / taper)
        mod = 1.0 + 0.24 * math.sin(2 * math.pi * f1 * t + ph1) \
                  + 0.13 * math.sin(2 * math.pi * f2 * t + ph2)
        return r0 * max(floor, env * mod)

    rings = []
    for i in range(n + 1):
        t = i / float(n)
        x = (t - 0.5) * length
        r = radius(t)
        ring = []
        for j in range(k):
            a = 2 * math.pi * j / k
            ring.append([x, r * math.cos(a), r * math.sin(a)])
        rings.append(ring)

    quads = []
    for i in range(n):
        for j in range(k):
            j2 = (j + 1) % k
            quads.append([rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]])
    quads.append(list(reversed(rings[0])))
    quads.append(rings[-1])
    _write(path, quads, name)
    return path
