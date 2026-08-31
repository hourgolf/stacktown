"""Restore the grade volume: AEM_Manual and the project's camera settings.

Without an unbound PostProcessVolume the level falls back to UE's DEFAULT
AUTO exposure, and every capture becomes a measurement of how full the frame
happens to be rather than of the model. Values match stage1_street.py, which
is where the look was originally settled.
"""
import unreal
import _path  # noqa: F401

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() == 'LOOK_Post':
        eas.destroy_actor(a)

ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume,
                                 unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
ppv.set_actor_label('LOOK_Post')
ppv.set_editor_property('unbound', True)
st = ppv.get_editor_property('settings')
st.set_editor_property('override_auto_exposure_method', True)
st.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
st.set_editor_property('override_camera_iso', True)
st.set_editor_property('camera_iso', 800.0)
st.set_editor_property('override_camera_shutter_speed', True)
st.set_editor_property('camera_shutter_speed', 60.0)
st.set_editor_property('override_depth_of_field_fstop', True)
st.set_editor_property('depth_of_field_fstop', 4.0)
st.set_editor_property('override_auto_exposure_bias', True)
st.set_editor_property('auto_exposure_bias', 0.0)
st.set_editor_property('override_auto_exposure_apply_physical_camera_exposure', True)
st.set_editor_property('auto_exposure_apply_physical_camera_exposure', True)
st.set_editor_property('override_bloom_intensity', True)
st.set_editor_property('bloom_intensity', 0.0)
st.set_editor_property('override_motion_blur_amount', True)
st.set_editor_property('motion_blur_amount', 0.0)
ppv.set_editor_property('settings', st)
print('LOOK_Post restored: AEM_Manual ISO 800 shutter 60 fstop 4 bloom 0')
les.save_current_level()
