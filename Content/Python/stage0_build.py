#!/usr/bin/env python3
"""
Stage 0 - three-bay recess comparison. Deterministic rebuild via the native
Unreal MCP bridge. Idempotent by actor label: existing BLD_/STAGE_/LIGHT_/
CAM_/LOOK_ actors are removed before rebuilding.

Numbers come from Docs/BAY_RECIPE.md. Scale: 1 uu = 1 cm, so mm/10 = uu.
"""
import ue, json

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
M = 'editor_toolset.toolsets.material.MaterialTools'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
F = '/Game/Stacktown/Materials'
OWNED = ('BLD_', 'STAGE_', 'LIGHT_', 'CAM_', 'LOOK_')

RECESS = {'BLD_Bay_A': (0, 7.5), 'BLD_Bay_B': (360, 15.0), 'BLD_Bay_C': (720, 25.0)}

ROLES = {
 'MI_concrete':    dict(c=(0.62,0.61,0.58), rmin=0.35, rmax=0.55, met=0.0, spec=0.5),
 'MI_paint_cream': dict(c=(0.80,0.78,0.73), rmin=0.35, rmax=0.50, met=0.0, spec=0.5),
 'MI_dark_metal':  dict(c=(0.13,0.13,0.14), rmin=0.30, rmax=0.45, met=0.6, spec=0.6),
 'MI_glass':       dict(c=(0.05,0.07,0.08), rmin=0.02, rmax=0.08, met=0.0, spec=1.0),
 'MI_model_board': dict(c=(0.34,0.32,0.30), rmin=0.40, rmax=0.55, met=0.0, spec=0.4),
 'MI_studio_grey': dict(c=(0.28,0.28,0.29), rmin=0.45, rmax=0.55, met=0.0, spec=0.3),
}
MATMAP = {'LeftPier':'MI_concrete','RightPier':'MI_concrete','Header':'MI_concrete',
 'Sill':'MI_concrete','Spandrel':'MI_paint_cream','MullionL':'MI_dark_metal',
 'MullionR':'MI_dark_metal','MullionC':'MI_dark_metal','MullionTop':'MI_dark_metal',
 'MullionBot':'MI_dark_metal','Glass':'MI_glass','InteriorCard':'MI_dark_metal',
 'BoardTop':'MI_model_board','BoardPlinth':'MI_model_board',
 'Card':'MI_studio_grey','Ground':'MI_studio_grey'}

def label(ref):
    try: return json.loads(ue.tool(A,'get_label',{'actor':ref}))['returnValue']
    except Exception: return ''

def wipe():
    acts = json.loads(ue.tool(S,'find_actors',{'name':'','tag':'','collision_channels':[]}))['returnValue']
    n = 0
    for a in acts:
        ref = a if isinstance(a, dict) else {'refPath': a}
        if label(ref).startswith(OWNED):
            ue.tool(S,'remove_from_scene',{'actor':ref}); n += 1
    print(f'  removed {n} pre-existing owned actors')

def mkactor(name, loc, cls='/Script/Engine.Actor', rot=None):
    x = {'location': loc}
    if rot: x['rotation'] = rot
    r = ue.tool(S,'add_to_scene_from_class',{'actor_type':{'refPath':cls},'name':name,'xform':x})
    ref = json.loads(r)['returnValue']
    ue.tool(A,'set_label',{'actor':ref,'label':name})
    return ref

def box(actor, name, x0,x1, y0,y1, z0,z1):
    ue.tool(P,'add_cube',{'actor':actor,'name':name,
        'dimensions':{'x':abs(x1-x0),'y':abs(y1-y0),'z':abs(z1-z0)},
        'local_transform':{'location':{'x':(x0+x1)/2.,'y':(y0+y1)/2.,'z':(z0+z1)/2.}}})

def build_bay(lbl, ox, R):
    a = mkactor(lbl, {'x':ox,'y':0,'z':0})
    box(a,'LeftPier',   0,60,     0,30,    0,360)
    box(a,'RightPier',  300,360,  0,30,    0,360)
    box(a,'Header',     60,300,   0,30,    300,360)
    box(a,'Spandrel',   60,300,   4,30,    0,90)
    box(a,'Sill',       55,305,  -4,R+8,   84,90)
    box(a,'MullionL',   60,65,    R,R+6,   90,300)
    box(a,'MullionR',   295,300,  R,R+6,   90,300)
    box(a,'MullionC',   177.5,182.5, R,R+6, 90,300)
    box(a,'MullionTop', 60,300,   R,R+6,   295,300)
    box(a,'MullionBot', 60,300,   R,R+6,   90,95)
    box(a,'Glass',      62,298,   R+8,R+9, 92,298)
    box(a,'InteriorCard',55,305,  R+48,R+49, 85,305)
    return a

def setp(ref, vals):
    return ue.tool(O,'set_properties',{'instance':ref,'values':json.dumps(vals)})

def materials():
    mat = {'refPath': F + '/M_StacktownMaster.M_StacktownMaster'}
    if 'true' not in ue.tool(AS,'exists',{'path':F+'/M_StacktownMaster'}):
        print('  master material missing - run mat.py first'); return {}
    made = {}
    for name, p in ROLES.items():
        if 'true' in ue.tool(AS,'exists',{'path':F+'/'+name}):
            made[name] = {'refPath': f'{F}/{name}.{name}'}; continue
        r = ue.tool(MI,'create',{'folder_path':F,'asset_name':name,'parent':mat})
        made[name] = json.loads(r)['returnValue']
        ue.tool(MI,'set_vector_parameter',{'instance':made[name],'name':'BaseColour',
            'value':{'r':p['c'][0],'g':p['c'][1],'b':p['c'][2],'a':1.0}})
        for pn, v in [('RoughMin',p['rmin']),('RoughMax',p['rmax']),
                      ('Metallic',p['met']),('Specular',p['spec'])]:
            ue.tool(MI,'set_scalar_parameter',{'instance':made[name],'name':pn,'value':v})
    return made

