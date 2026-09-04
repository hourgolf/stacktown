#!/usr/bin/env python3
"""D16's Failure: weathering toward the species grey, then char.

    python3 Content/Python/wear_failure.py --wire
    python3 Content/Python/wear_failure.py --greys     per-species grey targets
    python3 Content/Python/wear_failure.py --revert

D16: "Failure  0 -> 0.6 weathers toward THIS SPECIES' grey, 0.6 -> 1 chars.
Follows the species' own route and rate... Never overrides the species."

THE SHAPE, and it is inert twice over at Failure = 0:

    weather  = saturate(Failure / 0.6)
    char     = saturate((Failure - 0.6) / 0.4)
    out      = lerp( lerp(in, GreyTarget, weather), CharBlack, char )

At Failure = 0 both alphas are 0 and both lerps return their A pin exactly -
not approximately, the A pin itself. And GreyTarget defaults to a neutral
silver so a species that has declared no grey still weathers plausibly rather
than turning magenta.

WHY THIS IS WORTH BUILDING NOW AND WAS NOT BEFORE. Until 2026-09-03 the
curvature mask read VertexColor.R on meshes with no vertex colours and was
exactly zero, so nothing in the wear system could render. That is fixed
(OneMinus_0 <- Max_1) and Attention now measures 32x drift. Failure does not
depend on the mask at all - it works on base colour - but it would have been
built blind beside a system nobody could see.

THE COLD HALF OF D16'S ARGUMENT IS WHAT THIS BUYS: "pale -> honey -> dark
amber -> silver-grey -> black" runs WARM then COLD, so a struggling district
reads as cold patches in a warm field at board range with no UI at all.
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
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
LEDGER = os.path.join(W.OUT, 'failure_ledger.json')

# D16: open grain (oak, ash, sapele, pine) frays and greys earlier and cooler;
# dense (maple, cherry) hold their colour longer and grey warmer. Directions
# are the declaration's; magnitudes are a first pass for the owner's eye.
# TINTS AROUND 1.0, NOT TARGET COLOURS. The first version lerped to a flat
# grey and measured +65 levels at Failure 0.5 against a 0.45 floor - 145x
# noise, and the frame was bleached plaster with no grain. D16: "the species
# is legible right to the end". So the chain desaturates the wood and tints
# the RESULT, which keeps grain and figure and only removes the warmth.
# Below 1.0 darkens, above lifts; the R<B relationship is what reads cold.
# SECOND TUNING. The first tint set (0.82-0.94) moved the WHOLE weather half
# by 3.42 levels measured on the mass - 7.4x drift and invisible. D16 needs a
# struggling district to read as COLD PATCHES IN A WARM FIELD at board range,
# and 3 levels reads at no range at all.
#
# The lift comes from HUE as much as value: R well below B is what makes a
# surface read cold against a warm board, and a value drop alone would just
# look like shadow. So R is pushed down hardest, B least, and the whole set
# sits around 0.6-0.8 rather than 0.9.
GREYS = {
    'oak':    (0.60, 0.68, 0.78),   # the most characteristic silver-grey
    'ash':    (0.63, 0.70, 0.79),
    'sapele': (0.55, 0.62, 0.72),
    'pine':   (0.66, 0.72, 0.80),
    'maple':  (0.68, 0.74, 0.82),
    'cherry': (0.52, 0.59, 0.70),
    'walnut': (0.50, 0.57, 0.68),
}


def wire():
    W._pie_guard()
    script = r"""
import json
MAT={"refPath":"%s"}
VP ={"refPath":"/Script/Engine.MaterialExpressionVectorParameter"}
C3 ={"refPath":"/Script/Engine.MaterialExpressionConstant3Vector"}
SAT={"refPath":"/Script/Engine.MaterialExpressionSaturate"}
LRP={"refPath":"/Script/Engine.MaterialExpressionLinearInterpolate"}
DIV={"refPath":"/Script/Engine.MaterialExpressionDivide"}
SUB={"refPath":"/Script/Engine.MaterialExpressionSubtract"}
CON={"refPath":"/Script/Engine.MaterialExpressionConstant"}
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
                {"from_expression":a,"from_output_name":ao,"to_expression":b,"to_input_name":bi})
