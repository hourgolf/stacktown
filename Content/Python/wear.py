#!/usr/bin/env python3
"""D16 wear: the four per-instance scalars, and the proof that adding them
changes nothing for the 82 flagship materials that share this master.

    python3 Content/Python/wear.py --floor    the recompile-class noise floor
    python3 Content/Python/wear.py --wire     add the four CPD scalars
    python3 Content/Python/wear.py --prove    flagship frame vs the floor
    python3 Content/Python/wear.py --revert   delete exactly what --wire added
    python3 Content/Python/wear.py --clear    remove the proof subject

WHY A SHARED MASTER AT ALL. D16 puts wear at material level on purpose: D1
fixed patina there, genbuild_identity hashes SINK RECORDS and boxes carry no
material, so per-instance scalars cannot move the manifest. A generator-level
patina would land inside a contract that cannot be certified while the
flagship lane is dark. The cost is that M_StacktownMaster has 90 referencers
and only 8 are wood - so this file's real subject is the other 82.

THE FLOOR IS MEASURED ACROSS A RECOMPILE, NOT ACROSS TWO STATIC CAPTURES.
POLISH_PROTOCOL: "A measurement floor is measured ACROSS the perturbation
class it will judge. A noise floor from two captures of a static scene does
not cover a comparison spanning a shader recompile - Lumen's cache
invalidation measured 47.5 between captures of an IDENTICAL scene, a false
positive shaped exactly like a real finding." So --floor shoots, forces a
no-op recompile of this very master, and shoots again. That pair IS the
floor, and it is the only floor --prove is allowed to read against.

WHY THE WIRING IS INERT BY CONSTRUCTION, and why the obvious version is not.
The obvious splice is EdgeWearLift * Attention. With Attention defaulting to
0 that sets every flagship material's edge wear to ZERO - the opposite of
inert, and it would have shipped looking like a win because the wood board
never renders those materials. The neutral form multiplies instead by
(1 + Attention * AttentionGain), which is exactly 1.0 at Attention = 0.
Negative Attention is settled dust, positive is burnish; 0 is today.

Attention drives EdgeWearLift, NOT Age. D16 is explicit and the inversion is
the whole point: a long-loved block is old AND burnished, a neglected one
keeps sharp arrises because no hand has worn them. Age is oxidation along
the species' own curve and never touches the arris.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path            # noqa: F401,E402
import ue               # noqa: E402
import img              # noqa: E402
import wood_board as wb  # noqa: E402
import cpdmap          # noqa: E402

S, A, OBJ, APP = wb.S, wb.A, wb.OBJ, wb.APP
M = 'editor_toolset.toolsets.material.MaterialTools'
AT = 'editor_toolset.toolsets.asset.AssetTools'
import woodmaster as WM  # noqa: E402

# NOT wb.MASTER. Direction B edits its own fork; woodmaster.assert_not_shared
# makes writing to the flagship's master an error rather than a habit.
MAT = {'refPath': WM.TARGET}
OUT = os.path.join(wb.OUT, 'wear')
LEDGER = os.path.join(OUT, 'wire_ledger.json')
FLOOR = os.path.join(OUT, 'floor.json')

# The proof subject is FLAGSHIP materials, never wood - that is the whole
# point of the no-op half. Three that between them cover the master's main
# branches: a card albedo, a district colour, and a non-paper surface.
PROOF_MI = ('MI_card_ochre', 'MI_dist_slate', 'MI_concrete')
PROOF_AT = (-9000.0, -9000.0, 400.0)      # clear of the play board
PROOF_CAM = {'location': {'x': -8480.0, 'y': -10250.0, 'z': 620.0},
             'rotation': {'pitch': -7.0, 'yaw': 90.0, 'roll': 0.0}}
# THE DIFF IS READ ON THE SUBJECT, NOT ON THE FRAME. The first framing put the
# three cubes in about a tenth of the picture and the rest was empty ground -
# a floor computed over all of it is a floor of mostly nothing, and a real
# change confined to the cubes would have been averaged into invisibility.
# Fractions of width/height, resolved per image so a resolution change cannot
# silently move the window (grad_p90 taught this lane that one).
CROP = (0.20, 0.28, 0.82, 0.76)
# NOT redeclared here. The first wire assigned 0-3 and collided with
# GlowLevel, GlowState and Selection, which the declarations had reserved
# before wear existed. One authority, double-entry - cpdmap.py owns it.
WEAR = cpdmap.WEAR


def _pie_guard():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], \
        'PIE active - refusing to touch the level'


def _crop(im):
    return (int(im.w * CROP[0]), int(im.h * CROP[1]),
            int(im.w * CROP[2]), int(im.h * CROP[3]))


def _diff(pa, pb):
    a, b = img.load(pa), img.load(pb)
    assert (a.w, a.h) == (b.w, b.h), 'frames differ in size: %s vs %s' % (
        (a.w, a.h), (b.w, b.h))
    return img.mean_abs_diff(a, b, *_crop(a))


SETTLE_S = 9.0   # seconds held before each capture; see settle()


def _shoot(tag, settle_s=None):
    ue.tool(APP, 'SetCameraTransform', {'transform': PROOF_CAM})
    time.sleep(SETTLE_S if settle_s is None else settle_s)
    r = json.loads(ue.tool(APP, 'CaptureViewport', {
        'captureTransform': PROOF_CAM, 'annotations': [],
        'bShowUI': False}))['returnValue']
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, '%s.png' % tag)
    import base64
    open(p, 'wb').write(base64.b64decode(r['image']['data']))
    return p


def _expressions():
    return json.loads(ue.tool(M, 'get_expressions',
                              {'material_or_function': MAT}))['returnValue']


def _props(e, names):
    r = json.loads(ue.tool(OBJ, 'get_properties',
                           {'instance': e, 'properties': names}))['returnValue']
    return json.loads(r) if isinstance(r, str) else r


def _setp(e, values):
    ue.tool(OBJ, 'set_properties', {'instance': e, 'values': json.dumps(values)})


def find_param(name):
    """The named ScalarParameter node, or None. Discovered, never assumed."""
    for e in _expressions():
        if 'ScalarParameter' not in e['refPath'] or 'TextureSample' in e['refPath']:
            continue
        if _props(e, ['ParameterName']).get('ParameterName') == name:
            return e
    return None


def recompile():
    ue.tool(M, 'recompile', {'material_or_function': MAT})


def subject_up():
    """Spawn the three flagship-material boxes. Disposable, never saved."""
    _pie_guard()
    made = []
    for i, mi in enumerate(PROOF_MI):
        nm = 'WEARPROOF_%s' % mi
        got = json.loads(ue.tool(S, 'find_actors', {
            'name': nm, 'tag': '', 'collision_channels': []}))['returnValue']
        if got:
            made.append(got[0])
            continue
        loc = {'x': PROOF_AT[0] + i * 520.0, 'y': PROOF_AT[1], 'z': PROOF_AT[2]}
        a = json.loads(ue.tool(S, 'add_to_scene_from_class', {
            'actor_type': {'refPath': '/Script/Engine.StaticMeshActor'},
            'name': nm,
            'xform': {'location': loc,
                      'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                      'scale': {'x': 3.0, 'y': 3.0, 'z': 3.0}}}))['returnValue']
        comp = {'refPath': a['refPath'] + '.StaticMeshComponent0'}
        # mesh first, THEN material - a combined write drops the material,
        # the trap the beta lane logged in HANDOFF on 2026-09-02.
        _setp(comp, {'StaticMesh': '/Engine/BasicShapes/Cube.Cube'})
        _setp(comp, {'OverrideMaterials': ['%s/%s.%s' % (wb.MATD, mi, mi)]})
        got = json.loads(ue.tool(S, 'find_actors', {
            'name': nm, 'tag': '', 'collision_channels': []}))['returnValue']
        assert got, 'spawn reported success and the actor is not there: %s' % nm
        made.append(got[0])
    return made


def clear():
    _pie_guard()
    n = 0
    while True:
        got = json.loads(ue.tool(S, 'find_actors', {
            'name': 'WEARPROOF_', 'tag': '',
            'collision_channels': []}))['returnValue']
        if not got:
            break
        for a in got:
            ue.tool(S, 'remove_from_scene', {'actor': a})
            n += 1
    print('cleared %d proof actors' % n)


def floor():
    """Shoot, force a NO-OP recompile of this master, shoot again."""
    _pie_guard()
    subject_up()
    a1 = _shoot('floor_A1')
    recompile()                      # the perturbation class, with no edit
    time.sleep(6)
    a2 = _shoot('floor_A2')
    d = _diff(a1, a2)
    os.makedirs(OUT, exist_ok=True)
    json.dump({'a1': a1, 'a2': a2, 'mean_abs_diff': d, 'crop': list(CROP),
               'class': 'shader recompile, no graph edit',
               'subject': list(PROOF_MI)},
              open(FLOOR, 'w'), indent=1)
    print('FLOOR across a recompile: %.4f levels  (%s vs %s)' % (d, 'A1', 'A2'))
    return d


def wire():
    """Add the four CPD scalars AND the neutral Attention splice.

    Adding four DISCONNECTED parameters would pass --prove trivially while
    testing nothing: an unconnected node does not reach the shader. The risk
    worth proving is the splice, so it goes in the same edit.

    THE SPLICE, and why the obvious form is a trap. EdgeWearLift has exactly
    one consumer - Multiply_1 pin B - so the tempting edit is to multiply it
    by Attention. With Attention defaulting to 0 that sets edge wear to ZERO
    on all 82 flagship materials: the exact opposite of inert, and invisible
    from the wood board, which never renders them. The neutral form is

        lift' = EdgeWearLift * (1 + Attention * AttentionGain)

    which at Attention = 0 is EdgeWearLift * 1.0, exact in IEEE, not merely
    close. Negative Attention is settled dust, positive is burnish, 0 is
    today. AttentionGain is per-SPECIES (an MI override), not per-instance -
    D16's split: the instance says how far along, the species says which way.
    """
    _pie_guard()
    assert os.path.exists(FLOOR), 'refusing to edit before the floor is measured'
    script = r"""
