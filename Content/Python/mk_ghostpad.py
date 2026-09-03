#!/usr/bin/env python3
"""D22's ghost pad: five slabs with a raised rim, one per catalogue width.

    python3 Content/Python/mk_ghostpad.py            bake all five
    python3 Content/Python/mk_ghostpad.py --dry      print the boxes, no editor

The driver SELECTS by width; it must not scale. A 60 uu rim baked at 820 and
scaled to 2460 is 180 uu on the left and right edges and still 60 front and
back - two rim widths on one rectangle, which reads as a mistake rather than a
style. That is the whole reason there are five assets and not one.

GEOMETRY, NOT A MATERIAL BORDER. D22's rejections: a material border draws a
band of different COLOUR on a flat surface, which is another flat wash, and a
flat wash is what the coordinator's far-stop capture already showed does not
read; fresnel needs viewing-angle variation a flat pad at a fixed 25-degree
boom tilt does not have. A raised lip is a real surface at a different angle
to the key, so it returns a different LUMINANCE - that is what survives
downsampling.

THE RIM IS 12 uu, NOT D22's ORIGINAL 6. Worked from study_pose.json (fov
73.74) across the boom's reach ladder at the 2802 px capture width: 6 uu is
0.6 px at the survey stop and 14 px at the closest, and NO single height
serves a 24:1 zoom range. The survey stop is the wrong target - nobody places
a building from the survey view - so this is sized for the working stops:
12 uu reads 6 px at reach 3500, 17 px at 1350, 28 px at 800. The survey stop
keeps the driver's constant-screen-width debug outline, which is the right
tool for it.

Pivot front-left at ground, the catalogue's convention, so these drop straight
into the placement offsets the driver already applies. The chamfer is 4, NOT
the catalogue's 14 - see the constant for why, and it is a defect the dry run
caught rather than a capture.
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path        # noqa: F401,E402
import genbuild     # noqa: E402
import woodmap      # noqa: E402

OUT = '/Game/Stacktown/BakedWood'
RUNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Tools', 'rung.sh')
TMP = tempfile.gettempdir()

WIDTHS = (820, 1230, 1640, 2050, 2460)   # woodmap's 410 quanta
DEPTH = 1500.0        # BLOCK_DEPTH - the ghost shows the LOT, never varies
SLAB_TOP = 30.0       # slab top face above the plate
RIM_TOP = 42.0        # 12 uu proud of the slab
RIM_W = 60.0          # rim width in plan
# NOT the catalogue's 14. The rim stands 12 uu proud of the slab, and
# fastbake would bevel it at min(14, 0.35 * 42) = 14 - LARGER THAN THE STEP
# IT SITS ON, rounding the rim away completely and leaving a slab with a
# soft bulge. Caught in the dry run, which is the whole reason for having
# one: a 14 here would have been discovered as "the rim does not read" in a
# capture, and blamed on the 12 uu height rather than on the chamfer eating
# it. 4.0 is fastbake's own CHAMFER_DEFAULT, the card-edge value, and leaves
# 4 uu of flat vertical face plus two bevel faces on a 12 uu step.
#
# It is also right for the subject: a ghost is a piece that has NOT been
# carved yet, so a crisp arris is more honest here than the catalogue's
# hand-worked edge.
CHAMFER = 4.0
GHOST_MI = 'MI_ghost_accept'


def boxes_for(width):
    """A slab with a rim around it, pivot at the front-left corner (0,0,0).

    Four rim bars rather than a hollow frame: box() emits axis-aligned cubes
    and a frame is not one. The bars overlap at the corners, which costs four
    hidden cubes and buys a rim that is exactly RIM_W on every side - the
    thing the whole declaration turns on.
    """
    W, D = float(width), DEPTH
    a = genbuild.mkactor('GHOSTPAD_%d' % width, (0.0, 0.0, 0.0))
    # NAMES MUST CARRY A ROLE PREFIX. fastbake binds each box through
    # rolemap.material_for, and an unrecognised name returns None, which the
    # bake counts as "unbound" and skips - five skipped boxes produce
    # "fastbake: nothing to build", which is what plain 'Slab' and 'Rim_*'
    # got. 'Wall_' is the role that takes the job's `wall` material, the same
    # prefix build_mass uses for its own plinth.
    genbuild.box(a, 'Wall_Slab', 0.0, W, 0.0, D, 0.0, SLAB_TOP)
    genbuild.box(a, 'Wall_RimFront', 0.0, W, 0.0, RIM_W, 0.0, RIM_TOP)
    genbuild.box(a, 'Wall_RimBack', 0.0, W, D - RIM_W, D, 0.0, RIM_TOP)
    genbuild.box(a, 'Wall_RimLeft', 0.0, RIM_W, 0.0, D, 0.0, RIM_TOP)
    genbuild.box(a, 'Wall_RimRight', W - RIM_W, W, 0.0, D, 0.0, RIM_TOP)
    return a


def build(width, dry=False):
    name = 'SM_GhostPad_w%d' % width
    genbuild.record()
    with contextlib.redirect_stdout(io.StringIO()):
        boxes_for(width)
    rec = genbuild.drain()
    if dry:
        print('%s  %d boxes' % (name, sum(1 for r in rec if r['kind'] == 'box')))
        for r in rec:
            if r['kind'] == 'box':
                print('    %-10s c=%-28s d=%s' % (r['name'], r['c'], r['d']))
        return None
    job = {'boxes': rec, 'out': '%s/%s' % (OUT, name),
           'wall': GHOST_MI, 'roofmat': GHOST_MI, 'trim': GHOST_MI,
           'panel_overrides': {}, 'chamfer': CHAMFER}
    json.dump(job, open(os.path.join(TMP, 'stacktown_fastbake_job.json'), 'w'))
    r = subprocess.run([RUNG, 'fastbake.py'], capture_output=True, text=True,
                       cwd=HERE)
    ok = [l for l in (r.stdout or '').splitlines() if 'FASTBAKED' in l]
    if not ok:
        raise SystemExit('%s: bake produced no FASTBAKED line\n%s'
                         % (name, (r.stdout or '')[-600:]))
    print('  ' + ok[0].strip())
    return name


def main():
    dry = '--dry' in sys.argv
    made = []
    for w in WIDTHS:
        got = build(w, dry=dry)
        if got:
            made.append(got)
    if dry:
        print('\n--dry: nothing baked. %d widths, %d boxes each.'
              % (len(WIDTHS), 5))
        return
    print('BAKED %d ghost pads.' % len(made))
    print('The driver SELECTS by width and must not scale - see the docstring.')
    print('Acceptance is a MEASURED FRAME at the working stop and the closest '
          'stop, accept and refuse. A ghost that is not see-through is not a '
          'ghost, and a rim that reads as a kerb is not a rim.')


if __name__ == '__main__':
    main()
