"""Crop the viewport's letterbox/pillarbox before measuring.

The editor viewport does not always fill the captured buffer; when it does not,
the surround is pure black. Measuring the whole buffer then mixes a constant 0
into every statistic - it dropped board sd from 87 to 42 depending only on
whether the bars were there, which is a measurement artefact masquerading as a
lighting change. Find the live rectangle first, and measure only that.
"""
import img

def bounds(a, thresh=8, step=7):
    def col(x): return sum(a.px[y*a.w + x] for y in range(0, a.h, step))
    def row(y): return sum(a.px[y*a.w + x] for x in range(0, a.w, step))
    n_c = len(range(0, a.h, step)) * thresh
    n_r = len(range(0, a.w, step)) * thresh
    L = next((x for x in range(a.w) if col(x) > n_c), 0)
    R = next((x for x in range(a.w-1, -1, -1) if col(x) > n_c), a.w-1)
    T = next((y for y in range(a.h) if row(y) > n_r), 0)
    B = next((y for y in range(a.h-1, -1, -1) if row(y) > n_r), a.h-1)
    return L, T, R+1, B+1

def stats(path):
    a = img.load(path)
    L, T, R, B = bounds(a)
    v = img.patch(a, L, T, R, B)
    blown = 100.0*sum(1 for p in v if p >= 250)/len(v)
    crush = 100.0*sum(1 for p in v if p <= 4)/len(v)
    return dict(w=R-L, h=B-T, mean=img.mean(v), sd=img.sd(v),
                blown=blown, crushed=crush, box=(L, T, R, B))

# known answer: a frame with bars must measure the same as the same frame
# without them. Synthesise one rather than trust that it does.
class _F:  pass
if __name__ == '__main__':
    f = _F(); f.w, f.h = 20, 10
    f.px = [0]*20*10
    for y in range(2, 8):
        for x in range(5, 15): f.px[y*20+x] = 200
    L, T, R, B = bounds(f, thresh=8, step=1)
    assert (L, T, R, B) == (5, 2, 15, 8), (L, T, R, B)
    assert abs(img.mean(img.patch(f, L, T, R, B)) - 200.0) < 1e-6
    print('live.bounds self-check: pass')
