"""Bake convex-edge curvature into static-mesh vertex colour.

WHY
    The master material's edge wear was saturate((1 - max|n|)/EdgeWearWidth) -
    the WORLD NORMAL used as a curvature proxy. That is a structural assumption
    that the world is axis-aligned boxes with 45 degree chamfers. It is wrong
    two ways, and both are demonstrable rather than argued:
      * it keys off ORIENTATION, not geometry, so any 45 degree surface reads
        as fully worn. Rendered on the material's own preview sphere - which
        has no edges at all - it paints almost the entire sphere.
      * imported geometry has no 45 degree chamfer facets, so it gets nothing
        useful, which is what blocks using bought assets.

WHAT THIS COMPUTES
    A facet is a maximal group of coplanar adjacent triangles. A facet is a
    BEVEL if its width - the greatest distance from any of its vertices to its
    own convex crease boundary - is at most BAND world units. Bevel facets are
    painted; everything else is left clean.

    Grouping into facets first is what makes this work on dense imported
    meshes. Per-TRIANGLE width would call every triangle of a finely
    tessellated mesh narrow and paint the whole asset.

    Strength s = 1 - dot(n1, n2) across the crease, so a 45 degree chamfer
    gives 0.293. Stored as R = 1 - s.

WHY R = 1 - s AND NOT s
    Fail-safe. An unbaked mesh keeps its existing vertex colour, and the two
    values found in this project are white (1,1,1,1) and black (0,0,0,1).
    Under R = 1 - s, white reads as "no crease" and a mesh nobody has baked
    looks exactly as it does today rather than turning fully worn. Black meshes
    - SM_Baked_Sedan is one - would read as fully worn, so they are reported
    and must be baked or excluded, never assumed.

    The material then computes saturate((1 - VertexColor.R)/EdgeWearWidth),
    which is the SAME arithmetic as the old term with a real per-facet
    curvature in place of max|n|. A 45 degree chamfer lands on 0.977 where the
    old proxy gave 0.977, so geometry the old term got right does not move.
"""
import unreal, math, sys, json

GSA = unreal.GeometryScript_AssetUtils
GSQ = unreal.GeometryScript_MeshQueries
GSV = unreal.GeometryScript_VertexColors
GSS = unreal.GeometryScript_MeshSelection

BAND      = 6.0        # world uu; 40 mm chamfer -> 3.82 uu facet, plus margin
CREASE    = 12.0       # degrees; the ONE angle that separates facets.
                       # There must not be a second, smaller "planar" angle
                       # with a gap between them. With planar=3 and crease=12,
                       # a smoothly curved car panel - whose triangles meet at
                       # 3-8 degrees - neither merged into one facet nor formed
                       # creases, so it shattered into thousands of tiny
                       # facets that each measured as a narrow bevel:
                       # SM_Baked_Sedan reported 1888 bevel facets out of 2237.
                       # A facet is bounded by creases and by nothing else.
QUANT     = 1000.0     # position weld quantisation (1/1000 uu)
LEVELS    = 8          # strength quantisation for painting

def _key(v):
    return (int(round(v.x*QUANT)), int(round(v.y*QUANT)), int(round(v.z*QUANT)))

