"""Stage 1 materials. Paper-model language: cut edges and proud band courses
read LIGHTER than the printed faces, which is the core material cue in the
reference photo. Roles stay inside the MASTER_MATERIAL_SPEC vocabulary."""
import ue, json

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
F = '/Game/Stacktown/Materials'
PARENT = {'refPath': F + '/M_StacktownMaster.M_StacktownMaster'}

NEW = {
    'MI_wood':         dict(c=(0.32, 0.24, 0.17), rmin=0.40, rmax=0.55, met=0.0, spec=0.4),
    'MI_paint_accent': dict(c=(0.29, 0.38, 0.26), rmin=0.40, rmax=0.55, met=0.0, spec=0.4),
}
for name, p in NEW.items():
    if 'true' in ue.tool(AS, 'exists', {'path': F + '/' + name}):
        print('exists', name)
        continue
    r = ue.tool(MI, 'create', {'folder_path': F, 'asset_name': name, 'parent': PARENT})
    ref = json.loads(r)['returnValue']
    ue.tool(MI, 'set_vector_parameter', {'instance': ref, 'name': 'BaseColour',
            'value': {'r': p['c'][0], 'g': p['c'][1], 'b': p['c'][2], 'a': 1.0}})
    for pn, v in (('RoughMin', p['rmin']), ('RoughMax', p['rmax']),
                  ('Metallic', p['met']), ('Specular', p['spec'])):
        ue.tool(MI, 'set_scalar_parameter', {'instance': ref, 'name': pn, 'value': v})
    print('created', name)
ue.tool(AS, 'save_assets', {'asset_paths': [F + '/' + n for n in NEW]})

CREAM, CONC, DARK, GLASS = 'MI_paint_cream', 'MI_concrete', 'MI_dark_metal', 'MI_glass'
BOARD, GREY, WOOD, LEAF = 'MI_model_board', 'MI_studio_grey', 'MI_wood', 'MI_paint_accent'

EXACT = {
    'Core': CONC, 'RearWall': CONC, 'Header': CONC, 'RoofDeck': CONC,
    'BandCourse': CREAM,                      # proud paper edge - lighter
    'ParapetFront': CONC, 'ParapetL': CONC, 'ParapetR': CONC,
    'ParapetCap': CREAM,                      # cut edge - lighter
    'RooftopUnit': CONC, 'RooftopVent': DARK,
    'Plinth': CONC, 'PierL': CONC, 'PierR': CONC, 'PierMid': CONC,
    'Bulkhead': CREAM,
    'ShopGlassL': GLASS, 'ShopGlassR': GLASS, 'DoorGlass': GLASS,
    'ShopSillL': CREAM, 'ShopSillR': CREAM,
    'ShopInteriorL': DARK, 'ShopInteriorR': DARK,
    'ShopTransomL': DARK, 'ShopTransomR': DARK,
    'EntranceJambL': DARK, 'EntranceJambR': DARK, 'EntranceHead': DARK,
    'CanopySlab': CREAM, 'CanopyFascia': CREAM, 'CanopyUnder': CREAM,
    'Slab': DARK, 'RailTop': DARK, 'Stringer': DARK,
    'Sidewalk': CONC, 'CurbFace': CREAM, 'Road': GREY,
    'Trunk': WOOD, 'TrunkFork': WOOD,
    'CanopyA': LEAF, 'CanopyB': LEAF, 'CanopyC': LEAF,
    'CanopyD': LEAF, 'CanopyE': LEAF,
    'Grate': DARK,
    'BoardTop': BOARD, 'BoardPlinth': BOARD,
    'Card': GREY, 'Ground': GREY,
}
PREFIX = [('Pier', CONC), ('Glass', GLASS), ('Reveal', DARK), ('Rib', DARK),
          ('Post', DARK), ('Landing', DARK), ('Rail', DARK), ('Stair', DARK),
          ('Frm', DARK), ('Mul', DARK), ('ShopMul', DARK)]     # window frame + mullion grid


def pick(n):
    if n in EXACT:
        return EXACT[n]
    for p, m in PREFIX:
        if n.startswith(p):
            return m
    return None


acts = json.loads(ue.tool(S, 'find_actors',
                          {'name': '', 'tag': '', 'collision_channels': []}))['returnValue']
done, miss = 0, []
for a in acts:
    ref = a if isinstance(a, dict) else {'refPath': a}
    lbl = json.loads(ue.tool(A, 'get_label', {'actor': ref}))['returnValue']
    if not lbl.startswith(('BLD_', 'STAGE_', 'PROP_')):
        continue
    for c in json.loads(ue.tool(A, 'get_components', {'actor': ref}))['returnValue']:
        cn = c['refPath'].split('.')[-1]
        m = pick(cn)
        if m is None:
            if 'Billboard' not in cn and 'Scene' not in cn:
                miss.append(lbl + '/' + cn)
            continue
        ue.tool(O, 'set_properties', {'instance': c, 'values': json.dumps(
            {'OverrideMaterials': [{'refPath': '%s/%s.%s' % (F, m, m)}]})})
        done += 1
print('assigned %d components' % done)
print('UNASSIGNED (%d): %s' % (len(miss), miss[:12]))
