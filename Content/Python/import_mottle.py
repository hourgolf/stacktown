"""Import the generated mottle PNG as T_PaperMottle and bind it to the COARSE
octave's three samplers.

RUN LOCALLY is NOT required here - this uses the unreal module directly, so it
runs through uepy.

TWO PARAMETER NAMES, WHICH IS THE WHOLE POINT. All six samplers were called
PaperNormal, so any instance setting that parameter moved both octaves at
once and the coarse octave could never be given its own map. The three coarse
samplers become PaperMottle; the three fine ones keep PaperNormal. Existing
instances that set PaperNormal therefore now address the FINE octave only,
which is the correct half - the wall showed the fine octave at ~0.024 is what
reads as card.

The texture is a NORMAL MAP and must not be sRGB-decoded; getting that wrong
produces a washed, wrongly-signed perturbation that looks like a lighting bug.
"""
import os
import unreal

PNG = os.path.join(unreal.Paths.project_dir(), 'Saved', 'Textures', 'T_PaperMottle.png')
DEST = '/Game/Stacktown/Textures'
NAME = 'T_PaperMottle'
MASTER = '/Game/Stacktown/Materials/M_StacktownMaster'
COARSE = ('MaterialExpressionTextureSampleParameter2D_2',
          'MaterialExpressionTextureSampleParameter2D_3',
          'MaterialExpressionTextureSampleParameter2D_4')


def main():
    if not os.path.exists(PNG):
        raise SystemExit('run Tools/textures/mk_mottle.py first: %s' % PNG)
    path = '%s/%s' % (DEST, NAME)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    data = unreal.AutomatedAssetImportData()
    data.set_editor_property('destination_path', DEST)
    data.set_editor_property('filenames', [PNG])
    data.set_editor_property('replace_existing', True)
    got = unreal.AssetToolsHelpers.get_asset_tools().import_assets_automated(data)
    if not got:
        raise SystemExit('import produced nothing')
    tex = got[0]
    tex.set_editor_property('srgb', False)
    tex.set_editor_property('compression_settings',
                            unreal.TextureCompressionSettings.TC_NORMALMAP)
    unreal.EditorAssetLibrary.save_asset(path)
    print('IMPORTED %s  %dx%d  srgb=%s'
          % (tex.get_name(), tex.blueprint_get_size_x(), tex.blueprint_get_size_y(),
             tex.get_editor_property('srgb')))
    # IMPORT DELETES, AND DELETING NULLS EVERY REFERENCE THE MASTER HOLDS.
    # A null sampler renders black: the five-octave sweep measured exactly
    # that and returned 0.37-1.60 across every panel, which reads as "the new
    # map carries nothing" rather than "the script broke its own reference".
    # Re-binding is MCP-side and this file is unreal-module-side, so it lives
    # in rebind_mottle.py. ALWAYS RUN BOTH, in this order.
    print('MOTTLEPATH %s.%s' % (path, NAME))


if __name__ == '__main__':
    main()