def _sub(a,b): return (a.x-b.x, a.y-b.y, a.z-b.z)
def _dot3(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _norm(a):
    l = math.sqrt(_dot3(a,a))
    return (a[0]/l, a[1]/l, a[2]/l) if l > 1e-12 else (0.0,0.0,0.0)

def _pt_seg_dist(p, a, b):
    ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
    ap = (p[0]-a[0], p[1]-a[1], p[2]-a[2])
    dd = _dot3(ab,ab)
    t = 0.0 if dd < 1e-12 else max(0.0, min(1.0, _dot3(ap,ab)/dd))
    c = (a[0]+ab[0]*t, a[1]+ab[1]*t, a[2]+ab[2]*t)
    d = (p[0]-c[0], p[1]-c[1], p[2]-c[2])
    return math.sqrt(_dot3(d,d))


def analyse(dm, band=BAND):
    """Return (facets, tri_strength, report) without modifying the mesh."""
    dm, poslist, _ = GSQ.get_all_vertex_positions(dm, False)
    dm, trilist, _ = GSQ.get_all_triangle_indices(dm, False)
    P = unreal.GeometryScript_List.convert_vector_list_to_array(poslist)
    T = unreal.GeometryScript_List.convert_triangle_list_to_array(trilist)

    pos = [(p.x, p.y, p.z) for p in P]
    keys = [_key(p) for p in P]                # weld split positions by value

    tris, tn, tc = [], [], []
    for t in T:
        a, b, c = int(t.x), int(t.y), int(t.z)   # triangle list converts to IntVector
        if a < 0: tris.append(None); tn.append(None); tc.append(None); continue
        pa, pb, pc = pos[a], pos[b], pos[c]
        # Unreal is left-handed and its front faces wind clockwise, so the
        # OUTWARD normal is cross(c-a, b-a). With the other order every normal
        # on a closed mesh points inward, every convex edge tests as concave,
        # and the bake reports a mesh with zero creases while running clean.
        # _selfcheck below is what caught that and is why it stays in.
        n = _norm(_cross((pc[0]-pa[0],pc[1]-pa[1],pc[2]-pa[2]),
                         (pb[0]-pa[0],pb[1]-pa[1],pb[2]-pa[2])))
        tris.append((a,b,c)); tn.append(n)
        tc.append(((pa[0]+pb[0]+pc[0])/3.0, (pa[1]+pb[1]+pc[1])/3.0, (pa[2]+pb[2]+pc[2])/3.0))

    # edge -> triangles, keyed by welded POSITION not vertex id: the meshes in
    # this project come in with split positions (96 verts for 44 triangles on a
    # chamfered box), so an id-keyed edge map finds no shared edges at all and
    # reports a mesh with no creases whatsoever.
    edges = {}
    for ti, tv in enumerate(tris):
        if tv is None: continue
        ks = [keys[v] for v in tv]
        for i in range(3):
            e = tuple(sorted((ks[i], ks[(i+1)%3])))
            edges.setdefault(e, []).append(ti)

    crease_cos = math.cos(math.radians(CREASE))

    # union-find over coplanar adjacency -> facets
    parent = list(range(len(tris)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra

    creases = []          # (edge, t1, t2, strength)
    for e, ts in edges.items():
        if len(ts) != 2: continue
        t1, t2 = ts
        if tn[t1] is None or tn[t2] is None: continue
        d = _dot3(tn[t1], tn[t2])
        d = max(-1.0, min(1.0, d))
        if d >= crease_cos:
            union(t1, t2); continue        # same facet: not a crease
        # convex if each face's plane leaves the other's centroid behind it
        conv = _dot3(tn[t1], _sub_t(tc[t2], tc[t1])) < 0
        if conv:
            creases.append((e, t1, t2, 1.0 - d))

    facets = {}
    for ti, tv in enumerate(tris):
        if tv is None: continue
        facets.setdefault(find(ti), []).append(ti)

    # each facet's own convex crease boundary
    fcrease = {}
    for e, t1, t2, s in creases:
        for t in (t1, t2):
            fcrease.setdefault(find(t), []).append((e, s))

    tri_strength = {}
    widths = {}
    for fid, tlist in facets.items():
        cr = fcrease.get(fid)
        if not cr:
            widths[fid] = float('inf'); continue
        vs = set()
        for t in tlist: vs.update(tris[t])
        widths[fid] = _facet_halfwidth([pos[v] for v in vs], tn[tlist[0]])
        if widths[fid] <= band:
            s = max(s for _, s in cr)
            for t in tlist: tri_strength[t] = min(1.0, s)

    # SELF-CHECK: compare our geometric normals against Unreal's OWN face
    # normals on a sample of triangles.
    #
    # Two earlier versions of this check were wrong in ways that mattered:
    #   * "normals point away from the centroid" is only true of a convex
    #     shell. It failed SM_Bake_Narrow - 136 boxes in one mesh - at
    #     3100/5984 while the winding was perfectly consistent.
    #   * signed volume is only meaningful on a CLOSED mesh, and the generated
    #     buildings are hollow facades, so it read 1.84e9 on a mesh with no
    #     interior. It also compared against GetMeshVolumeArea's first return
    #     value, which is the surface AREA, not the volume.
    # Asking Unreal for the same quantity works on open, closed, convex and
    # compound meshes alike, and it tests the one thing that actually went
    # wrong here: handedness.
    ids = [i for i, t in enumerate(tris) if t is not None]
    sample = ids[::max(1, len(ids)//200)][:200]
    agreed = 0
    for i in sample:
        un, valid = GSQ.get_triangle_face_normal(dm, i)
        if valid and _dot3(tn[i], (un.x, un.y, un.z)) > 0:
            agreed += 1
    orientation_ok = bool(sample) and agreed >= 0.9*len(sample)
    closed = GSQ.get_num_open_border_edges(dm) == 0

    report = {
        'triangles': sum(1 for t in tris if t is not None),
        'normals_agree': '%d/%d' % (agreed, len(sample)),
        'closed': closed,
        'orientation_ok': orientation_ok,
        'facets': len(facets),
        'creases': len(creases),
        'bevel_facets': sum(1 for f, w in widths.items() if w <= band),
        'painted_tris': len(tri_strength),
        'width_histogram': _hist([widths[k] for k in facets]),
        'painted_area_pct': round(100.0*_area(tris, pos, tri_strength.keys())
                                  / max(_area(tris, pos, range(len(tris))), 1e-9), 1),
    }
    return facets, tri_strength, report


def _facet_halfwidth(points, normal):
    """Half the facet's narrowest in-plane extent - how far into the facet you
    can get from its own boundary.

    The first version measured the greatest distance from a facet VERTEX to the
    facet's crease boundary, which is 0 for every facet of a chamfered box:
    each facet is bounded by creases on all sides, so all its vertices lie ON
    the boundary. It called all 26 facets bevels and painted the entire mesh.
    What matters is the facet's THICKNESS, not where its corners are.

    Rotating calipers in the facet plane rather than PCA - no degenerate case
    when the points are collinear-ish, which the 450 x 0.6 faces of a mullion
    very nearly are.
    """
    if len(points) < 3: return 0.0
    n = normal or (0.0, 0.0, 1.0)
    # any in-plane basis
    seed = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = _norm(_cross(n, seed))
    v = _norm(_cross(n, u))
    best = float('inf')
    STEPS = 18
    for k in range(STEPS):
        a = math.pi*k/STEPS
        ca, sa = math.cos(a), math.sin(a)
        d = (u[0]*ca + v[0]*sa, u[1]*ca + v[1]*sa, u[2]*ca + v[2]*sa)
        projs = [_dot3(d, p) for p in points]
        best = min(best, max(projs) - min(projs))
    return best/2.0


def _hist(ws):
    """Facet half-width distribution, so the band can be chosen from the data
    rather than invented. Inventing a threshold and then judging against it is
    a documented failure mode in this project."""
    buckets = [0.5, 1, 2, 4, 6, 10, 25, 100, float('inf')]
    out = {}
    for b in buckets:
        lo = 0 if b == buckets[0] else buckets[buckets.index(b)-1]
        n = sum(1 for w in ws if lo < w <= b)
        if n: out['%g-%g' % (lo, b)] = n
    return out


def _area(tris, pos, ids):
    """Surface area of a set of triangles. Triangle COUNT is a bad proxy for how
    much of a mesh is worn - a building is mostly small mullion boxes by count
    and mostly wall by area."""
    tot = 0.0
    for i in ids:
        tv = tris[i]
        if tv is None: continue
        a, b, c = pos[tv[0]], pos[tv[1]], pos[tv[2]]
        cr = _cross(_sub_t(b, a), _sub_t(c, a))
        tot += 0.5*math.sqrt(_dot3(cr, cr))
    return tot


def _sub_t(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def bake(path, band=BAND, write=False):
    sm = unreal.load_asset(path)
    if not sm: return {'path': path, 'error': 'missing'}
    dm = unreal.DynamicMesh()
    dm, ok = GSA.copy_mesh_from_static_mesh(
        sm, dm, unreal.GeometryScriptCopyMeshFromAssetOptions(),
        unreal.GeometryScriptMeshReadLOD())
    facets, tri_strength, rep = analyse(dm, band)
    rep['path'] = path.split('/')[-1]
    if not write:
        return rep
    # Material slot NAMES are how imported assets bind to the role vocabulary,
    # and copying a mesh back into an asset is exactly where this project has
    # lost them before (skeletal->static bakes kept the slot COUNT and dropped
    # the names). Record them and compare afterwards rather than assuming.
    slots_before = [str(m.material_slot_name) for m in sm.get_editor_property('static_materials')]

    # clean everywhere, then paint the bevel facets in quantised bands
    GSV.set_mesh_constant_vertex_color(dm, unreal.LinearColor(1,1,1,1),
                                       unreal.GeometryScriptColorFlags(), True)
    buckets = {}
    for t, s in tri_strength.items():
        lvl = max(1, min(LEVELS, int(round(s*LEVELS))))
        buckets.setdefault(lvl, []).append(t)
    for lvl, tlist in sorted(buckets.items()):
        s = lvl/float(LEVELS)
        sel = unreal.GeometryScriptMeshSelection()
        dm, sel = GSS.convert_index_array_to_mesh_selection(
            dm, tlist, unreal.GeometryScriptMeshSelectionType.TRIANGLES)
        val = 1.0 - s
        GSV.set_mesh_selection_vertex_color(
            dm, sel, unreal.LinearColor(val, val, val, 1.0),
            unreal.GeometryScriptColorFlags(), True)
    opts = unreal.GeometryScriptCopyMeshToAssetOptions()
    # recompute_normals averages across box faces and turns crisp card into a
    # soft ribbon - the meshes already carry the per-face normals they need.
    opts.set_editor_property('enable_recompute_normals', False)
    opts.set_editor_property('enable_recompute_tangents', False)
    opts.set_editor_property('replace_materials', False)
    opts.set_editor_property('use_original_vertex_order', True)
    GSA.copy_mesh_to_static_mesh(dm, sm, opts, unreal.GeometryScriptMeshWriteLOD())

    slots_after = [str(m.material_slot_name) for m in sm.get_editor_property('static_materials')]
    rep['slots_kept'] = slots_before == slots_after
    if not rep['slots_kept']:
        rep['slots_before'] = slots_before
        rep['slots_after'] = slots_after
    rep['tris_after'] = sm.get_num_triangles(0)
    rep['written'] = True
    return rep


def level_meshes():
    """Every Stacktown mesh placed in the current level, minus the vehicle and
    pedestrian bakes - those are single-sided shells on M_StacktownMaster_2S,
    which does not read vertex colour."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = set()
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m: continue
            p = m.get_path_name().split('.')[0]
            # NEVER bake into /Engine content or into licensed donor packs.
            # Donor meshes are normalised into Content/Stacktown/Source first;
            # writing vertex colours into AssetsvilleTown in place would modify
            # marketplace content that is not even in this repository.
            if not p.startswith('/Game/Stacktown/'): continue
            if '/SM_Baked_' in p: continue
            out.add(p)
    return sorted(out)


def main(paths=None, write=False, band=BAND):
    paths = paths or level_meshes()
    problems = []
    for p in paths:
        r = bake(p, band, write)
        if not r.get('orientation_ok') or (write and not r.get('slots_kept')):
            problems.append(r)
        print(json.dumps(r))
    print('%d meshes, %d problems' % (len(paths), len(problems)))
    return problems


if __name__ == '__main__':
    args = json.loads(ARGS) if 'ARGS' in dir() else {}
    main(args.get('paths'), args.get('write', False), args.get('band', BAND))
