"""Dump a material graph: every expression, its properties, and its inputs.

Walks BACKWARDS from the material's output properties, so what it prints is the
subgraph that actually compiles. Nodes not reachable from an output are listed
separately at the end - that distinction is the whole point: an unconnected node
contributes nothing however correct it looks, and this project has already lost
time to a parameter that was bound everywhere and reaching nothing.

Property names are discovered per expression CLASS via list_properties. Asking
get_properties for a name the class does not have returns "{}" for the WHOLE
call, silently, which is how the first version of this dumper reported every
parameter as nameless.
"""
import json, sys, ue

M = 'editor_toolset.toolsets.material.MaterialTools'
O = 'editor_toolset.toolsets.object.ObjectTools'

MATPATH = sys.argv[1] if len(sys.argv) > 1 else \
    '/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster'
MAT = {'refPath': MATPATH}

OUTPUTS = ['MP_BaseColor','MP_Metallic','MP_Specular','MP_Roughness','MP_Normal',
           'MP_EmissiveColor','MP_Opacity','MP_OpacityMask','MP_AmbientOcclusion',
           'MP_WorldPositionOffset','MP_PixelDepthOffset','MP_Anisotropy','MP_Tangent',
           'MP_Displacement','MP_SubsurfaceColor']

WANT = ['parameterName','defaultValue','group','texture','samplerType','r','g','b','a',
        'constant','constA','constB','const1','const2','scale','levels','period',
        'coordinateIndex','uTiling','vTiling','function','desc','bClampResult',
        'outputMin','outputMax','value','defaultValue_R']

def j(raw):
    try: return json.loads(raw)['returnValue']
    except Exception: return None

def cls(e):
    return e['refPath'].split(':')[-1].rstrip('0123456789').rstrip('_')

_schema = {}
def schema(e):
    c = cls(e)
    if c not in _schema:
        s = j(ue.tool(O,'list_properties',{'instance':e}))
        try: _schema[c] = set(json.loads(s).keys())
        except Exception: _schema[c] = set()
    return _schema[c]

_pcache = {}
def props(e):
    k = e['refPath']
    if k in _pcache: return _pcache[k]
    ask = [p for p in WANT if p in schema(e)]
    d = {}
    if ask:
        r = ue.tool(O,'get_properties',{'instance':e,'properties':ask})
        try: d = json.loads(json.loads(r)['returnValue'])
        except Exception: d = {}
    d = {k2:v for k2,v in d.items() if v not in (None,'','None',[],{})}
    _pcache[k] = d
    return d

_icache = {}
def inputs(e):
    k = e['refPath']
    if k not in _icache:
        r = j(ue.tool(M,'get_expression_inputs',
                      {'material_or_function':MAT,'expression':e})) or []
        _icache[k] = [x for x in r if isinstance(x,dict)]
    return _icache[k]

def label(e):
    p = props(e)
    c = cls(e).replace('MaterialExpression','')
    bits = []
    if c.endswith('ComponentMask'):
        bits.append('mask=' + (''.join(ch for ch,k in zip('RGBA','rgba') if p.get(k) is True) or '-'))
    for key in ('parameterName','defaultValue','constant','const1','const2',
                'texture','samplerType','scale','coordinateIndex','period','group'):
        if key in p:
            v = p[key]
            if isinstance(v,dict): v = v.get('refPath','?').split('.')[-1]
            bits.append('%s=%s' % (key,v))
    return ('%s  %s' % (c,'  '.join(bits))).rstrip()

def walk(e, depth, pin, visited, out):
    tag = e['refPath']
    dup = tag in visited
    out.append('%s%s%s%s' % ('   '*depth, (pin+': ') if pin else '',
                             label(e), '   [^ shown above]' if dup else ''))
    if dup: return
    visited.add(tag)
    for inp in inputs(e):
        src = inp.get('expression')
        if isinstance(src,dict) and src.get('refPath'):
            out_name = inp.get('output_name') or ''
            nm = inp.get('input_name') or ''
            if out_name: nm = '%s <%s>' % (nm, out_name)
            walk(src, depth+1, nm, visited, out)

print('=== %s ===' % MATPATH)
allex = j(ue.tool(M,'get_expressions',{'material_or_function':MAT})) or []
print('expressions in graph: %d\n' % len(allex))

connected = set()
for prop in OUTPUTS:
    r = j(ue.tool(M,'get_property_input',{'material':MAT,'material_property':prop}))
    src = r.get('expression') if isinstance(r,dict) else None
    if not (isinstance(src,dict) and src.get('refPath')): continue
    out, visited = [], set()
    walk(src, 1, '', visited, out)
    connected |= visited
    print(prop); print('\n'.join(out)); print()

orphans = [e for e in allex if e['refPath'] not in connected]
print('--- NOT reachable from any material output (%d of %d) ---' % (len(orphans),len(allex)))
for e in orphans:
    print('   ', label(e))
