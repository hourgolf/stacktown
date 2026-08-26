"""Set the studio floor/backdrop albedo. Diagnostic - restores from a note.

The target arrives in a temp FILE, not argv: rung.sh hands the script to the
editor over remote execution and sys.argv does not survive the trip - the same
thing that made WIPE_LOTS arrive empty.

    echo 0.06    > $TMPDIR/stacktown_studio_albedo_set.txt
    echo restore > $TMPDIR/stacktown_studio_albedo_set.txt
"""
import os, json, sys, tempfile
import unreal

P = '/Game/Stacktown/Materials/MI_studio_grey'
NOTE = os.path.join(tempfile.gettempdir(), 'stacktown_studio_albedo.json')
mel = unreal.MaterialEditingLibrary
mi = unreal.load_asset(P)
cur = mel.get_material_instance_vector_parameter_value(mi, 'BaseColour')

SET = os.path.join(tempfile.gettempdir(), 'stacktown_studio_albedo_set.txt')
arg = open(SET).read().strip() if os.path.exists(SET) else None
if arg == 'restore':
    if not os.path.exists(NOTE):
        raise SystemExit('no saved value to restore')
    o = json.load(open(NOTE))
    col = (o['r'], o['g'], o['b'])
else:
    if not os.path.exists(NOTE):
        json.dump(dict(r=cur.r, g=cur.g, b=cur.b), open(NOTE, 'w'))
    v = float(arg)
    # keep the hue, move the value: the studio is a warm neutral and turning
    # it into a pure grey would change two things at once
    s = v / max(cur.r, 1e-6)
    col = (cur.r*s, cur.g*s, cur.b*s)

mel.set_material_instance_vector_parameter_value(
    mi, 'BaseColour', unreal.LinearColor(col[0], col[1], col[2], 1.0))
unreal.EditorAssetLibrary.save_asset(P, only_if_is_dirty=False)
print('  studio albedo (%.3f %.3f %.3f) -> (%.3f %.3f %.3f)'
      % (cur.r, cur.g, cur.b, col[0], col[1], col[2]))
