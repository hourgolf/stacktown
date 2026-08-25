"""Restore PaperNormalAmount to the master's normal chain.

triplanar.py rebuilt MP_Normal as a vertex-normal-weighted sum of three
PaperNormal samples and did not carry the amplitude control across. The
parameter survived as an orphan expression, every card instance still sets it
to 2.0, and it has reached nothing since. Measured before this change:
PaperNormalAmount 2.0 -> 0.0 moved a flat pier's high-pass SD by 1.4 sigma
(nothing) while PaperTiling - which feeds the SAME three samplers - moved it by
100.8 sigma. M_StacktownMaster_2S never got the triplanar rewrite and still
carries the original Lerp(flat, sample, amount); this restores that construct
on top of the triplanar sum, so the two masters agree again.

Lerp rather than a multiply: a multiply would scale Z as well and shorten the
normal instead of tilting it, and lerping from (0,0,1) is what the 2S master
already does, so instance values keep the meaning they were authored with.
"""
import matlib as ml, json, sys

PATH = '/Game/Stacktown/Materials/M_StacktownMaster'
MAT  = ml.mat(PATH + '.M_StacktownMaster')

# clean up any probe nodes left from schema discovery
for e in ml.exprs(MAT):
    if e['refPath'].endswith('MaterialExpressionConstant3Vector_1'):
        ml.ue.tool(ml.M, 'delete_expression', {'material_or_function': MAT, 'expression': e})
        print('removed stray probe node')

cur = ml.property_input(MAT, 'MP_Normal')
if not cur: raise SystemExit('MP_Normal has no input - refusing to guess')
print('MP_Normal currently driven by %s' % cur['refPath'].split(':')[-1])

amt = ml.find_param(MAT, 'PaperNormalAmount')
if not amt: raise SystemExit('PaperNormalAmount parameter not found')
print('reusing existing PaperNormalAmount parameter (instance values keep meaning)')

flat = ml.addx(MAT, ml.E + 'Constant3Vector')
ml.setp(flat, {'constant': {'r': 0.0, 'g': 0.0, 'b': 1.0, 'a': 1.0}})
print('flat tangent normal (0,0,1) added:', ml.props(flat, ['constant']))

lerp = ml.addx(MAT, ml.E + 'LinearInterpolate')
ml.wire(flat, lerp, 'A')
ml.wire(cur,  lerp, 'B')
ml.wire(amt,  lerp, 'Alpha')

r = ml.ue.tool(ml.M, 'connect_to_output',
               {'expression': lerp, 'output_name': '', 'material_property': 'MP_Normal'})
print('MP_Normal ->', r[:80])
print(ml.finish(MAT, PATH, save=False)[:120])
