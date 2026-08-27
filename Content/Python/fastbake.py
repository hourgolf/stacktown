"""Turn a recorded box list into a StaticMesh in ONE editor pass.

    job: {"boxes": [...], "out": "/Game/...", "wall": ..., "roofmat": ...}

The slow path spends ~0.2 s per box on an MCP round trip, spawns an actor per
part, runs a role sweep over the level and then merges - twelve minutes for a
vernacular t5. Nothing about that work needs a round trip or an actor: the
geometry is known before the editor is touched, and the material follows from
the component NAME through rolemap.

So this skips actors entirely. Boxes go straight into a DynamicMesh with a
material per role, and out as an asset.

The geometry is IDENTICAL by construction - it is the same genbuild call with
the sink armed, not a second implementation. fastbake_check.py proves that
against the slow path rather than asserting it.
"""
import os, json, math, tempfile
import unreal
import _path  # noqa: F401
import rolemap

JOB = os.path.join(tempfile.gettempdir(), 'stacktown_fastbake_job.json')
OUT = os.path.join(tempfile.gettempdir(), 'stacktown_fastbake_result.json')
F = '/Game/Stacktown/Materials'
GSA = unreal.GeometryScript_AssetUtils
GSE = unreal.GeometryScript_MeshEdits
GSP = unreal.GeometryScript_Primitives
GSN = unreal.GeometryScript_NewAssetUtils
GSM = unreal.GeometryScript_MeshModeling

# MEASURED, both by fastbake_check.py:
#
#   append_box puts a box's BASE on its transform, not its centre - so every
#   part rode half its own height too high and the first preview came out
#   2331 uu against the slow path's 1985.
#
#   The slow path's add_cube makes a 44-triangle cube, not a 12-triangle one:
#   it is CHAMFERED. 4 uu is the card-edge value from MINIATURE_RECIPE and it
#   is what catches light along every arris. A sharp box is not a cheaper
#   version of this look, it is a different look.
CHAMFER = 4.0
ORIGIN = unreal.GeometryScriptPrimitiveOriginMode.CENTER

job = json.load(open(JOB))
boxes = job['boxes']
out_path = job['out']
wall, roofmat, trim = job.get('wall'), job.get('roofmat'), job.get('trim')
# The material study puts six variants on one mesh, so a component can name
# which panel it belongs to and take that panel's wall material. Keyed on the
# `_S<n>_` tag in the component name; absent for every normal building.
PANEL = job.get('panel_overrides') or {}


def wall_for(comp):
    if PANEL:
        for tag, mi in PANEL.items():
            if ('_%s_' % tag) in comp:
                return mi
    return wall

_m = {}
def M(n):
    if n not in _m:
        _m[n] = unreal.EditorAssetLibrary.load_asset('%s/%s.%s' % (F, n, n))
    return _m[n]

# actor records carry the family (from the label) and the local transform the
# boxes are relative to
actors = {}
for i, e in enumerate(boxes):
    if e['kind'] == 'actor':
        actors[i] = e

acc = unreal.DynamicMesh()
mats = []
opts = unreal.GeometryScriptPrimitiveOptions()
_bo = {}
def bopts(dist):
    k = round(dist, 2)
    if k not in _bo:
        o = unreal.GeometryScriptMeshBevelOptions()
        o.set_editor_property('bevel_distance', k)
        _bo[k] = o
    return _bo[k]
made, unbound, chamfered, donors = 0, [], 0, 0
_donor = {}


def donor(path):
    if path not in _donor:
        _donor[path] = unreal.EditorAssetLibrary.load_asset(path)
    return _donor[path]


