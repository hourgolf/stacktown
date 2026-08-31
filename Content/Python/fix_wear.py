"""Replace the edge-wear normal proxy with baked curvature.

BEFORE   wear = saturate((1 - max|PixelNormalWS|) / EdgeWearWidth)
AFTER    wear = saturate((1 - VertexColor.R)     / EdgeWearWidth)

Only the SOURCE of the term changes; the OneMinus / Divide / Saturate chain and
EdgeWearWidth are reused untouched, so every instance value keeps its meaning
and the edit is one wire. curvebake.py stores R = 1 - crease strength, and a 45
degree chamfer has crease strength 0.293, so it lands on 0.977 - which is what
the old proxy computed for the same chamfer. Geometry the old term got right
does not move; the cases it got wrong are the ones that change.

The path to the OneMinus is WALKED from MP_BaseColor rather than searched for
by class. There are five OneMinus nodes in this graph and three of them belong
to abandoned seam chains that are not connected to anything.
"""
import matlib as ml, json, sys

# Takes a material path so the same edit can be applied to every master. The 2S
# master needs it too: wiring 2S materials onto the vehicles while its wear
# still read PixelNormalWS would put curved bodywork straight back on the
# orientation proxy and undo the vehicle fix.
PATH = sys.argv[1] if len(sys.argv) > 1 else '/Game/Stacktown/Materials/M_StacktownMaster'
MAT  = ml.mat(PATH + '.' + PATH.rsplit('/', 1)[-1])

def inputs(e):
    r = ml.ue.tool(ml.M,'get_expression_inputs',
                   {'material_or_function':MAT,'expression':e})
    try: return json.loads(r)['returnValue']
    except Exception: return []

def pin(e, name):
    for i in inputs(e):
        if i.get('input_name') == name and isinstance(i.get('expression'), dict):
            return i['expression']
    return None

def cls(e): return e['refPath'].split(':')[-1].rstrip('0123456789_')

# MP_BaseColor -> Lerp(seam) -> A: Lerp(wear) -> Alpha: Saturate -> Divide -> A: OneMinus
seam = ml.property_input(MAT, 'MP_BaseColor')
assert cls(seam).endswith('LinearInterpolate'), cls(seam)
wear = pin(seam, 'A');      assert cls(wear).endswith('LinearInterpolate'), cls(wear)
sat  = pin(wear, 'Alpha');  assert cls(sat).endswith('Saturate'), cls(sat)
div  = pin(sat, '') or pin(sat, 'None') or inputs(sat)[0]['expression']
assert cls(div).endswith('Divide'), cls(div)
om   = pin(div, 'A');       assert cls(om).endswith('OneMinus'), cls(om)
wid  = pin(div, 'B')
print('walked to: %s  (divisor %s)' % (om['refPath'].split(':')[-1],
      ml.props(wid, ['parameterName']).get('parameterName')))
assert ml.props(wid, ['parameterName']).get('parameterName') == 'EdgeWearWidth'

old = inputs(om)
print('OneMinus currently fed by: %s' % ', '.join(
    cls(i['expression']) for i in old if isinstance(i.get('expression'), dict)))

if any('MaterialExpressionVertexColor' in e['refPath'] for e in ml.exprs(MAT)):
    raise SystemExit('VertexColor node already present - already migrated?')
vc = ml.addx(MAT, ml.E + 'VertexColor')
mask = ml.addx(MAT, ml.E + 'ComponentMask')
ml.setp(mask, {'r': True, 'g': False, 'b': False, 'a': False})
ml.wire(vc, mask, ml.pins(mask)[0])
ml.wire(mask, om, ml.pins(om)[0])
print('rewired OneMinus <- VertexColor.R')
print(ml.finish(MAT, PATH, save=False)[:120])
