"""The city table. A block is an origin, a yaw, and a list of lots.

Block A faces -Y onto the street. Block B is the far side of the same street,
built from the same generator and rotated 180 degrees - under yaw 180 a lot at
local x 0..W lands at world X0-W..X0, and local +Y (depth) runs to -Y, so B's
origin sits at the FAR kerb and the buildings grow away from the street.
"""
# ---------------------------------------------------------------------------
# ROADS ARE DERIVED, NOT PLACED.
#
# The carriageway was 740 uu. Cars park 150 uu off each kerb and are 252 wide,
# so parked cars occupied 552 of it and left a 188 uu gap - 1.9 m, not a
# passable street. Every facade line was also a hand-written constant, so
# changing a road width meant editing six of them and hoping.
#
# Now the widths are the input and the facade lines fall out of them. A street
# is two parking lanes and two running lanes:
#     250 park + 350 run + 350 run + 250 park = 1200, plus margin -> 1400
# ---------------------------------------------------------------------------
ROAD_W      = 1400.0       # carriageway: parking both sides plus two lanes
WALK_W      = 430.0        # footway each side
SERV_ROAD_W = 900.0        # the back service street is narrower on purpose
SERV_WALK   = 250.0

CORRIDOR      = ROAD_W + 2*WALK_W          # facade line to facade line
SERV_CORRIDOR = SERV_ROAD_W + 2*SERV_WALK

STREET_FACE_A = 0.0                                    # block A
STREET_FACE_B = STREET_FACE_A - CORRIDOR               # block B, across street 1
BLOCK_B_DEPTH = 790.0
BLOCK_B_REAR  = STREET_FACE_B - BLOCK_B_DEPTH
STREET_FACE_C = BLOCK_B_REAR - CORRIDOR                # block C north, over street 2
BLOCK_C_SEP   = 1280.0                                 # C's two rows, back to back
STREET_FACE_D = STREET_FACE_C - BLOCK_C_SEP            # block C south
STREET3_FAR   = STREET_FACE_D - SERV_CORRIDOR
# The board grows south for the houses, exactly as it grew east for the avenue.
# Block F fronts the service street opposite the park.
BLOCK_F_DEPTH = 820.0
BLOCK_F_REAR  = STREET3_FAR - BLOCK_F_DEPTH
BOARD_S       = BLOCK_F_REAR - 300.0
STREET_FACE_E = STREET_FACE_B                          # block D fronts street 1 too

AVENUE_W = 4400.0
AVENUE_E = AVENUE_W + CORRIDOR
BLOCK_D_X = AVENUE_E + 4100.0                          # block D's far end
BOARD_E   = BLOCK_D_X + 300.0

STREETS = [
    (STREET_FACE_B, STREET_FACE_A, WALK_W),   # 1: between A and B
    (STREET_FACE_C, BLOCK_B_REAR,  WALK_W),   # 2: behind B, in front of C
    (STREET3_FAR,   STREET_FACE_D, SERV_WALK),# 3: the service street
]

# North-south roads. Same shape as STREETS - two frontage lines and a pavement
# width - so the same builder handles both and an intersection is simply where
# one crosses the other.
AVENUES = [
    (AVENUE_W, AVENUE_E, WALK_W),
]

