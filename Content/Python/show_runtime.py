"""Rescan and jump the Content Browser to the runtime assets.

They were made by Python, so the Content Browser may not have noticed them.
Also probe whether graph NODES can be authored - if K2Node classes are exposed
and a graph can be edited, the manual wiring goes away entirely.
"""
import unreal
RT = '/Game/Stacktown/Runtime'
ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.scan_paths_synchronous([RT, '/Game/Stacktown/Baked'], force_rescan=True)
found = [str(a.package_name) for a in ar.get_assets_by_path(RT, recursive=True)]
print('registry sees: %s' % ', '.join(sorted(p.split('/')[-1] for p in found)))
objs = [unreal.load_asset(p) for p in found]
objs = [o for o in objs if o]
if objs:
    unreal.EditorAssetLibrary.sync_browser_to_objects([o.get_path_name() for o in objs])
    print('content browser synced to %d assets' % len(objs))

print('--- can graph nodes be authored? ---')
for n in ('K2Node_CallFunction', 'K2Node_VariableGet', 'K2Node_IfThenElse',
          'KismetEditorUtilities', 'EdGraph', 'BlueprintGraphLibrary'):
    print('  %-28s %s' % (n, 'present' if getattr(unreal, n, None) else 'MISSING'))
bp = unreal.load_asset('%s/BP_Parcel' % RT)
try:
    graphs = bp.get_editor_property('ubergraph_pages')
    print('  ubergraph pages readable: %s' % bool(graphs))
except Exception as e:
    print('  ubergraph pages: %s' % str(e)[:80])
