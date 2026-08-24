"""Stage 1 print pass.

At ~95 m the camera resolves nothing finer than ~4 px, so surface grain is
invisible and adding it would be wasted (and MASTER_MATERIAL_SPEC forbids
large-scale albedo variation anyway - "the trap"). Print character at this
framing is tonal separation and line work at PANEL scale.

Two concrete problems in the current frame:
  1. Window frames/mullions and the interior cards both used MI_dark_metal, so
     each window read as one black mass with no printed frame inside it.
  2. Every floor's glazing was identical. The paper reference varies window
     treatment floor to floor, and that variation is a printed characteristic,
     not weathering.
"""
import unreal

F = '/Game/Stacktown/Materials'
MASTER = unreal.EditorAssetLibrary.load_asset(F + '/M_StacktownMaster.M_StacktownMaster')
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def instance(name, colour, rmin, rmax, met=0.0, spec=0.5, opacity=None):
    path = '%s/%s' % (F, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = unreal.EditorAssetLibrary.load_asset(path + '.' + name)
    else:
        at = unreal.AssetToolsHelpers.get_asset_tools()
        mi = at.create_asset(name, F, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', MASTER)
    L = unreal.MaterialEditingLibrary
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(colour[0], colour[1], colour[2], 1.0))
    for k, v in (('RoughMin', rmin), ('RoughMax', rmax),
                 ('Metallic', met), ('Specular', spec)):
        L.set_material_instance_scalar_parameter_value(mi, k, v)
    if opacity is not None:
        L.set_material_instance_scalar_parameter_value(mi, 'Opacity', opacity)
        mi.set_editor_property('base_property_overrides', _translucent())
    unreal.EditorAssetLibrary.save_asset(path)
    return mi


def _translucent():
    o = unreal.MaterialInstanceBasePropertyOverrides()
    o.set_editor_property('override_blend_mode', True)
    o.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    return o


# printed frame line - mid grey, reads against BOTH the white wall and the
# dark interior. Previously these were near-black and vanished into the glass.
frame = instance('MI_frame_print', (0.30, 0.30, 0.31), 0.32, 0.46, 0.15, 0.45)
# blocked-in interior - near black, so the glazing reads deep behind the frame
interior = instance('MI_interior', (0.030, 0.032, 0.036), 0.45, 0.60)
# second glazing tone for floor-to-floor variation
glass_b = instance('MI_glass_b', (0.085, 0.080, 0.062), 0.02, 0.08,
                   0.0, 1.0, opacity=0.34)
glass_a = unreal.EditorAssetLibrary.load_asset(F + '/MI_glass.MI_glass')
print('instances ready: frame_print, interior, glass_b')

FRAME_PREFIX = ('Frm', 'Mul', 'ShopMul', 'ShopTransom')
INTERIOR_EXACT = {'ShopInteriorL', 'ShopInteriorR'}
counts = {'frame': 0, 'interior': 0, 'glass_a': 0, 'glass_b': 0}

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith(('BLD_',)):
        continue
    floor = None
    if lbl.startswith('BLD_Floor_'):
        floor = int(lbl.rsplit('_', 1)[1])
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_name()
        if n.startswith(FRAME_PREFIX):
            c.set_editor_property('override_materials', [frame])
            counts['frame'] += 1
        elif n in INTERIOR_EXACT or n.startswith('Reveal'):
            c.set_editor_property('override_materials', [interior])
            counts['interior'] += 1
        elif n.startswith('Glass') and floor is not None:
            # alternate glazing tone by floor, as the reference does
            use_b = floor % 2 == 0
            c.set_editor_property('override_materials', [glass_b if use_b else glass_a])
            counts['glass_b' if use_b else 'glass_a'] += 1

print('reassigned: %d frame lines, %d interiors, %d glass A, %d glass B'
      % (counts['frame'], counts['interior'], counts['glass_a'], counts['glass_b']))
les.save_current_level()
print('saved')
