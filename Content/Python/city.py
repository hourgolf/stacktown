"""The city table. A block is an origin, a yaw, and a list of lots.

Block A faces -Y onto the street. Block B is the far side of the same street,
built from the same generator and rotated 180 degrees - under yaw 180 a lot at
local x 0..W lands at world X0-W..X0, and local +Y (depth) runs to -Y, so B's
origin sits at the FAR kerb and the buildings grow away from the street.
"""
STREET_FACE_A = 0.0        # block A facade line
STREET_FACE_B = -1600.0    # block B facade line, across the road

BLOCKS = [
  dict(name='A', origin=(0.0, STREET_FACE_A, 0.0), yaw=0.0, lots=[
     dict(kind='gen', name='Narrow', x0=1080.0, width=860.0,  depth=700.0,
          floors=6, gf_h=380.0, fl_h=330.0, parapet=70.0,  bays=2,
          canopy=None, setback=90.0,  roof_units=1, seed=11, wall='MI_card_ochre'),
     dict(kind='av',  name='AV',     x0=1955.0, width=1200.0, depth=800.0,
          floors=3, fl_h=300.0, wall='MI_card_sage'),
     dict(kind='gen', name='Mid',    x0=3170.0, width=980.0,  depth=750.0,
          floors=5, gf_h=400.0, fl_h=350.0, parapet=90.0,  bays=3,
          canopy=None, setback=120.0, roof_units=1, seed=37, wall='MI_card_rose'),
  ]),
  dict(name='B', origin=(4150.0, STREET_FACE_B, 0.0), yaw=180.0, lots=[
     dict(kind='gen', name='Bank',   x0=0.0,    width=1120.0, depth=780.0,
          floors=4, gf_h=460.0, fl_h=360.0, parapet=130.0, bays=3,
          canopy=220.0, setback=None, roof_units=2, seed=71, wall='MI_paint_cream'),
     dict(kind='gen', name='Slim',   x0=1120.0, width=740.0,  depth=700.0,
          floors=7, gf_h=360.0, fl_h=300.0, parapet=60.0,  bays=2,
          canopy=None,  setback=70.0, roof_units=1, seed=83, wall='MI_card_rose'),
     dict(kind='gen', name='Hall',   x0=1860.0, width=1340.0, depth=820.0,
          floors=3, gf_h=520.0, fl_h=420.0, parapet=150.0, bays=4,
          canopy=260.0, setback=None, roof_units=2, seed=97, wall='MI_card_ochre'),
  ]),
]