def run():
    ex=call("editor_toolset.toolsets.material.MaterialTools.get_expressions",
            {"material_or_function":MAT})["returnValue"]
    fail=None
    for e in ex:
        if "ScalarParameter" in e["refPath"] and "TextureSample" not in e["refPath"]:
            if getp(e,["ParameterName"]).get("ParameterName")=="Failure": fail=e
        if "VectorParameter" in e["refPath"]:
            if getp(e,["ParameterName"]).get("ParameterName")=="GreyTarget":
                return {"error":"GreyTarget already present, refusing to re-add"}
    if fail is None: return {"error":"Failure scalar not found - run wear.py --wire"}
    bc=call("editor_toolset.toolsets.material.MaterialTools.get_property_input",
            {"material":MAT,"material_property":"MP_BaseColor"})["returnValue"]
    if isinstance(bc,str): bc=json.loads(bc)
    driver=(bc.get("expression") or {}).get("refPath")
    if not driver: return {"error":"BaseColor has no driver"}
    added=[]
    grey=addx(VP,-1200,1400)
    setp(grey,{"ParameterName":"GreyTarget","Group":"Wear",
               "DefaultValue":{"r":0.58,"g":0.57,"b":0.55,"a":1.0}})
    if getp(grey,["ParameterName"]).get("ParameterName")!="GreyTarget":
        return {"error":"GreyTarget read-back"}
    added.append({"role":"GreyTarget","refPath":grey["refPath"]})
    black=addx(C3,-1200,1540); setp(black,{"Constant":{"r":0.05,"g":0.045,"b":0.04}})
    added.append({"role":"CharBlack","refPath":black["refPath"]})
    k06=addx(CON,-1500,1240); setp(k06,{"R":0.6})
    added.append({"role":"K_0.6","refPath":k06["refPath"]})
    k04=addx(CON,-1500,1300); setp(k04,{"R":0.4})
    added.append({"role":"K_0.4","refPath":k04["refPath"]})
    dw=addx(DIV,-1350,1200); added.append({"role":"Fail/0.6","refPath":dw["refPath"]})
    sw=addx(SAT,-1250,1200); added.append({"role":"weather","refPath":sw["refPath"]})
    sb=addx(SUB,-1350,1320); added.append({"role":"Fail-0.6","refPath":sb["refPath"]})
    dc=addx(DIV,-1300,1320); added.append({"role":"(Fail-0.6)/0.4","refPath":dc["refPath"]})
    sc=addx(SAT,-1250,1320); added.append({"role":"char","refPath":sc["refPath"]})
    lw=addx(LRP,-1050,1420); added.append({"role":"lerp(in,Grey,weather)","refPath":lw["refPath"]})
    lc=addx(LRP,-900,1460);  added.append({"role":"lerp(.,Black,char)","refPath":lc["refPath"]})
    conn(fail,"",dw,"A"); conn(k06,"",dw,"B"); conn(dw,"",sw,"")
    conn(fail,"",sb,"A"); conn(k06,"",sb,"B")
    conn(sb,"",dc,"A");   conn(k04,"",dc,"B"); conn(dc,"",sc,"")
    conn({"refPath":driver},"",lw,"A"); conn(grey,"",lw,"B"); conn(sw,"",lw,"Alpha")
    conn(lw,"",lc,"A"); conn(black,"",lc,"B"); conn(sc,"",lc,"Alpha")
    call("editor_toolset.toolsets.material.MaterialTools.connect_to_output",
         {"expression":lc,"output_name":"","material_property":"MP_BaseColor"})
    call("editor_toolset.toolsets.material.MaterialTools.recompile",
         {"material_or_function":MAT})
    return {"added":added,"basecolor_driver":driver}
""" % WM.TARGET
    P = 'editor_toolset.toolsets.programmatic.ProgrammaticToolset'
    r = json.loads(ue.tool(P, 'execute_tool_script', {'script': script}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    assert 'error' not in r, 'failure wire refused: %s' % r
    os.makedirs(W.OUT, exist_ok=True)
    json.dump(r, open(LEDGER, 'w'), indent=1)
    for a in r['added']:
        print('  + %-22s %s' % (a['role'], a['refPath'].rsplit(':', 1)[-1]))
    print('  BaseColor re-pointed; original driver recorded')
    return r


def greys():
    for s, (r, g, b) in sorted(GREYS.items()):
        mi = {'refPath': '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s' % (s, s)}
        ue.tool(MIT, 'set_vector_parameter', {
            'instance': mi, 'name': 'GreyTarget',
            'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
        got = json.loads(ue.tool(MIT, 'get_vector_parameter', {
            'instance': mi, 'name': 'GreyTarget'}))['returnValue']
        if isinstance(got, str):
            got = json.loads(got)
        assert abs(got['r'] - r) < 1e-4, '%s grey read-back %s' % (s, got)
        print('  %-8s %.2f %.2f %.2f' % (s, r, g, b))


def revert():
    W._pie_guard()
    led = json.load(open(LEDGER))
    ue.tool(M, 'connect_to_output', {
        'expression': {'refPath': led['basecolor_driver']},
        'output_name': '', 'material_property': 'MP_BaseColor'})
    for a in led['added']:
        ue.tool(M, 'delete_expression', {'material_or_function': W.MAT,
                                         'expression': {'refPath': a['refPath']}})
    W.recompile()
    print('reverted %d expressions; BaseColor restored' % len(led['added']))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else '--wire'
    {'--wire': wire, '--greys': greys, '--revert': revert}[cmd]()
