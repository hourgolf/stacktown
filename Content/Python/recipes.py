"""A building is a RECIPE, not a model.

This is the thing the sandbox has actually been building for a week, and the
reason it is worth more than a folder of meshes: genbuild.build(spec) takes a
parameter set and emits geometry, so a new variant costs a parameter rather
than a modelling day.

A recipe is: a style, a base spec that never changes, and a list of TIERS. A
tier is the same building further along - more floors, a porch instead of a
stoop, dormers, a garage. Upgrading is moving up a tier and rebaking.

THE SEED LIVES IN THE BASE, NOT THE TIER. That is the whole trick: an upgraded
building keeps its jitter, its colour and its roof pitch, so it reads as the
same house grown rather than a different house swapped in.

`fits(width, depth)` is what the grammar asks when it has a parcel and needs to
know which recipes could stand on it. Pure functions, no Unreal import.
"""

RECIPES = {
    'cottage': dict(
        label='Cottage', style='house', district=('residential',),
        base=dict(kind='gen', style='house', depth=1500.0, gf_h=200.0,
                  fl_h=190.0, parapet=0.0, bays=3, wall='MI_paint_cream',
                  roofmat='MI_shingle_grey', seed=41),
        tiers=[
            dict(name='cabin',   floors=0, roof='gable', entry='stoop',
                 dormers=0, bay=False, garage=False),
            dict(name='house',   floors=1, roof='gable', entry='porch',
                 dormers=0, bay=True,  garage=False),
            dict(name='extended', floors=1, roof='gable', entry='porch',
                 dormers=2, bay=True,  garage=True),
        ],
        fits=lambda w, d: 700.0 <= w <= 1100.0 and d >= 1200.0),

    'walkup': dict(
        label='Walk-up', style='walkup', district=('residential', 'edge'),
        base=dict(kind='gen', style='walkup', depth=1500.0, gf_h=250.0,
                  fl_h=225.0, parapet=44.0, bays=4, wall='MI_precast_buff',
                  roofmat='MI_shingle_grey', seed=131),
        tiers=[
            dict(name='two-storey',   floors=1),
            dict(name='three-storey', floors=2),
            dict(name='four-storey',  floors=3),
        ],
        fits=lambda w, d: 1200.0 <= w <= 1600.0 and d >= 1200.0),
}


def spec_for(rid, tier, name, x0, width):
    """The full spec for one recipe at one tier, on a parcel."""
    r = RECIPES[rid]
    s = dict(r['base'])
    s.update(r['tiers'][tier])
    s.pop('name', None)
    s['name'] = name
    s['x0'] = x0
    s['width'] = width
    return s


def tier_count(rid):
    return len(RECIPES[rid]['tiers'])


def tier_name(rid, tier):
    return RECIPES[rid]['tiers'][tier]['name']


def asset_name(rid, tier, width):
    """One baked mesh per recipe, tier and parcel width. Width is part of the
    identity because the generator lays bays out across it - two widths are two
    different buildings, not one mesh scaled."""
    return 'SM_Bld_%s_t%d_w%d' % (rid, tier, int(round(width)))
