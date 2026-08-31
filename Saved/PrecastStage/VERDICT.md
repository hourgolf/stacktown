# Precast confirmation — owner verdict, 2026-08-30

**"Reads as cast panel, proceed."**

Given on the staged frames in this directory: Foundry and Depot north
elevations, judge mode (f/4, ISO 800, DOF off, 70 mm gate optic), plus
one show frame each at the locked lens (f/2.8, 400 mm back, ISO derived
from dof.HERO) and one labelled wide reference (depot_REF_wide40 — NOT a
gate framing; the Depot cannot fit the 70 mm optic from the yard's
~4,434 uu maximum standoff).

The question these frames existed to answer: does plaster_cast read as
cast precast panel, or as painted card? Answered: CAST PANEL.

What this unlocks: WORKS-BRICK may now proceed — this confirmation was
sequenced before it because works-brick destroys the only precast walls
available to judge. Sequence of record continues: owner commit word →
full 548 wave (re-seeds regression baselines) → works-brick → read #2.

Open question surfaced during staging — CORRECTED 2026-08-30 by the
design session's per-mesh measurement: the coordinator's "Depot cannot
fit the 70 mm optic" was INVERTED. The 3,604 width came from
get_actor_bounds, which is inflated (the Depot's actor bounds reach the
Foundry's edge). True mesh spans: Foundry 1,852 / Depot 1,552. Against
the real northern limit (STAGE_Backdrop at y=8672, standoff cap ~4,506):
the DEPOT FITS the gate optic comfortably; the Foundry's roofline fits;
the Foundry WITH ITS STACK does not (needs ~7,494). The open framing-
doctrine question for the owner is therefore about the FOUNDRY'S STACK
only. Also corrected: there are no buildings north of the yard — the
model board ends at y=4510 and the next thing north is the backdrop;
the coordinator's early "camera inside a building" frames were the
backdrop, not a building line. Same disease both times: a convenient
accessor (actor bounds; an inferred obstruction) returning something
plausible and wrong.