def assign(roles):
    acts = json.loads(ue.tool(S,'find_actors',{'name':'','tag':'','collision_channels':[]}))['returnValue']
    n = 0
    for a in acts:
        ref = a if isinstance(a, dict) else {'refPath': a}
        if not label(ref).startswith(('BLD_','STAGE_')): continue
        for c in json.loads(ue.tool(A,'get_components',{'actor':ref}))['returnValue']:
            cn = c['refPath'].split('.')[-1]
            if cn in MATMAP:
                setp(c, {'OverrideMaterials':[roles[MATMAP[cn]]]}); n += 1
    print(f'  assigned {n} components')
    return n

def main():
    print('=== wipe ==='); wipe()
    print('=== bays ===')
    for lbl,(ox,R) in RECESS.items():
        build_bay(lbl, ox, R); print(f'  {lbl}: recess {R*10:.0f}mm')
    print('=== stage ===')
    b = mkactor('STAGE_ModelBoard', {'x':0,'y':0,'z':0})
    box(b,'BoardTop',   -60,1140, -80,90, -10,0)
    box(b,'BoardPlinth',-48,1128, -68,78, -30,-10)
    k = mkactor('STAGE_Backdrop', {'x':0,'y':0,'z':0})
    box(k,'Card', -900,1980, 430,440, -30,1100)
    g = mkactor('STAGE_Ground', {'x':0,'y':0,'z':0})
    box(g,'Ground', -2000,3100, -1500,435, -40,-30)
    print('=== lights / camera / post ===')
    key = mkactor('LIGHT_Key', {'x':-520.66,'y':-1060.66,'z':1230.31}, '/Script/Engine.RectLight')
    fil = mkactor('LIGHT_Fill',{'x':1600.66,'y':-1060.66,'z':600.0},  '/Script/Engine.RectLight')
    setp({'refPath':key['refPath']+'.LightComponent0'},
         {'Intensity':300000.0,'bUseTemperature':True,'Temperature':4500.0,
          'SourceWidth':900.0,'SourceHeight':600.0,'IntensityUnits':'Lumens',
          'AttenuationRadius':8000.0,'BarnDoorAngle':88.0})
    setp({'refPath':fil['refPath']+'.LightComponent0'},
         {'Intensity':40000.0,'bUseTemperature':True,'Temperature':7200.0,
          'SourceWidth':1400.0,'SourceHeight':900.0,'IntensityUnits':'Lumens',
          'AttenuationRadius':8000.0,'BarnDoorAngle':88.0})
    for lt in (key, fil):
        ue.tool(A,'look_at',{'actor':lt,'target':{'x':540,'y':0,'z':180}})
    cam = mkactor('CAM_Hero', {'x':540,'y':-2378,'z':685},
                  '/Script/CinematicCamera.CineCameraActor', {'pitch':-12,'yaw':90,'roll':0})
    cc = {'refPath': cam['refPath'] + '.CameraComponent'}
    setp(cc, {'CurrentFocalLength':70.0})
    setp(cc, {'Filmback':{'SensorWidth':36.0,'SensorHeight':24.0}})
    setp(cc, {'FocusSettings':{'focusMethod':'Disable'}})
    setp(cam, {'AutoActivateForPlayer':'Player0'})
    # Second angle for gate line E4. 25 deg off-axis in plan, same 70mm /
    # -12 pitch / same distance, so it is inside the intended envelope.
    camb = mkactor('CAM_Hero_B', {'x':1545.0,'y':-2155.0,'z':685.0},
                   '/Script/CinematicCamera.CineCameraActor',
                   {'pitch':-12.0,'yaw':115.0,'roll':0})
    ccb = {'refPath': camb['refPath'] + '.CameraComponent'}
    setp(ccb, {'CurrentFocalLength':70.0})
    setp(ccb, {'Filmback':{'SensorWidth':36.0,'SensorHeight':24.0}})
    setp(ccb, {'FocusSettings':{'focusMethod':'Disable'}})
    ppv = mkactor('LOOK_Post', {'x':540,'y':0,'z':180}, '/Script/Engine.PostProcessVolume')
    setp(ppv, {'bUnbound':True})
    setp(ppv, {'Settings':{
        'bOverride_AutoExposureMethod':True,'autoExposureMethod':'AEM_Manual',
        'bOverride_CameraISO':True,'cameraISO':800.0,
        'bOverride_CameraShutterSpeed':True,'cameraShutterSpeed':60.0,
        'bOverride_DepthOfFieldFstop':True,'depthOfFieldFstop':4.0,
        'bOverride_AutoExposureBias':True,'autoExposureBias':0.0,
        'bOverride_AutoExposureApplyPhysicalCameraExposure':True,
        'autoExposureApplyPhysicalCameraExposure':True,
        'bOverride_BloomIntensity':True,'bloomIntensity':0.0,
        'bOverride_MotionBlurAmount':True,'motionBlurAmount':0.0}})
    print('=== materials ===')
    roles = materials()
    if roles: assign(roles)
    print('=== done ===')

if __name__ == '__main__':
    main()
