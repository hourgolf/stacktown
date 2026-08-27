"""A key/fill rig sized and aimed for a BLOCK, not a building. Sandbox only.

`Docs/ONE_BUILDING_GATE.md` Stage 2, carried forward unchanged:

    Light intensity scales with the inverse square of rig distance.
    Re-derive it; do not reuse Stage 1 numbers at a block rig distance.

So this derives rather than guesses. The board rig is measured on disk - key
950,000 lm standing 5,595 uu off the board, fill 520,000 lm at 4,301 uu - and
the block values are those scaled by (new distance / old distance)^2. The
emitters scale linearly with the same ratio, because a softbox that lights one
building edge-to-edge is a hard little source at fifteen thousand.

It is ADDITIVE. The board rig is untouched: STAGE_Key and STAGE_Fill keep
lighting the board and the shelf, and these two only reach the street.

Both are MOVABLE. Two lights with a radius that covers a whole block would
otherwise sit in UE's 4-per-pixel stationary overlap budget for every pixel
they touch, which is the thing that had 19 overlapping stationary pairs in
this level before.

  reads: stacktown_blockrig.json {x0,y0,x1,y1,z1, rig_dist, clear}
"""
import unreal
import _path  # noqa: F401
import json
import math
import os
import tempfile

# Sandbox_Bench built these first; Stage2_Street is now their own room
# (streetroom.py). Both are allowed: the bench copy stays usable until
# the owner confirms the new map, which was their explicit instruction.
SANDBOX = ('Sandbox_Bench', 'Stage2_Street')
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not any(k in eus.get_editor_world().get_path_name() for k in SANDBOX):
    raise SystemExit('blockrig.py runs only in %s' % ', '.join(SANDBOX))

# the board rig, MEASURED - the reference the inverse square is taken from
RIG_DIST_DEFAULT = 14000.0   # streetroom.py sizes the room from this

REF = {'key': (950000.0, 5595.0, 2600.0, 1700.0, 4500.0),
       'fill': (520000.0, 4301.0, 4000.0, 2600.0, 7200.0)}

job = json.load(open(os.path.join(tempfile.gettempdir(),
                                  'stacktown_blockrig.json')))
if job.get('clear'):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith('BLOCK_'):
            eas.destroy_actor(a)
            n += 1
    print('blockrig: cleared %d' % n)
    raise SystemExit(0)

cx = (float(job['x0']) + float(job['x1'])) / 2.0
cy = (float(job['y0']) + float(job['y1'])) / 2.0
cz = float(job.get('z1', 2000.0)) * 0.42
RD = float(job.get('rig_dist', RIG_DIST_DEFAULT))
REACH = math.hypot(float(job['x1']) - float(job['x0']),
                   float(job['y1']) - float(job['y0'])) / 2.0 + 900.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('BLOCK_'):
        eas.destroy_actor(a)


def aim(loc, target):
    """Yaw/pitch that points a light's forward (+X) at `target`."""
    dx, dy, dz = (target[i] - loc[i] for i in range(3))
    d = math.hypot(dx, dy)
    return (math.degrees(math.atan2(dz, d)),          # pitch
            math.degrees(math.atan2(dy, dx)))         # yaw


def put(name, which, az_deg, elev_deg):
    base_i, base_d, base_w, base_h, temp = REF[which]
    ratio = RD / base_d
    inten = base_i * ratio * ratio                    # inverse square
    w, h = base_w * ratio, base_h * ratio             # emitter scales linearly
    az, el = math.radians(az_deg), math.radians(elev_deg)
    horiz = RD * math.cos(el)
    loc = (cx + horiz * math.cos(az), cy + horiz * math.sin(az),
           cz + RD * math.sin(el))
    pitch, yaw = aim(loc, (cx, cy, cz))
    a = eas.spawn_actor_from_class(unreal.RectLight,
                                   unreal.Vector(*loc),
                                   unreal.Rotator(0.0, pitch, yaw))
    a.set_actor_label('BLOCK_%s' % name)
    for c in a.get_components_by_class(unreal.RectLightComponent):
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
        c.set_editor_property('intensity', inten)
        c.set_editor_property('source_width', w)
        c.set_editor_property('source_height', h)
        # ONLY AS FAR AS THE SUBJECT. RD * 2.6 was 36,400 uu, which reached
        # the shelf's near corner 21,000 away - a block rig quietly relighting
        # the review bench is exactly the kind of side effect that makes two
        # captures incomparable later. Sized to the rig distance plus the
        # subject's own half-diagonal, and no further.
        # In a dedicated street map there is no review bench to protect, so
        # the rig can reach the whole room. In Sandbox_Bench it must not:
        # RD*2.6 = 36,400 uu reached the shelf's near corner 21,000 away, and
        # a block rig quietly relighting the review surface makes two captures
        # incomparable. Keyed on the LEVEL because that is the actual fact
        # that decides it.
        _room = 'Stage2_Street' in unreal.get_editor_subsystem(
            unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
        c.set_editor_property('attenuation_radius',
                              RD * 2.6 if _room else RD + REACH)
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', temp)
        c.set_editor_property('cast_shadows', which == 'key')
        got = c.get_editor_property('intensity')
        assert abs(got - inten) < 1.0, '%s intensity did not take' % name
    print('  BLOCK_%-5s  %10.0f lm  emitter %.0f x %.0f  %.0fK  at (%.0f,%.0f,%.0f)'
          % (name, inten, w, h, temp, loc[0], loc[1], loc[2]))
    print('             ratio %.2f from a %.0f uu reference rig, squared = %.2f'
          % (ratio, base_d, ratio * ratio))


# key from the south-west and high; fill opposite, lower and cooler, so the
# canyon gets light down BOTH elevations instead of one lit side and one black
put('Key', 'key', -128.0, 34.0)
put('Fill', 'fill', 52.0, 16.0)
les.save_current_level()
print('blockrig: rig distance %.0f uu, centred on (%.0f, %.0f, %.0f)'
      % (RD, cx, cy, cz))
