import sys, time; sys.path.insert(0,'.')
from genbuild import build
import genbuild as _gb
_gb.live()   # this script builds into the OPEN level; see genbuild._LIVE
t=time.time()
build(dict(name='Wide', x0=2020.0, width=1240.0, depth=800.0,
           floors=3, gf_h=420.0, fl_h=380.0, parapet=110.0, bays=4,
           canopy=220.0, setback=None, roof_units=2, seed=23))
build(dict(name='Mid', x0=3300.0, width=980.0, depth=750.0,
           floors=5, gf_h=400.0, fl_h=350.0, parapet=90.0, bays=3,
           canopy=None, setback=120.0, roof_units=1, seed=37))
print('elapsed %.0fs'%(time.time()-t))
