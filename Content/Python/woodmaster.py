#!/usr/bin/env python3
"""Which master direction B is allowed to edit. One place, by construction.

Owner, 2026-09-02: "nothing we're doing in this direction B wood city should
be affecting the flagship models or the teams handling the flagship project
for now. these are separate projects with different yet similar looks. The
wood city is an easier to render and scale version that we can then hopefully
borrow some mechanics for flagship down the road."

This lane argued AGAINST forking - 195 expressions duplicated, and the grain,
paper and seam work forked with them - and was overruled on a principle that
outranks the argument: the twin is a SEPARATE PROJECT, not a skin. Recorded
rather than quietly complied with, because the reasoning matters if anyone
later wonders why two masters exist.

SHARED is named here only so that scripts can ASSERT THEY ARE NOT TOUCHING
IT. Nothing in direction B may write to it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wood_board as wb  # noqa: E402

MATD = wb.MATD
SHARED = wb.MASTER                                  # the flagship's. read-only.
FORK = '%s/M_WoodMaster.M_WoodMaster' % MATD        # direction B's own
TARGET = FORK                                       # everything wear writes to

# The instances direction B owns outright. Deliberately NOT including the
# MI_board_* / MI_model_board family: those dress the studio and the plate,
# and whether the flagship also renders them is a REFERENCER QUESTION, not an
# assumption. fork.py --plan answers it before anything is re-parented.
WOOD_MIS = tuple('%s/MI_wood_%s.MI_wood_%s' % (MATD, s, s) for s in
                 ('maple', 'pine', 'ash', 'oak', 'cherry', 'sapele', 'walnut'))
CANDIDATE_SHARED = ('MI_board_plot', 'MI_board_road', 'MI_model_board',
                    'MI_studio_grey')


def assert_not_shared(path):
    """Refuse any write aimed at the flagship's master. Called by wear.py."""
    if path.split('.')[0] == SHARED.split('.')[0]:
        raise AssertionError(
            'direction B may not edit the shared master (%s). The owner put '
            'the flagship out of this lane on 2026-09-02; use FORK.' % SHARED)
