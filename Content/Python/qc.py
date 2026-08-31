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

# --- archetype thresholds ---------------------------------------------------
# The archetype registry (archetypes.py) may judge a rule at a different
# number than the street one, but the number itself lives HERE, next to
# DETAIL_MIN, for the reason this file exists at all: two copies of a
# threshold is how a rule quietly stops agreeing with the rule it was
# derived from.
#
# PROVISIONAL, and marked so on purpose: no industrial geometry exists yet -
# the archetype is declared before the first model, which is the point - so
# this number is a declared intent, not a measurement. HANDOFF §5: "do not
# invent a threshold and then judge against it." Before the first real
# industrial model is gated for a bake, measure it and set this from the
# measurement, the way DETAIL_MIN was set from the built city.
DETAIL_MIN_INDUSTRIAL = 0.25   # parts per m2 of elevation, industrial shell
