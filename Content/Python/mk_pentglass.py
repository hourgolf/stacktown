"""Glazing for a glass PENTHOUSE, which is not glazing for a window.

MI_glass_b sits at luminance 0.080 and MI_interior at 0.052. On a window that
is right: a dark room behind glass reads as a dark opening, and the opening is
what you want to see. Build a whole two-storey box out of the same two
materials on a dark_metal frame (0.131) and every surface of it is under 0.14
against a wall at 0.750 - so it renders as a black monolith sitting on a white
building, which is exactly how it looked.

A glass penthouse in daylight is the opposite: it takes the sky, and you see
INTO a lit volume rather than at a dark one. So the glass lifts to roughly
sky-grey and the interior behind it goes PALE - a lit room, not a void. The
dark frame stays dark, which is what then reads as a frame instead of
disappearing into its own glazing.

Assertions rather than taste: the glass must clear the void it replaced, and
the frame must still separate from the glass, or the box loses its structure.
"""
import unreal

L = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
F = '/Game/Stacktown/Materials'

SPECS = [
    # name, source to duplicate, colour, scalar overrides
    ('MI_glass_pent', 'MI_glass_b', (0.430, 0.468, 0.505),
     {'RoughMin': 0.04, 'RoughMax': 0.10, 'Specular': 0.66}),
    ('MI_interior_lit', 'MI_interior', (0.620, 0.596, 0.556),
     {'RoughMin': 0.55, 'RoughMax': 0.72, 'Specular': 0.30}),
]


def lum(c):
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]


def read(n):
    mi = eal.load_asset('%s/%s' % (F, n))
    c = L.get_material_instance_vector_parameter_value(mi, 'BaseColour')
    return (c.r, c.g, c.b)


old_glass = lum(read('MI_glass_b'))
frame = lum(read('MI_dark_metal'))
made = {}
for name, src, col, scal in SPECS:
    path = '%s/%s' % (F, name)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    if not eal.duplicate_asset('%s/%s' % (F, src), path):
        raise SystemExit('could not duplicate %s' % src)
    mi = eal.load_asset(path)
    L.set_material_instance_vector_parameter_value(
        mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
    for k, v in scal.items():
        L.set_material_instance_scalar_parameter_value(mi, k, v)
    eal.save_asset(path, only_if_is_dirty=False)
    made[name] = lum(col)
    print('  %-18s (%.3f %.3f %.3f)  lum %.3f  from %s'
          % (name, col[0], col[1], col[2], lum(col), src))

g, i = made['MI_glass_pent'], made['MI_interior_lit']
print()
print('  glass    %.3f  (was %.3f - a %.1fx lift off the void)'
      % (g, old_glass, g/old_glass))
print('  interior %.3f  (behind the glass, and lighter than it)' % i)
print('  frame    %.3f  (unchanged, so it still reads as a frame)' % frame)
fails = []
if g < 0.35:
    fails.append('glass at %.3f is still reading as a void' % g)
if i <= g:
    fails.append('interior %.3f is not lighter than glass %.3f' % (i, g))
if g - frame < 0.20:
    fails.append('frame %.3f does not separate from glass %.3f' % (frame, g))
for f in fails:
    print('FAIL  %s' % f)
if fails:
    raise SystemExit('penthouse glazing does not meet its own spec')
print('OK: a lit volume in a dark frame, not a black box')
