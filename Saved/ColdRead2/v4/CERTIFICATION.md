# v4 set — certified for the reader (design session, 2026-08-30)

Certified frames: **tell_judge, tell_show, b70_mid_judge, street_judge**
(+ board_check as verification, not a read frame). b70_wide and
b70_near are UNREVIEWED ALTERNATES — not certified, stated rather than
implied.

## The room-change record (conditions of certification, wording binding)

1. **The board change is MEASURABLE AT ~132x THE NOISE FLOOR, BELOW THE
   THRESHOLD TWO SETS OF EYES COULD DETECT SIDE BY SIDE.** (Facade band
   28.8 dB against the pre-room baseline; unchanged-scene noise floor
   ~50 dB by the stated settle criterion; independent eyes on the
   side-by-side and on board_check found no difference a reader could
   call.) NOT "sub-visible" — the instrument saw a great deal; the eyes
   could not. Different claims; only the second is true.
2. **The mechanism is OCCLUSION, not emission.** M_StudioWall is unlit
   with use_emissive_for_dynamic_area_lighting=False - it CANNOT emit
   onto the board, and that closes the fill-light contamination class
   permanently. But opaque walls wrapped around a model OCCLUDE the
   SkyLight: less ambient reaches the board. Both facts are true
   together; the 28.8 dB is the occlusion, not a leak. A room around a
   model changes its light because rooms do.
3. **The tell is measured IN JUDGE ONLY.** In tell_show the water-tower
   lattice is sharpest and the coping run is soft — the physics floor of
   f/2.8 on the 400 back at 860 uu, behaving as measured. Show mode is
   STRUCTURALLY INCAPABLE of answering the surface question at zoom
   range; a reader's silence about surfaces in show mode is NOT a
   surface pass. Judge-first ordering is what makes the read valid.

## Apparatus check (resolved)

Inside the room footprint: ST 19, LAMP 10, HERO 3, BLOCK 1, LENSRIG 1.
ACCEPT / SHELF / STUDY / SWATCH / DONOR-shelf all OUTSIDE — gate
instruments unaffected by the room. The LENSRIG actor is **LENSRIG_P0,
the owner's flyable boom pawn** — deliberate, owner-approved, saved
state (not the stray removed from Stage2_Block, which was a copy). It
has NO mesh (its camera component spawns at BeginPlay) and renders
nothing in game-view captures; confirmed absent from every reviewed
frame. It stays.

## Focus calibration note (carried from the shoot record)

tell_show focus: subject at 860 uu, SETTING 1250 — the DOF focal-
distance setting is not the euclidean subject distance at close range
(sweep-measured ratio ~1.45 at this pose; ~1.0 at 3897). Calibrate by
sweep per pose until the mechanism is found.
