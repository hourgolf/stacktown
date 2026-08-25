"""The board's light rig, derived from the board.

WHY THE OLD ONE FAILED. Two rect lights and nothing else - no SkyLight, no
directional. A rect light falls off with the INVERSE SQUARE of distance, and
LIGHT_Key sat off the south-west corner where the first block used to be. When
the board was 4900 x 3600 that covered it. The board is now 10700 x 7600, so
block D at the far end received roughly a twelfth of block A's illuminance:
measured facade means of 150 against 29. Anything the two rects missed was
genuinely black, which is why it read as a pitch-dark room rather than a night
exterior - and "everything was captured in a black void, which reads as a
render" is failure 5 in AGENTS.md.

WHAT REPLACES IT. Distance-independent sources do the covering:

  LIGHT_Sky    a SkyLight. The base ambient that stops anything being pure
               black. Cool, low - the night sky, and the reason an unlit
               elevation still reads as a surface rather than a hole.
  LIGHT_Moon   a DirectionalLight. Does not attenuate, so the far corner of a
               10700 uu board gets the same illuminance as the near one. Set on
               MINIATURE_RECIPE's key geometry - 45 degrees off axis, 35 degrees
               elevation - so shadow direction is unchanged from every capture
               taken so far.

The two rect lights stay, re-centred over the BOARD instead of over block A,
as the warm studio key and cool wrap that give the model its modelling. Their
intensity is scaled by the inverse square of the new distance, exactly as
MINIATURE_RECIPE says it must be.

Exposure is NOT touched. The gate fixes it at ISO 800, f/4, 1/60 and the rig
moves to meet it, never the other way round.
"""
import unreal, math
import _path
from city import BOARD_N
from city import BOARD_S, BOARD_E

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

X0, X1 = -300.0, BOARD_E
# the board grew north for the works; a rig sized to the old edge lights an
# island and leaves the rest in a void, which is what the first works
# capture showed at mean 60
Y0, Y1 = BOARD_S, BOARD_N
CX, CY = (X0 + X1)/2.0, (Y0 + Y1)/2.0
DIAG = math.hypot(X1 - X0, Y1 - Y0)

import sys, json
_A = json.loads(ARGS) if 'ARGS' in dir() else {}
# MINIATURE_RECIPE's key geometry. 'sunyaw' exists so the sun azimuth can be
# varied on its own - it is the one thing that decides which side of a lot is
# in shadow, and that had to be isolated from exposure before either was tuned.
KEY_YAW, KEY_PITCH = _A.get('sunyaw', 45.0), 35.0
MODE = _A.get('mode', 'night')           # 'day' or 'night'
MOON_TEMP = 7200.0
MOON_I = _A.get('moon', 0.85)            # lux; a night exterior, not daylight
SKY_I = _A.get('sky', 0.55)
FILL_D_I = _A.get('dfill', 0.9)          # directional fill, no shadows
KEY_D = DIAG * 0.95                      # key standoff from board centre
KEY_I_AT = (3400770.5, 6900.0)           # the tuned intensity, and the distance
FILL_I_AT = (1067534.625, 6900.0)        # it was tuned at

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() in ('LIGHT_Sky', 'LIGHT_Moon', 'LIGHT_MoonFill',
                               'LIGHT_Sun', 'LIGHT_Atmosphere'):
        eas.destroy_actor(a)


def place(cls, label, loc, rot):
    a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    a.set_actor_label(label)
    return a


