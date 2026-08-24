"""Stage 1 part 2 - ground floor, canopy, balcony, street, tree, stage, rig."""
import ue, json, math

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
O = 'editor_toolset.toolsets.object.ObjectTools'

W, D = 1080.0, 800.0
GF_H, FL_H, N_FL, PARAPET = 420.0, 360.0, 4, 90.0
TOTAL = GF_H + N_FL * FL_H + PARAPET


def mkactor(name, loc=(0, 0, 0), cls='/Script/Engine.Actor', rot=None):
    x = {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]}}
    if rot:
        x['rotation'] = {'pitch': rot[0], 'yaw': rot[1], 'roll': rot[2]}
    r = ue.tool(S, 'add_to_scene_from_class',
                {'actor_type': {'refPath': cls}, 'name': name, 'xform': x})
    ref = json.loads(r)['returnValue']
    ue.tool(A, 'set_label', {'actor': ref, 'label': name})
    return ref


def box(actor, name, x0, x1, y0, y1, z0, z1):
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': abs(x1 - x0), 'y': abs(y1 - y0), 'z': abs(z1 - z0)},
        'local_transform': {'location': {'x': (x0 + x1) / 2.0,
                                         'y': (y0 + y1) / 2.0,
                                         'z': (z0 + z1) / 2.0}}})


def setp(ref, vals):
    return ue.tool(O, 'set_properties', {'instance': ref, 'values': json.dumps(vals)})


print('=== ground floor (entrance inset, gate A4) ===')
g = mkactor('BLD_GroundFloor')
box(g, 'Plinth', -6, W + 6, -12, 62, 0, 30)
box(g, 'PierL', 0, 52, 0, 60, 30, 380)
box(g, 'PierR', W - 52, W, 0, 60, 30, 380)
box(g, 'PierMid', 520, 572, 0, 60, 30, 380)
box(g, 'Bulkhead', -4, W + 4, -8, 60, 380, GF_H)
# shopfront glazing recessed 400 mm behind the pier face
box(g, 'ShopGlassL', 52, 520, 40, 43, 40, 372)
box(g, 'ShopGlassR', 572, W - 52, 40, 43, 40, 372)
# Dark interior card behind the shopfront. Without it the glazing showed the
# bright concrete core and washed out - MASTER_MATERIAL_SPEC's glass rule:
# emptiness behind glass reads as a hole. The upper floors already had this.
box(g, 'ShopInteriorL', 46, 526, 52, 58, 30, 376)
box(g, 'ShopInteriorR', 566, W - 46, 52, 58, 30, 376)
# shopfront mullion grid, matching the upper-floor printed-grid language
for k in range(1, 5):
    mx = 52 + (520 - 52) * k / 5.0
    box(g, 'ShopMulL%d' % k, mx - 3, mx + 3, 34, 41, 40, 372)
    mx2 = 572 + (W - 52 - 572) * k / 5.0
    box(g, 'ShopMulR%d' % k, mx2 - 3, mx2 + 3, 34, 41, 40, 372)
box(g, 'ShopTransomL', 52, 520, 34, 41, 300, 306)
box(g, 'ShopTransomR', 572, W - 52, 34, 41, 300, 306)
box(g, 'ShopSillL', 46, 526, 34, 62, 30, 40)
box(g, 'ShopSillR', 566, W - 46, 34, 62, 30, 40)
# entrance inset a further 300 mm - the deepest reveal on the building
box(g, 'EntranceJambL', 700, 726, 40, 76, 30, 372)
box(g, 'EntranceJambR', 826, 852, 40, 76, 30, 372)
box(g, 'EntranceHead', 700, 852, 40, 76, 340, 372)
box(g, 'DoorGlass', 726, 826, 74, 76, 30, 340)
print('   shopfront recessed 400 mm, entrance a further 300 mm')

print('=== canopy (A6 projection 1 of 3, 2.2 m) ===')
c = mkactor('BLD_Canopy')
# Deepened from 1.5 m to 2.2 m and given a taller fascia. The projection alone
# read as only a ~20-level tonal step; what sells it is the hard shadow it
# throws across the recessed shopfront, and that scales with depth.
box(c, 'CanopySlab', -16, W + 16, -220, 2, 386, 402)
box(c, 'CanopyFascia', -16, W + 16, -228, -220, 366, 402)
box(c, 'CanopyUnder', -14, W + 14, -220, 0, 380, 386)
for i in range(7):
    x = 20 + i * 170
    box(c, 'Rib%d' % i, x, x + 6, -220, 0, 374, 380)
print('   canopy projects 2.2 m with deep fascia + ribs')

print('=== balcony (A6 projection 2 of 3) ===')
b = mkactor('BLD_Balcony')
zb = GF_H + 2 * FL_H
box(b, 'Slab', 400, 680, -120, -55, zb + 40, zb + 52)
box(b, 'RailTop', 400, 680, -120, -112, zb + 52, zb + 100)
for i in range(6):
    x = 408 + i * 54
    box(b, 'Post%d' % i, x, x + 5, -118, -113, zb + 52, zb + 100)
print('   balcony at floor 3')

print('=== fire escape (A6 projection 3 of 3) ===')
fe = mkactor('BLD_FireEscape')
for n in range(N_FL):
    z = GF_H + n * FL_H + 40
    box(fe, 'Landing%d' % n, 30, 200, -96, -40, z, z + 8)
    box(fe, 'Rail%d' % n, 30, 200, -96, -90, z + 8, z + 52)
    if n < N_FL - 1:
        box(fe, 'Stair%d' % n, 60, 170, -80, -50, z + 8, z + FL_H)
