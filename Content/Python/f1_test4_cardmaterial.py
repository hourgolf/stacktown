"""F1 test 4 — card material response.

Owner's diagnosis: the optics help, but the MATERIALS are what stop it reading
as a model. Agreed, and there is a specific reason.

MASTER_MATERIAL_SPEC specifies a painted roughness band of 0.35-0.55 with
specular 0.5. That is painted styrene - the look the spec was written for. The
chosen direction is now PRINTED CARD, which is a different material: rougher,
much lower specular, scattering rather than reflecting. A 0.35-0.55 band with
0.5 specular gives a faintly plastic response, and at 95 m roughness and
specular are among the very few material properties that still read at all.

The spec's warning "do not widen to add realism" was aimed at adding grunge and
tonal variation. This is not that - it is retuning the band for a different
physical material, and it stays narrow.

Also sets grain between the moderate and heavy settings the owner compared.
"""
import unreal

F = '/Game/Stacktown/Materials'
L = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# printed card: rougher band, much lower specular. Still narrow (0.16 wide).
CARD = {
    'MI_concrete':    (0.64, 0.80, 0.22),
    'MI_paint_cream': (0.62, 0.78, 0.20),
    'MI_model_board': (0.66, 0.82, 0.18),
    'MI_studio_grey': (0.68, 0.84, 0.16),
    'MI_frame_print': (0.55, 0.72, 0.28),
    'MI_paint_accent': (0.60, 0.76, 0.22),
    'MI_canopy_accent': (0.60, 0.76, 0.22),
    'MI_wood':        (0.62, 0.80, 0.20),
}
for name, (rmin, rmax, spec) in CARD.items():
    p = '%s/%s' % (F, name)
    if not unreal.EditorAssetLibrary.does_asset_exist(p):
        print('  missing', name)
        continue
    mi = unreal.EditorAssetLibrary.load_asset(p + '.' + name)
    L.set_material_instance_scalar_parameter_value(mi, 'RoughMin', rmin)
    L.set_material_instance_scalar_parameter_value(mi, 'RoughMax', rmax)
    L.set_material_instance_scalar_parameter_value(mi, 'Specular', spec)
    unreal.EditorAssetLibrary.save_asset(p)
    print('%-18s rough %.2f-%.2f  spec %.2f' % (name, rmin, rmax, spec))

# grain between moderate (0.80) and heavy (1.45)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
ppv = acts['LOOK_Post']
s = ppv.get_editor_property('settings')
for k, v in (('film_grain_intensity', 1.05),
             ('film_grain_intensity_shadows', 1.25),
             ('film_grain_intensity_midtones', 1.00),
             ('film_grain_intensity_highlights', 0.62)):
    s.set_editor_property(k, v)
ppv.set_editor_property('settings', s)
print('film grain -> 1.05 (between moderate 0.80 and heavy 1.45)')

les.save_current_level()
print('saved')
