"""Create the benchmark sandbox map as an ASSET COPY - never by loading.

`load_level` over remote execution crashes this editor, and the same risk
applies to new_level: both switch the current world out from under the running
Python session. So the map is made with duplicate_asset, which copies the
package on disk and leaves the open level alone.

Stage1_Building is the base because it already carries a stage and a light
rig. Whatever else it contains gets cleared by bench.py the first time that
runs IN the sandbox - which it will only do there, never in Stage2_Block.
"""
import unreal

SRC = '/Game/Maps/Stage1_Building'
DST = '/Game/Maps/Sandbox_Bench'
eal = unreal.EditorAssetLibrary
if eal.does_asset_exist(DST):
    print('sandbox already exists at %s' % DST)
else:
    if not eal.does_asset_exist(SRC):
        raise SystemExit('no source map at %s' % SRC)
    ok = eal.duplicate_asset(SRC, DST)
    print('created %s from %s: %s' % (DST, SRC, bool(ok)))
    eal.save_asset(DST, only_if_is_dirty=False)
print('current level is untouched')
