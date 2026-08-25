"""Open the Blueprint editor for BP_Parcel.

The Components panel lives in the Blueprint editor, which is a separate window
from the level editor - the walkthrough said "double-click BP_Parcel" without
saying where to find it.
"""
import unreal
aes = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
paths = ['/Game/Stacktown/Runtime/BP_Parcel',
         '/Game/Stacktown/Runtime/DA_Catalogue']
assets = [unreal.load_asset(p) for p in paths]
assets = [a for a in assets if a]
aes.open_editor_for_assets(assets)
print('opened editors for: %s' % ', '.join(a.get_name() for a in assets))
