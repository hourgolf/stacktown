"""The test city's rig: DERIVED from the board rig, and a room, not a sky.

RUN THROUGH rung.sh - it mutates. TestCity only. Idempotent.

THE DERIVATION, not a choice. blockrig.py's rule carried forward unchanged:
intensity scales with the INVERSE SQUARE of rig distance and the emitter
scales LINEARLY, from the measured board rig

    key   950,000 lm at 5,595 uu, emitter 2600 x 1700, 4500 K (warm)
    fill  520,000 lm at 4,301 uu, emitter 4000 x 2600, 7200 K (cool)

Rig distance is derived too, from the same reference: the board rig stood at
2.97x its subject's half-diagonal, so this one does the same at the city's.
Scaling by inverse square is what keeps the ILLUMINANCE AT THE SUBJECT equal
to the reference, which is why the judge exposure does not need retuning.

THIS IS A TRANSPLANT, NOT A NEW DESIGN. The Sandbox street is the thing a
cold reader passed on 2026-08-30, so it - not first principles - is the
standard a near-final test city is measured against. Every element of that
rig comes across: key and fill scaled by the documented inverse square, and
the sun, sky and atmosphere copied unchanged because they are not
distance-dependent.

AN EARLIER VERSION OF THIS FILE OMITTED THE SUN AND SKY on my own argument
that a model in a room has neither, and that a parallel source cannot produce
the falloff or the shadow character read #2 found missing. That argument may
well be right - it is the first hypothesis on the record's list - but it was
UNTESTED, and building the test city on it would have shipped my hypothesis
as the product. It stays a hypothesis, to be settled by the lighting
investigation on a rig that matches the one that passed.

The room is here for the same doctrine - "a model in a black void is a
render, a model in a lit room is a model" - and because a rig with nothing to
bounce off is only half a rig.
"""
import json
import math
import os
import tempfile

import unreal

# THE DERIVATION OVER-DELIVERS AND THE SWEEP SETTLES IT. Inverse-square
# preserves illuminance for a POINT source; scaling the emitter linearly (the
# precedent's rule, which keeps angular size constant) makes the source
# 0.46-0.93x the rig distance, and an area source that large no longer obeys
# the point formula. Measured: 99.9% blown at scale 1.0 against 0.0% on the
# known-good v4 frames. SCALE is the measured correction, swept not guessed.
# SCALE IS 1.0 - THE DERIVATION IS CORRECT AND NEEDS NO FUDGE.
# For most of this session it sat at 0.0040, a number I swept and described
# as "measured". It was not measuring the rig; it was compensating for
# AUTO-EXPOSURE. A fresh PostProcessVolume meters automatically, so lensrig's
# shutter/ISO/aperture did nothing and the scene re-adapted to whatever was in
# frame - every light value I swept was cancelled by the metering chasing it.
# That is why the sun had to fall to 3 lux and the key to 1/250 to "look
# right", and why nothing transplanted.
# With LOOK_Post in MANUAL metering the transplanted values land in family
# with the frames a cold reader passed, on the first try and with no sweep:
#     street   74.9 / 59.7 / 0.0% blown   against the passing 62.3 / 44.4
#     oblique 122.7 / 49.8 / 0.0%         against the passing 107.8 / 58.3
SCALE = 1.0
_job = os.path.join(tempfile.gettempdir(), 'stacktown_citylight.json')
if os.path.exists(_job):
    _j = json.load(open(_job))
    SCALE = float(_j.get('scale', 1.0))
    OUTDOOR = _j.get('outdoor', 'full')
    SUN_LUX = float(_j.get('sun_lux', 430.0))
else:
    OUTDOOR = 'full'
    SUN_LUX = 430.0

eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if 'TestCity' not in eus.get_editor_world().get_path_name():
    raise SystemExit('citylight.py runs only in TestCity')

