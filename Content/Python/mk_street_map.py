"""Create the street's own map as an ASSET COPY - never by loading.

Same reasoning as mk_sandbox.py, which is the proven pattern here:
`load_level` and `new_level` both switch the current world out from under the
running Python session and crash this editor over remote execution.
`duplicate_asset` copies the package on disk and leaves the open level alone.

WHY A SEPARATE MAP. The street and the catalogue review shelf were sharing
Sandbox_Bench - 19 street actors against 249 actors of workshop furniture.
That forced the block rig's attenuation radius down to keep it from relighting
the bench, which cost the street's far end light and drew a visible circular
falloff edge across the board (POLISH_BACKLOG S5, S8). Two rooms, two jobs.

Sandbox_Bench is the source because it already carries the street, the board,
the backdrop and both light rigs. streetroom.py then strips the furniture out
of the COPY - and refuses to run anywhere but in the copy, because the same
purge pointed at the bench would destroy the shelf.
"""
import unreal

SRC = '/Game/Maps/Sandbox_Bench'
DST = '/Game/Maps/Stage2_Street'
eal = unreal.EditorAssetLibrary
if eal.does_asset_exist(DST):
    print('street map already exists at %s' % DST)
else:
    if not eal.does_asset_exist(SRC):
        raise SystemExit('no source map at %s' % SRC)
    ok = eal.duplicate_asset(SRC, DST)
    print('created %s from %s: %s' % (DST, SRC, bool(ok)))
    eal.save_asset(DST, only_if_is_dirty=False)
print('current level is untouched - open %s by hand to work in it' % DST)