box(fe, 'Stringer', 30, 38, -96, -40, GF_H + 40, GF_H + N_FL * FL_H)
print('   fire escape, %d landings' % N_FL)

print('=== sidewalk + curb (gate A5) ===')
st = mkactor('STAGE_Street')
box(st, 'Sidewalk', -700, 1780, -430, -6, -15, 0)
box(st, 'CurbFace', -700, 1780, -466, -430, -15, 0)
box(st, 'Road', -700, 1780, -1150, -466, -30, -15)
print('   curb 150 mm with a visible vertical face')

print('=== tree (paper cutout, crossed cards - no import, no purchase) ===')
t = mkactor('PROP_Tree', (1330.0, -230.0, 0.0))
# Layered card tree: overlapping flats at varied angles rather than a single
# crossed pair, so the silhouette is irregular the way a hand-cut one is.
box(t, 'Trunk', -11, 11, -9, 9, 0, 210)
box(t, 'TrunkFork', -34, 34, -7, 7, 190, 250)
box(t, 'CanopyA', -150, 150, -4, 4, 215, 520)
box(t, 'CanopyB', -4, 4, -130, 130, 235, 495)
box(t, 'CanopyC', -112, 112, -3, 3, 255, 430)
box(t, 'CanopyD', -3, 3, -96, 96, 300, 560)
box(t, 'CanopyE', -78, 78, -3, 3, 180, 330)
box(t, 'Grate', -46, 46, -46, 46, -3, 0)
print('   layered card tree, 5.6 m, 5 overlapping flats')

print('=== stage ===')
bd = mkactor('STAGE_ModelBoard')
box(bd, 'BoardTop', -900, 2000, -1300, 1100, -46, -30)
box(bd, 'BoardPlinth', -880, 1980, -1280, 1080, -80, -46)
kd = mkactor('STAGE_Backdrop')
box(kd, 'Card', -3600, 4700, 1100, 1130, -80, 4200)
gr = mkactor('STAGE_Ground')
box(gr, 'Ground', -7000, 8000, -6000, 1120, -92, -80)
print('   board with stepped edge, backdrop, ground')

print('=== lights / camera / post ===')
cx, cz = 540.0, TOTAL / 2.0
dist = 4200.0
kx = cx - dist * math.sin(math.radians(45))
ky = -dist * math.cos(math.radians(45))
kz = cz + dist * math.tan(math.radians(35))
key = mkactor('LIGHT_Key', (kx, ky, kz), '/Script/Engine.RectLight')
fil = mkactor('LIGHT_Fill', (cx + dist * math.sin(math.radians(45)),
                             ky, cz + 400), '/Script/Engine.RectLight')
setp({'refPath': key['refPath'] + '.LightComponent0'},
     {'Intensity': 1580000.0, 'bUseTemperature': True, 'Temperature': 4500.0,
      'SourceWidth': 2600.0, 'SourceHeight': 1700.0, 'IntensityUnits': 'Lumens',
      'AttenuationRadius': 26000.0, 'BarnDoorAngle': 88.0})
setp({'refPath': fil['refPath'] + '.LightComponent0'},
     {'Intensity': 210000.0, 'bUseTemperature': True, 'Temperature': 7200.0,
      'SourceWidth': 4000.0, 'SourceHeight': 2600.0, 'IntensityUnits': 'Lumens',
      'AttenuationRadius': 26000.0, 'BarnDoorAngle': 88.0})
for lt in (key, fil):
    ue.tool(A, 'look_at', {'actor': lt, 'target': {'x': cx, 'y': 0, 'z': cz}})

d = 9479.0
camy = -d * math.cos(math.radians(12))
camz = cz + d * math.sin(math.radians(12))
cam = mkactor('CAM_Hero', (cx, camy, camz),
              '/Script/CinematicCamera.CineCameraActor', (-12.0, 90.0, 0.0))
cc = {'refPath': cam['refPath'] + '.CameraComponent'}
setp(cc, {'CurrentFocalLength': 70.0})
setp(cc, {'Filmback': {'SensorWidth': 36.0, 'SensorHeight': 24.0}})
setp(cc, {'FocusSettings': {'focusMethod': 'Disable'}})
print('   camera at (%.0f, %.0f, %.0f)  70 mm  -12 deg' % (cx, camy, camz))

ppv = mkactor('LOOK_Post', (cx, 0, cz), '/Script/Engine.PostProcessVolume')
setp(ppv, {'bUnbound': True})
setp(ppv, {'Settings': {
    'bOverride_AutoExposureMethod': True, 'autoExposureMethod': 'AEM_Manual',
    'bOverride_CameraISO': True, 'cameraISO': 800.0,
    'bOverride_CameraShutterSpeed': True, 'cameraShutterSpeed': 60.0,
    'bOverride_DepthOfFieldFstop': True, 'depthOfFieldFstop': 4.0,
    'bOverride_AutoExposureBias': True, 'autoExposureBias': 0.0,
    'bOverride_AutoExposureApplyPhysicalCameraExposure': True,
    'autoExposureApplyPhysicalCameraExposure': True,
    'bOverride_BloomIntensity': True, 'bloomIntensity': 0.0,
    'bOverride_MotionBlurAmount': True, 'motionBlurAmount': 0.0}})
print('=== part 2 done ===')