# the board rig, MEASURED - the reference the inverse square is taken from.
# (intensity lm, distance uu, emitter w, emitter h, temperature K)
REF = {'key': (950000.0, 5595.0, 2600.0, 1700.0, 4500.0),
       'fill': (520000.0, 4301.0, 4000.0, 2600.0, 7200.0)}
REF_BOARD_HALF_DIAG = 1882.0        # STAGE_ModelBoard 2900 x 2400
REF_KEY_DIST = REF['key'][1]
DIST_PER_HALF_DIAG = REF_KEY_DIST / REF_BOARD_HALF_DIAG      # 2.973

# MEASURED for THIS room, not inherited. M_StudioWall's default
# brightness was tuned for the Sandbox studio room; in a room this much
# larger the wall fills the street framing and blows it out. Swept on
# that framing: 60 -> 35.0% blown, 20 -> 30.1%, 8 -> 0.0%, 3 -> 0.0%.
# Wall brightness has to be derived per room the same way intensity is.
SKY_CUBE = '/Engine/EngineResources/GrayLightTextureCube.GrayLightTextureCube'
SKY_I = 12.0                # the bench knee: crush 1.38%, falloff held
WALL = '/Game/Stacktown/Materials/MI_studio_wall_city.MI_studio_wall_city'
# the FLOOR is LIT, not self-lit. The walls are self-lit so they can
# never spill onto the board; the floor is the surface the model stands
# near, and a lit floor is what produces CONTACT SHADOW where things
# touch - fifth in the studio-director's list of what reads as physical.
# Self-lit, it also blew out: 10% blown oblique, 25% street.
FLOOR = '/Game/Stacktown/Materials/MI_studio_grey.MI_studio_grey'
CUBE = '/Engine/BasicShapes/Cube.Cube'
OWNED = ('CITY_Key', 'CITY_Fill', 'CITY_StreetKey', 'CITY_Room', 'CITY_Sun',
         'CITY_Sky',
         'CITY_Atmosphere', 'LOOK_Post', 'TC_PROVISIONAL')

# ANGLES ARE MEASURED FROM THE BOARD RIG TOO, not invented. The first
# version claimed to keep "the board rig's own relationship" and then used
# 225/45 - key and fill OPPOSED at 180 degrees, which is a different lighting
# design wearing the lineage's numbers. The board rig on disk is
#     LIGHT_Key   pitch -35.0  yaw  45.0
#     LIGHT_Fill  pitch  -5.4  yaw 135.0
# 90 degrees apart, fill low and to the side. Measured warm cast of the
# invented version against the sandbox board frame: R-B +28.8 vs +8.4.
KEY_AZ, KEY_TILT = 45.0, -35.0
# THE FILL'S MEASURED TILT DOES NOT TRANSPLANT, and this is the one place the
# board rig's numbers had to be overruled rather than copied. -5.4 degrees is
# correct for a fill 4,301 uu from ONE building on a 2,900 x 2,400 board: at
# that angle it rakes in under the eaves. Carried onto a 15,300 x 8,460 board
# cut by 2,260 uu canyons it reaches NOTHING at ground level - the horizontal
# shadow reach at 5.4 degrees is height x 10.58, so a 300 uu parapet alone
# shadows 3,175 uu, more than the full corridor. The fill was lighting roofs
# and upper facades only.
# The replacement is derived from the same threshold the street keys use: to
# clear a facade at the 1,130 building line and still reach the far kerb at
# -700, a lamp on the 45-degree diagonal needs elevation E with
#     height x (1/tan E) x sin 45 < 1,830
# The catalogue's MEDIAN height across TestCity's lots is 1,232 uu, which
# needs E > 25.4 degrees. 30 degrees clears the median with margin and stays
# well below the key's 35 so the two still read as key and fill.
FILL_AZ, FILL_TILT = 135.0, -30.0


