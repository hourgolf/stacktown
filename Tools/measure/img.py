"""Fast-enough image measurement without numpy.

PNG is decoded by routing it through `sips -s format bmp`, because a pure-python
PNG unfilter over 3.1 M pixels costs about a minute per frame and this rig runs
dozens of frames. BMP is a flat byte array with a header.

All statistics here are RELATIVE. Absolute luma thresholds are worthless across
captures with different exposure or vignetting (HANDOFF §5), so nothing in this
file compares an image to a constant - only images to each other, or a patch to
its own detrended self.
"""
import os, struct, subprocess, math

class Img:
    __slots__ = ('w','h','px')      # px: bytearray of luma, row-major, len w*h

    def __init__(self, w, h, px):
        self.w, self.h, self.px = w, h, px

    def at(self, x, y):
        return self.px[y*self.w + x]

def load(path):
    """PNG or BMP -> Img of 8-bit luma."""
    if path.lower().endswith('.png'):
        bmp = path + '.bmp'
        if (not os.path.exists(bmp)) or os.path.getmtime(bmp) < os.path.getmtime(path):
            subprocess.run(['sips','-s','format','bmp',path,'--out',bmp],
                           check=True, capture_output=True)
        path = bmp
    d = open(path,'rb').read()
    if d[:2] != b'BM': raise ValueError('not a BMP: %s' % path)
    off = struct.unpack('<I', d[10:14])[0]
    w, h = struct.unpack('<ii', d[18:26])
    bpp  = struct.unpack('<H', d[28:30])[0]
    if bpp not in (24, 32): raise ValueError('expected 24/32bpp, got %d' % bpp)
    px_bytes = bpp // 8
    topdown = h < 0
    h = abs(h)
    stride = ((w*px_bytes + 3)//4)*4      # BMP rows pad to 4 bytes; 24bpp needs it
    px = bytearray(w*h)
    # Rec.709 luma, integer weights /1024 so the whole loop stays in ints.
    KR, KG, KB = 218, 732, 74
    for y in range(h):
        srow = off + (y if topdown else (h-1-y))*stride
        row = d[srow:srow+stride]
        base = y*w
        for x in range(w):
            i = x*px_bytes
            # sips writes BGR(A)
            b, g, r = row[i], row[i+1], row[i+2]
            px[base+x] = (r*KR + g*KG + b*KB) >> 10
    return Img(w, h, px)

def patch(im, x0, y0, x1, y1):
    return [im.px[y*im.w + x] for y in range(y0,y1) for x in range(x0,x1)]

def mean(v):
    return sum(v)/float(len(v)) if v else 0.0

def sd(v):
    if len(v) < 2: return 0.0
    m = mean(v)
    return math.sqrt(sum((a-m)**2 for a in v)/(len(v)-1))

def detrended_sd(im, x0, y0, x1, y1):
    """SD of a patch after removing its own smooth illumination gradient.

    A facade's lighting falloff swings wider than any surface feature, so raw
    patch SD measures the light rig, not the surface. Fit and remove a plane
    (least squares in x and y), then measure what is left.
    """
    pts = [(x, y, im.px[y*im.w+x]) for y in range(y0,y1) for x in range(x0,x1)]
    n = float(len(pts))
    if n < 8: return 0.0
    mx = sum(p[0] for p in pts)/n; my = sum(p[1] for p in pts)/n
    mz = sum(p[2] for p in pts)/n
    sxx = syy = sxy = sxz = syz = 0.0
    for x,y,z in pts:
        dx, dy, dz = x-mx, y-my, z-mz
        sxx += dx*dx; syy += dy*dy; sxy += dx*dy; sxz += dx*dz; syz += dy*dz
    det = sxx*syy - sxy*sxy
    if abs(det) < 1e-9: a = b = 0.0
    else:
        a = ( syy*sxz - sxy*syz)/det
        b = (-sxy*sxz + sxx*syz)/det
    res = [z - mz - a*(x-mx) - b*(y-my) for x,y,z in pts]
    return math.sqrt(sum(r*r for r in res)/(n-1))

def mean_abs_diff(a, b, x0=None, y0=None, x1=None, y1=None):
    if a.w != b.w or a.h != b.h: raise ValueError('size mismatch')
    x0 = 0 if x0 is None else x0; y0 = 0 if y0 is None else y0
    x1 = a.w if x1 is None else x1; y1 = a.h if y1 is None else y1
    tot = 0; n = 0
    for y in range(y0,y1):
        ra = a.px[y*a.w+x0:y*a.w+x1]; rb = b.px[y*b.w+x0:y*b.w+x1]
        tot += sum(abs(p-q) for p,q in zip(ra,rb)); n += (x1-x0)
    return tot/float(n)

def pct_blown(im, thresh=250):
    n = sum(1 for v in im.px if v >= thresh)
    return 100.0*n/len(im.px)

def pct_crushed(im, thresh=4):
    n = sum(1 for v in im.px if v <= thresh)
    return 100.0*n/len(im.px)


def highpass_sd(im, x0, y0, x1, y1, r=4):
    """SD of the patch after removing a (2r+1)-square local mean.

    Whole-frame mean-abs-diff and plane-detrended SD BOTH miss a change in
    surface micro-detail: measured here, PaperTiling 0.05 -> 0.40 visibly
    changed the fibre on a pier and moved whole-frame diff by 4.1 (floor 3.9)
    and detrended patch SD by 0.15 on 20.2. The eye saw it immediately.
    Detrending removes a PLANE; a facade's structure is not a plane, so macro
    contrast still dominates. Subtracting a LOCAL mean leaves only detail
    finer than the window, which is what "does this read as card" is about.
    """
    w = x1 - x0
    rows = [[im.px[y*im.w + x] for x in range(x0, x1)] for y in range(y0, y1)]
    h = len(rows)
    # separable box blur
    blur = [[0.0]*w for _ in range(h)]
    for y in range(h):
        row = rows[y]; acc = []
        for x in range(w):
            a = max(0, x-r); b = min(w, x+r+1)
            acc.append(sum(row[a:b])/float(b-a))
        blur[y] = acc
    out = []
    for y in range(h):
        a = max(0, y-r); b = min(h, y+r+1)
        for x in range(w):
            m = sum(blur[yy][x] for yy in range(a, b))/float(b-a)
            out.append(rows[y][x] - m)
    return sd(out)


def gradient_energy(im, x0, y0, x1, y1):
    """Mean |horizontal first difference| inside a patch - a cheap, robust
    proxy for how much fine structure the surface carries."""
    tot = 0; n = 0
    for y in range(y0, y1):
        base = y*im.w
        for x in range(x0, x1-1):
            tot += abs(im.px[base+x+1] - im.px[base+x]); n += 1
    return tot/float(n) if n else 0.0


def anisotropy(im, x0, y0, x1, y1, r=4):
    """Directional bias of the surface detail in a patch.

    Returns (mean|dx|, mean|dy|, ratio) of the HIGH-PASS residual, so the
    facade's own lighting gradient does not swamp the texture. A single-plane
    world projection leaves one image axis with almost no variation on any
    surface perpendicular to the missing coordinate - corduroy - and this is
    the number that names it. Isotropic paper gives a ratio near 1.
    """
    w = x1 - x0
    rows = [[im.px[y*im.w + x] for x in range(x0, x1)] for y in range(y0, y1)]
    h = len(rows)
    blur = []
    for y in range(h):
        row = rows[y]; acc = []
        for x in range(w):
            a = max(0, x-r); b = min(w, x+r+1)
            acc.append(sum(row[a:b])/float(b-a))
        blur.append(acc)
    res = [[0.0]*w for _ in range(h)]
    for y in range(h):
        a = max(0, y-r); b = min(h, y+r+1)
        for x in range(w):
            m = sum(blur[yy][x] for yy in range(a, b))/float(b-a)
            res[y][x] = rows[y][x] - m
    dx = [abs(res[y][x+1]-res[y][x]) for y in range(h) for x in range(w-1)]
    dy = [abs(res[y+1][x]-res[y][x]) for y in range(h-1) for x in range(w)]
    mx, my = mean(dx), mean(dy)
    return mx, my, (max(mx, my)/max(min(mx, my), 1e-6))
