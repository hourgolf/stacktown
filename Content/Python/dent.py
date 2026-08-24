"""A real dent, by subtraction.

Additive geometry cannot make damage: a block at a corner reads as an extra
piece stuck on, which is what the first attempt looked like. Taking material
away is the only honest version, so this opens GeometryScripting - the one
tool in the uproject that had never been used.

The cap mesh is used by exactly one component (BLD_Roof/ParapetCap), verified
before touching it, so a dented duplicate is safe and OneBuildingTest is
nowhere near this.

Two subtractions, not one. A single sphere scoops a clean crescent that reads
as machining. A squashed sphere biting the top-front corner plus a smaller one
just along the edge gives the asymmetric, twice-handled look of a corner that
has been knocked.
"""
import unreal

SRC = '/Game/Stacktown/Meshes/SM_Cw_1100p0_46p0_12p0'
DST = '/Game/Stacktown/Meshes/SM_ParapetCap_Dented'
GSA = unreal.GeometryScript_AssetUtils
GSP = unreal.GeometryScript_Primitives
GSB = unreal.GeometryScript_MeshBooleans
GSN = unreal.GeometryScript_Normals

src = unreal.EditorAssetLibrary.load_asset(SRC + '.SM_Cw_1100p0_46p0_12p0')
b = src.get_bounds().box_extent
print('source half-extents: %.1f %.1f %.1f' % (b.x, b.y, b.z))

if unreal.EditorAssetLibrary.does_asset_exist(DST):
    unreal.EditorAssetLibrary.delete_asset(DST)
if not unreal.EditorAssetLibrary.duplicate_asset(SRC, DST):
    raise SystemExit('duplicate failed')
dst = unreal.EditorAssetLibrary.load_asset(DST + '.SM_ParapetCap_Dented')
print('duplicated ->', dst.get_name())

mesh = unreal.DynamicMesh()
mesh, out = GSA.copy_mesh_from_static_mesh(
    dst, mesh, unreal.GeometryScriptCopyMeshFromAssetOptions(),
    unreal.GeometryScriptMeshReadLOD())
print('copy in:', out, 'tris', mesh.get_triangle_count())

popts = unreal.GeometryScriptPrimitiveOptions()
bopts = unreal.GeometryScriptMeshBooleanOptions()
ident = unreal.Transform()

# +X front-top corner in mesh-local space: (+bx, -by, +bz).
# SIZE AGAINST THE MATERIAL, NOT THE OBJECT. The cap is 1100 long but only 12
# THICK, and the first attempt used radius 21 - it cut straight through and
# left a ribbon. Each sphere now sits mostly ABOVE the top face so only its
# lower cap enters the card, taking ~2 uu out of 12.
BITES = [((b.x - 2.0, -b.y + 2.0, b.z + 5.0), 9.0, (1.30, 1.00, 0.80)),
         ((b.x - 17.0, -b.y + 1.0, b.z + 2.6), 6.5, (1.15, 0.90, 0.80))]

for i, (centre, r, scale) in enumerate(BITES):
    tool = unreal.DynamicMesh()
    tool = GSP.append_sphere_lat_long(tool, popts, unreal.Transform(), r, 14, 22)
    xf = unreal.Transform(unreal.Vector(*centre), unreal.Rotator(0, 0, 0),
                          unreal.Vector(*scale))
    mesh = GSB.apply_mesh_boolean(mesh, ident, tool, xf,
                                  unreal.GeometryScriptBooleanOperation.SUBTRACT, bopts)
    print('bite %d at (%.0f,%.0f,%.0f) r=%.0f -> tris %d'
          % (i, centre[0], centre[1], centre[2], r, mesh.get_triangle_count()))

# FLAT, not smooth. recompute_normals averaged across the box faces and turned
# a crisp piece of card into a soft ribbon. Card has hard edges.
mesh = GSN.set_per_face_normals(mesh)

mesh, out = GSA.copy_mesh_to_static_mesh(
    mesh, dst, unreal.GeometryScriptCopyMeshToAssetOptions(),
    unreal.GeometryScriptMeshWriteLOD())
print('copy out:', out)
unreal.EditorAssetLibrary.save_asset(DST)
print('saved', DST, 'tris now', dst.get_num_triangles(0))