def _lamp(eas, label, az, tilt, dist, ref, aim):
    base_i, base_d, base_w, base_h, temp = ref
    ratio = dist / base_d
    inten = base_i * ratio * ratio * SCALE         # inverse square x sweep
    w, h = base_w * ratio, base_h * ratio          # emitter linear
    a = math.radians(az)
    loc = unreal.Vector(aim[0] + dist * math.cos(a),
                        aim[1] + dist * math.sin(a),
                        aim[2] + dist * math.tan(math.radians(-tilt)))
    dx, dy, dz = aim[0] - loc.x, aim[1] - loc.y, aim[2] - loc.z
    rot = unreal.Rotator(0.0,                                  # roll
                         math.degrees(math.atan2(dz, math.hypot(dx, dy))),
                         math.degrees(math.atan2(dy, dx)))
    act = eas.spawn_actor_from_class(unreal.RectLight, loc, rot)
    act.set_actor_label(label)
    for c in act.get_components_by_class(unreal.RectLightComponent):
        # MOVABLE on the COMPONENT, per blockrig - a radius this size would
        # otherwise sit in UE's 4-per-pixel stationary overlap budget for
        # every pixel it touches. Actor has no set_mobility.
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
        c.set_editor_property('intensity', inten)
        c.set_editor_property('source_width', w)
        c.set_editor_property('source_height', h)
        c.set_editor_property('attenuation_radius', dist * 2.6)
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', temp)
        got = c.get_editor_property('intensity')
        assert abs(got - inten) < 1.0, '%s intensity did not take' % label
    print('%-9s %10.0f lm at %8.0f uu  emitter %6.0f x %-6.0f %.0fK'
          ' (ratio %.3f, squared %.2f)'
          % (label, inten, dist, w, h, temp, ratio, ratio * ratio))
    return math.hypot(loc.x - aim[0], loc.y - aim[1])


# THE STREET KEY, measured on Sandbox_Bench 2026-08-31 and transplanted by
# the same rule as everything else in this file.
#
# WHY IT EXISTS. A single board-scale lamp cannot light a street canyon. The
# derivation puts CITY_Key 25,988 uu out on the 45-degree diagonal at 35
# degrees elevation; the corridors are 2,260 uu wide, so any facade over
# 1,812 uu shadows the whole carriageway - 33% of the catalogue options that
# fit TestCity's lots. The identical fault was MEASURED on the bench, where
# the key stood 9,147 uu outside a 2,096 uu canyon: the road carried no cast
# shadow anywhere and its brightness ran 0.71x near/far - DARKER toward the
# camera, which is backwards for any light with falloff.
# Moving that key above the canyon, behind the camera, raking along the
# street's length gave 3.3-3.9x (+1.7 to +2.0 stops) and sd 53.6 against the
# passing frame's 45.7, at matched exposure.
#
# THE REFERENCE, measured: 5,733,620 lm at 8,000 uu standoff, emitter
# 3,751 x 2,453, 4,500 K, 45 degrees elevation, aimed along the corridor from
# a point 9% into the run. Intensity by inverse square and emitter linearly,
# exactly as REF is used above.
STREET_REF = (5733620.0, 8000.0, 3751.0, 2453.0, 4500.0)
STREET_ELEV = 45.0
STREET_STANDOFF_PER_RUN = 8000.0 / 12777.0      # bench standoff / visible run
STREET_AIM_ALONG = 0.09                          # fraction into the run
STREET_AZ = (-0.99, -0.14)                       # back along, a touch to one side


