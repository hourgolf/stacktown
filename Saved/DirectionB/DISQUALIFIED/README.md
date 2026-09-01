# Disqualified capture evidence

Frames here are KEPT AS RECORD and must not be cited as evidence of how
anything looks. They are not deleted: a disqualified frame is still the proof
of how it failed.

## DOF_lensoff_0/1/2.png — disqualified 2026-08-31

Captured 20:17:07-13 as the "no lens" control for the depth-of-field contact
sheet, and shown to the owner as one.

Measured: **image mean 8.2-8.3, with 22.6-23.1% of pixels crushed to black**
(strided Rec.709 sample). Its three companion conditions in the same sheet
measure 145.2-145.5. The control was therefore about five stops darker than
the conditions it existed to be compared against, so any difference a reader
saw between them was dominated by brightness, not focus.

Cause: `LOOK_Post` runs `AEM_Manual` with
`autoExposureApplyPhysicalCameraExposure` true, so `depthOfFieldFstop` drives
EXPOSURE as well as defocus. The lens-off condition was expressed as f/22,
which is not "no lens" - it is "no lens, five stops down". The 36/150/400 mm
ladder held exposure constant correctly (145.4 / 145.4 / 145.6, matched to
0.2) and remains valid; only this control broke the rule.

Consequence beyond these three frames: f/22 was left as the volume's resting
state by the run's end-of-run restore, so every capture taken afterwards was
underexposed until it was found and repaired the same day. A baked set
measured image mean 8.0 where its own reference framing measured 102.4.

A valid lens-off control still needs shooting: same framing, deep focus, ISO
paid against the aperture so only focus varies. `Tools/measure/dof.py`
documents that arithmetic, and its own comments had warned about this exact
trap - "a brightness ladder wearing a depth-of-field label".

Enforcement now exists in code rather than in comments:
`Tools/measure/ue.py` refuses any `CaptureViewport` whose lens state is
neither the gate condition (f/4, ISO 800, 1/60) nor explicitly declared via
`ue.declare_lens()`. Proven by planted defect - undeclared f/22 is refused
with the stop error named.

See also `../SUSPECT.md`, a separate and earlier darkness incident.
