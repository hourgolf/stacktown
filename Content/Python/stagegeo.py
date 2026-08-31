"""Where the stage's surfaces are. Pure constants, no side effects.

These were only in stage.py, inside the executable part, so anything that
wanted to put an object on the floor had to hard-code a number or guess one.
Both the shelf and the donor sheet guessed z=0 - which is the BOARD's top, not
the floor's - and every model laid out past the edge of the board hung 128 uu
in the air. The buildings were correct; the thing placing them was not.

  z = 0        top of STAGE_ModelBoard (the model board slab, -80..0)
  z = -128     top of STAGE_Ground (the room floor the board sits on)

An object belongs on the board if it is inside BOARD_X/BOARD_Y, and on the
room floor otherwise. `floor_z_at` answers that so nobody has to remember it.
"""
BOARD_TOP_Z = 0.0
FLOOR_Z = -128.0

# STAGE_ModelBoard as stage.py builds it: centre (550, -100), 2900 x 2400
BOARD_X = (-900.0, 2000.0)
BOARD_Y = (-1300.0, 1100.0)


def on_board(x, y):
    return BOARD_X[0] <= x <= BOARD_X[1] and BOARD_Y[0] <= y <= BOARD_Y[1]


def floor_z_at(x, y):
    """The z an object's BASE should sit at to rest on whatever is beneath."""
    return BOARD_TOP_Z if on_board(x, y) else FLOOR_Z


def _selftest():
    assert floor_z_at(600.0, -100.0) == BOARD_TOP_Z, 'board centre is the board'
    assert floor_z_at(5000.0, 0.0) == FLOOR_Z, 'past the board is the floor'
    assert floor_z_at(-4000.0, -1200.0) == FLOOR_Z, 'donor grid is the floor'
    # the board sits ON the floor, never in it
    assert BOARD_TOP_Z > FLOOR_Z


_selftest()
