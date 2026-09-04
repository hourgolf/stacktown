#!/usr/bin/env python3
"""D16's Scorch: fire burns TOP-DOWN, and the shape is the whole point.

    python3 Content/Python/wear_scorch.py --wire
    python3 Content/Python/wear_scorch.py --revert

D16: "SCORCH - the event. Fire burns top-down: roofs and upper faces blacken,
the lower block is sound. Surface char, so sanding reaches good timber.
Repairable by refinishing. No economic effect." And the reason it exists at
all: "Partial and top-down reads as ACCIDENT; total and uniform reads as
FAILURE. Same colour, different shape, legible at board distance."

SO SCORCH DELIBERATELY REUSES CharBlack. It is not a different colour from
char and must not become one - if the two were told apart by hue the player
would learn a colour code instead of reading the building. The distinction is
DISTRIBUTION: char is uniform over the whole piece, scorch is a gradient from
the top. That is the entire design and it costs one height mask.

    h     = (localZ - boundsMin.z) / boundsExtents.z      0 at the base, 1 at the crown
    mask  = saturate((h - (1 - Scorch)) / FEATHER)
    out   = lerp(in, CharBlack, mask)

At Scorch = 0 the mask is saturate((h - 1) / FEATHER), and h <= 1 everywhere,
so it is 0 across the whole surface - inert by construction, not by a default
that happens to be zero. At Scorch = 1 the burn reaches the base.

Height is taken from the OBJECT'S OWN BOUNDS rather than world Z, so a tower
and a flat both burn their top third when Scorch is 0.33. World Z would burn
a fixed altitude and leave short buildings untouched, which is a different
mechanic and not this one.
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
LEDGER = os.path.join(W.OUT, 'scorch_ledger.json')
FEATHER = 0.14   # how soft the burn line is, as a fraction of the height


def wire():
    W._pie_guard()
    script = r"""
import json
MAT={"refPath":"%s"}
OLB={"refPath":"/Script/Engine.MaterialExpressionObjectLocalBounds"}
LPO={"refPath":"/Script/Engine.MaterialExpressionLocalPosition"}
CM ={"refPath":"/Script/Engine.MaterialExpressionComponentMask"}
SUB={"refPath":"/Script/Engine.MaterialExpressionSubtract"}
DIV={"refPath":"/Script/Engine.MaterialExpressionDivide"}
SAT={"refPath":"/Script/Engine.MaterialExpressionSaturate"}
OM ={"refPath":"/Script/Engine.MaterialExpressionOneMinus"}
CON={"refPath":"/Script/Engine.MaterialExpressionConstant"}
LRP={"refPath":"/Script/Engine.MaterialExpressionLinearInterpolate"}
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
    scorch=None; black=None
    for e in ex:
        if "ScalarParameter" in e["refPath"] and "TextureSample" not in e["refPath"]:
            if getp(e,["ParameterName"]).get("ParameterName")=="Scorch": scorch=e
        if "Constant3Vector" in e["refPath"]:
            c=getp(e,["Constant"]).get("Constant") or {}
            if abs((c.get("r") or 1)-0.05)<1e-3 and abs((c.get("g") or 1)-0.045)<1e-3:
                black=e     # CharBlack, reused on purpose - see the docstring
    if scorch is None: return {"error":"Scorch scalar not found"}
    if black is None:  return {"error":"CharBlack not found - run wear_failure.py --wire"}
    bc=call("editor_toolset.toolsets.material.MaterialTools.get_property_input",
            {"material":MAT,"material_property":"MP_BaseColor"})["returnValue"]
    if isinstance(bc,str): bc=json.loads(bc)
    driver=(bc.get("expression") or {}).get("refPath")
    if not driver: return {"error":"BaseColor has no driver"}
    added=[]
    olb=addx(OLB,-2000,1700); added.append({"role":"ObjectLocalBounds","refPath":olb["refPath"]})
    lpo=addx(LPO,-2000,1840); added.append({"role":"LocalPosition","refPath":lpo["refPath"]})
    mmin=addx(CM,-1850,1700); setp(mmin,{"R":False,"G":False,"B":True,"A":False})
    added.append({"role":"Min.z","refPath":mmin["refPath"]})
    mext=addx(CM,-1850,1770); setp(mext,{"R":False,"G":False,"B":True,"A":False})
    added.append({"role":"Extents.z","refPath":mext["refPath"]})
    rel=addx(SUB,-1700,1800); added.append({"role":"localZ-minZ","refPath":rel["refPath"]})
    h=addx(DIV,-1600,1800);   added.append({"role":"h","refPath":h["refPath"]})
    inv=addx(OM,-1700,1930);  added.append({"role":"1-Scorch","refPath":inv["refPath"]})
    dif=addx(SUB,-1500,1880); added.append({"role":"h-(1-Scorch)","refPath":dif["refPath"]})
    fe=addx(CON,-1500,1960);  setp(fe,{"R":%s})
    added.append({"role":"FEATHER","refPath":fe["refPath"]})
    dv=addx(DIV,-1400,1900);  added.append({"role":"/FEATHER","refPath":dv["refPath"]})
    msk=addx(SAT,-1300,1900); added.append({"role":"scorch mask","refPath":msk["refPath"]})
    lrp=addx(LRP,-1150,1860); added.append({"role":"lerp(in,Black,mask)","refPath":lrp["refPath"]})
    conn(olb,"Min",mmin,""); conn(olb,"Extents",mext,"")
    conn(lpo,"Z",rel,"A");   conn(mmin,"",rel,"B")
    conn(rel,"",h,"A");      conn(mext,"",h,"B")
    conn(scorch,"",inv,"")
    conn(h,"",dif,"A");      conn(inv,"",dif,"B")
    conn(dif,"",dv,"A");     conn(fe,"",dv,"B")
    conn(dv,"",msk,"")
    conn({"refPath":driver},"",lrp,"A"); conn(black,"",lrp,"B"); conn(msk,"",lrp,"Alpha")
    call("editor_toolset.toolsets.material.MaterialTools.connect_to_output",
         {"expression":lrp,"output_name":"","material_property":"MP_BaseColor"})
    call("editor_toolset.toolsets.material.MaterialTools.recompile",
         {"material_or_function":MAT})
    return {"added":added,"basecolor_driver":driver,"reused_charblack":black["refPath"]}
""" % (WM.TARGET, FEATHER)
    P = 'editor_toolset.toolsets.programmatic.ProgrammaticToolset'
    r = json.loads(ue.tool(P, 'execute_tool_script', {'script': script}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    assert 'error' not in r, 'scorch wire refused: %s' % r
    os.makedirs(W.OUT, exist_ok=True)
    json.dump(r, open(LEDGER, 'w'), indent=1)
    for a in r['added']:
        print('  + %-22s %s' % (a['role'], a['refPath'].rsplit(':', 1)[-1]))
    print('  reuses CharBlack (shape tells scorch from char, never colour)')
    return r


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
    {'--wire': wire, '--revert': revert}[sys.argv[1] if len(sys.argv) > 1 else '--wire']()