for e in boxes:
    if e['kind'] == 'mesh':
        # DONOR GEOMETRY, appended the same way bake_merge does it. Without
        # this the fast path could only ever emit boxes, and the kit pieces
        # that fix the things boxes cannot do would be stuck outside it.
        sm = donor(e['asset'])
        if not sm:
            unbound.append('%s (missing %s)' % (e['name'], e['asset']))
            continue
        a = actors.get(e['actor'], {})
        fam = (a.get('name', 'BLD2_x').split('_')[0]) or 'BLD2'
        mname = e.get('mat') or rolemap.material_for(
            e['name'], wall_for(e['name']), roofmat, fam, trim)
        mi = M(mname) if mname else None
        if not mi:
            unbound.append('%s (no material)' % e['name'])
            continue
        # PER SLOT, not one material for the whole mesh. A donor tree is bark
        # plus alpha-masked leaf cards; giving every slot the same opaque
        # material turns the leaf cards into solid dark quads, which is why
        # every tree and bush baked here came out looking burnt. rolemap.SLOT
        # is the same vocabulary step_roles uses on the level.
        slots = sm.get_editor_property('static_materials')
        mlist = []
        for _sl in slots:
            _n = rolemap.material_for_slot(_sl.material_slot_name, mname)
            _mi = M(_n) if _n else None
            if not _mi:
                _mi = mi
            mlist.append(_mi)
        if not mlist:
            mlist = [mi]
        piece = unreal.DynamicMesh()
        piece, _ = GSA.copy_mesh_from_static_mesh(
            sm, piece, unreal.GeometryScriptCopyMeshFromAssetOptions(),
            unreal.GeometryScriptMeshReadLOD())
        al, ar = a.get('loc', [0, 0, 0]), a.get('rot', [0, 0, 0])
        br = e['r']
        # float or (x, y, z) - a donor trimmed to a bay is scaled on one axis
        _s = e.get('s', 1.0)
        sc = [float(_s)] * 3 if isinstance(_s, (int, float)) \
            else [float(v) for v in _s]
        local = unreal.Transform(
            unreal.Vector(e['c'][0], e['c'][1], e['c'][2]),
            unreal.Rotator(br[2], br[0], br[1]),
            unreal.Vector(sc[0], sc[1], sc[2]))
        world = unreal.Transform(
            unreal.Vector(al[0], al[1], al[2]),
            unreal.Rotator(ar[2], ar[0], ar[1]),
            unreal.Vector(1.0, 1.0, 1.0))
        acc, mats = GSE.append_mesh_transformed_with_materials(
            acc, mats, piece, mlist, [local], world)
        made += 1
        donors += 1
        continue
    if e['kind'] != 'box':
        continue
    a = actors.get(e['actor'], {})
    fam = (a.get('name', 'BLD2_x').split('_')[0]) or 'BLD2'
    mname = rolemap.material_for(e['name'], wall_for(e['name']), roofmat, fam,
                                 trim)
    if not mname:
        unbound.append(e['name'])
        continue
    mi = M(mname)
    if not mi:
        unbound.append('%s(missing %s)' % (e['name'], mname))
        continue
    # actor transform, then the box's own local transform under it
    al, ar = a.get('loc', [0, 0, 0]), a.get('rot', [0, 0, 0])
    piece = unreal.DynamicMesh()
    d = e['d']
    piece = GSP.append_box(piece, opts, unreal.Transform(), d[0], d[1], d[2],
                           origin=ORIGIN)
    # clamp the chamfer: many parts are 2-6 uu thick (glazing bars, glass) and
    # a 4 uu bevel on a 2 uu box is not a chamfer, it is a collapse
    # GeometryScript_MeshBevel does not exist; the function lives on
    # MeshModeling as apply_mesh_polygroup_bevel. The first version caught the
    # AttributeError in a bare `except: pass` and reported success with sharp
    # boxes - a check that returns ok while asking the wrong question, which
    # is the one failure mode this project has agreed to stop repeating. It
    # raises now, and the tri count is asserted below.
    bev = min(CHAMFER, 0.35 * min(d))
    if bev > 0.15:
        _r = GSM.apply_mesh_polygroup_bevel(piece, bopts(bev))
        piece = _r[0] if isinstance(_r, tuple) else _r
        chamfered += 1
    br = e['r']
    local = unreal.Transform(
        unreal.Vector(e['c'][0], e['c'][1], e['c'][2]),
        unreal.Rotator(br[2], br[0], br[1]),          # roll, pitch, yaw
        unreal.Vector(1.0, 1.0, 1.0))
    world = unreal.Transform(
        unreal.Vector(al[0], al[1], al[2]),
        unreal.Rotator(ar[2], ar[0], ar[1]),
        unreal.Vector(1.0, 1.0, 1.0))
    acc, mats = GSE.append_mesh_transformed_with_materials(
        acc, mats, piece, [mi], [local], world)
    made += 1

if not made:
    raise SystemExit('fastbake: nothing to build')
tri = unreal.GeometryScript_MeshQueries.get_num_triangle_i_ds(acc)
o = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
o.set_editor_property('enable_recompute_normals', False)
o.set_editor_property('enable_recompute_tangents', True)
folder, name = out_path.rsplit('/', 1)
if unreal.EditorAssetLibrary.does_asset_exist(out_path):
    unreal.EditorAssetLibrary.delete_asset(out_path)
sm, _outcome = GSN.create_new_static_mesh_asset_from_mesh(acc, out_path, o)
assert sm, 'asset not created at %s' % out_path
# CARRY THE MATERIALS. create_new_static_mesh_asset_from_mesh does NOT take
# them from the accumulator - bake_merge sets static_materials explicitly
# afterwards and this skipped it, so the first fast bakes came out with every
# slot None and a WorldGridMaterial in slot 0. Nothing caught it: the gate
# runs on the SOURCE actors before the merge, so no rule in this project has
# ever looked at a BAKED asset's materials. The assertion below is that rule.
sm.set_editor_property('static_materials',
                       [unreal.StaticMaterial(
                           material_interface=m,
                           material_slot_name=unreal.Name(
                               m.get_name() if m else 'None'))
                        for m in mats])
unreal.EditorAssetLibrary.save_asset(out_path, only_if_is_dirty=False)
bound = [m.material_interface.get_name() if m.material_interface else None
         for m in sm.get_editor_property('static_materials')]
bad = [i for i, m in enumerate(bound)
       if m is None or m in ('WorldGridMaterial', 'DefaultMaterial')]
if bad:
    raise SystemExit('fastbake: %d of %d baked slots carry no material (%s) - '
                     'the mesh would render as default grey'
                     % (len(bad), len(bound), bad[:6]))
slots = len(bound)
# A chamfered box is 44 triangles, a sharp one 12. If the average is near 12
# the bevel silently did nothing and the card edge - the thing the whole look
# rests on - is gone.
per = tri / float(made)
json.dump(dict(parts=made, tris=tri, slots=slots, chamfered=chamfered,
               tris_per_part=round(per, 1),
               unbound=sorted(set(unbound))[:8]), open(OUT, 'w'))
print('  FASTBAKED %s  parts %d (%d donor)  tris %d (%.1f/part)  chamfered %d  slots %d%s'
      % (name, made, donors, tri, per, chamfered, slots,
         '' if not unbound else '  UNBOUND %s' % sorted(set(unbound))[:4]))
if chamfered and not donors and per < 20.0:
    raise SystemExit('fastbake: %d parts bevelled but only %.1f tris/part - '
                     'the chamfer did not take' % (chamfered, per))
