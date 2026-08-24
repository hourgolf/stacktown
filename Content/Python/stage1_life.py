"""Stage 1 colour + print character, and the E4 second angle.

Colour deliberately does NOT come from albedo variation across the facade -
BAY_RECIPE calls large-scale albedo variation "the trap" and the master
material spec forbids it. It comes from (a) warm practicals behind the glazing,
which the gate explicitly permits, and (b) one saturated accent on the canopy,
used sparingly per MASTER_MATERIAL_SPEC's paint_accent role.
"""
import unreal, math

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

for lbl in list(acts):
    if lbl.startswith(('LIGHT_Practical', 'CAM_Hero_B')):
        eas.destroy_actor(acts[lbl])

W = 1080.0
GF_H, FL_H = 420.0, 360.0


def rect_light(name, loc, yaw, temp, lumens, sw, sh, atten):
    a = eas.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*loc),
                                   unreal.Rotator(0.0, 0.0, yaw))
    a.set_actor_label(name)
    c = a.rect_light_component
    c.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
    c.set_editor_property('intensity', lumens)
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', temp)
    c.set_editor_property('source_width', sw)
    c.set_editor_property('source_height', sh)
    c.set_editor_property('attenuation_radius', atten)
    c.set_editor_property('cast_shadows', False)
    return a


# --- shopfront practicals: warm interior glow behind the glazing ---
rect_light('LIGHT_Practical_ShopL', (286.0, 49.0, 230.0), 270.0, 2700.0,
           4200.0, 460.0, 300.0, 560.0)
rect_light('LIGHT_Practical_ShopR', (800.0, 49.0, 230.0), 270.0, 2750.0,
           3700.0, 440.0, 300.0, 560.0)
print('shopfront practicals added (2700 K)')

# --- a few lit upper windows: uneven, the way a real building is ---
LIT = [(1, 0, 2900.0, 7000.0), (2, 2, 3000.0, 6000.0), (4, 1, 2800.0, 6600.0)]
BAYS = [(60.0, 300.0), (420.0, 660.0), (780.0, 1020.0)]
for floor, bay, temp, lm in LIT:
    bx0, bx1 = BAYS[bay]
    z = GF_H + (floor - 1) * FL_H + FL_H * 0.5
    rect_light('LIGHT_Practical_F%dB%d' % (floor, bay),
               ((bx0 + bx1) / 2.0, 45.0, z), 270.0, temp, lm, 230.0, 200.0, 900.0)
print('%d upper-window practicals added' % len(LIT))

# --- one saturated accent, used sparingly: the canopy fascia ---
acc = unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Materials/MI_paint_accent.MI_paint_accent')
fascia = unreal.EditorAssetLibrary.load_asset(
    '/Game/Stacktown/Materials/MI_canopy_accent.MI_canopy_accent') \
    if unreal.EditorAssetLibrary.does_asset_exist(
        '/Game/Stacktown/Materials/MI_canopy_accent') else None
if fascia is None:
    at = unreal.AssetToolsHelpers.get_asset_tools()
    fascia = at.create_asset('MI_canopy_accent', '/Game/Stacktown/Materials',
                             unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    fascia.set_editor_property('parent', unreal.EditorAssetLibrary.load_asset(
        '/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster'))
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    fascia, 'BaseColour', unreal.LinearColor(0.38, 0.12, 0.10, 1.0))
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    fascia, 'RoughMin', 0.35)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    fascia, 'RoughMax', 0.50)
unreal.EditorAssetLibrary.save_asset('/Game/Stacktown/Materials/MI_canopy_accent')
can = acts.get('BLD_Canopy')
n = 0
for c in can.get_components_by_class(unreal.StaticMeshComponent):
    if c.get_name() in ('CanopyFascia',):
        c.set_editor_property('override_materials', [fascia])
        n += 1
print('canopy fascia recoloured on %d component(s)' % n)

# --- E4 second angle: 28 deg off-axis, same 70 mm / -12 deg / same distance ---
cx, cz = 540.0, 975.0
d = 9479.0
a = math.radians(28.0)
bx = cx + d * math.cos(math.radians(12)) * math.sin(a)
by = -d * math.cos(math.radians(12)) * math.cos(a)
bz = cz + d * math.sin(math.radians(12))
yaw = math.degrees(math.atan2(0 - by, cx - bx))
camb = eas.spawn_actor_from_class(
    unreal.CineCameraActor, unreal.Vector(bx, by, bz),
    unreal.Rotator(0.0, -12.0, yaw))
camb.set_actor_label('CAM_Hero_B')
cc = camb.get_cine_camera_component()
cc.set_editor_property('current_focal_length', 70.0)
fb = cc.get_editor_property('filmback')
fb.set_editor_property('sensor_width', 36.0)
fb.set_editor_property('sensor_height', 24.0)
cc.set_editor_property('filmback', fb)
fs = cc.get_editor_property('focus_settings')
fs.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
cc.set_editor_property('focus_settings', fs)
print('CAM_Hero_B at (%.0f, %.0f, %.0f) yaw %.1f  70 mm  -12 deg' % (bx, by, bz, yaw))

les.save_current_level()
print('saved')