def _street_key(eas, label, axis, lo, hi, cross_c, roof_clear):
    """One lamp ABOVE one corridor, raking along its length."""
    base_i, base_d, base_w, base_h, temp = STREET_REF
    run = hi - lo
    dist = run * STREET_STANDOFF_PER_RUN
    elev = STREET_ELEV
    # the lamp must clear the rooflines it is raking over, or it is occluded
    # by the near parapets exactly like the rig it replaces. Raise it until
    # it does rather than trusting 45 degrees to be tall enough.
    need = math.degrees(math.asin(min(0.985, roof_clear / dist))) if dist else elev
    if need > elev:
        print('   %s: 45 deg puts the lamp at %.0f uu, below the %.0f uu'
              ' roofline - raised to %.1f deg'
              % (label, dist * math.sin(math.radians(elev)), roof_clear, need))
        elev = need
    ce, se = math.cos(math.radians(elev)), math.sin(math.radians(elev))
    aim_along = lo + run * STREET_AIM_ALONG
    a_off, c_off, z = dist * ce * STREET_AZ[0], dist * ce * STREET_AZ[1], dist * se
    if axis == 'x':
        aim = (aim_along, cross_c, 0.0)
        loc = (aim[0] + a_off, aim[1] + c_off, z)
    else:
        aim = (cross_c, aim_along, 0.0)
        loc = (aim[0] + c_off, aim[1] + a_off, z)
    ratio = dist / base_d
    inten = base_i * ratio * ratio * SCALE
    w, h = base_w * ratio, base_h * ratio
    dx, dy, dz = aim[0] - loc[0], aim[1] - loc[1], aim[2] - loc[2]
    rot = unreal.Rotator(0.0,
                         math.degrees(math.atan2(dz, math.hypot(dx, dy))),
                         math.degrees(math.atan2(dy, dx)))
    act = eas.spawn_actor_from_class(unreal.RectLight,
                                     unreal.Vector(*loc), rot)
    act.set_actor_label(label)
    for c in act.get_components_by_class(unreal.RectLightComponent):
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
        c.set_editor_property('intensity', inten)
        c.set_editor_property('source_width', w)
        c.set_editor_property('source_height', h)
        c.set_editor_property('attenuation_radius', (run + dist) * 1.4)
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', temp)
    print('%-16s %10.0f lm at %8.0f uu, %.1f deg over the %s corridor'
          '  (z %.0f, emitter %.0f x %.0f)'
          % (label, inten, dist, elev, axis, loc[2], w, h))


def _rooflines(eas):
    """p90 of the placed buildings - what a street lamp has to clear."""
    tops = []
    for a in eas.get_all_level_actors():
        if not a.get_actor_label().startswith('TC_Bld'):
            continue
        o, e = a.get_actor_bounds(False)
        tops.append(o.z + e.z)
    if not tops:
        return None
    tops.sort()
    return tops[int(len(tops) * 0.9)]


