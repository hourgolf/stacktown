"""The one place actor label families are spelled.

`check_clear.py` once reported "0 lamp/vehicle intersections" while searching
for `SUR_lamp*` and `VEH_*`. The actors are `LAMP_s*`, `LAMP_a*` and
`BAKED_veh*`. The check was not wrong about the world; it was asking about
actors that do not exist, and it answered "clean" with total confidence. No
check spells a family itself any more - they all read it from here, and
NAME-01 fails when the level contains a family this file does not list, so a
script that invents a new prefix is caught the pass it is written.

A FAMILY is the leading run of capitals in an actor label:
    LIGHT2_Narrow_Interior_Shop -> LIGHT
    SUR_zone_Greens_t0          -> SUR
    LAMPLIGHT_s1F_0             -> LAMPLIGHT   (not LAMP - longest run wins)

Anything finer than a family is decided by the MESH, not the label. Label
conventions drift between scripts; a mesh name is a fact about the asset. The
zone planting bag is the case that forces this: it puts bushes in labels ending
`_t`, so `_t` does not mean tree and never did.
"""
import re

_FAMILY = re.compile(r'^[A-Z]+')


def family(label):
    m = _FAMILY.match(label or '')
    return m.group(0) if m else ''


# family -> (what it is, which script authors it)
REGISTRY = {
    'CAM':       ('cameras',                                  'cam_*.py'),
    'LOOK':      ('the post-process volume, fixed exposure',   'stage setup'),
    'STAGE':     ('board, backdrop, ground plane, street',     'step_stage2.py'),
    'LIGHT':     ('sun, sky, atmosphere, key, fill, practicals',
                                              'light_rig.py, practicals.py'),
    'LAMP':      ('street lamp columns and arms',              'street_lamps.py'),
    'LAMPLIGHT': ('the light a lamp emits',                    'lamp_lights.py'),
    'ROAD':      ('carriageway, footway and crossing slabs',   'step_stage2.py'),
    'BLD':       ('generated building mass',                   'genbuild.py'),
    'CORE':      ('the solid mass standing behind a facade',   'step_cores3.py'),
    'ELEV':      ('flank and rear elevations',                 'step_elevations.py'),
    'AV':        ('Assetsville-derived building parts',        'step_av.py'),
    'ZONE':      ('non-building lots: plaza, park, vacant',    'zones.py'),
    'SUR':       ('surface dressing: planting, furniture, signals, roof kit',
                                              'fix4_props.py, zones.py'),
    'BAKED':     ('baked static vehicles',                     'place_baked.py'),
    'CAT':       ('the baked catalogue on its display pad, not the city',
                                              'place_catalogue.py'),
    'PLOT':      ('a lot around a home: garden, fences, drive, shed',
                                              'genbuild.build_house / build_walkup'),
    'SHOP':      ('shopfront dressing: awnings, fascia boards, signs',
                                              'step_shopfronts.py'),
    'PROP':      ('yard props, and the Stage 1 tree kept deliberately',
                                              'yard_props.py, stage 1'),
    'BENCH':     ('the benchmark stand cameras: hero, street, roof', 'bench.py'),
    'STAND':     ('the benchmark model itself, parked off-board',    'bench.py'),
    'STUDY':     ('the material study wall, one variable per panel', 'study.py'),
}

# Families wiped and rebuilt on every dressing pass. Anything here must be
# removable by label alone, or it accumulates - 401 stale props once roofed the
# plaza because the wipe matched `SUR_prop*` and `SUR_tree*` and nothing else.
# PROP joined 2026-08-25: yard_props.py made the family a real dressing pass
# (wiped and rebuilt by label), and while it was missing here the containers
# were invisible to DRESS-04 (on board) and DRESS-06 (duplicate wipes).
DRESSING = ('SUR', 'BAKED', 'LAMP', 'LAMPLIGHT', 'SHOP', 'PROP')

# --- mesh-level classification ---------------------------------------------
def is_vehicle(label, mesh):
    return family(label) == 'BAKED' and (mesh or '').startswith('SM_Baked_')

def is_lamp(label, mesh):
    return family(label) == 'LAMP'

def is_tree(label, mesh):
    return (mesh or '').startswith('SM_tree_')

def is_bush(label, mesh):
    return (mesh or '').startswith('SM_bush_')

def is_planting(label, mesh):
    return is_tree(label, mesh) or is_bush(label, mesh)

# --- the role vocabulary ----------------------------------------------------
# Role-in-the-component-name is how one sweep binds every material in the
# project, and until now the list of roles lived only inside step_roles.py -
# which imports `unreal` and therefore cannot be read by anything that has to
# run without an editor. The per-model gate needs exactly that: to ask "does
# every component here carry a role I recognise" BEFORE a bake, as a pure
# function it can self-test.
#
# So the vocabulary lives here with the families, for the same reason the
# families do. step_roles validates its own table against this on import; a
# role bound there and missing here is a bug in one of the two, and the gate
# says which.
# Leaf_/Planter_/Brick_ added 2026-08-27, owner-approved, recorded in
# MASTER_MATERIAL_SPEC. DONOR MESHES now carry roles like everything else.
# They did not, which was invisible only because piece() silently placed
# nothing; once donors actually landed, GATE-01 refused all 548 combinations
# for having a component with no role. Three of their materials had no role
# that resolved to them, so the vocabulary had to grow rather than the names
# being bent to fit - bending them would have repainted every donor, since
# step_roles binds material FROM the role.
#   Leaf_    the alpha-masked foliage cards (per-slot still refines trunk)
#   Planter_ the ubkit flowerbed parts
#   Brick_   the chimney - owner's look decision: it stays brick regardless
#            of the lot's wall colour, which is the classic card-model read
# MI_bloom_cool is a Bloom_ SUFFIX variant, not a role - see rolemap.BLOOM.
ROLES = (
    'Wall_', 'Band_', 'Glass_', 'Interior_', 'Frame_', 'Mullion_',
    'Accent_', 'Roof_', 'Tile_', 'Ground_', 'Gravel_', 'Grass_',
    'Kerbing_', 'Bloom_', 'Rail_', 'Timber_', 'Mural_',
    'Leaf_', 'Planter_', 'Brick_', 'GrassCard_',
)


def role(name):
    """The role prefix a component name carries, or None."""
    return next((r for r in ROLES if (name or '').startswith(r)), None)