BLOCKS = [
  dict(name='A', origin=(0.0, STREET_FACE_A, 0.0), yaw=0.0,
       abuts_low=True, abuts_high=False, lots=[
     dict(kind='gen', name='Narrow', x0=1080.0, width=860.0,  depth=700.0,
          floors=6, gf_h=380.0, fl_h=330.0, parapet=70.0,  bays=2,
          canopy=None, setback=90.0,  roof_units=1, seed=11, wall='MI_card_ochre'),
     dict(kind='av',  name='AV',     x0=1955.0, width=1200.0, depth=800.0,
          floors=3, fl_h=300.0, wall='MI_card_sage'),
     dict(kind='gen', name='Mid',    x0=3170.0, width=980.0,  depth=750.0,
          floors=5, gf_h=400.0, fl_h=350.0, parapet=90.0,  bays=3,
          canopy=None, setback=120.0, roof_units=1, seed=37, wall='MI_card_rose'),
  ]),
  # --- Block C: an ISLAND block, two rows back to back ---------------------
  # Row N faces +Y onto street 2, row S faces -Y onto street 3, and their rears
  # meet on a party line at y -4690, so neither rear is ever seen and neither
  # needs an elevation. Late-modern: same generator, style='modern'.
  # The rows' facade lines are 1280 uu apart (-4050 to -5330), so for any pair of
# lots that overlap in X, depth_N + depth_S must not exceed that or they eat
# into each other. Plaza 660 + Annex 660 = 1320 failed the geometry check by
# 60 uu the moment the depths were varied for massing.
#
# island_with: these two rows are BACK TO BACK and share a rear party line,
  # so a lot in one may share a wall with a lot in the other. Without this the
  # geometry check calls every cross-row touch a non-neighbour overlap - it
  # found four of them the moment it started looking at more than block A.
  dict(name='CN', origin=(4150.0, STREET_FACE_C, 0.0), yaw=180.0,
       abuts_low=False, abuts_high=False, island_with='CS', lots=[
     dict(kind='gen', name='Tower',  x0=0.0,    width=1000.0, depth=640.0,
          floors=7, gf_h=520.0, fl_h=400.0, parapet=90.0,  bays=3,
          canopy=None, setback=140.0, roof_units=2, seed=131,
          wall='MI_concrete',      style='modern', corner=True),
     # The hole in the street wall IS the period. A 1970s superblock sets its
     # tower back behind a public plaza, and Slab was the shortest lot in the
     # row, so it is the one that becomes open space.
     # 1500 x 610 was a light well, not a square: 15 x 6 m between a 34 m tower
     # and a 25 m block, in permanent shadow at the sun's 52 degree elevation.
     # Widened to 2150 by taking frontage from both neighbours.
     # RENAMED 2026-08-24. This was 'Forecourt', kind='plaza'. It is 2150 x 610
     # - and 62 of that depth is the front offset and 162 the paved apron, so
     # the lawn is 370 uu, 3.7 m. That is a GREEN: a planted strip off the
     # pavement with a path through it. Calling it a plaza did not make it one,
     # and widening it earlier made it longer rather than deeper. A real plaza
     # is paving-dominant with a focus, and needs depth this block does not
     # have; it belongs on a block that does.
     dict(kind='green', name='Green', x0=1000.0, width=2150.0, depth=610.0,
          seed=137),
     dict(kind='gen', name='Terrace', x0=3150.0, width=1000.0, depth=630.0,
          floors=5, gf_h=540.0, fl_h=380.0, parapet=100.0, bays=3,
          canopy=None, setback=110.0, roof_units=1, seed=139,
          wall='MI_precast_grey',  style='modern', corner=True),
  ]),
  dict(name='CS', origin=(0.0, STREET_FACE_D, 0.0), yaw=0.0,
       abuts_low=False, abuts_high=False, lots=[
     dict(kind='gen', name='Annex',  x0=0.0,    width=1300.0, depth=640.0,
          floors=2, gf_h=560.0, fl_h=440.0, parapet=110.0, bays=4,
          canopy=None, setback=None, roof_units=1, seed=149,
          wall='MI_precast_buff',  style='modern', corner=True),
     dict(kind='gen', name='Court',  x0=1300.0, width=1400.0, depth=620.0,
          floors=6, gf_h=500.0, fl_h=390.0, parapet=85.0,  bays=4,
          canopy=None, setback=120.0, roof_units=1, seed=151,
          wall='MI_concrete',      style='modern'),
     dict(kind='gen', name='Civic',  x0=2700.0, width=1450.0, depth=630.0,
          floors=4, gf_h=580.0, fl_h=430.0, parapet=170.0, bays=4,
          canopy=None, setback=None, roof_units=2, seed=157,
          wall='MI_precast_grey',  style='modern', corner=True),
  ]),
  # --- Block D: across the avenue, 1930s -----------------------------------
  # A single row between streets 1 and 2, like block B, but east of the
  # intersection. Its high-x lot (world X 6000) is the AVENUE corner - the one
  # that reads at the intersection - so it gets the flank treatment and a
  # shopfront that turns.
  dict(name='D', origin=(BLOCK_D_X, STREET_FACE_E, 0.0), yaw=180.0,
       abuts_low=False, abuts_high=False, rear_street=True, lots=[
     dict(kind='gen', name='Empire',  x0=0.0,    width=1400.0, depth=760.0,
          floors=7, gf_h=500.0, fl_h=340.0, parapet=120.0, bays=3,
          canopy=None, setback=None, roof_units=1, seed=211,
          wall='MI_paint_cream',  style='deco', corner=True),
     dict(kind='gen', name='Bijou',   x0=1400.0, width=1300.0, depth=760.0,
          floors=5, gf_h=480.0, fl_h=330.0, parapet=100.0, bays=3,
          canopy=None, setback=None, roof_units=1, seed=223,
          wall='MI_precast_buff', style='deco'),
     dict(kind='gen', name='Marquee', x0=2700.0, width=1400.0, depth=760.0,
          floors=9, gf_h=520.0, fl_h=330.0, parapet=140.0, bays=3,
          canopy=None, setback=None, roof_units=2, seed=227,
          wall='MI_paint_cream',  style='deco', corner=True),
  ]),
  # --- Block E: the city park -----------------------------------------------
  # Between streets 2 and 3, east of block C. It was empty board - a block-sized
  # rectangle of nothing, ringed by pavement, trees and parked cars because the
  # street furniture follows the STREETS whether or not anything stands behind
  # them. From the ground it read as a paved void, which is what "sand pit"
  # meant. A full-block park is a real use for it, fronts both streets, and
  # exercises kind='park'.
  dict(name='E', origin=(BLOCK_D_X, STREET_FACE_C, 0.0), yaw=180.0,
       abuts_low=False, abuts_high=False, lots=[
     # Block E is yaw 180, so LOCAL +x runs WEST in world space: local
     # 2700..4100 is world X 6660..8060, the west end. Plaza west, park east.
     dict(kind='park',  name='Greens', x0=0.0,    width=2700.0, depth=1280.0,
          wall=None, seed=307),
     dict(kind='plaza', name='Square', x0=2700.0, width=1400.0, depth=1280.0,
          wall=None, seed=911),
  ]),
  # rear_street: block B's back faces street 2, which did not exist when this
  # block was built. A rear that fronts a road is an elevation, not a party
  # line, so these lots get one.
  dict(name='B', origin=(4150.0, STREET_FACE_B, 0.0), yaw=180.0,
       abuts_low=False, abuts_high=False, rear_street=True, lots=[
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

  # --- Block F: houses, across the service street from the park --------------
  # The first residential lots. A house is not a small office block: two
  # storeys, a pitched roof, a porch, and - the part that actually reads as
  # residential - a SETBACK, so the street line is gardens and fences rather
  # than shopfronts. They are detached, so each lot is wider than its house and
  # the gap between them is the point.
  dict(name='F', origin=(BLOCK_D_X, STREET3_FAR, 0.0), yaw=180.0,
       abuts_low=False, abuts_high=False, lots=[
     dict(kind='gen', style='house', name='Elm',    x0=0.0,    width=820.0,
          depth=BLOCK_F_DEPTH, floors=1, gf_h=200.0, fl_h=190.0, parapet=0.0,
          bays=3, wall='MI_paint_cream', seed=41),
     dict(kind='gen', style='house', name='Maple',  x0=820.0,  width=820.0,
          depth=BLOCK_F_DEPTH, floors=1, gf_h=210.0, fl_h=185.0, parapet=0.0,
          bays=3, wall='MI_card_sage', seed=57),
     dict(kind='gen', style='house', name='Cedar',  x0=1640.0, width=820.0,
          depth=BLOCK_F_DEPTH, floors=1, gf_h=195.0, fl_h=195.0, parapet=0.0,
          bays=3, wall='MI_card_ochre', seed=73),
     dict(kind='gen', style='house', name='Birch',  x0=2460.0, width=820.0,
          depth=BLOCK_F_DEPTH, floors=1, gf_h=205.0, fl_h=188.0, parapet=0.0,
          bays=3, wall='MI_card_rose', seed=89),
     dict(kind='gen', style='house', name='Willow', x0=3280.0, width=820.0,
          depth=BLOCK_F_DEPTH, floors=1, gf_h=200.0, fl_h=192.0, parapet=0.0,
          bays=3, wall='MI_paint_cream', seed=97),
  ]),

  # --- Block G: walk-up apartments, the same lane, west of the avenue --------
  # Block F runs to the avenue's east kerb and had no room left, so "adjacent"
  # is the next block along the same street rather than the next lot. Which is
  # also how a real neighbourhood grades: houses at one end, walk-ups where the
  # lane meets the through road.
  dict(name='G', origin=(AVENUE_W, STREET3_FAR, 0.0), yaw=180.0,
       abuts_low=False, abuts_high=False, lots=[
     dict(kind='gen', style='walkup', name='Alder',  x0=0.0,    width=1330.0,
          depth=BLOCK_F_DEPTH, floors=2, gf_h=250.0, fl_h=225.0, parapet=44.0,
          bays=4, wall='MI_precast_buff', seed=131),
     dict(kind='gen', style='walkup', name='Rowan',  x0=1330.0, width=1420.0,
          depth=BLOCK_F_DEPTH, floors=2, gf_h=258.0, fl_h=232.0, parapet=40.0,
          bays=4, wall='MI_card_ochre', seed=149),
     dict(kind='gen', style='walkup', name='Hazel',  x0=2750.0, width=1350.0,
          depth=BLOCK_F_DEPTH, floors=2, gf_h=246.0, fl_h=228.0, parapet=46.0,
          bays=4, wall='MI_precast_grey', seed=167),
  ]),
]
