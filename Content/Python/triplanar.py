"""Triplanar paper projection.

The paper normal was world-position projected on XZ alone. On a face whose
normal is X the X coordinate does not vary across the surface, so the texture
varied only in Z: measured 13.5x anisotropy on a block end wall (rows 5.68 vs
cols 0.42) against 0.7x on a -Y facade. Corduroy, not paper.

Samples the same PaperNormal texture on all three planes and blends by the
surface normal. Blend weights come from VertexNormalWS, NOT PixelNormalWS -
using the pixel normal to weight the normal map that produces it is circular.

PaperTiling is wired into the projection here, which also fixes it being inert:
a 4x change previously moved the measured detail by nothing.
"""
import ue, json

M='editor_toolset.toolsets.material.MaterialTools'
O='editor_toolset.toolsets.object.ObjectTools'
AS='editor_toolset.toolsets.asset.AssetTools'
E='/Script/Engine.MaterialExpression'
MAT={'refPath':'/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster'}

def addx(cls):
    r=ue.tool(M,'add_expression',{'material_or_function':MAT,
                                  'expression_class':{'refPath':cls}})
    if 'ERROR' in r: raise SystemExit('add %s failed: %s'%(cls,r[:140]))
    return json.loads(r)['returnValue']
def setp(ref,vals):
    r=ue.tool(O,'set_properties',{'instance':ref,'values':json.dumps(vals)})
    if '"returnValue":true' not in r: print('   warn set',list(vals),r[:90])
def pins(e):
    return json.loads(ue.tool(M,'get_expression_input_names',{'expression':e}))['returnValue']
def wire(frm,to,pin=None,out=''):
    names=pins(to); cands=[pin] if pin else (names or [''])
    for p in cands:
        r=ue.tool(M,'connect_expressions',{'from_expression':frm,'from_output_name':out,
                                           'to_expression':to,'to_input_name':p})
        if 'ERROR' not in r and 'TOOL-ERROR' not in r: return True
    print('   FAILED wire into',names); return False
def one(cls,src,out=''):
    n=addx(cls); p=pins(n); wire(src,n,p[0] if p else '',out); return n

# reuse the existing PaperTiling parameter so instance values keep meaning
ex=json.loads(ue.tool(M,'get_expressions',{'material_or_function':MAT}))['returnValue']
tiling=None; papertex=None
for e in ex:
    def props(node, names):
        r=ue.tool(O,'get_properties',{'instance':node,'properties':names})
        try: return json.loads(json.loads(r)['returnValue'])
        except Exception: return {}
    if 'ScalarParameter' in e['refPath']:
        if props(e,['ParameterName']).get('ParameterName')=='PaperTiling': tiling=e
    if 'TextureSampleParameter2D' in e['refPath'] and papertex is None:
        d=props(e,['ParameterName','Texture'])
        if d.get('ParameterName')=='PaperNormal': papertex=d.get('Texture')
if not tiling: raise SystemExit('PaperTiling parameter not found')
print('reusing PaperTiling; PaperNormal texture:', papertex)

wp=addx(E+'WorldPosition')
scaled=addx(E+'Multiply'); wire(wp,scaled,'A','XYZ'); wire(tiling,scaled,'B')

PLANES=(('R','G','yz_for_X'),('R','B','xz_for_Y'),('R','G','xy_for_Z'))
MASKS=((False,True,True),(True,False,True),(True,True,False))   # YZ, XZ, XY
samples=[]
for (r,g,b),label in zip(MASKS,('YZ','XZ','XY')):
    m=addx(E+'ComponentMask'); setp(m,{'R':r,'G':g,'B':b,'A':False})
    wire(scaled,m,pins(m)[0])
    s=addx(E+'TextureSampleParameter2D')
    setp(s,{'ParameterName':'PaperNormal','SamplerType':'SAMPLERTYPE_Normal'})
    if papertex: setp(s,{'Texture':papertex})
    wire(m,s,'UVs')
    samples.append(s)
    print('  plane %s sampled'%label)

vn=addx(E+'VertexNormalWS')
av=one(E+'Abs',vn)
comps=[]
for r,g,b in ((True,False,False),(False,True,False),(False,False,True)):
    m=addx(E+'ComponentMask'); setp(m,{'R':r,'G':g,'B':b,'A':False})
    wire(av,m,pins(m)[0]); comps.append(m)
s1=addx(E+'Add'); wire(comps[0],s1,'A'); wire(comps[1],s1,'B')
s2=addx(E+'Add'); wire(s1,s2,'A'); wire(comps[2],s2,'B')
weights=[]
for c in comps:
    d=addx(E+'Divide'); wire(c,d,'A'); wire(s2,d,'B'); weights.append(d)

terms=[]
for s,w in zip(samples,weights):
    mul=addx(E+'Multiply'); wire(s,mul,'A'); wire(w,mul,'B'); terms.append(mul)
a1=addx(E+'Add'); wire(terms[0],a1,'A'); wire(terms[1],a1,'B')
a2=addx(E+'Add'); wire(a1,a2,'A'); wire(terms[2],a2,'B')

print('normal ->', ue.tool(M,'connect_to_output',
      {'expression':a2,'output_name':'','material_property':'MP_Normal'})[:60])
ue.tool(M,'layout_expressions',{'material_or_function':MAT})
ue.tool(M,'recompile',{'material_or_function':MAT})
ue.tool(AS,'save_assets',{'asset_paths':['/Game/Stacktown/Materials/M_StacktownMaster']})
print('recompiled and saved')
