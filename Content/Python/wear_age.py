#!/usr/bin/env python3
"""D16's Age: oxidation along THIS SPECIES' own curve. Walnut runs backwards.

    python3 Content/Python/wear_age.py --wire     splice Age into BaseColor
    python3 Content/Python/wear_age.py --tints    write the per-species tints
    python3 Content/Python/wear_age.py --revert   undo, restoring BaseColor

wear.py --wire creates the four scalars but connects only Attention. Age,
Failure and Scorch were left FLOATING - present on the instance, readable,
driving nothing. An Age ladder shot in that state would have produced three
identical frames, and the pass would have reported the renderer's drift as a
finding about wood. Confirmed by counting downstream consumers before
building anything: Age 0, Attention 1, Failure 0, Scorch 0.

THE SHAPE, and why it is inert twice over:

    BaseColor' = BaseColor * lerp(White, AgedTint, saturate(Age))

At Age = 0 the lerp returns White and the multiply is x1.0, exact. And
AgedTint DEFAULTS to white, so even at Age = 1 a species that has not
declared a curve renders unchanged. Two independent reasons for nothing to
happen, which is the right number for a splice into BaseColor on a master
82 flagship materials share.

THE SPECIES CURVES ARE THE DECLARATION'S, NOT INVENTED HERE. D16: pine
yellows and oranges strongly and fast; cherry darkens and reddens
dramatically; sapele the same but slower; maple ambers slowly toward gold
from near-white; ash mild amber; oak moderate amber and the most
characteristic silver-grey when weathered; walnut LIGHTENS, fading toward
honey-brown under UV - the opposite of every other species here. A single
shared "age toward honey" curve would have been wrong for one of seven and
slightly wrong for the rest.
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
import wood_board as wb  # noqa: E402
import wear as W        # noqa: E402
import woodmaster as WM  # noqa: E402

M = W.M
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
LEDGER = os.path.join(W.OUT, 'age_ledger.json')

# Multiplicative tint at Age = 1. Ratios carry the DIRECTION D16 fixed;
# magnitudes are a first pass for the owner's eye, not measured constants.
TINTS = {
    'pine':   (1.10, 0.92, 0.68),   # yellows and oranges strongly, and fast
    'cherry': (0.78, 0.52, 0.42),   # darkens and reddens dramatically
    'sapele': (0.85, 0.62, 0.52),   # same direction, slower
    'maple':  (1.05, 0.94, 0.74),   # ambers slowly toward gold
    'ash':    (1.00, 0.93, 0.80),   # mild amber
    'oak':    (0.95, 0.86, 0.70),   # moderate amber
    'walnut': (1.28, 1.18, 1.02),   # LIGHTENS - the one that runs backwards
}


def wire():
    W._pie_guard()
    assert W.find_param('Age') is not None, 'run wear.py --wire first'
    script = r"""
import json
MAT={"refPath":"%s"}
VP ={"refPath":"/Script/Engine.MaterialExpressionVectorParameter"}
C3 ={"refPath":"/Script/Engine.MaterialExpressionConstant3Vector"}
SAT={"refPath":"/Script/Engine.MaterialExpressionSaturate"}
LRP={"refPath":"/Script/Engine.MaterialExpressionLinearInterpolate"}
MUL={"refPath":"/Script/Engine.MaterialExpressionMultiply"}
def call(n,a): return execute_tool(n,json.dumps(a))
def addx(c,x,y):
    return call("editor_toolset.toolsets.material.MaterialTools.add_expression",
                {"material_or_function":MAT,"expression_class":c,"x":x,"y":y})["returnValue"]
def setp(e,v):
    return call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                {"instance":e,"values":json.dumps(v)})
def getp(e,n):
    r=call("editor_toolset.toolsets.object.ObjectTools.get_properties",
           {"instance":e,"properties":n})["returnValue"]
    return json.loads(r) if isinstance(r,str) else r
def conn(a,ao,b,bi):
    return call("editor_toolset.toolsets.material.MaterialTools.connect_expressions",
                {"from_expression":a,"from_output_name":ao,
                 "to_expression":b,"to_input_name":bi})
