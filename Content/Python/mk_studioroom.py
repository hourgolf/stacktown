"""The studio room around the street: four walls + floor, SELF-LIT.

Replaces the scratch-spawned room (design session, 2026-08-30) with a
committed, rerunnable build - same bounds, different light treatment:

  - M_StudioWall is UNLIT emissive (a sound-stage cyclorama). Unlit
    ignores every light in the level, and use_emissive_for_dynamic_area_
    lighting=False keeps its emission OUT of Lumen GI - so the room is
    visible from every angle while contributing PROVABLY ZERO light to
    the model board. The fill lights it replaces reached the board
    (W fill 13,691 uu from street centre against a 30,000 attenuation -
    caught by the design session's own arithmetic), which is why
    self-lit is the right mechanism, not just a taste.
  - The west wall stays at x=-3000 DELIBERATELY: it keeps the ACCEPT
    rigs (x -20000..-6000) outside the room so bench apparatus cannot
    float into a read framing. Keep that constraint in any resize.
  - Deletes LIGHT_RoomFill_* if present. Idempotent; does not save.

Room bounds (design session's, preserved): x -3000..35000,
y -52000..-16000, floor top -400 (under the board's -268, no z-fight).
"""
import unreal

MEL = unreal.MaterialEditingLibrary
FOLDER = '/Game/Stacktown/Materials'
GREY = (0.135, 0.145, 0.165)   # dim studio blue-grey, tuned by eye
BRIGHT = 0.55

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print('level:', w.get_name())
assert w.get_name() == 'Sandbox_Bench', 'wrong level loaded - abort'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()

# --- material: unlit emissive, zero GI contribution -------------------------
MAT = FOLDER + '/M_StudioWall'
if eal.does_asset_exist(MAT):
    mat = eal.load_asset(MAT)
    for e in list(MEL.get_material_expressions(mat) or []):
        MEL.delete_material_expression(mat, e)
else:
    mat = at.create_asset('M_StudioWall', FOLDER, unreal.Material,
                          unreal.MaterialFactoryNew())
mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property('use_emissive_for_dynamic_area_lighting', False)
col = MEL.create_material_expression(
    mat, unreal.MaterialExpressionVectorParameter, -500, 0)
col.set_editor_property('parameter_name', 'WallColor')
col.set_editor_property('default_value',
                        unreal.LinearColor(GREY[0], GREY[1], GREY[2], 1.0))
br = MEL.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -500, 200)
br.set_editor_property('parameter_name', 'Brightness')
br.set_editor_property('default_value', BRIGHT)
mul = MEL.create_material_expression(
    mat, unreal.MaterialExpressionMultiply, -250, 80)
MEL.connect_material_expressions(col, '', mul, 'A')
MEL.connect_material_expressions(br, '', mul, 'B')
MEL.connect_material_property(mul, '',
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(mat)
eal.save_asset(MAT, only_if_is_dirty=False)
print('M_StudioWall compiled (unlit, GI-inert)')

# --- room geometry: ensure the five faces exist with the agreed bounds ------
CUBE = '/Engine/BasicShapes/Cube'
X0, X1, Y0, Y1, Z0, Z1 = -3000.0, 35000.0, -52000.0, -16000.0, -300.0, 20000.0
CX, CY, CZ = (X0+X1)/2, (Y0+Y1)/2, (Z0+Z1)/2
T = 100.0
FACES = {
  'STAGE_BackdropStreet_N': ((CX, Y1, CZ), ((X1-X0)/100, T/100, (Z1-Z0)/100)),
  'STAGE_BackdropStreet_S': ((CX, Y0, CZ), ((X1-X0)/100, T/100, (Z1-Z0)/100)),
  'STAGE_BackdropStreet_E': ((X1, CY, CZ), (T/100, (Y1-Y0)/100, (Z1-Z0)/100)),
  'STAGE_BackdropStreet_W': ((X0, CY, CZ), (T/100, (Y1-Y0)/100, (Z1-Z0)/100)),
  'STAGE_BackdropStreet_Floor': ((CX, CY, -450.0),
                                 ((X1-X0)/100, (Y1-Y0)/100, 1.0)),
}
existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
mesh = eal.load_asset(CUBE)
wallmat = eal.load_asset(MAT)
for name, (loc, scale) in FACES.items():
    a = existing.get(name)
    if a is None:
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(*loc))
        a.set_actor_label(name)
        print('spawned', name)
    a.set_actor_location(unreal.Vector(*loc), False, False)
    a.set_actor_scale3d(unreal.Vector(*scale))
    smc = a.static_mesh_component
    smc.set_static_mesh(mesh)
    for i in range(smc.get_num_materials()):
        smc.set_material(i, wallmat)
    smc.set_editor_property('cast_shadow', False)
print('room faces ensured, all on M_StudioWall, shadows off')

# --- the fills that reached the board go ------------------------------------
n = 0
for lbl, a in existing.items():
    if lbl.startswith('LIGHT_RoomFill'):
        eas.destroy_actor(a)
        n += 1
print('deleted %d contaminating RoomFill light(s)' % n)
print('NOT saved - verification first, save is a separate step')
