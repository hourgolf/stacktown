"""The district palette. Cited to CANON slots 1 and 5.

THE TENSION, AND ITS RESOLUTION. MASTER_MATERIAL_SPEC says "Restrained...
roughly four values plus glass", and it is right that palette sprawl killed
the last project. But slot 5 is blessed for KIT-FAMILY COHERENCE: "wildly
different buildings cohering because one fabrication family made them". Its
palette is olive, black, teal, forest, cream, yellow, oxblood - far wider than
four values - and it reads as one model city anyway.

The resolving principle, which is the project's own core insight: coherence
comes from FABRICATION, not from a narrow palette. Every colour below is the
same card, the same tooth, the same roughness band, the same seam and wear -
cut from one sheet and painted differently. That is what a modelmaker does,
and it is why slot 5 holds together.

Slot 1 supplies the muted end (brick red, buff, blue-grey - a real N-scale
layout); slot 5 supplies the saturated end. Neither is invented.

WHAT THIS IS NOT: albedo variation WITHIN a surface. Slot 1's Ignore is
explicit - "large-scale albedo variation is the documented trap". Each
building is ONE flat painted colour; the variety is between buildings.
"""
import unreal

L = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
F = '/Game/Stacktown/Materials'
SRC = 'MI_paint_cream'          # the family everything is cut from

# name                     colour                  cited
PALETTE = [
    ('MI_dist_brick',      (0.395, 0.198, 0.150)),  # slot 1 brick
    ('MI_dist_buff',       (0.615, 0.520, 0.395)),  # slot 1 buff brick
    ('MI_dist_slate',      (0.330, 0.375, 0.430)),  # slot 1 blue-grey
    ('MI_dist_olive',      (0.400, 0.395, 0.245)),  # slot 5 olive
    ('MI_dist_teal',       (0.185, 0.360, 0.400)),  # slot 5 teal
    ('MI_dist_forest',     (0.150, 0.290, 0.225)),  # slot 5 dark green
    # deeper and bluer than brick: at (0.330,0.160,0.155) the two were 0.075
    # apart and the separation assert refused them - two dark reds is not a
    # palette, it is one colour twice. Same trap the mural paints hit.
    ('MI_dist_oxblood',    (0.245, 0.100, 0.135)),  # slot 5 red-brown
    ('MI_dist_ochre',      (0.640, 0.500, 0.180)),  # slot 5 yellow
    ('MI_dist_bone',       (0.700, 0.680, 0.630)),  # the muted default
]
MIN_SEP = 0.13      # between any two, so a street reads as varied


def dist(a, b):
    return sum((x - y)**2 for x, y in zip(a, b)) ** 0.5


made = []
for name, col in PALETTE:
    path = '%s/%s' % (F, name)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    if not eal.duplicate_asset('%s/%s' % (F, SRC), path):
        raise SystemExit('could not duplicate %s' % SRC)
    mi = eal.load_asset(path)
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    eal.save_asset(path, only_if_is_dirty=False)
    lum = 0.2126*col[0] + 0.7152*col[1] + 0.0722*col[2]
    made.append((name, col, lum))
    print('  %-18s (%.3f %.3f %.3f)  lum %.3f' % (name, col[0], col[1], col[2], lum))

worst = None
for i in range(len(PALETTE)):
    for j in range(i+1, len(PALETTE)):
        d = dist(PALETTE[i][1], PALETTE[j][1])
        if worst is None or d < worst[0]:
            worst = (d, PALETTE[i][0], PALETTE[j][0])
print()
print('  closest pair: %s vs %s at %.3f (min %.2f)'
      % (worst[1], worst[2], worst[0], MIN_SEP))
if worst[0] < MIN_SEP:
    raise SystemExit('two district colours read as one')
lums = sorted(m[2] for m in made)
print('  luminance spread %.3f to %.3f' % (lums[0], lums[-1]))
print('OK: %d district colours, one fabrication family (cut from %s)'
      % (len(made), SRC))