import json
MAT = {"refPath": "%s"}
SP  = {"refPath": "/Script/Engine.MaterialExpressionScalarParameter"}
MUL = {"refPath": "/Script/Engine.MaterialExpressionMultiply"}
ADD = {"refPath": "/Script/Engine.MaterialExpressionAdd"}
CON = {"refPath": "/Script/Engine.MaterialExpressionConstant"}
def call(n, a): return execute_tool(n, json.dumps(a))
def addx(cls, x, y):
    return call("editor_toolset.toolsets.material.MaterialTools.add_expression",
                {"material_or_function": MAT, "expression_class": cls,
                 "x": x, "y": y})["returnValue"]
def setp(e, v):
    return call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                {"instance": e, "values": json.dumps(v)})
def getp(e, n):
    r = call("editor_toolset.toolsets.object.ObjectTools.get_properties",
             {"instance": e, "properties": n})["returnValue"]
    return json.loads(r) if isinstance(r, str) else r
def conn(a, ao, b, bi):
    return call("editor_toolset.toolsets.material.MaterialTools.connect_expressions",
                {"from_expression": a, "from_output_name": ao,
                 "to_expression": b, "to_input_name": bi})
def run():
    ex = call("editor_toolset.toolsets.material.MaterialTools.get_expressions",
              {"material_or_function": MAT})["returnValue"]
    named = {}
    for e in ex:
        if "ScalarParameter" in e["refPath"] and "TextureSample" not in e["refPath"]:
            named[getp(e, ["ParameterName"]).get("ParameterName")] = e
    for n in ("Age", "Attention", "Failure", "Scorch", "AttentionGain"):
        if n in named:
            return {"error": "parameter already present, refusing to re-add: " + n}
    lift = named.get("EdgeWearLift")
    if lift is None:
        return {"error": "EdgeWearLift not found"}
    added = []
    # the four per-instance scalars, all CPD, all default 0
    for name, idx in %s:
        e = addx(SP, -2100, 120 + idx*110)
        setp(e, {"ParameterName": name, "DefaultValue": 0.0,
                 "bUseCustomPrimitiveData": True, "PrimitiveDataIndex": idx,
                 "Group": "Wear"})
        b = getp(e, ["ParameterName","DefaultValue","bUseCustomPrimitiveData",
                     "PrimitiveDataIndex"])
        if b.get("ParameterName") != name or b.get("bUseCustomPrimitiveData") is not True \
           or b.get("PrimitiveDataIndex") != idx or b.get("DefaultValue") != 0.0:
            return {"error": "read-back disagrees for " + name, "got": b}
        added.append({"role": name, "refPath": e["refPath"]})
        if name == "Attention": att = e
    # per-species gain, NOT custom primitive data
    gain = addx(SP, -2100, 600)
    setp(gain, {"ParameterName": "AttentionGain", "DefaultValue": 0.8,
                "bUseCustomPrimitiveData": False, "Group": "Wear"})
    added.append({"role": "AttentionGain", "refPath": gain["refPath"]})
    one = addx(CON, -1850, 500); setp(one, {"R": 1.0})
    added.append({"role": "One", "refPath": one["refPath"]})
    m1 = addx(MUL, -1650, 560); added.append({"role":"Att*Gain","refPath":m1["refPath"]})
    a1 = addx(ADD, -1450, 530); added.append({"role":"1+AttGain","refPath":a1["refPath"]})
    m2 = addx(MUL, -1250, 480); added.append({"role":"Lift*Mult","refPath":m2["refPath"]})
    conn(att, "", m1, "A"); conn(gain, "", m1, "B")
    conn(one, "", a1, "A"); conn(m1,   "", a1, "B")
    conn(lift,"", m2, "A"); conn(a1,   "", m2, "B")
    # re-point the single consumer: Multiply_1 pin B
    consumer = None
    for e in ex:
        try:
            ins = call("editor_toolset.toolsets.material.MaterialTools.get_expression_inputs",
                       {"material_or_function": MAT, "expression": e})["returnValue"]
        except Exception:
            continue
        if isinstance(ins, str): ins = json.loads(ins)
        for i in ins:
            if not isinstance(i, dict): continue
            x = i.get("expression")
            rp = x.get("refPath") if isinstance(x, dict) else x
            if rp == lift["refPath"]:
                consumer = {"refPath": e["refPath"], "pin": i.get("input_name")}
    if consumer is None:
        return {"error": "EdgeWearLift consumer vanished between reads"}
    conn(m2, "", {"refPath": consumer["refPath"]}, consumer["pin"])
    call("editor_toolset.toolsets.material.MaterialTools.recompile",
         {"material_or_function": MAT})
    return {"added": added, "consumer": consumer, "lift": lift["refPath"]}
