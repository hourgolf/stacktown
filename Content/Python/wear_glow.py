#!/usr/bin/env python3
"""B4's lot-state glow: emissive = GlowTint(GlowState) x GlowLevel x NightAmount.

    python3 Content/Python/wear_glow.py --wire
    python3 Content/Python/wear_glow.py --revert

D23, proven buildable 2026-09-03 once the runtime CPD push landed. Two states,
not three:

    for sale   GlowLevel 0.35   GlowState 0.50
    owned      GlowLevel 0.15   GlowState 0.50

FOR SALE GLOWS BRIGHTER THAN OWNED. Owned is the default condition of a
working city; light every one of them and the board is a runway. Attention
belongs on what can still be acted on, so a finished city goes quiet.

NO GLOW FOR "RECENTLY UPGRADED", by D16's own argument: an upgrade already
reads as PALE TIMBER through Age ("pull the block, sand it back, refit it"),
and a glow on top says it twice - the same objection D22 and D23 raise to
progress bars and icons. It is also the wrong kind of signal: a glow should
tell the player something they do not know, and "you just upgraded this" is
the one fact they are certain of. GlowState's range is held for ACTIVITY -
is this building earning - which is economic, invisible in the timber, and the
economy's to define.

TWO INDEPENDENT ZEROS, both MULTIPLIES and never lerps:
  GlowLevel 0   -> black, so an unset lot is off by construction
  NightAmount 0 -> black, so a daylit board shows nothing at all
A lerp would make "off" a value that happens to be small; a multiply makes it
arithmetic. MP_EmissiveColor is currently unconnected, so nothing is displaced.

GlowTint is a THREE-POINT gradient, not a two-point lerp: red at 0, neutral
warm at 0.5, green at 1. A straight lerp from red to green passes through a
muddy olive at the neutral point, which is where most lots sit.
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
import cpdmap           # noqa: E402

M = W.M
MPC = '/Game/Stacktown/Materials/MPC_WoodCity.MPC_WoodCity'
LEDGER = os.path.join(W.OUT, 'glow_ledger.json')

GLOW_CH = {'GlowLevel': cpdmap.index('GlowLevel'),
           'GlowState': cpdmap.index('GlowState')}


def wire():
    W._pie_guard()
    script = r"""
