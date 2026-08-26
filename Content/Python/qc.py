"""The QC constants, spelled once, importable without an editor.

DETAIL_MIN and MAT_MIN were defined inside invariants.py, which imports
snapshot, which imports `unreal` - so nothing outside a running editor could
read them. The per-model gate needs the SAME numbers and has to self-test
headlessly, and the obvious shortcut was to write 0.70 and 4 again in a second
file. Two copies of a threshold is how a rule quietly stops agreeing with the
rule it was derived from.

Pure data and one regex. No imports beyond `re`, deliberately: everything in
this project that has to be checkable without a level depends on that staying
true.
"""
import re

DETAIL_MIN = 0.70        # parts per square metre of street elevation
MAT_MIN = 4              # distinct material instances on a building
DENSITY_MIN = 0.10       # parts per square metre of ground, for an open lot

# a component the engine renamed after a name collision
AUTO_NAME = re.compile(r'^StaticMesh(Component)?_?\d+$')

# materials that mean "nothing was ever bound here"
DEFAULT_MATS = ('WorldGridMaterial', 'DefaultMaterial',
                'DefaultDeferredDecalMaterial')
