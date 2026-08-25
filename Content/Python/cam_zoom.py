import unreal, math, sys
import _path  # repo tool paths; replaces a dead scratchpad path
from lots import LOTS
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label()=='CAM_Zoom': eas.destroy_actor(a)
n=[l for l in LOTS if l['name']=='Narrow'][0]
# street trees sit at X 560,1680,2800,3920 - aim between them and put the
# camera on the far side so none of them enters frame
t=(n['x0']+n['width']*0.22, 0.0, 950.0)
D,PITCH,ANG=900.0,-6.0,-22.0
p=math.radians(abs(PITCH)); horiz=D*math.cos(p)
x=t[0]+horiz*math.sin(math.radians(ANG)); y=t[1]-horiz*math.cos(math.radians(ANG))
z=t[2]+D*math.sin(p)
yaw=math.degrees(math.atan2(t[1]-y,t[0]-x))
cam=eas.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(x,y,z),
                               unreal.Rotator(0.0,PITCH,yaw))
cam.set_actor_label('CAM_Zoom')
c=cam.get_cine_camera_component()
c.set_editor_property('current_focal_length',70.0)
fb=c.get_editor_property('filmback'); fb.set_editor_property('sensor_width',36.0)
fb.set_editor_property('sensor_height',24.0); c.set_editor_property('filmback',fb)
fs=c.get_editor_property('focus_settings')
fs.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE)
c.set_editor_property('focus_settings',fs)
fw=2*D*math.tan(math.radians(28.84/2))
print('CAM_Zoom on %s: frame %.0f uu, 0.4%% threshold %.1f uu'%(n['name'],fw,fw*0.004))
les.save_current_level()
