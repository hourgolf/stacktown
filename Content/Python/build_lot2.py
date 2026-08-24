import sys, time; sys.path.insert(0,'.')
from genbuild import build
t=time.time()
h=build(dict(name='Narrow', x0=1120.0, width=860.0, depth=700.0,
             floors=6, gf_h=380.0, fl_h=330.0, parapet=70.0, bays=2,
             canopy=None, setback=90.0, roof_units=1, seed=11))
print('elapsed %.1fs'%(time.time()-t))