def _daylight():
    """Daylight: a real sky, a sun, and an exposure that suits them.

    A model photographed OUTSIDE, which is how architectural models are usually
    photographed. The card, the board and the backdrop are unchanged - what
    changes is that there is now an environment for them to sit in, so the void
    past the board edge becomes sky instead of nothing.

    EXPOSURE HAS TO MOVE. The gate fixes ISO 800, f/4, 1/60 - that is a night
    exposure, about EV 7. Daylight is nearer EV 15, so at the night settings the
    frame is eight stops over and everything is white. The gate's requirement is
    that exposure be FIXED and MANUAL, not that it be those three numbers, and
    the numbers were chosen for a dark studio. Day gets its own fixed set.
    """
    atmo = eas.spawn_actor_from_class(unreal.SkyAtmosphere,
                                      unreal.Vector(CX, CY, 0.0), unreal.Rotator())
    atmo.set_actor_label('LIGHT_Atmosphere')

    sx = CX - DIAG*math.cos(math.radians(KEY_YAW))
    sy = CY - DIAG*math.sin(math.radians(KEY_YAW))
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight,
        unreal.Vector(sx, sy, DIAG*0.8), unreal.Rotator(0.0, -SUN_PITCH, KEY_YAW))
    sun.set_actor_label('LIGHT_Sun')
    sc_ = sun.get_components_by_class(unreal.DirectionalLightComponent)[0]
    sc_.set_editor_property('intensity', SUN_I)
    sc_.set_editor_property('use_temperature', True)
    sc_.set_editor_property('temperature', 5600.0)
    sc_.set_editor_property('cast_shadows', True)
    sc_.set_editor_property('atmosphere_sun_light', True)
    sc_.set_editor_property('forward_shading_priority', 10)

    sky = eas.spawn_actor_from_class(unreal.SkyLight,
        unreal.Vector(CX, CY, 4000.0), unreal.Rotator())
    sky.set_actor_label('LIGHT_Sky')
    kc = sky.get_components_by_class(unreal.SkyLightComponent)[0]
    kc.set_editor_property('source_type', unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
    # REAL-TIME CAPTURE OFF. It is what the Lumen warning is about - "Cached
    # lighting in Lumen and real-time sky capture lighting is going to be
    # clipped" - and it buys nothing here: the sun is static, so the sky it
    # captures never changes. One explicit recapture gives the same ambient
    # without asking Lumen to reconcile a live capture against its cache.
    kc.set_editor_property('real_time_capture', False)
    kc.set_editor_property('intensity', SKY_I)
    kc.set_editor_property('cast_shadows', True)
    kc.set_editor_property('lower_hemisphere_is_black', False)
    kc.recapture_sky()

    # the two rect lights are a studio rig and would double-light a sunlit
    # scene; parked at zero rather than deleted so night mode can restore them
    for lbl in ('LIGHT_Key', 'LIGHT_Fill'):
        act = next((a for a in eas.get_all_level_actors()
                    if a.get_actor_label() == lbl), None)
        if act:
            act.get_components_by_class(unreal.RectLightComponent)[0]\
               .set_editor_property('intensity', 0.0)

    ppv = next((a for a in eas.get_all_level_actors()
                if isinstance(a, unreal.PostProcessVolume)), None)
    if ppv:
        st = ppv.get_editor_property('settings')
        st.set_editor_property('override_camera_iso', True)
        st.set_editor_property('camera_iso', ISO)
        st.set_editor_property('override_camera_shutter_speed', True)
        st.set_editor_property('camera_shutter_speed', SHUTTER)
        st.set_editor_property('override_depth_of_field_fstop', True)
        st.set_editor_property('depth_of_field_fstop', FSTOP)
        ppv.set_editor_property('settings', st)
    # Lumen caches lighting at a pre-exposure and warns ACROSS THE RENDER when
    # the scene exposure leaves that range: "Cached lighting in Lumen and
    # real-time sky capture lighting is going to be clipped... Exposure: 14.9".
    # Daylight is ~8 stops off the night exposure this project was built at, so
    # the cached range has to move with it.
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    # NOT 14.9. The warning names that number as the scene exposure, but the
    # cvar is a pre-exposure MULTIPLIER, not a cache range: setting it to 14.9
    # brightened the frame by eight stops, to mean 227 with 7.5% blown. Zero is
    # neutral, and the fix for the warning is to keep the scene inside the
    # cached range rather than to move the range to the scene.
    # UNRESOLVED: at the exposure daylight needs (8.9) Lumen prints "Cached
    # lighting in Lumen and real-time sky capture lighting is going to be
    # clipped... Safe exposure range: [-12.0, ...]" across the viewport. Its
    # ceiling sits between 6.9 and 8.9. Dimming the sun two stops and opening
    # the aperture two stops silences it and gives an identical image at
    # exposure 6.9 - but that image is dusk, not daylight, because the whole
    # scene is then two stops darker in absolute terms.
    #
    # The cvar the message names is a pre-exposure MULTIPLIER: setting it to
    # 14.9 brightened the frame eight stops rather than moving a cache range.
    # Left at 0. The warning is an editor viewport overlay and belongs to the
    # capture rig, not the scene - but it IS in these captures, which is the
    # same class of defect as the axis gizmo, so it stays flagged.
    for cmd in ('r.EyeAdaptation.CachedLightingPreExposure %g' % PRE_EXP,):
        unreal.SystemLibrary.execute_console_command(w, cmd)
    print('DAYLIGHT  sun %.2f lux %.0f deg elevation | sky %.2f | ISO %d f/%.1f 1/%d'
          % (SUN_I, SUN_PITCH, SKY_I, ISO, FSTOP, SHUTTER))
    print('board %.0f x %.0f' % (X1 - X0, Y1 - Y0))


if MODE == 'day':
    # Tuned by sweeping the APERTURE, not the lights. Sun and sky sweeps kept
    # producing nonsense - reducing the sun raised the frame mean twice - and
    # the reason is Lumen and the real-time sky capture re-converging after
    # every change. f-stop is post-process, so it moves the image without
    # touching the lighting state, and the sweep came out monotonic at once:
    # f/8 -> 128.4, f/13 -> 55.1, f/18 -> 25.6.
    #
    # ISO 800 / 1/60 are the gate's own numbers. Only the aperture moves between
    # night and day, which keeps the "one camera photographing a model" reading
    # intact - the sun here is a studio lamp, not the actual sun.
    # THE LEVER WAS BACKWARDS. Stopping down to f/8 and leaving the sun at 260
    # produced Lumen's "cached lighting is going to be clipped... Exposure: 8.9"
    # warning across the viewport. That number is the exposure COMPENSATION the
    # engine applies, so closing the aperture RAISES it. The fix is the
    # opposite of what it looks like: light the scene brighter and open the
    # aperture, so less compensation is needed and the exposure lands back
    # inside Lumen's cached range. f/4 clears it, and once the aperture is
    # open the LIGHT is free to rise. Sun and sky were then tuned separately,
    # because they do different jobs: the sun sets the contrast, the sky sets
    # how dark a shadow goes, and the actual complaint was always the shadowed
    # side. Measured on the live viewport rectangle only - the earlier numbers
    # mixed in the pillarbox and were worth nothing. Board / plaza means:
    #     sky  8 -> 189 / 116  (0.62)   plaza still murky
    #     sky 14 -> 193 / 138  (0.71)   colour and cast shadow both hold
    #     sky 22 -> 204 / 167  (0.82)   plaza lit, but the board washes out
    # 14 was the knee FOR THAT SCENE. Then the planting plan landed and the
    # scene itself changed: oversized pale canopies shrank and 216 lamp
    # components went from the bright WorldGridMaterial checker to dark metal,
    # which took the board from 193 to 158 at an untouched rig. Re-measured:
    #     sky 14 -> 158 /  88     sky 22 -> 175 / 110     sky 38 -> 194 / 115
    # 22 sat where 14 did. Then the scene changed AGAIN - shingle roofs instead
    # of white ones, backs of houses, gardens, twice the component count - and
    # 22 read as washed out. Re-measured on the board:
    #     sky 10 -> 149 / sd 43.1     sky 14 -> 160 / 42.0     sky 22 -> 178 / 40.9
    # 10 it is. THE TRADE IS REAL and worth stating: sky is the lever that
    # lifts shadow, so the shadowed north-facing elevations and the Green go
    # back to being the darkest things on the board. Washed out was the
    # complaint; if the shadows now read as too dark, this is the number to
    # move and the plaza geometry is the other half of the answer.
    # The lesson is the reusable part: a light rig is tuned against a SCENE, so
    # changing what is in the scene invalidates it. This is the third time.
    SUN_I = _A.get('sun', 430.0)
    SUN_PITCH = _A.get('elev', 52.0)
    SKY_I = _A.get('sky', 10.0)
    ISO = _A.get('iso', 800)
    FSTOP = _A.get('fstop', 4.0)
    SHUTTER = _A.get('shutter', 60)
    PRE_EXP = _A.get('preexp', 0.0)
    _daylight()
    raise SystemExit(0)


# --- sky: the base that stops anything being pure black ---------------------
sky = place(unreal.SkyLight, 'LIGHT_Sky', (CX, CY, 4000.0), (0.0, 0.0, 0.0))
sc = sky.get_components_by_class(unreal.SkyLightComponent)[0]
# A NEUTRAL CUBEMAP TINTED COOL, not a captured scene and not an empty
# specified cubemap. Both of those give BLACK:
#   - SLS_SPECIFIED_CUBEMAP with nothing assigned has nothing to sample.
#   - SLS_CAPTURED_SCENE with real-time capture printed a warning ACROSS THE
#     RENDER saying it needs a SkyAtmosphere, a VolumetricCloud or an IsSky
#     mesh or it will be black - and there is none of those here, so every
#     "sky" reading up to this point was measuring nothing.
# A grey cubemap multiplied by a cool colour is even ambient from every
# direction with no sky dome drawn, which is what a model on a board wants.
sc.set_editor_property('source_type', unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
sc.set_editor_property('cubemap', unreal.load_asset(
    '/Engine/EngineResources/GrayLightTextureCube.GrayLightTextureCube'))
sc.set_editor_property('real_time_capture', False)
sc.set_editor_property('intensity', SKY_I)
sc.set_editor_property('light_color', unreal.Color(176, 196, 226, 255))   # cool night sky
sc.set_editor_property('cast_shadows', False)
sc.set_editor_property('lower_hemisphere_is_black', False)
sc.recapture_sky()

# --- moon: distance-independent, so the far corner is lit like the near one --
mx = CX - DIAG*math.cos(math.radians(KEY_YAW))
my = CY - DIAG*math.sin(math.radians(KEY_YAW))
moon = place(unreal.DirectionalLight, 'LIGHT_Moon',
             (mx, my, DIAG*0.7), (0.0, -KEY_PITCH, KEY_YAW))
mc = moon.get_components_by_class(unreal.DirectionalLightComponent)[0]
mc.set_editor_property('intensity', MOON_I)
mc.set_editor_property('use_temperature', True)
mc.set_editor_property('temperature', MOON_TEMP)
mc.set_editor_property('cast_shadows', True)
# Two directionals otherwise print "Multiple directional lights are competing
# to be the single one used for forward shading" across the render. The key
# wins explicitly.
mc.set_editor_property('forward_shading_priority', 10)

# --- the fill is a SECOND DIRECTIONAL, not a bigger skylight -----------------
# A captured-scene skylight has almost nothing to capture here: the environment
# is a dark studio, so multiplying it up multiplies very little. Measured, the
# street moved 22.7 -> 26.2 for a 3.0 skylight, which is not enough to matter.
# A directional does not attenuate, so a dim one from the opposite side lifts
# every surface the moon misses by the same amount wherever it is on a 10700 uu
# board. Shadows OFF - a fill that casts its own shadows is a second key.
fx = CX + DIAG*math.cos(math.radians(KEY_YAW))
fy2 = CY + DIAG*math.sin(math.radians(KEY_YAW))
mfill = place(unreal.DirectionalLight, 'LIGHT_MoonFill',
              (fx, fy2, DIAG*0.5), (0.0, -18.0, KEY_YAW + 180.0))
fc = mfill.get_components_by_class(unreal.DirectionalLightComponent)[0]
fc.set_editor_property('intensity', FILL_D_I)
fc.set_editor_property('use_temperature', True)
fc.set_editor_property('temperature', 8200.0)
fc.set_editor_property('cast_shadows', False)
fc.set_editor_property('forward_shading_priority', 0)

# --- re-centre the two rects over the BOARD, scaled by inverse square --------
for lbl, (base_i, base_d), yaw, pitch, frac in (
        ('LIGHT_Key',  KEY_I_AT,  KEY_YAW,        KEY_PITCH, 0.95),
        ('LIGHT_Fill', FILL_I_AT, KEY_YAW + 180.0, 6.0,      1.05)):
    act = next((a for a in eas.get_all_level_actors()
                if a.get_actor_label() == lbl), None)
    if not act:
        print('  %s missing' % lbl); continue
    d = DIAG * frac
    lx = CX - d*math.cos(math.radians(yaw))
    ly = CY - d*math.sin(math.radians(yaw))
    lz = d*math.sin(math.radians(pitch)) + 800.0
    act.set_actor_location(unreal.Vector(lx, ly, lz), False, False)
    act.set_actor_rotation(unreal.Rotator(0.0, -pitch, yaw), False)
    c = act.get_components_by_class(unreal.RectLightComponent)[0]
    # intensity scales with the INVERSE SQUARE of rig distance - the one line
    # of MINIATURE_RECIPE that makes a rig portable between board sizes
    scaled = base_i * (d / base_d) ** 2
    c.set_editor_property('intensity', scaled)
    c.set_editor_property('attenuation_radius', DIAG * 2.4)
    c.set_editor_property('source_width', DIAG * 0.42)
    c.set_editor_property('source_height', DIAG * 0.28)
    print('  %-11s d %.0f  I %.3g -> %.3g  (x%.2f)' % (lbl, d, base_i, scaled, (d/base_d)**2))

print('board %.0f x %.0f, diagonal %.0f' % (X1 - X0, Y1 - Y0, DIAG))
print('LIGHT_Sky   intensity %.2f  cool ambient' % SKY_I)
print('LIGHT_Moon  intensity %.2f  %.0fK  pitch %.0f yaw %.0f  (no attenuation)'
      % (MOON_I, MOON_TEMP, KEY_PITCH, KEY_YAW))
print('LIGHT_MoonFill intensity %.2f  8200K  pitch 18 yaw %.0f  shadows off'
      % (FILL_D_I, KEY_YAW + 180.0))
