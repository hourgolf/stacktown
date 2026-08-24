"""Chamfered-box static mesh generation for Stage 0 (gate line B6).

Geometry Script's bevel library is not exposed to Python in UE 5.8, so the
chamfer is authored directly through StaticMeshDescription instead.

A chamfered box = 6 inset face quads + 12 edge strips + 8 corner triangles.
Winding is fixed by comparing each polygon's Newell normal against its
centroid (valid because the solid is convex and centred on the origin).
"""
import unreal

MESH_DIR = '/Game/Stacktown/Meshes'


def _verts(h, c):
    """Vertex table keyed by (face_axis, face_sign, other_axis_signs tuple)."""
    V = {}
    for a in range(3):
        others = [i for i in range(3) if i != a]
        for s in (-1, 1):
            for sb in (-1, 1):
                for sd in (-1, 1):
                    p = [0.0, 0.0, 0.0]
                    p[a] = s * h[a]
                    p[others[0]] = sb * (h[others[0]] - c)
                    p[others[1]] = sd * (h[others[1]] - c)
                    V[(a, s, sb, sd)] = tuple(p)
    return V


def _polys(h, c):
    V = _verts(h, c)
    polys = []
    for a in range(3):
        o = [i for i in range(3) if i != a]
        for s in (-1, 1):
            polys.append([V[(a, s, sb, sd)]
                          for sb, sd in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a in range(3):
        for b in range(a + 1, 3):
            d = [i for i in range(3) if i not in (a, b)][0]
            oa = [i for i in range(3) if i != a]
            ob = [i for i in range(3) if i != b]
            for s in (-1, 1):
                for t in (-1, 1):
                    def va(sd):
                        k = [None, None]
                        k[oa.index(b)] = t
                        k[oa.index(d)] = sd
                        return V[(a, s, k[0], k[1])]

                    def vb(sd):
                        k = [None, None]
                        k[ob.index(a)] = s
                        k[ob.index(d)] = sd
                        return V[(b, t, k[0], k[1])]
                    polys.append([va(-1), va(1), vb(1), vb(-1)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                sg = (sx, sy, sz)
                tri = []
                for a in range(3):
                    o = [i for i in range(3) if i != a]
                    tri.append(V[(a, sg[a], sg[o[0]], sg[o[1]])])
                polys.append(tri)
    return polys


def _newell(poly):
    n = [0.0, 0.0, 0.0]
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        n[0] += (p[1] - q[1]) * (p[2] + q[2])
        n[1] += (p[2] - q[2]) * (p[0] + q[0])
        n[2] += (p[0] - q[0]) * (p[1] + q[1])
    return n


def build(name, dims, chamfer, material=None):
    """dims = (x,y,z) full size in uu. Returns the StaticMesh asset."""
    h = [d / 2.0 for d in dims]
    c = min(chamfer, 0.45 * min(dims))          # never collapse a thin box
    polys = _polys(h, c)

    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (MESH_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm = at.create_asset(name, MESH_DIR, unreal.StaticMesh, None)
    smd = sm.create_static_mesh_description()
    pg = smd.create_polygon_group()

    made = 0
    for poly in polys:
        n = _newell(poly)
        cen = [sum(p[i] for p in poly) / len(poly) for i in range(3)]
        if sum(n[i] * cen[i] for i in range(3)) < 0:
            poly = list(reversed(poly))
        vinsts = []
        for p in poly:
            v = smd.create_vertex()
            smd.set_vertex_position(vertex_id=v,
                                    position=unreal.Vector(p[0], p[1], p[2]))
            vi = smd.create_vertex_instance(vertex_id=v)
            vinsts.append(vi)
        # UE 5.8 binds create_polygon as create_polygon(group) -> (id, ...),
        # with the vertex instances set in a second call.
        res = smd.create_polygon(pg)
        pid = res[0] if isinstance(res, (tuple, list)) else res
        smd.set_polygon_vertex_instances(polygon_id=pid,
                                         vertex_instance_i_ds=vinsts)
        made += 1

    sm.build_from_static_mesh_descriptions([smd], False)
    if material is not None:
        sm.static_materials = [unreal.StaticMaterial(material_interface=material)]
    unreal.EditorAssetLibrary.save_asset(path)
    return sm, made, c