""" % (WM.TARGET, repr(list(WEAR)))
    P = 'editor_toolset.toolsets.programmatic.ProgrammaticToolset'
    r = json.loads(ue.tool(P, 'execute_tool_script', {'script': script}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    assert 'error' not in r, 'wire refused: %s' % r
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(LEDGER, 'w'), indent=1)
    for a in r['added']:
        print('  + %-14s %s' % (a['role'], a['refPath'].rsplit('.', 1)[-1]))
    print('  re-pointed %s pin %s' % (r['consumer']['refPath'].rsplit('.', 1)[-1],
                                      r['consumer']['pin']))
    print('wired %d expressions, ledger at %s' % (len(r['added']), LEDGER))
    return r


def prove():
    _pie_guard()
    f = json.load(open(FLOOR))
    subject_up()
    b = _shoot('proof_B')
    d = _diff(f['a2'], b)
    ok = d <= f['mean_abs_diff']
    print('floor (recompile class): %.4f' % f['mean_abs_diff'])
    print('after the edit:          %.4f' % d)
    print('VERDICT:', 'INERT - within the floor' if ok else
          'NOT INERT - the edit moved a flagship material. REVERT.')
    json.dump({'floor': f['mean_abs_diff'], 'after': d, 'inert': ok,
               'subject': list(PROOF_MI), 'frame': b},
              open(os.path.join(OUT, 'proof.json'), 'w'), indent=1)
    return ok


def settle(n=None, delay=None):
    """Shoot the same untouched scene N times and watch the numbers move.

    The floor this file first used was two captures seconds apart across a
    recompile: 0.7091. The real comparison spans MINUTES of editor work, and
    --recheck proved the gap alone produces 2.76 - larger than the 2.13 the
    edit was convicted on. So the floor was not a floor, it was a lucky pair,
    and POLISH_PROTOCOL's "settle to a criterion" was the half of the rule
    this lane skipped.

    This measures the drift as a function of elapsed time with NOTHING
    changing, which is the only way to know what a real delta has to beat.
    """
    _pie_guard()
    n = int(sys.argv[2]) if len(sys.argv) > 2 else (n or 6)
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else (delay or SETTLE_S)
    subject_up()
    import time as _t
    t0 = _t.time()
    shots = []
    print('%d shots, %.0fs held before each' % (n, delay))
    for i in range(n):
        p = _shoot('settle_%d' % i, settle_s=delay)
        shots.append((round(_t.time() - t0, 1), p))
    base = shots[0][1]
    print('%-9s %-10s %s' % ('elapsed', 'vs first', 'vs previous'))
    rows = []
    for i, (el, p) in enumerate(shots):
        d0 = _diff(base, p)
        dp = _diff(shots[i - 1][1], p) if i else 0.0
        rows.append({'elapsed': el, 'vs_first': d0, 'vs_prev': dp})
        print('%-9.1f %-10.4f %.4f' % (el, d0, dp))
    worst = max(r['vs_first'] for r in rows)
    print()
    print('WORST drift with nothing changed: %.4f levels' % worst)
    print('Any real finding must beat that, not the 0.7091 pair.')
    json.dump({'delay_s': delay, 'rows': rows},
              open(os.path.join(OUT, 'settle_%.0fs.json' % delay), 'w'), indent=1)
    return rows


def paired():
    """The instrument that survives drift: wire and revert REPEATEDLY, and
    read the two populations against each other.

    A single before/after cannot answer this. --settle proved consecutive
    captures of an UNTOUCHED scene differ by 0.4-0.9 levels and accumulate to
    2.2-2.6 over the couple of minutes a wire takes - the same size as the
    2.13 the edit was convicted on. So one number carries no information.

    Cycling does. Each cycle shoots across a wire and then across a revert,
    so every sample is adjacent in time and every sample spans exactly one
    recompile. Drift hits both populations equally and cancels:

        inert      -> wire-spanning and revert-spanning diffs are one
                      population, both sitting on the drift noise
        not inert  -> wire-spanning diffs sit systematically higher

    Leaves the master REVERTED: every cycle ends with a revert, and the
    ledger's restore-then-delete runs each time.
    """
    _pie_guard()
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    subject_up()
    prev = _shoot('paired_A0')
    wired, reverted = [], []
    for i in range(n):
        wire()
        b = _shoot('paired_B%d' % i)
        wired.append(_diff(prev, b))
        revert()
        a = _shoot('paired_A%d' % (i + 1))
        reverted.append(_diff(b, a))
        prev = a
        print('  cycle %d  across wire %.4f   across revert %.4f'
              % (i, wired[-1], reverted[-1]))
    mw = sum(wired) / len(wired)
    mr = sum(reverted) / len(reverted)
    print()
    print('across a WIRE   mean %.4f   %s' % (mw, ['%.3f' % x for x in wired]))
    print('across a REVERT mean %.4f   %s' % (mr, ['%.3f' % x for x in reverted]))
    sep = mw - mr
    print('separation: %+.4f levels' % sep)
    if max(wired) <= max(reverted) * 1.5:
        print('READING: one population. The edit is INERT within an '
              'instrument that can see drift.')
    else:
        print('READING: the wire population sits higher. The edit MOVES a '
              'flagship material.')
    json.dump({'wire': wired, 'revert': reverted, 'mean_wire': mw,
               'mean_revert': mr}, open(os.path.join(OUT, 'paired.json'), 'w'),
              indent=1)
    return wired, reverted


def recheck():
    """The third leg of the A-B-A: shoot again AFTER the revert.

    A failing --prove has two possible causes and they are not
    distinguishable from one number. Either the edit really moved a flagship
    material, or the scene drifted between A2 and B - Lumen convergence over
    a gap the floor never covered, which is the census-drift error this lane
    already made once. Reverting and re-shooting separates them:

        C within the floor of A2  ->  the state is restored, and the delta
                                      at B was the EDIT.
        C as far from A2 as B was ->  the delta was TIME, and the edit was
                                      never shown to do anything.
    """
    _pie_guard()
    f = json.load(open(FLOOR))
    subject_up()
    c = _shoot('recheck_C')
    d_c = _diff(f['a2'], c)
    pr = json.load(open(os.path.join(OUT, 'proof.json')))
    print('floor (recompile class): %.4f' % f['mean_abs_diff'])
    print('A2 -> B  (edit applied): %.4f' % pr['after'])
    print('A2 -> C  (edit reverted):%.4f' % d_c)
    if d_c <= f['mean_abs_diff']:
        print('READING: state restored. The B delta was THE EDIT.')
    else:
        print('READING: C is off too - the delta is DRIFT, not the edit.')
        print('         The floor did not cover the gap between captures.')
    json.dump({'floor': f['mean_abs_diff'], 'b': pr['after'], 'c': d_c,
               'frame': c}, open(os.path.join(OUT, 'recheck.json'), 'w'), indent=1)
    return d_c


def revert():
    """Delete what --wire added AND put the original wire back.

    Deleting the nodes alone would leave Multiply_1 pin B dangling - the
    flagship's edge wear silently gone, which is worse than the edit this
    reverts. So the original connection is restored FIRST, from the ledger.
    """
    _pie_guard()
    led = json.load(open(LEDGER))
    ue.tool(M, 'connect_expressions', {
        'from_expression': {'refPath': led['lift']}, 'from_output_name': '',
        'to_expression': {'refPath': led['consumer']['refPath']},
        'to_input_name': led['consumer']['pin']})
    print('  restored %s pin %s <- EdgeWearLift' % (
        led['consumer']['refPath'].rsplit('.', 1)[-1], led['consumer']['pin']))
    for a in led['added']:
        ue.tool(M, 'delete_expression', {'material_or_function': MAT,
                                         'expression': {'refPath': a['refPath']}})
        print('  deleted', a['role'])
    recompile()
    for a in led['added']:
        if a['role'] in ('Age', 'Attention', 'Failure', 'Scorch', 'AttentionGain'):
            assert find_param(a['role']) is None, '%s survived deletion' % a['role']
    print('reverted %d expressions' % len(led['added']))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else '--floor'
    {'--floor': floor, '--wire': wire, '--prove': prove,
     '--revert': revert, '--clear': clear, '--recheck': recheck, '--settle': settle, '--paired': paired}[cmd]()
