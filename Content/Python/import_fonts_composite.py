"""Fallback: re-import the fonts so the ENGINE builds the UFont wrapper.

    ./Tools/rung.sh import_fonts_composite.py

WHY THIS EXISTS. The HUD renders every glyph as the missing-glyph box, and
one candidate is that a raw UFontFace does not draw through SlateFontInfo in
this build even though it assigns and reads back. The composite route needs a
UFont, and the earlier attempt to build one in Python died on
unreal.TypefaceEntry, which is not exposed.

THERE IS A WAY ROUND THAT AND IT IS NOT A CLICK PATH: FontFileImportFactory
carries `batch_create_font_asset`, so the ENGINE creates the UFont alongside
the FontFace at import. Nothing has to construct a Typeface by hand.

WHAT WAS ALREADY RULED OUT, by measurement rather than theory: the font data
IS embedded. LoadingPolicy reads LazyLoad, which sounds like the culprit, but
each .uasset is its .ttf plus about 1.5 KB (F_Tomorrow_Regular 61,091 vs
59,520; F_SpaceMono_Bold 99,789 vs 98,232). Nothing is being streamed from
the source path at draw time, so "the face never loaded its data" is not the
explanation and this script does not pretend it is.

RUN THIS ONLY IF THE BETA LANE'S DIAGNOSIS POINTS AT THE FACE ITSELF. If the
cause is on the SlateFontInfo side - a typeface_font_name that resolves to
nothing being the cheapest candidate - a second set of assets fixes nothing
and leaves eight fonts where four belong.
"""
import os
import unreal
import _path  # noqa: F401

SRC = os.path.join(unreal.Paths.project_dir(), 'Tools', 'fonts', 'source',
                   'googlefonts')
DEST = '/Game/Stacktown/UI/Fonts'
FILES = ['Tomorrow-Regular.ttf', 'Tomorrow-Medium.ttf',
         'Tomorrow-SemiBold.ttf', 'SpaceMono-Bold.ttf']


def main():
    factory = unreal.FontFileImportFactory()
    factory.set_editor_property('batch_create_font_asset',
                                unreal.BatchCreateFontAsset.YES)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    before = set(unreal.EditorAssetLibrary.list_assets(DEST, recursive=True))
    for fn in FILES:
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            raise SystemExit('missing source: %s' % src)
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', src)
        task.set_editor_property('destination_path', DEST)
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', False)
        task.set_editor_property('save', False)
        task.set_editor_property('factory', factory)
        tools.import_asset_tasks([task])
    after = set(unreal.EditorAssetLibrary.list_assets(DEST, recursive=True))
    new = sorted(after - before)
    print('new assets: %d' % len(new))
    fonts = []
    for p in new:
        a = unreal.load_asset(p.split('.')[0])
        cls = a.get_class().get_name() if a else '?'
        print('   %-34s %s' % (p.split('.')[0].split('/')[-1], cls))
        if cls == 'Font':
            fonts.append(p.split('.')[0])
    if not fonts:
        print('NO UFont produced - batch_create_font_asset did not fire. Do '
              'not hand-build one; report it and use the content-browser '
              'route instead.')
    else:
        print('UFont assets for SetFont: %s' % fonts)


main()
