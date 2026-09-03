"""Clear the dirty flag on the flagship's master by reloading it from disk.

    ./Tools/rung.sh reload_shared.py        (guarded by reload_shared_check.py)

WHY THIS EXISTS. Direction B edited M_StacktownMaster and reverted the edit
fully: 195 expressions, BaseColor back on LinearInterpolate_3, Multiply_1 pin
B back on EdgeWearLift, all read back. The CONTENT is correct. But the dirty
flag survives a revert, and while it is set any save-all re-serialises the
flagship's master and lands a changed LFS oid in the repo - a flagship asset
change committed by the wooden-city lane, arriving as a side effect of
somebody else's tidy-up.

"The content is back" and "the asset is clean" are different facts. The first
was verified and reported as though it settled the second.

THIS WRITES NOTHING. Reloading discards the in-memory copy and restores disk
truth, which is why it is safe and why the lane that set the flag clears it.

THE GUARD IS NOT IN THIS FILE. reload_shared_check.py runs the equivalence
check from outside using tools this lane has proven - get_expressions and
get_property_input - because the in-editor Python API for counting material
expressions is not one this lane has verified, and a guard that silently
returns None is not a guard. Run the check first; it refuses if the in-memory
copy holds anything real.
"""
import unreal
import _path  # noqa: F401

ASSET = '/Game/Stacktown/Materials/M_StacktownMaster'

# EditorAssetLibrary has no reload in this build; the entry point is
# EditorLoadingAndSavingUtils.reload_packages, which takes PACKAGES, not
# asset paths, and an interaction mode. LOAD_ALL_CHANGED is the
# non-interactive one - an interactive mode would sit waiting on a dialog
# nobody is watching.
if not hasattr(unreal.EditorLoadingAndSavingUtils, 'reload_packages'):
    raise SystemExit(
        'no reload entry point found. Do NOT work around this by saving the '
        'asset - that is the exact outcome this script exists to prevent.')

mat = unreal.load_asset(ASSET)
if mat is None:
    raise SystemExit('no asset at %s' % ASSET)
pkg = mat.get_outermost()
print('reloading package %s' % pkg.get_name())
unreal.EditorLoadingAndSavingUtils.reload_packages(
    [pkg], unreal.ReloadPackagesInteractionMode.ASSUME_POSITIVE)
print('reloaded - now run reload_shared_check.py --after')
