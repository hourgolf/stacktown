"""Paths as centrelines, not as rectangles.

A path was a rectangle everywhere in this project, and a rectangle cannot
answer the three questions everything placed outdoors has to ask: where along
it am I, which side of it am I on, and which way does it run. So seating,
lighting and tree pits each grew their own arithmetic, and the park ended up
with a bench dropped on each of seven overlapping boxes.

A Path is a centreline (a to b) plus a width. It yields its rectangle when
something needs a slab, and it yields POINTS ALONG IT WITH A BEARING when
something needs to be placed. Pure functions, no Unreal import, same as
citygeom and zonelayout - so it can be self-tested without an editor.

Block-local coordinates, like everything else that feeds a builder.
"""
import math


class Path(object):
    def __init__(self, a, b, width, name=''):
        self.a, self.b, self.width, self.name = a, b, float(width), name

    @property
    def length(self):
        return math.hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])

    @property
    def bearing(self):
        """Degrees, the direction the path runs from a to b."""
        return math.degrees(math.atan2(self.b[1] - self.a[1], self.b[0] - self.a[0]))

    def point(self, t):
        return (self.a[0] + (self.b[0] - self.a[0])*t,
                self.a[1] + (self.b[1] - self.a[1])*t)

    def normal(self):
        """Unit vector 90 degrees left of the direction of travel."""
        L = self.length or 1.0
        return (-(self.b[1] - self.a[1])/L, (self.b[0] - self.a[0])/L)

    def rect(self):
        """Axis-aligned slab. Exact for an axis-aligned path, which is what a
        card model uses; a diagonal returns its bounding box and the caller is
        expected to know that."""
        nx, ny = self.normal()
        h = self.width/2.0
        xs = [self.a[0] + s*nx*h for s in (-1, 1)] + [self.b[0] + s*nx*h for s in (-1, 1)]
        ys = [self.a[1] + s*ny*h for s in (-1, 1)] + [self.b[1] + s*ny*h for s in (-1, 1)]
        return (min(xs), min(ys), max(xs), max(ys))

    def along(self, spacing, margin=0.0, side=0.0, facing=None):
        """[(x, y, yaw)] spaced down the path.

        `side` offsets perpendicular: +1 is one full half-width to the left of
        travel, -1 to the right, 0 on the centreline. `facing` is the bearing
        each item should look along; None means 'across the path, outward',
        which is what a bench or a shopfront wants.
        """
        L = self.length
        usable = L - 2*margin
        if usable <= 0 or spacing <= 0:
            return []
        n = max(1, int(usable // spacing))
        nx, ny = self.normal()
        off = side*self.width/2.0
        out = []
        for i in range(n + 1):
            t = (margin + usable*(i/float(n) if n else 0.5))/L
            px, py = self.point(t)
            yaw = facing if facing is not None else math.degrees(math.atan2(ny, nx))
            if facing is None and side < 0:
                yaw += 180.0
            out.append((px + nx*off, py + ny*off, yaw))
        return out


def rects(paths):
    return [p.rect() for p in paths]


if __name__ == '__main__':
    # known answers, checked before anything trusts this
    p = Path((0.0, 0.0), (1000.0, 0.0), 100.0)
    assert abs(p.length - 1000.0) < 1e-6
    assert abs(p.bearing - 0.0) < 1e-6
    assert p.rect() == (0.0, -50.0, 1000.0, 50.0), p.rect()
    n = p.normal()
    assert abs(n[0]) < 1e-9 and abs(n[1] - 1.0) < 1e-9, n
    pts = p.along(500.0, margin=100.0)
    assert len(pts) == 2, pts
    assert abs(pts[0][0] - 100.0) < 1e-6 and abs(pts[-1][0] - 900.0) < 1e-6, pts
    assert all(abs(y) < 1e-9 for _x, y, _c in pts)
    left = p.along(800.0, margin=100.0, side=1.0)
    assert abs(left[0][1] - 50.0) < 1e-6, left
    right = p.along(800.0, margin=100.0, side=-1.0)
    assert abs(right[0][1] + 50.0) < 1e-6, right
    # outward from the RIGHT of an eastward path is -Y, i.e. 270 deg. The
    # first version of this assertion expected 180 and the code was right.
    assert abs((right[0][2] % 360.0) - 270.0) < 1e-6, right[0][2]
    assert abs((left[0][2] % 360.0) - 90.0) < 1e-6, left[0][2]
    v = Path((0.0, 0.0), (0.0, 800.0), 60.0)
    assert v.rect() == (-30.0, 0.0, 30.0, 800.0), v.rect()
    assert abs(v.bearing - 90.0) < 1e-6
    print('paths.py self-check: pass')
