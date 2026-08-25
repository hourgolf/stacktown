"""Shared helpers for editing the master material over MCP."""
import ue, json

M  = 'editor_toolset.toolsets.material.MaterialTools'
O  = 'editor_toolset.toolsets.object.ObjectTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
E  = '/Script/Engine.MaterialExpression'

def mat(path):
    return {'refPath': path}

def addx(MAT, cls):
    r = ue.tool(M,'add_expression',{'material_or_function':MAT,
                                    'expression_class':{'refPath':cls}})
    if 'ERROR' in r: raise SystemExit('add %s failed: %s' % (cls, r[:200]))
    return json.loads(r)['returnValue']

def props(node, names):
    r = ue.tool(O,'get_properties',{'instance':node,'properties':names})
    try: return json.loads(json.loads(r)['returnValue'])
    except Exception: return {}

def schema(node):
    r = ue.tool(O,'list_properties',{'instance':node})
    try: return set(json.loads(json.loads(r)['returnValue']).keys())
    except Exception: return set()

def setp(ref, vals):
    r = ue.tool(O,'set_properties',{'instance':ref,'values':json.dumps(vals)})
    if '"returnValue":true' not in r:
        print('   WARN set %s -> %s' % (list(vals), r[:120]))
        return False
    return True

def pins(e):
    return json.loads(ue.tool(M,'get_expression_input_names',{'expression':e}))['returnValue']

def wire(frm, to, pin=None, out=''):
    names = pins(to)
    cands = [pin] if pin else (names or [''])
    for p in cands:
        r = ue.tool(M,'connect_expressions',
                    {'from_expression':frm,'from_output_name':out,
                     'to_expression':to,'to_input_name':p})
        if 'ERROR' not in r and 'TOOL-ERROR' not in r: return True
    raise SystemExit('FAILED wire into %s (tried %s)' % (names, cands))

def exprs(MAT):
    return json.loads(ue.tool(M,'get_expressions',{'material_or_function':MAT}))['returnValue']

def find_param(MAT, name, kind='ScalarParameter'):
    for e in exprs(MAT):
        if kind in e['refPath'] and props(e,['parameterName']).get('parameterName') == name:
            return e
    return None

def property_input(MAT, prop):
    r = ue.tool(M,'get_property_input',{'material':MAT,'material_property':prop})
    try: return json.loads(r)['returnValue']['expression']
    except Exception: return None

def finish(MAT, path, save=False):
    ue.tool(M,'layout_expressions',{'material_or_function':MAT})
    r = ue.tool(M,'recompile',{'material_or_function':MAT})
    if 'ERROR' in r: raise SystemExit('recompile FAILED: %s' % r[:300])
    if save:
        ue.tool(AS,'save_assets',{'asset_paths':[path]})
    return r
