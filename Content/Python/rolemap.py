"""Role prefix -> material name. Pure, so both backends read the same table.

step_roles.py held this and imports `unreal`, so the fast bake path could not
reach it. Copying the table into fastbake would be two answers to "what colour
is a Timber_", and this project has been bitten by a duplicated table roughly
once a session. So the table moved here and step_roles imports it.

`material_for` is the whole contract: give it a component name and the lot's
wall/roof choices, get the material instance name back.
"""
import labels

SHARED = {
    'Glass_': 'MI_glass_b',
    'Interior_': 'MI_interior',
    'Frame_': 'MI_frame_print',
    'Mullion_': 'MI_frame_print',
    'Accent_': 'MI_canopy_accent',
    'Roof_': 'MI_concrete',
    # ground roles, for zones that are not buildings
    'Ground_': 'MI_concrete',
    'Grass_': 'MI_grass',
    'Kerbing_': 'MI_paint_cream',
    # a yard is not a car park: the apron is laid concrete, the rest compacted
    # ground. NOT MI_precast_buff - measured, that is (0.745,0.700,0.612)
    # against concrete's (0.700,0.672,0.616) and the two do not separate.
    'Gravel_': 'MI_gravel',
    # a rail or post is dark painted metal, not window-frame print
    'Rail_': 'MI_dark_metal',
    # decking, planters and pergolas on a reclaimed roof
    'Timber_': 'MI_wood',
    # paint on a wall; the panel suffix picks which of the three
    'Mural_': 'MI_mural_a',
    # a raised bed is PLANTING; on MI_grass it is a raised bed of grass
    'Bloom_': 'MI_bloom_warm',
}

# Some families want a different material for the SAME role. A lamp column is
# dark painted metal, not the window-frame print - both are 'Frame_' because
# both are a frame, and role-in-the-name is about what a part IS.
FAMILY = {'LAMP': {'Frame_': 'MI_dark_metal'}}

# A mural is three colours, so panels differ by SUFFIX rather than role.
# NOT the card colours: measured against MI_paint_cream their smallest
# per-channel deltas are 0.020, 0.040 and 0.163 - invisible. See mk_mural.py.
MURAL = {'A': 'MI_mural_a', 'B': 'MI_mural_b', 'C': 'MI_mural_c'}

# Components whose ROLE is right but whose SUBJECT wants a different material.
# A penthouse is glazed and has an interior, so Glass_/Interior_ are the
# correct roles - but a window's glass is a dark opening (lum 0.080) and a
# glass penthouse is a lit volume. Matched on prefix, checked BEFORE the role
# table, so nothing else in the project moves.
SPECIAL = {
    'Glass_Pent': 'MI_glass_pent',
    'Interior_Pent': 'MI_interior_lit',
}

DEFAULT_WALL = 'MI_paint_cream'
DEFAULT_ROOF = 'MI_shingle_grey'

# roles bound by prefix here, plus the three resolved per-lot below
BOUND = set(SHARED) | {'Tile_', 'Wall_', 'Band_'} | {
    r for o in FAMILY.values() for r in o}


def material_for(comp, wall=None, roofmat=None, family='BLD2'):
    """The material instance name for one component. None if nothing binds it."""
    if comp.startswith('Mural_'):
        return MURAL.get(comp[-1], SHARED['Mural_'])
    for pre, mi in SPECIAL.items():
        if comp.startswith(pre):
            return mi
    fam = FAMILY.get(family, {})
    for r in fam:
        if comp.startswith(r):
            return fam[r]
    for r in SHARED:
        if comp.startswith(r):
            return SHARED[r]
    if comp.startswith('Tile_'):
        return roofmat or DEFAULT_ROOF
    if comp.startswith('Wall_') or comp.startswith('Band_'):
        return wall or DEFAULT_WALL
    return None


def _selftest():
    assert material_for('Wall_Pier0', wall='MI_precast_buff') == 'MI_precast_buff'
    assert material_for('Band_Course', wall='MI_precast_buff') == 'MI_precast_buff'
    assert material_for('Tile_Step2', roofmat='MI_shingle_brown') == 'MI_shingle_brown'
    assert material_for('Glass_B0') == 'MI_glass_b'
    assert material_for('Timber_Deck') == 'MI_wood'
    assert material_for('Mural_B') == 'MI_mural_b'
    assert material_for('Frame_Post', family='LAMP') == 'MI_dark_metal'
    assert material_for('Frame_Post', family='BLD2') == 'MI_frame_print'
    assert material_for('StaticMeshComponent0') is None
    # the penthouse takes its own glazing; every other window does not
    assert material_for('Glass_Pent0F') == 'MI_glass_pent'
    assert material_for('Interior_Pent1') == 'MI_interior_lit'
    assert material_for('Glass_B0') == 'MI_glass_b'
    assert material_for('Interior_Shop') == 'MI_interior'
    # the vocabulary must match labels.ROLES exactly, or the gate cannot see
    # a role that is bound, or a listed role binds to nothing
    assert BOUND == set(labels.ROLES), (sorted(BOUND ^ set(labels.ROLES)),)
    return True


if __name__ == '__main__':
    print('rolemap self-test:', _selftest())
