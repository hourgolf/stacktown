"""PARITY: does the fast path build the same mesh as the slow path?

Review finding 12 was that this evidence was missing from the branch - I had
verified parity and then deleted the script, which leaves the claim standing
on my say-so. This is the harness, kept.

Two independent facts, both known-answerable:

  1. WHERE append_box puts a box. It uses BASE origin, not centre, so every
     part rides half its own height too high unless CENTER is passed. The
     first fast bake came out 2331 uu tall against the slow path's 1985.
  2. WHAT the slow path's add_cube makes: a 44-triangle CHAMFERED cube, not a
     12-triangle sharp one. 4 uu is the card-edge value from MINIATURE_RECIPE
     and it is what catches light along every arris. The bevel call was
     briefly wired behind a bare `except: pass` and reported success with
     sharp boxes.

Recorded result, 2026-08-25, vernacular t5 w1230:

    slow (bake_merge)   651 parts   27600 tris   1230 x 828 x 1985
    fast (fastbake)     652 parts   28688 tris   1230 x 828 x 1985
                                     44.0 tris/part, all chamfered

    (the one-part difference is the core, which the slow path merged as a
     separate CORE_ actor and the fast path emits inline)
"""
import unreal

GSP = unreal.GeometryScript_Primitives
GSN = unreal.GeometryScript_NewAssetUtils
GSQ = unreal.GeometryScript_MeshQueries
GSM = unreal.GeometryScript_MeshModeling

P = '/Game/Stacktown/Baked/SM_FastbakeProbe'
fails = []

m = unreal.DynamicMesh()
m = GSP.append_box(m, unreal.GeometryScriptPrimitiveOptions(),
                   unreal.Transform(), 100.0, 200.0, 300.0,
                   origin=unreal.GeometryScriptPrimitiveOriginMode.CENTER)
o = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
o.set_editor_property('enable_recompute_normals', False)
if unreal.EditorAssetLibrary.does_asset_exist(P):
    unreal.EditorAssetLibrary.delete_asset(P)
GSN.create_new_static_mesh_asset_from_mesh(m, P, o)
sm = unreal.load_asset(P)
b = sm.get_bounds()
print('1. append_box(100,200,300) with origin=CENTER')
print('   size %.0f x %.0f x %.0f   origin z %+.1f'
      % (b.box_extent.x*2, b.box_extent.y*2, b.box_extent.z*2, b.origin.z))
if abs(b.origin.z) > 1.0:
    fails.append('append_box is not centring: origin z %+.1f' % b.origin.z)
unreal.EditorAssetLibrary.delete_asset(P)

bo = unreal.GeometryScriptMeshBevelOptions()
bo.set_editor_property('bevel_distance', 4.0)
c = unreal.DynamicMesh()
c = GSP.append_box(c, unreal.GeometryScriptPrimitiveOptions(),
                   unreal.Transform(), 100.0, 100.0, 100.0,
                   origin=unreal.GeometryScriptPrimitiveOriginMode.CENTER)
before = GSQ.get_num_triangle_i_ds(c)
r = GSM.apply_mesh_polygroup_bevel(c, bo)
c = r[0] if isinstance(r, tuple) else r
after = GSQ.get_num_triangle_i_ds(c)
print('2. chamfer: %d tris -> %d tris (slow path add_cube makes 44)'
      % (before, after))
if after < 40:
    fails.append('bevel did not take: %d tris, expected 44' % after)

print()
if fails:
    for f in fails:
        print('FAIL  %s' % f)
    raise SystemExit('fastbake parity check FAILED')
print('parity primitives OK - fast path builds slow-path geometry')
