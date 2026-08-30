"""THE CLAMPED-NEIGHBOUR AUDIT - a source check, not a geometry one.

Run it after touching any bay/post loop:  python3 Tools/measure/clampaudit.py

FOUR instances of this family were fixed by hand before anyone wrote this -
the front pier and its window opening, the flank pilaster and its spandrel,
the front pilaster and its spandrel - each found by reading geometry off a
census and each treated as its own bug. That is the same road the lapped-span
family took, and the lesson from that one was that the moment to suspect a
family is the SECOND instance.

The fault is always the same two lines, near each other:

    POST placed with a clamp     px = min(base + k*step, limit)
    NEIGHBOUR from the raw grid  wx1 = base + (k+1)*step

The post is pulled in so it cannot overhang; the thing beside it is still
measured off the grid the post left. Geometry-level detection finds the
SYMPTOM (a coplanar pair); this finds the CAUSE, in source, including cases
that happen not to produce a visible pair today.

Reports every clamped placement, and whether a raw-grid expression using the
same step appears within a window of lines after it.

IT OVER-REPORTS BY DESIGN and the judgement stays human. A continuous RUN
that tiles a whole elevation edge to edge - the deco stepped parapet - uses
the raw grid legitimately, because nothing was clamped out of its way. Read
the two lines before believing the pairing; the tool finds candidates, not
verdicts.
"""
import re, sys

FILES = ['Content/Python/genbuild.py', 'Content/Python/step_elevations.py']
CLAMP = re.compile(r'=\s*min\(\s*([A-Za-z_0-9]+)\s*\+\s*(\w+)\s*\*\s*([A-Za-z_0-9]+)\s*,')
WINDOW = 140

for fn in FILES:
    lines = open(fn).readlines()
    print('\n=== %s ===' % fn)
    for i, ln in enumerate(lines):
        m = CLAMP.search(ln)
        if not m:
            continue
        base, idx, step = m.groups()
        # a raw-grid use of the SAME base and step, without min(), nearby
        raw = re.compile(r'%s\s*\+\s*\(?\s*\w+\s*\+\s*1\s*\)?\s*\*\s*%s'
                         % (re.escape(base), re.escape(step)))
        hits = [(j + 1, lines[j].strip())
                for j in range(i, min(len(lines), i + WINDOW))
                if raw.search(lines[j]) and 'min(' not in lines[j]]
        status = 'RAW GRID NEARBY' if hits else 'ok - no raw-grid sibling'
        print('  L%-5d clamp on %s + %s*%s   %s' % (i + 1, base, idx, step, status))
        for j, t in hits[:2]:
            print('        L%-5d %s' % (j, t[:88]))
