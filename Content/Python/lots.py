"""The block layout. Lots tile edge to edge; adjacent buildings share a party
wall rather than leaving a slot, which is what closed the crushed-black column
at frame centre."""
STAGE1_END = 1080.0
LOTS = [
    dict(kind='gen', name='Narrow', x0=1080.0, width=860.0,  depth=700.0,
         floors=6, gf_h=380.0, fl_h=330.0, parapet=70.0,  bays=2,
         canopy=None,  setback=90.0,  roof_units=1, seed=11, wall='MI_card_ochre'),
    dict(kind='av',  name='AV',     x0=1955.0, width=1200.0, depth=800.0,
         floors=3, fl_h=300.0, wall='MI_card_sage'),
    dict(kind='gen', name='Mid',    x0=3170.0, width=980.0,  depth=750.0,
         floors=5, gf_h=400.0, fl_h=350.0, parapet=90.0,  bays=3,
         canopy=None,  setback=120.0, roof_units=1, seed=37, wall='MI_card_rose'),
]