def build():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cube = unreal.load_asset(CUBE)
    wall = unreal.load_asset(WALL)
    floor_mat = unreal.load_asset(FLOOR)

    board = [a for a in eas.get_all_level_actors()
             if a.get_actor_label() == 'TC_Board']
    if not board:
        raise SystemExit('no TC_Board - run mk_testcity.py first')
    o, e = board[0].get_actor_bounds(False)
    bx0, bx1 = o.x - e.x, o.x + e.x
    by0, by1 = o.y - e.y, o.y + e.y
    half_diag = math.hypot(bx1 - bx0, by1 - by0) / 2.0
    dist = half_diag * DIST_PER_HALF_DIAG

    killed = 0
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith(OWNED):
            eas.destroy_actor(a)
            killed += 1

    aim = ((bx0 + bx1) / 2.0, (by0 + by1) / 2.0, 600.0)
    print('board %.0f x %.0f, half-diagonal %.0f -> rig distance %.0f'
          ' (SCALE %.4f)' % (bx1 - bx0, by1 - by0, half_diag, dist, SCALE))
    print('cleared %d actor(s), including the provisional sun and sky' % killed)
    _lamp(eas, 'CITY_Key', KEY_AZ, KEY_TILT, dist, REF['key'], aim)
    _lamp(eas, 'CITY_Fill', FILL_AZ, FILL_TILT, dist, REF['fill'], aim)

    # A LAMP PER CORRIDOR. This is how a modelmaker lights a diorama - one
    # lamp per sightline - and it is O(streets), which for a two-street test
    # city is two lamps. It is NOT proposed as the answer at full city scale;
    # that question is open and belongs to the coordinator.
    roof = _rooflines(eas)
    if roof is None:
        print('no TC_Bld actors - street keys SKIPPED (run'
              ' mk_testcity_builds.py first)')
    else:
        print('placed rooflines p90 %.0f uu - street keys must clear it' % roof)
        clear = roof + 500.0
        _street_key(eas, 'CITY_StreetKey_A', 'x', bx0, bx1, 0.0, clear)
        _street_key(eas, 'CITY_StreetKey_C', 'y', by0, by1, 0.0, clear)

    # the room: walls only, self-lit M_StudioWall so they can never spill
    # light onto the board (the contamination class closed on 2026-08-30).
    m = dist * 1.15
    rx0, rx1, ry0, ry1 = bx0 - m, bx1 + m, by0 - m, by1 + m
    rz0, rz1, t = -300.0, dist * 0.9, 200.0
    zc, zs = (rz0 + rz1) / 2.0, (rz1 - rz0) / 100.0
    for nm, (cx, cy, sx, sy) in (
            ('N', ((rx0 + rx1) / 2.0, ry1, (rx1 - rx0) / 100.0, t / 100.0)),
            ('S', ((rx0 + rx1) / 2.0, ry0, (rx1 - rx0) / 100.0, t / 100.0)),
            ('E', (rx1, (ry0 + ry1) / 2.0, t / 100.0, (ry1 - ry0) / 100.0)),
            ('W', (rx0, (ry0 + ry1) / 2.0, t / 100.0, (ry1 - ry0) / 100.0))):
        a = eas.spawn_actor_from_object(cube, unreal.Vector(cx, cy, zc),
                                        unreal.Rotator(0, 0, 0))
        a.set_actor_label('CITY_Room_%s' % nm)
        a.set_actor_scale3d(unreal.Vector(sx, sy, zs))
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_material(0, wall)
    # A FLOOR. Walls alone are not a room: beyond the board there is nothing
    # to stand on, and any sightline that clears the board's edge falls into
    # void. That is the identical fault found and fixed in the Sandbox studio
    # room earlier the same day - and I rebuilt it here, which is why the
    # lesson is written down rather than remembered. It sits BELOW the board
    # so the board still reads as a raised object with an edge.
    fa = eas.spawn_actor_from_object(
        cube, unreal.Vector((rx0 + rx1) / 2.0, (ry0 + ry1) / 2.0, -500.0),
        unreal.Rotator(0, 0, 0))
    fa.set_actor_label('CITY_Room_Floor')
    fa.set_actor_scale3d(unreal.Vector((rx1 - rx0) / 100.0,
                                       (ry1 - ry0) / 100.0, 2.0))
    for c in fa.get_components_by_class(unreal.StaticMeshComponent):
        c.set_material(0, floor_mat)
    print('room x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f (4 walls + floor,'
          ' self-lit)' % (rx0, rx1, ry0, ry1, rz0, rz1))

    pv = eas.spawn_actor_from_class(unreal.PostProcessVolume,
                                    unreal.Vector(*aim), unreal.Rotator(0, 0, 0))
    pv.set_actor_label('LOOK_Post')
    pv.set_editor_property('unbound', True)
    # MANUAL METERING, and this is the whole reason the transplant would not
    # settle. lensrig sets shutter, ISO and aperture - but those drive
    # exposure ONLY in manual metering. A fresh PostProcessVolume defaults to
    # auto-exposure, so the camera settings were ignored and the scene
    # re-adapted to whatever was in frame. Every light value I swept was being
    # cancelled by the auto-exposure chasing it, which is why the sun had to
    # fall to 3 lux - 1/143 of the transplanted value - to look right.
    st = pv.get_editor_property('settings')
    st.set_editor_property('auto_exposure_method',
                           unreal.AutoExposureMethod.AEM_MANUAL)
    st.set_editor_property('override_auto_exposure_method', True)
    st.set_editor_property('auto_exposure_bias', 0.0)
    st.set_editor_property('override_auto_exposure_bias', True)
    pv.set_editor_property('settings', st)
    print('LOOK_Post placed, MANUAL metering - lensrig now controls exposure')

    # THE OUTDOOR LAYER, transplanted unchanged from the street that passed.
    # These are not distance-dependent, so they copy across as-is:
    #     LIGHT_Sun   DirectionalLight pitch -52 yaw 45 intensity 430
    #     LIGHT_Sky   SkyLight
    #     LIGHT_Atmosphere SkyAtmosphere
    if OUTDOOR == 'none':
        print('outdoor layer OMITTED (diagnostic)')
        return
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight,
                                     unreal.Vector(0.0, 0.0, 14000.0),
                                     unreal.Rotator(0.0, -52.0, 45.0))
    sun.set_actor_label('CITY_Sun')
    for c in sun.get_components_by_class(unreal.DirectionalLightComponent):
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity', SUN_LUX)
    if OUTDOOR == 'sun':
        print('outdoor layer: sun only (diagnostic)')
        return
    # A SPECIFIED GREY CUBEMAP, NOT A CAPTURED SCENE. This spawned a bare
    # SkyLight and set only mobility - no source type, no intensity, no
    # recapture - which leaves UE's default SLS_CAPTURED_SCENE. Two ways that
    # is wrong, both of them MEASURED on the bench on 2026-08-31:
    #   1. A captured-scene skylight replays whatever was in the scene when it
    #      was baked. The bench's was baked with the sun at 430, so zeroing
    #      the sun did not remove the sun - it removed its DIRECTION and left
    #      its energy pouring in omnidirectionally. Every "sun off" reading
    #      was measuring a laundered sun. Sky 10 -> 0 moved that frame 15
    #      levels while the bake was hot.
    #   2. With nothing skylike to capture it is simply BLACK - sky 100 vs 0
    #      moved the frame 0.13 levels once the bake had gone dark. This file
    #      spawned CITY_Sky BEFORE CITY_Atmosphere and never recaptured, so
    #      whatever it held was undefined, and OUTDOOR='sun_sky' returns
    #      before the atmosphere exists - meaning that diagnostic mode could
    #      never differ from 'sun'.
    # light_rig.py already solved this for the night rig and the fix is
    # verbatim: a grey cubemap tinted cool is even ambient from every
    # direction with no sky dome drawn, it needs no atmosphere, and its
    # intensity is an HONEST knob. Swept on the bench: crush fell 4.87% ->
    # 1.38% from 0.5 to 12 while the road falloff held, so 12 is the knee.
    sky = eas.spawn_actor_from_class(unreal.SkyLight,
                                     unreal.Vector(0.0, 0.0, 14000.0),
                                     unreal.Rotator(0, 0, 0))
    sky.set_actor_label('CITY_Sky')
    for c in sky.get_components_by_class(unreal.SkyLightComponent):
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('source_type',
                              unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        c.set_editor_property('cubemap', unreal.load_asset(SKY_CUBE))
        c.set_editor_property('real_time_capture', False)
        c.set_editor_property('intensity', SKY_I)
        c.set_editor_property('light_color', unreal.Color(176, 196, 226, 255))
        c.set_editor_property('cast_shadows', False)
        c.set_editor_property('lower_hemisphere_is_black', False)
        c.recapture_sky()
    print('CITY_Sky: specified grey cubemap, intensity %.1f (not a capture)'
          % SKY_I)
    if OUTDOOR == 'sun_sky':
        print('outdoor layer: sun + sky (diagnostic)')
        return
    atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere,
                                     unreal.Vector(0.0, 0.0, 0.0),
                                     unreal.Rotator(0, 0, 0))
    atm.set_actor_label('CITY_Atmosphere')
    print('outdoor layer: sun %.1f lux, sky light, atmosphere' % SUN_LUX)




build()
