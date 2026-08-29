"""Import the CC0 Poly Haven brick candidates, settings baked at the gate.

FULLY VERSIONED, no custody gap. These arrive with PROVENANCE.md naming the
asset pages and the CC0 licence, so unlike the pack brick they can live in
Content/Stacktown/Textures and carry their import settings in the repo. The
fresh-clone regression that made a backwards brick invisible cannot recur for
these.

THE GREEN CHECK IS THE POINT, and it happens HERE, at admission. Both files
are nor_gl - OpenGL green, green=up - and UE samples DirectX. Left alone they
would render exactly the defect they were brought in to replace: brick faces
recessed, mortar proud. flip_green_channel is set at import and the result is
verified BY LOOKING at lit coursing, because the detail metric is
direction-blind and reads an inverted map identically (measured: 2.39/1.24
either way).
"""
import os
import unreal

SRC = os.path.join(unreal.Paths.project_dir(), 'Tools', 'textures', 'source', 'polyhaven')
DEST = '/Game/Stacktown/Textures'
FILES = ['brick_wall_001_nor_gl_2k.png', 'brick_wall_02_nor_gl_2k.png']


def main():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for fn in FILES:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            raise SystemExit('missing source: %s' % p)
        name = 'T_' + fn.replace('_nor_gl_2k.png', '') + '_N'
        dst = '%s/%s' % (DEST, name)
        if unreal.EditorAssetLibrary.does_asset_exist(dst):
            unreal.EditorAssetLibrary.delete_asset(dst)
        data = unreal.AutomatedAssetImportData()
        data.set_editor_property('destination_path', DEST)
        data.set_editor_property('filenames', [p])
        data.set_editor_property('replace_existing', True)
        got = tools.import_assets_automated(data)
        if not got:
            raise SystemExit('import produced nothing for %s' % fn)
        t = got[0]
        if t.get_name() != name:
            unreal.EditorAssetLibrary.rename_asset(
                t.get_path_name().split('.')[0], dst)
            t = unreal.load_asset(dst)
        t.set_editor_property('srgb', False)
        t.set_editor_property('compression_settings',
                              unreal.TextureCompressionSettings.TC_NORMALMAP)
        # nor_gl -> UE samples DirectX: flip at the gate
        t.set_editor_property('flip_green_channel', True)
        unreal.EditorAssetLibrary.save_asset(dst)
        print('  IMPORTED %-26s %dx%d srgb=%s flip_green=%s comp=%s'
              % (t.get_name(), t.blueprint_get_size_x(), t.blueprint_get_size_y(),
                 t.get_editor_property('srgb'),
                 t.get_editor_property('flip_green_channel'),
                 str(t.get_editor_property('compression_settings')).split('.')[-1][:12]))


if __name__ == '__main__':
    main()
