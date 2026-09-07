#!/usr/bin/env python3
"""THE per-instance Custom Primitive Data channel map. One authority.

    python3 Content/Python/cpdmap.py     self-test against the live master

The declarations reserved this layout before wear existed, and warned why:
"If patina silently claims float 0 and glow retrofits later, that is the
two-copies-of-one-table drift this project is bitten by roughly once a
session." Wear then did the mirror image of that on 2026-09-02 - the first
wire claimed 1, 2 and 3, which GlowLevel, GlowState and Selection already
own. Caught by reading the declaration before believing the code. The map
lives here now so the next claim has one place to look.

D16 also NARROWED channel 0. The original entry read "Age 0..1 unworn ->
handled: edge polish, sheen, grain contrast", folding oxidation and burnish
together. D16 split them, and the split is the whole point of the ladder: a
long-loved block is old AND burnished, a neglected one keeps sharp arrises
because no hand has worn them. So Age keeps channel 0 and means oxidation
along the species' own curve; edge polish moves to Attention.
"""
CHANNELS = (
    (0, 'Age',       'oxidises along THIS species curve; walnut lightens'),
    (1, 'GlowLevel', 'B4 night window emission, 0 = daytime carved mass'),
    (2, 'GlowState', 'B4 encoded hue: green positive / red negative'),
    (3, 'Selection', 'the selection ring, separate so it never recolours state'),
    (4, 'Attention', 'edge burnish vs settled dust; -1 sharp, 0 today, +1 polished'),
    (5, 'Failure',   '0->0.3 tired (never alarming); 0.6 failed; 0.6->0.8 neglect chars - the 0.3-0.6 band stays empty (LOOK 2026-09-07 08:42)'),
    (6, 'Scorch',    'blackens TOP-DOWN, surface only, repairable'),
    (7, None,        'reserved'),
)

# The channels wear owns. The rest belong to B4's glow and to selection.
WEAR = tuple((n, i) for i, n, _ in CHANNELS if n in
             ('Age', 'Attention', 'Failure', 'Scorch'))


def index(name):
    for i, n, _ in CHANNELS:
        if n == name:
            return i
    raise KeyError(name)


def selftest():
    """Double-entry: the material must agree with this table, read back from
    the asset - never a comment in two files."""
    import json
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), 'Tools', 'measure'))
    import _path      # noqa: F401
    import wear as W  # noqa
    bad = []
    for name, idx in WEAR:
        e = W.find_param(name)
        if e is None:
            bad.append('%s: absent from the master' % name)
            continue
        p = W._props(e, ['PrimitiveDataIndex', 'bUseCustomPrimitiveData',
                         'DefaultValue'])
        if p.get('PrimitiveDataIndex') != idx:
            bad.append('%s: master says ch%s, map says ch%d'
                       % (name, p.get('PrimitiveDataIndex'), idx))
        if p.get('bUseCustomPrimitiveData') is not True:
            bad.append('%s: not reading custom primitive data' % name)
        if p.get('DefaultValue') != 0.0:
            bad.append('%s: default %s, must be 0.0 to stay inert'
                       % (name, p.get('DefaultValue')))
    for line in bad:
        print('  FAIL', line)
    print('cpdmap self-test:', 'PASS' if not bad else '%d FAILURES' % len(bad))
    return not bad


if __name__ == '__main__':
    raise SystemExit(0 if selftest() else 1)
