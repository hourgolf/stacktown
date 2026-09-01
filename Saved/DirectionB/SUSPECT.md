# Suspect capture evidence — the second darkness incident

The `SUSPECT_*.png` frames in this directory are KEPT AS RECORD and must not be
cited as evidence of how anything looks. They are the receipt for an incident,
which is a different kind of evidence from the one they were shot to be.

## What happened

Fourteen frames captured 2026-08-31 at 17:39 and 17:57 measure, by strided
Rec.709 sample:

| frames | mean | crushed to black |
|---|---|---|
| `SUSPECT_wood_on_FLAGSHIP_massing_blockhero_0..3`  | 37.5–37.7 | **54.3%** |
| `SUSPECT_wood_on_FLAGSHIP_massing_playerzoom_0..3` | 40.6–42.1 | **42.4%** |
| `SUSPECT_DIRECTIONB_massing_blockhero_0..2`        | 35.6      | **58.2%** |
| `SUSPECT_DIRECTIONB_massing_playerzoom_0..2`       | 41.9      | **50.0%** |

Between 42% and 58% of every one of those frames was black.

## Cause — and it is not the f/22 leak

This predates the `LOOK_Post` f/22 incident by two and a half hours and has a
separate cause: `wood_massing.py` and `wood_on_buildings.py` both staged their
subjects at `y = 60000`, which is **outside `CITY_Room`** (x ±37536, y ±34116).
The subjects were photographed in a black void with no floor, no walls and no
bounce.

That is `AGENTS.md` founding failure 5 verbatim — "Everything was captured in a
black void, which reads as a render. A model photographed in a lit room reads
as a model" — recurring in a lane that had already fixed it once, in
`wood_board.py`, and left unfixed in these two scripts.

## Why the record is kept

The owner said "I can't see anything" **twice**, and both times it was read as
a note about the material and the look. It was neither. It was a measurable
fact about the frame: half the pixels were at zero. These frames are the proof
that the observation was literally true and that it was misread, which is worth
more than the pictures ever were.

Standing doctrine this supports: when the owner reports an observation, treat it
as ground truth about the frame before treating it as a judgment about the work.

## Replacement

Both scripts now stage at `y = 20000`, on the lit floor inside `CITY_Room`, and
were re-shot to the original filenames. `Tools/measure/ue.py` additionally
refuses any capture whose lens state is undeclared and off the gate condition,
which closes the *other* darkness route.

Note both subjects are superseded approaches — flagship forms re-skinned in
timber, and `massing_only`, which subtracted the fill rather than the void.
Their value is historical: they are the evidence behind the decision to write
`build_mass`. Judge current direction-B look on the baked set (`SETB_*`).
