#!/usr/bin/env python3
"""D24's window slots: light through etched openings, invisible by day.

    python3 Content/Python/wear_windows.py --wire
    python3 Content/Python/wear_windows.py --revert

B1 "windowless masses BY DAY", B4 "windows exist only as night light through
etched slots". A window here is not a hole or a pane - by day there is nothing
there at all, because the whole emissive term is multiplied by NightAmount = 0.
That is construction, not tuning: no daylight frame can show a window and no
badly-set value can leak one in.

BANDS AND BAYS, NOT STRIPES. A horizontal band alone reads as a fluorescent
tube running through the block. Breaking it along the facade gives a rhythm of
separate lights, which is what a window grid is - and it is the difference
between a building and a striped box.

    floors = frac(localZ / FLOOR)   lit band  BAND_A..BAND_B      22%
    bays   = frac(localX / BAY)     lit part  BAY_A..BAY_B        55%
    window = band * bays * verticalFaces
    coverage ~ 12%

REUSES what the other chains already compute rather than duplicating it:
LocalPosition from the Scorch chain, and the |normal| the curvature mask
builds. Parts are the budget in this direction and so are nodes.

verticalFaces suppresses the ROOF. A window on a roof is wrong, and the top
face would otherwise carry the brightest slots because it faces the boom most
directly.

SOFT EDGES on every band. A hard step aliases badly at board range, where a
window is two or three pixels; a short ramp reads as a lit opening rather than
as a flickering dot.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path            # noqa: F401,E402
import ue               # noqa: E402
import woodmaster as WM  # noqa: E402
import wear as W        # noqa: E402

M = W.M
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
MAT = {'refPath': WM.TARGET}
LEDGER = os.path.join(W.OUT, 'windows_ledger.json')

FLOOR = 320.0          # uu between floors
BAND_A, BAND_B = 0.15, 0.37      # the lit stripe within a floor  (22%)
BAY = 200.0            # uu between window centres along the facade
BAY_A, BAY_B = 0.20, 0.75        # the lit part of a bay          (55%)
SOFT_Z, SOFT_X = 0.03, 0.05      # ramp widths, in frac units
VFACE_HI, VFACE_SOFT = 0.60, 0.20  # |n.z| above which a face is roof


def _add(cls, x, y):
    return json.loads(ue.tool(M, 'add_expression', {
        'material_or_function': MAT,
        'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
        'x': x, 'y': y}))['returnValue']


def _set(n, v):
    ue.tool(OBJ, 'set_properties', {'instance': n, 'values': json.dumps(v)})


def _conn(a, ao, b, bi):
    ue.tool(M, 'connect_expressions', {'from_expression': a, 'from_output_name': ao,
                                       'to_expression': b, 'to_input_name': bi})


def _band(src, out_name, lo, hi, soft, x, y, added):
    """saturate((v-lo)/soft) * saturate((hi-v)/soft) - a soft-edged stripe."""
    klo = _add('Constant', x, y); _set(klo, {'R': lo}); added.append((out_name+'_lo', klo))
    khi = _add('Constant', x, y+40); _set(khi, {'R': hi}); added.append((out_name+'_hi', khi))
    ks = _add('Constant', x, y+80); _set(ks, {'R': soft}); added.append((out_name+'_soft', ks))
    s1 = _add('Subtract', x+150, y);   added.append((out_name+'_v-lo', s1))
    d1 = _add('Divide',   x+250, y);   added.append((out_name+'_/soft1', d1))
    a1 = _add('Saturate', x+340, y);   added.append((out_name+'_satA', a1))
    s2 = _add('Subtract', x+150, y+60); added.append((out_name+'_hi-v', s2))
    d2 = _add('Divide',   x+250, y+60); added.append((out_name+'_/soft2', d2))
    a2 = _add('Saturate', x+340, y+60); added.append((out_name+'_satB', a2))
    mu = _add('Multiply', x+440, y+30); added.append((out_name, mu))
    _conn(src, '', s1, 'A');  _conn(klo, '', s1, 'B')
    _conn(s1, '', d1, 'A');   _conn(ks, '', d1, 'B');  _conn(d1, '', a1, '')
    _conn(khi, '', s2, 'A');  _conn(src, '', s2, 'B')
    _conn(s2, '', d2, 'A');   _conn(ks, '', d2, 'B');  _conn(d2, '', a2, '')
    _conn(a1, '', mu, 'A');   _conn(a2, '', mu, 'B')
    return mu


def wire():
    W._pie_guard()
    ex = json.loads(ue.tool(M, 'get_expressions', {'material_or_function': MAT}))['returnValue']
    names = {e['refPath'].rsplit(':', 1)[-1]: e for e in ex}
    for need in ('MaterialExpressionLocalPosition_1', 'MaterialExpressionComponentMask_3'):
        assert need in names, 'expected to reuse %s and it is not there' % need
    lpos = names['MaterialExpressionLocalPosition_1']   # Scorch's
    absnz = names['MaterialExpressionComponentMask_3']  # |normal|.z from the curvature chain
    glow = json.load(open(os.path.join(W.OUT, 'glow_ledger.json')))
    gref = {a['role']: a['refPath'] for a in glow['added']}
    added = []

    # --- floors: frac(localZ / FLOOR) ---
    kf = _add('Constant', -3200, 2700); _set(kf, {'R': FLOOR}); added.append(('FLOOR', kf))
    dz = _add('Divide', -3050, 2680);   added.append(('localZ/FLOOR', dz))
    fz = _add('Frac', -2950, 2680);     added.append(('frac floors', fz))
    _conn(lpos, 'Z', dz, 'A'); _conn(kf, '', dz, 'B'); _conn(dz, '', fz, '')
    bandz = _band(fz, 'band', BAND_A, BAND_B, SOFT_Z, -2800, 2640, added)

    # --- bays: frac(localX / BAY) ---
    mx = _add('ComponentMask', -3200, 2900); _set(mx, {'R': True, 'G': False, 'B': False, 'A': False})
    added.append(('localX mask', mx))
    _conn(lpos, 'XYZ', mx, '')
    kb = _add('Constant', -3200, 2960); _set(kb, {'R': BAY}); added.append(('BAY', kb))
    dx = _add('Divide', -3050, 2900);   added.append(('localX/BAY', dx))
    fx = _add('Frac', -2950, 2900);     added.append(('frac bays', fx))
    _conn(mx, '', dx, 'A'); _conn(kb, '', dx, 'B'); _conn(dx, '', fx, '')
    bandx = _band(fx, 'bays', BAY_A, BAY_B, SOFT_X, -2800, 2860, added)

    # --- verticalFaces: suppress the roof ---
    kv = _add('Constant', -2800, 3100); _set(kv, {'R': VFACE_HI}); added.append(('VFACE_HI', kv))
    kvs = _add('Constant', -2800, 3140); _set(kvs, {'R': VFACE_SOFT}); added.append(('VFACE_SOFT', kvs))
    sv = _add('Subtract', -2650, 3100); added.append(('hi-|nz|', sv))
    dv = _add('Divide', -2550, 3100);   added.append(('/soft', dv))
    av = _add('Saturate', -2450, 3100); added.append(('verticalFaces', av))
    _conn(kv, '', sv, 'A'); _conn(absnz, '', sv, 'B')
    _conn(sv, '', dv, 'A'); _conn(kvs, '', dv, 'B'); _conn(dv, '', av, '')

    # --- window = band * bays * verticalFaces, then into the glow chain ---
    m1 = _add('Multiply', -2300, 2800); added.append(('band*bays', m1))
    m2 = _add('Multiply', -2200, 2860); added.append(('window mask', m2))
    _conn(bandz, '', m1, 'A'); _conn(bandx, '', m1, 'B')
    _conn(m1, '', m2, 'A');    _conn(av, '', m2, 'B')
    m3 = _add('Multiply', -1050, 2560); added.append(('glow*window', m3))
    _conn({'refPath': gref['x GlowScale']}, '', m3, 'A')
    _conn(m2, '', m3, 'B')
    ue.tool(M, 'connect_to_output', {'expression': m3, 'output_name': '',
                                     'material_property': 'MP_EmissiveColor'})
    ue.tool(M, 'recompile', {'material_or_function': MAT})
    rec = [{'role': r, 'refPath': n['refPath']} for r, n in added]
    json.dump({'added': rec, 'prev_emissive': gref['x GlowScale']},
              open(LEDGER, 'w'), indent=1)
    r = json.loads(ue.tool(M, 'get_property_input', {
        'material': MAT, 'material_property': 'MP_EmissiveColor'}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    e = r.get('expression') if isinstance(r, dict) else None
    got = ((e.get('refPath') if isinstance(e, dict) else e) or '?')
    print('added %d nodes; coverage ~%.0f%% of a facade'
          % (len(rec), 100 * (BAND_B - BAND_A) * (BAY_B - BAY_A)))
    print('MP_EmissiveColor <- %s   %s'
          % (got.rsplit(':', 1)[-1],
             'OK' if got == m3['refPath'] else 'WRONG'))
    return rec


def revert():
    W._pie_guard()
    led = json.load(open(LEDGER))
    ue.tool(M, 'connect_to_output', {'expression': {'refPath': led['prev_emissive']},
                                     'output_name': '',
                                     'material_property': 'MP_EmissiveColor'})
    for a in led['added']:
        ue.tool(M, 'delete_expression', {'material_or_function': MAT,
                                         'expression': {'refPath': a['refPath']}})
    W.recompile()
    print('reverted %d nodes; emissive back to the unmasked glow' % len(led['added']))


if __name__ == '__main__':
    {'--wire': wire, '--revert': revert}[sys.argv[1] if len(sys.argv) > 1 else '--wire']()
