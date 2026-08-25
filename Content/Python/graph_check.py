"""Is PaperTiling connected to anything in the master graph?"""
import json, sys
import _path  # repo tool paths; replaces a dead scratchpad path
import ue
M='editor_toolset.toolsets.material.MaterialTools'
O='editor_toolset.toolsets.object.ObjectTools'
MAT={'refPath':'/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster'}
ex=json.loads(ue.tool(M,'get_expressions',{'material_or_function':MAT}))['returnValue']
params={}
for e in ex:
    if 'ScalarParameter' in e['refPath']:
        r=ue.tool(O,'get_properties',{'instance':e,'properties':['ParameterName','DefaultValue']})
        try: d=json.loads(json.loads(r)['returnValue'])
        except Exception: continue
        params.setdefault(d.get('ParameterName'),[]).append((e,d.get('DefaultValue')))
print('scalar parameters in the master:')
for k in sorted(params):
    print('   %-20s x%d  default %s'%(k,len(params[k]),params[k][0][1]))
print()
print('total expressions in graph:',len(ex))
from collections import Counter
kinds=Counter(e['refPath'].split('.')[-1].rstrip('0123456789_').replace('MaterialExpression','') for e in ex)
print('node kinds:',dict(kinds))
