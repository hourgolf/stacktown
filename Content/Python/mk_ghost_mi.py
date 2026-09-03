"""D22's two ghost instances. Needs an editor grant; creation only, no swap.

    ./Tools/rung.sh mk_ghost_mi.py

MI_ghost_accept   uncarved board: the road inlay's tone, translucent, proud rim
MI_ghost_refuse   an empty red outline - no fill

WHY THE BLEND-MODE OVERRIDE IS THE WHOLE JOB. Blend mode lives on the MASTER,
and M_WoodMaster is BLEND_Opaque. Setting an Opacity value on an instance of
an opaque master does nothing: it sets, it reads back, and it draws a solid
block - the same "reads as set, draws nothing" shape as the CPD failure D22
routes around. So each instance carries bOverride_BlendMode with
BLEND_Translucent, and only then does the master's already-connected Opacity
parameter do real work.

Checked before writing this: M_WoodMaster's MP_Opacity IS connected, driven by
the Opacity ScalarParameter. The fork needs no change.

THE OVERRIDE IS ASSERTED THREE TIMES, AND THE THIRD ONE IS THE REAL TEST.
In-memory after setting it; again after an explicit-path save; and again after
the package is RELOADED FROM DISK. Only the third proves the flag survived
serialisation - a property that sticks on the live object and not in the saved
asset is the identical failure one editor restart later, and `load_asset` after
a save hands back the same in-memory object, so it cannot see the difference.
The reload route is EditorLoadingAndSavingUtils.reload_packages (HANDOFF §5).

VALUES ARE D22's AND ARE A FIRST PASS. Opacity and the rim are the two numbers
most likely wrong, and neither is judgeable from arithmetic - the proof is a
measured frame at the far stop and a close stop. A ghost that is not
see-through is not a ghost, and that is what the frame catches.
"""
import unreal
import _path  # noqa: F401

FORK = '/Game/Stacktown/Materials/M_WoodMaster'
DEST = '/Game/Stacktown/Materials'

# (name, base colour sRGB, opacity)  - D22
GHOSTS = [
    ('MI_ghost_accept', (0.874, 0.839, 0.788), 0.34),   # #DFD6C9, the inlay
    ('MI_ghost_refuse', (0.706, 0.278, 0.180), 0.00),   # #B4472E, no fill
]


def _translucent(mi):
    """True only if this instance really overrides blend mode to translucent.
    Both halves are checked: an override VALUE with the flag off is inert."""
    if mi is None:
        return False
    ov = mi.get_editor_property('base_property_overrides')
    return bool(ov.get_editor_property('override_blend_mode')) and \
        ov.get_editor_property('blend_mode') == unreal.BlendMode.BLEND_TRANSLUCENT


def main():
    parent = unreal.load_asset(FORK)
    if parent is None:
        raise SystemExit('no fork at %s - run fork.py --fork first' % FORK)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for name, rgb, opacity in GHOSTS:
        path = '%s/%s' % (DEST, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            mi = unreal.load_asset(path)
        else:
            mi = at.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
            mi.set_editor_property('parent', parent)
        # the override, without which the opacity is decorative
        ov = mi.get_editor_property('base_property_overrides')
        ov.set_editor_property('override_blend_mode', True)
        ov.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        mi.set_editor_property('base_property_overrides', ov)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, 'Opacity', opacity)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            mi, 'BaseTint', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        unreal.MaterialEditingLibrary.update_material_instance(mi)
        if not _translucent(mi):
            raise SystemExit('%s: override did not stick in memory' % name)
        made.append((name, path, opacity))

    # SAVE, then prove it survived. Explicit paths only - never save_assets([]).
    paths = [p for _, p, _ in made]
    if not unreal.EditorAssetLibrary.save_loaded_assets(
            [unreal.load_asset(p) for p in paths], False):
        raise SystemExit('save refused')
    for name, path, _ in made:
        if not _translucent(unreal.load_asset(path)):
            raise SystemExit('%s: override lost on save' % name)

    # THE ONE THAT MATTERS: round-trip through disk. load_asset after a save
    # returns the same in-memory object and cannot see a serialisation loss.
    pkgs = [unreal.load_asset(p).get_outermost() for p in paths]
    unreal.EditorLoadingAndSavingUtils.reload_packages(
        pkgs, unreal.ReloadPackagesInteractionMode.ASSUME_POSITIVE)
    for name, path, _ in made:
        fresh = unreal.load_asset(path)
        if fresh is None:
            raise SystemExit('%s: gone after reload' % name)
        if not _translucent(fresh):
            raise SystemExit(
                '%s: BLEND MODE LOST THROUGH DISK. The override held in memory '
                'and did not serialise - do NOT ship this; the ghost would be '
                'translucent this session and a solid block the next.' % name)
        op = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
            fresh, 'Opacity')
        print('  %-18s %s  opacity %.2f  translucent AFTER DISK ROUND-TRIP'
              % (name, path, op))
    print('CREATED %d and proven through disk. Driver swap is the beta lane\'s; '
          'look acceptance is a measured frame at the far stop and a close '
          'stop - a ghost that is not see-through is not a ghost.' % len(made))


main()
