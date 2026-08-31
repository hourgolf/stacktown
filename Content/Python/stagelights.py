"""Set the stage key and fill. Reads /tmp/stacktown_keyfill.json.

The two softboxes were fully authored - a 2600x1700 key at 4500 K from the
upper left with barn doors, a 4000x2600 fill at 7200 K opposite - and both
sat at intensity 0.0, so the model was lit by sun and sky alone.

They are also set MOVABLE here. Two stationary lights with a 26,000 uu radius
cover every pixel of the stage and count against UE's 4-overlap stationary
budget whether or not they emit anything; there were 19 overlapping stationary
pairs. Movable lights do not take part in that budget.

Intensity is linear in the render before the tonemapper saturates, so the
right way to pick a number is to measure one and scale, not to guess twice.
That is how KEY/FILL below were arrived at:

  50,000 / 20,000   ->  +1.007 mean on the board  (calibration probe)
  600,000 / 240,000 ->  +14.2% mean, +5.8% sd
  950,000 / 520,000 ->  +23.8% mean, +7.8% sd, 0.000% clipped   <- chosen

The numbers look enormous because a 2600 x 1700 emitter at ~4,000 uu is a
26-metre softbox forty metres away in this unit system.

AIM THEM AT SOMETHING. LIGHT_Key is at (-2430,-2970) pointing yaw 45, i.e. at
the MODEL BOARD at (550,-100). sheet_stage.py parks models at (-12000,-2640),
behind the light and outside its barn doors - turning the key on moved a
sheet-stage frame by -0.5 of a mean, which reads exactly like "the lights do
nothing". Use boardstage.py to judge stage lighting.

MOBILITY IS NOT A FLICKER FIX, though it was offered as one. Measured on one
camera with intensity held constant: MOVABLE gave a 12-frame spread of 0.130,
STATIONARY gave 0.046 - both non-monotonic noise. What mobility DOES do is
take these two 26,000 uu lights out of UE's 4-per-pixel stationary overlap
budget: overlapping stationary pairs in this level went 19 -> 8.
"""
import unreal
import _path  # noqa: F401
import json
import os
import tempfile

# the tuned stage values, used when no job file is present
KEY, FILL = 950000.0, 520000.0

JOB = os.path.join(tempfile.gettempdir(), 'stacktown_keyfill.json')
job = (json.load(open(JOB)) if os.path.exists(JOB)
       else {'key': KEY, 'fill': FILL, 'movable': True})
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

WANT = {'LIGHT_Key': float(job['key']), 'LIGHT_Fill': float(job['fill'])}
# explicit either way, so a control run can put them back to STATIONARY and
# isolate mobility from intensity
MOVABLE = bool(job.get('movable', True))
MOB = unreal.ComponentMobility.MOVABLE if MOVABLE \
    else unreal.ComponentMobility.STATIONARY
done = 0
for a in eas.get_all_level_actors():
    L = a.get_actor_label()
    if L not in WANT:
        continue
    for c in a.get_components_by_class(unreal.RectLightComponent):
        c.set_mobility(MOB)
        c.set_editor_property('intensity', WANT[L])
        got = c.get_editor_property('intensity')
        mob = str(c.get_editor_property('mobility')).split('.')[-1]
        # read back: setting mobility on a stationary light can be refused
        ok = abs(got - WANT[L]) < 0.5
        print('  %-11s intensity -> %9.1f (read %9.1f) %s  mobility %s'
              % (L, WANT[L], got, 'ok' if ok else '*** NOT APPLIED ***', mob))
        if not ok:
            raise AssertionError('%s did not take the intensity it was given'
                                 % L)
        done += 1
if done != len(WANT):
    raise AssertionError('expected %d lights, set %d' % (len(WANT), done))
les.save_current_level()
print('stagelights: %d set' % done)
