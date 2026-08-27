"""Assemble Uniblocks kit pieces into things we need. Pure placement maths.

MEASURED, not assumed. The first attempt guessed offsets and produced a row of
separated slabs, because every piece type carries a different origin:

    end_base / end_wall_t10 / end_wall_top_t10   x 0..50,  y -50..0
    side_base_x50                                x 0..100, y -50..0
    side_wall_x50t10 / side_wall_top_x50t10      x 0..100, y -10..0

Two consequences the arithmetic has to respect:

  * `side_wall` is only 10 DEEP - it is ONE long wall, not a channel. A bed
    needs it twice: once at the back and once translated to the front edge.
  * the far end cap must be turned 180 about its own offset origin. Yaw 180
    maps local (lx,ly) to world (px-lx, py-ly), so the actor goes at
    (length, -DEPTH) rather than at the corner it visually occupies.

Nothing here imports `unreal`: it returns placements as plain data, so the
layout can be self-tested and so both the actor path and the fast bake path
can consume it.
"""
# Full package paths, because fastbake loads by path and a bare mesh name is
# not resolvable. Verified on disk: every flowerbed piece lives here.
GARDEN = '/Game/Uniblocks/Meshes/Garden/Parts/'
STEM = GARDEN + 'SM_UBP_Flowerbed_'
SEG = 100.0          # a side segment
CAP = 50.0           # an end cap
DEPTH = 50.0         # front to back
WALL_H = 100.0       # top of wall / where the coping sits
WALL_D = 10.0        # how deep a side wall piece is


def bed(segments=2, thickness='t10', x=0.0, y=0.0, z=0.0):
    """A raised bed: end cap + `segments` side runs + end cap.

    Returns [(mesh, (x, y, z), yaw)]. Length is CAP + segments*SEG + CAP.
    """
    if segments < 1:
        raise ValueError('a bed needs at least one side segment')
    st = thickness
    out = []
    # low end cap, at the origin corner
    for mesh, dz in (('end_base', 0.0), ('end_wall_%s' % st, 0.0),
                     ('end_wall_top_%s' % st, WALL_H)):
        out.append((STEM + mesh, (x, y, z + dz), 0.0))
    # side runs: base spans the full depth, walls are placed twice
    for k in range(segments):
        sx = x + CAP + k * SEG
        out.append((STEM + 'side_base_x50', (sx, y, z), 0.0))
        for dy in (0.0, -(DEPTH - WALL_D)):        # back wall, then front
            out.append((STEM + 'side_wall_x50%s' % st, (sx, y + dy, z), 0.0))
            out.append((STEM + 'side_wall_top_x50%s' % st,
                        (sx, y + dy, z + WALL_H), 0.0))
    # high end cap, turned 180 about its own offset origin
    L = CAP + segments * SEG + CAP
    for mesh, dz in (('end_base', 0.0), ('end_wall_%s' % st, 0.0),
                     ('end_wall_top_%s' % st, WALL_H)):
        out.append((STEM + mesh, (x + L, y - DEPTH, z + dz), 180.0))
    return out


def bed_length(segments):
    return CAP + segments * SEG + CAP


def bed_extent(segments, x=0.0, y=0.0):
    """The rectangle a bed occupies: (x0, y0, x1, y1)."""
    return (x, y - DEPTH, x + bed_length(segments), y)


def short(mesh):
    """The piece name without its package path, for component naming."""
    return mesh.rsplit('/', 1)[-1][len('SM_UBP_Flowerbed_'):]


def _footprint(mesh):
    """Local (x0, y0, x1, y1) of a piece, from the measured bounds above."""
    n = short(mesh)
    if n.startswith('end'):
        return (0.0, -DEPTH, CAP, 0.0)
    if n.startswith('side_base'):
        return (0.0, -DEPTH, SEG, 0.0)
    return (0.0, -WALL_D, SEG, 0.0)          # side walls and copings


def _selftest():
    import math
    for segs in (1, 2, 4):
        ps = bed(segs)
        x0, y0, x1, y1 = bed_extent(segs)
        for mesh, (px, py, _pz), yaw in ps:
            fx0, fy0, fx1, fy1 = _footprint(mesh)
            c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            xs, ys = [], []
            for lx, ly in ((fx0, fy0), (fx1, fy0), (fx0, fy1), (fx1, fy1)):
                xs.append(px + lx*c - ly*s)
                ys.append(py + lx*s + ly*c)
            # nothing may stick out of the bed's own rectangle
            assert min(xs) >= x0 - 0.5 and max(xs) <= x1 + 0.5, (mesh, xs)
            assert min(ys) >= y0 - 0.5 and max(ys) <= y1 + 0.5, (mesh, ys)
        # both end caps present, and one base per side segment
        assert all(m.startswith(GARDEN) for m, _p, _y in ps), 'paths must be full'
        assert sum(1 for m, _p, _y in ps if m.endswith('end_base')) == 2
        assert sum(1 for m, _p, _y in ps if 'side_base' in m) == segs
        # walls twice per segment: a side wall is one wall, not a channel
        assert sum(1 for m, _p, _y in ps if 'side_wall_x50t' in m) == segs*2
    return True


if __name__ == '__main__':
    print('ubkit self-test:', _selftest())
    for segs in (1, 2, 3):
        print('  %d segment(s): %4.0f uu long, %2d pieces'
              % (segs, bed_length(segs), len(bed(segs))))
