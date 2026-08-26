"""Three mural paints that actually read against a cream wall.

The first mural used MI_card_ochre / rose / sage and vanished. Measured
against MI_paint_cream (0.780, 0.748, 0.678) their smallest per-channel
deltas are 0.020, 0.040 and 0.163 - the card palette is a family of pale
tinted whites designed to sit TOGETHER on a model, not to contrast with each
other. Same mistake as reaching for MI_precast_buff to make gravel.

THE METRIC CHANGED, deliberately. The gravel fix asserted a minimum
per-channel delta of 0.25, which was right for two neutral greys where any
difference has to come from lightness. Paint on a wall is a different problem:
a deep teal and a cream wall can share a channel and still read from across a
street, because what separates them is LUMINANCE and hue. So this asserts
luminance contrast against the wall, and Euclidean separation between the
three so the blocks read as three colours rather than a smudge.

Built from MI_paint_cream so every card parameter - paper fibre, roughness
band, seam chain, wear - is identical to the wall it is painted on. It is
paint on that wall, not a different material stuck to it.
"""
import unreal

SRC = '/Game/Stacktown/Materials/MI_paint_cream'
WALL = (0.780, 0.748, 0.678)
MURALS = {
    'MI_mural_a': (0.620, 0.255, 0.110),   # rust
    'MI_mural_b': (0.145, 0.395, 0.420),   # teal
    # NOT a mustard. (0.720, 0.520, 0.130) failed the separation assert at
    # 0.284 against the rust - two oranges reading as one smudge. A cream wall
    # sits at luminance 0.75, so anything bright enough to be a third colour
    # is also close to the wall; the three have to spread around the wheel
    # instead of along it.
    'MI_mural_c': (0.330, 0.120, 0.300),   # plum
}
MIN_LUM = 0.20     # against the wall
MIN_SEP = 0.30     # between any two mural colours


def lum(c):
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]


def dist(a, b):
    return sum((x - y)**2 for x, y in zip(a, b)) ** 0.5


mel = unreal.MaterialEditingLibrary
wl = lum(WALL)
for name, col in sorted(MURALS.items()):
    path = '/Game/Stacktown/Materials/%s' % name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    if not unreal.EditorAssetLibrary.duplicate_asset(SRC, path):
        raise SystemExit('could not duplicate %s' % SRC)
    mi = unreal.load_asset(path)
    mel.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    # paint on rendered brick is flatter than the painted card around it
    mel.set_material_instance_scalar_parameter_value(mi, 'RoughMin', 0.70)
    mel.set_material_instance_scalar_parameter_value(mi, 'RoughMax', 0.86)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    d = abs(lum(col) - wl)
    print('%-12s (%.3f %.3f %.3f)  lum %.3f  vs wall %.3f  delta %.3f  %s'
          % (name, col[0], col[1], col[2], lum(col), wl, d,
             'reads' if d >= MIN_LUM else 'TOO CLOSE'))
    if d < MIN_LUM:
        raise AssertionError('%s does not separate from the wall (%.3f < %.3f)'
                             % (name, d, MIN_LUM))

keys = sorted(MURALS)
for i in range(len(keys)):
    for j in range(i+1, len(keys)):
        sep = dist(MURALS[keys[i]], MURALS[keys[j]])
        print('  %s vs %s  separation %.3f  %s'
              % (keys[i][-1], keys[j][-1], sep,
                 'ok' if sep >= MIN_SEP else 'TOO CLOSE'))
        if sep < MIN_SEP:
            raise AssertionError('%s and %s read as one colour'
                                 % (keys[i], keys[j]))
print('OK: three mural paints, each readable on the wall and against each other')
