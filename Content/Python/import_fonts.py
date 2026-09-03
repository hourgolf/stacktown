"""Import the OFL fonts the HUD calls for, as Font Face + Font assets.

    ./Tools/rung.sh import_fonts.py

Sources and licences are in Tools/fonts/source/googlefonts/PROVENANCE.md,
downloaded 2026-09-02 at the owner's explicit word.

ONLY WHAT THE HUD USES IS IMPORTED. The owner chose Tomorrow over Six Caps
after a side by side, so Six Caps is not imported; Erica One is not imported
either - it is a poster face whose home is a title card, not a thin bar
(DIRECTION_B_HUD.md section 3). Both stay in the repo as sources. Importing
every downloaded file would leave two unused Font assets in the content
browser looking like part of the HUD.

NO UFont WRAPPER IS NEEDED, which the first attempt got wrong. SlateFontInfo
takes the FontFace directly - `SlateFontInfo(font_object=<FontFace>, size=N)`
binds and reads back - so the imported FontFace IS the asset the beta lane
assigns. The first pass tried to build a UFont around each face and died on
unreal.TypefaceEntry, which is not exposed to Python; the wrapper was never
required. SlateFontInfo also carries `letter_spacing`, so the spec's +0.03em
on the Tomorrow labels is set in code with everything else.
"""
import os
import unreal
import _path  # noqa: F401

SRC = os.path.join(unreal.Paths.project_dir(), 'Tools', 'fonts', 'source',
                   'googlefonts')
DEST = '/Game/Stacktown/UI/Fonts'

# (source file, asset name). Names match DIRECTION_B_HUD.md's CODE STYLES half.
FONTS = [
    ('Tomorrow-Regular.ttf',  'F_Tomorrow_Regular'),
    ('Tomorrow-Medium.ttf',   'F_Tomorrow_Medium'),
    ('Tomorrow-SemiBold.ttf', 'F_Tomorrow_SemiBold'),
    ('SpaceMono-Bold.ttf',    'F_SpaceMono_Bold'),
]


def main():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for fn, name in FONTS:
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            raise SystemExit('missing source: %s' % src)
        dst = '%s/%s' % (DEST, name)
        # The first attempt created empty UFont assets at these paths before
        # it died on TypefaceEntry. They are debris from a wrong theory, not
        # content: clear them rather than import around them, or the name the
        # spec points at resolves to an empty Font forever.
        if unreal.EditorAssetLibrary.does_asset_exist(dst):
            existing = unreal.load_asset(dst)
            if existing is not None and \
                    existing.get_class().get_name() != 'FontFace':
                print('  clearing stray %s at %s'
                      % (existing.get_class().get_name(), dst))
                unreal.EditorAssetLibrary.delete_asset(dst)
        if not unreal.EditorAssetLibrary.does_asset_exist(dst):
            # a first pass named these <name>_Face before it was clear the
            # FontFace IS the asset SetFont wants; adopt any it left behind
            stale = dst + '_Face'
            if unreal.EditorAssetLibrary.does_asset_exist(stale):
                unreal.EditorAssetLibrary.rename_asset(stale, dst)
            else:
                data = unreal.AutomatedAssetImportData()
                data.set_editor_property('destination_path', DEST)
                data.set_editor_property('filenames', [src])
                data.set_editor_property('replace_existing', True)
                got = tools.import_assets_automated(data)
                if not got:
                    raise SystemExit('import produced nothing for %s' % fn)
                cur = got[0].get_path_name().split('.')[0]
                if cur != dst:
                    unreal.EditorAssetLibrary.rename_asset(cur, dst)
        face = unreal.load_asset(dst)
        if face is None or face.get_class().get_name() != 'FontFace':
            raise SystemExit('not a FontFace at %s: %r' % (dst, face))
        # prove the thing the beta lane will actually construct
        info = unreal.SlateFontInfo(font_object=face, size=20)
        if info.get_editor_property('font_object') != face:
            raise SystemExit('SlateFontInfo would not bind %s' % name)
        made.append((name, dst))

    print('IMPORTED %d font faces' % len(made))
    for name, path in made:
        print('  %-22s %s' % (name, path))
    print('NOT imported, deliberately: Six Caps (the owner chose Tomorrow), '
          'Erica One (title card, not HUD), SpaceMono-Regular')


main()