import json
MAT={"refPath":"%s"}
SP ={"refPath":"/Script/Engine.MaterialExpressionScalarParameter"}
C3 ={"refPath":"/Script/Engine.MaterialExpressionConstant3Vector"}
CON={"refPath":"/Script/Engine.MaterialExpressionConstant"}
MUL={"refPath":"/Script/Engine.MaterialExpressionMultiply"}
SUB={"refPath":"/Script/Engine.MaterialExpressionSubtract"}
SAT={"refPath":"/Script/Engine.MaterialExpressionSaturate"}
LRP={"refPath":"/Script/Engine.MaterialExpressionLinearInterpolate"}
COL={"refPath":"/Script/Engine.MaterialExpressionCollectionParameter"}
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
    for e in ex:
        if "ScalarParameter" in e["refPath"] and "TextureSample" not in e["refPath"]:
            if getp(e,["ParameterName"]).get("ParameterName") in ("GlowLevel","GlowState"):
                return {"error":"glow parameters already present, refusing to re-add"}
    em=call("editor_toolset.toolsets.material.MaterialTools.get_property_input",
            {"material":MAT,"material_property":"MP_EmissiveColor"})["returnValue"]
    # an UNCONNECTED output pin does not come back as a dict here - it comes
    # back as a bare value, so .get() on it raises. That is the state we
    # expect and it must not be an error.
    if isinstance(em,str):
        try: em=json.loads(em)
        except Exception: em=None
    prev=None
    if isinstance(em,dict):
        e=em.get("expression")
        prev=e.get("refPath") if isinstance(e,dict) else None
    if prev: return {"error":"MP_EmissiveColor already driven by "+prev}
    added=[]
    lvl=addx(SP,-2400,2200)
    setp(lvl,{"ParameterName":"GlowLevel","DefaultValue":0.0,
              "bUseCustomPrimitiveData":True,"PrimitiveDataIndex":%d,"Group":"Glow"})
    b=getp(lvl,["ParameterName","bUseCustomPrimitiveData","PrimitiveDataIndex","DefaultValue"])
    if b.get("bUseCustomPrimitiveData") is not True or b.get("PrimitiveDataIndex")!=%d \
       or b.get("DefaultValue")!=0.0:
        return {"error":"GlowLevel read-back","got":b}
    added.append({"role":"GlowLevel","refPath":lvl["refPath"]})
    st=addx(SP,-2400,2280)
    setp(st,{"ParameterName":"GlowState","DefaultValue":0.5,
             "bUseCustomPrimitiveData":True,"PrimitiveDataIndex":%d,"Group":"Glow"})
    added.append({"role":"GlowState","refPath":st["refPath"]})
    red=addx(C3,-2200,2360);  setp(red,{"Constant":{"r":1.0,"g":0.35,"b":0.28}})
    added.append({"role":"RedNegative","refPath":red["refPath"]})
    warm=addx(C3,-2200,2430); setp(warm,{"Constant":{"r":1.0,"g":0.78,"b":0.48}})
    added.append({"role":"NeutralWarm","refPath":warm["refPath"]})
    grn=addx(C3,-2200,2500);  setp(grn,{"Constant":{"r":0.45,"g":1.0,"b":0.55}})
    added.append({"role":"GreenPositive","refPath":grn["refPath"]})
    two=addx(CON,-2200,2300); setp(two,{"R":2.0})
    added.append({"role":"K_2","refPath":two["refPath"]})
    half=addx(CON,-2200,2340); setp(half,{"R":0.5})
    added.append({"role":"K_0.5","refPath":half["refPath"]})
    lo=addx(MUL,-2050,2280);  added.append({"role":"state*2","refPath":lo["refPath"]})
    slo=addx(SAT,-1950,2280); added.append({"role":"sat(state*2)","refPath":slo["refPath"]})
    sh=addx(SUB,-2050,2340);  added.append({"role":"state-0.5","refPath":sh["refPath"]})
    hi=addx(MUL,-1950,2340);  added.append({"role":"(state-.5)*2","refPath":hi["refPath"]})
    shi=addx(SAT,-1880,2340); added.append({"role":"sat((state-.5)*2)","refPath":shi["refPath"]})
    l1=addx(LRP,-1750,2400);  added.append({"role":"lerp(Red,Warm)","refPath":l1["refPath"]})
    l2=addx(LRP,-1600,2440);  added.append({"role":"lerp(.,Green)","refPath":l2["refPath"]})
    m1=addx(MUL,-1450,2400);  added.append({"role":"tint*GlowLevel","refPath":m1["refPath"]})
    night=addx(COL,-1600,2540)
    setp(night,{"Collection":"%s","ParameterName":"NightAmount"})
    added.append({"role":"NightAmount","refPath":night["refPath"]})
    m2=addx(MUL,-1300,2460);  added.append({"role":"x NightAmount","refPath":m2["refPath"]})
    conn(st,"",lo,"A");  conn(two,"",lo,"B");  conn(lo,"",slo,"")
    conn(st,"",sh,"A");  conn(half,"",sh,"B")
    conn(sh,"",hi,"A");  conn(two,"",hi,"B");  conn(hi,"",shi,"")
    conn(red,"",l1,"A"); conn(warm,"",l1,"B"); conn(slo,"",l1,"Alpha")
    conn(l1,"",l2,"A");  conn(grn,"",l2,"B");  conn(shi,"",l2,"Alpha")
    conn(l2,"",m1,"A");  conn(lvl,"",m1,"B")
    conn(m1,"",m2,"A");  conn(night,"",m2,"B")
    call("editor_toolset.toolsets.material.MaterialTools.connect_to_output",
         {"expression":m2,"output_name":"","material_property":"MP_EmissiveColor"})
    call("editor_toolset.toolsets.material.MaterialTools.recompile",
         {"material_or_function":MAT})
    return {"added":added}
""" % (WM.TARGET, GLOW_CH['GlowLevel'], GLOW_CH['GlowLevel'], GLOW_CH['GlowState'], MPC)
    P = 'editor_toolset.toolsets.programmatic.ProgrammaticToolset'
    r = json.loads(ue.tool(P, 'execute_tool_script', {'script': script}))['returnValue']
    if isinstance(r, str):
        r = json.loads(r)
    assert 'error' not in r, 'glow wire refused: %s' % r
    os.makedirs(W.OUT, exist_ok=True)
    json.dump(r, open(LEDGER, 'w'), indent=1)
    for a in r['added']:
        print('  + %-20s %s' % (a['role'], a['refPath'].rsplit(':', 1)[-1]))
    return r


def revert():
    W._pie_guard()
    led = json.load(open(LEDGER))
    ue.tool(M, 'disconnect_from_output',
            {'material': W.MAT, 'material_property': 'MP_EmissiveColor'})
    for a in led['added']:
        ue.tool(M, 'delete_expression', {'material_or_function': W.MAT,
                                         'expression': {'refPath': a['refPath']}})
    W.recompile()
    print('reverted %d expressions; emissive disconnected' % len(led['added']))


if __name__ == '__main__':
    {'--wire': wire, '--revert': revert}[sys.argv[1] if len(sys.argv) > 1 else '--wire']()
