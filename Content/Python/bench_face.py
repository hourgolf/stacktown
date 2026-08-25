"""Which way does SM_bench face at yaw 0? Decided from vertices, not guessed.

The bounds are symmetric across the short axis, so they cannot answer it. A
bench's backrest is the TALL part and the seat is the LOW part, and they sit on
opposite sides of the seat's centreline. So: take the mean short-axis position
of the high vertices and of the low ones. The back is where the high ones are;
the bench faces the other way.

Self-check first, on a synthetic bench whose answer is known.
"""
import unreal
GSA = unreal.GeometryScript_AssetUtils
GSQ = unreal.GeometryScript_MeshQueries


def split(pos, short_i, hi_z, lo_z):
    high = [p[short_i] for p in pos if p[2] >= hi_z]
    low = [p[short_i] for p in pos if p[2] <= lo_z]
    if not high or not low:
        return None
    return sum(high)/len(high), sum(low)/len(low)


# known answer: a bench whose backrest is deliberately at -X, seat at +X.
fake = [(0, -30, 90), (0, -30, 100), (0, -28, 95),      # back, high, at -X
        (0, 10, 40), (0, 20, 40), (0, 15, 45)]          # seat, low, at +X
h, l = split(fake, 1, 60, 50)
assert h < l, 'split() cannot tell a known backrest from a known seat'

sm = unreal.load_asset('/Game/AssetsvilleTown/Meshes/StreetProps/SM_bench.SM_bench')
dm = unreal.DynamicMesh()
dm, ok = GSA.copy_mesh_from_static_mesh(
    sm, dm, unreal.GeometryScriptCopyMeshFromAssetOptions(),
    unreal.GeometryScriptMeshReadLOD())
dm, poslist, _ = GSQ.get_all_vertex_positions(dm, False)
P = unreal.GeometryScript_List.convert_vector_list_to_array(poslist)
pos = [(p.x, p.y, p.z) for p in P]
zs = [p[2] for p in pos]
zmin, zmax = min(zs), max(zs)
print('verts %d   z %.1f..%.1f' % (len(pos), zmin, zmax))
# long axis is Y (measured), so the short axis is X -> index 0
hi_z = zmin + (zmax - zmin)*0.72
lo_z = zmin + (zmax - zmin)*0.45
r = split(pos, 0, hi_z, lo_z)
if not r:
    print('could not separate back from seat')
else:
    back_x, seat_x = r
    print('mean X of high verts %+.1f (backrest)   of low verts %+.1f (seat)'
          % (back_x, seat_x))
    print('AT YAW 0 THE BENCH FACES %s' % ('+X' if seat_x > back_x else '-X'))