def run():
    ex=call("editor_toolset.toolsets.material.MaterialTools.get_expressions",
            {"material_or_function":MAT})["returnValue"]
    age=None; tint_exists=False
    for e in ex:
        if "ScalarParameter" in e["refPath"] and "TextureSample" not in e["refPath"]:
            if getp(e,["ParameterName"]).get("ParameterName")=="Age": age=e
        if "VectorParameter" in e["refPath"]:
            if getp(e,["ParameterName"]).get("ParameterName")=="AgedTint": tint_exists=True
    if age is None: return {"error":"Age scalar not found"}
    if tint_exists: return {"error":"AgedTint already present, refusing to re-add"}
    bc=call("editor_toolset.toolsets.material.MaterialTools.get_property_input",
            {"material":MAT,"material_property":"MP_BaseColor"})["returnValue"]
    if isinstance(bc,str): bc=json.loads(bc)
    driver=(bc.get("expression") or {}).get("refPath")
    if not driver: return {"error":"BaseColor has no driver to splice after"}
    added=[]
    tint=addx(VP,-1900,900)
    setp(tint,{"ParameterName":"AgedTint","Group":"Wear",
               "DefaultValue":{"r":1.0,"g":1.0,"b":1.0,"a":1.0}})
    b=getp(tint,["ParameterName","DefaultValue"])
    if b.get("ParameterName")!="AgedTint": return {"error":"tint read-back","got":b}
    added.append({"role":"AgedTint","refPath":tint["refPath"]})
    white=addx(C3,-1900,1040); setp(white,{"Constant":{"r":1.0,"g":1.0,"b":1.0}})
    added.append({"role":"White","refPath":white["refPath"]})
    sat=addx(SAT,-1700,1160); added.append({"role":"saturate(Age)","refPath":sat["refPath"]})
    lrp=addx(LRP,-1500,1000); added.append({"role":"lerp(W,Tint,Age)","refPath":lrp["refPath"]})
    mul=addx(MUL,-1300,940);  added.append({"role":"BaseColor*Tint","refPath":mul["refPath"]})
    conn(age,"",sat,"")
    conn(white,"",lrp,"A"); conn(tint,"",lrp,"B"); conn(sat,"",lrp,"Alpha")
    conn({"refPath":driver},"",mul,"A"); conn(lrp,"",mul,"B")
    call("editor_toolset.toolsets.material.MaterialTools.connect_to_output",
         {"expression":mul,"output_name":"","material_property":"MP_BaseColor"})
    call("editor_toolset.toolsets.material.MaterialTools.recompile",
         {"material_or_function":MAT})
    return {"added":added,"basecolor_driver":driver}
""" % WM.TARGET
    P = 'editor_toolset.toolsets.programmatic.ProgrammaticToolset'
    r = json.loads(ue.tool(P, 'execute_tool_script', {'script': script}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    assert 'error' not in r, 'age wire refused: %s' % r
    os.makedirs(W.OUT, exist_ok=True)
    json.dump(r, open(LEDGER, 'w'), indent=1)
    for a in r['added']:
        print('  + %-18s %s' % (a['role'], a['refPath'].rsplit('.', 1)[-1]))
    print('  BaseColor re-pointed, original driver recorded for revert')
    return r


def tints():
    """Per-species AgedTint. Direction is D16's; magnitude is a first pass."""
    for s, (r, g, b) in sorted(TINTS.items()):
        mi = {'refPath': '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s' % (s, s)}
        ue.tool(MIT, 'set_vector_parameter', {
            'instance': mi, 'name': 'AgedTint',
            'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
        got = json.loads(ue.tool(MIT, 'get_vector_parameter', {
            'instance': mi, 'name': 'AgedTint'}))['returnValue']
        if isinstance(got, str):
            got = json.loads(got)
        assert abs(got['r'] - r) < 1e-4 and abs(got['b'] - b) < 1e-4, \
            '%s tint read-back %s' % (s, got)
        way = 'LIGHTENS' if (r + g + b) / 3.0 > 1.0 else 'darkens'
        print('  %-8s %.2f %.2f %.2f   %s' % (s, r, g, b, way))


def clear_tints():
    for s in TINTS:
        mi = {'refPath': '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s' % (s, s)}
        try:
            ue.tool(MIT, 'set_parameter_override',
                    {'instance': mi, 'name': 'AgedTint', 'override': False})
        except Exception as e:
            print('  %s: %s' % (s, str(e)[:70]))
    print('  tints cleared to parent white')


def revert():
    W._pie_guard()
    led = json.load(open(LEDGER))
    clear_tints()
    ue.tool(M, 'connect_to_output', {
        'expression': {'refPath': led['basecolor_driver']},
        'output_name': '', 'material_property': 'MP_BaseColor'})
    print('  BaseColor restored to', led['basecolor_driver'].rsplit('.', 1)[-1])
    for a in led['added']:
        ue.tool(M, 'delete_expression', {'material_or_function': W.MAT,
                                         'expression': {'refPath': a['refPath']}})
        print('  deleted', a['role'])
    W.recompile()
    print('reverted %d expressions' % len(led['added']))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else '--wire'
    {'--wire': wire, '--tints': tints, '--revert': revert,
     '--clear-tints': clear_tints}[cmd]()
