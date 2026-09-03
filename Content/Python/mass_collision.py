"""Give the wooden masses collision so a click can select a building.

    ./Tools/rung.sh mass_collision.py                     the one test asset
    echo '{"all":true}' > $TMPDIR/stacktown_mass_collision.json
    ./Tools/rung.sh mass_collision.py                     every SM_WMass_*

    (rung.sh forwards no arguments, and an env var does not reach the editor's
    process either - see the note in main(). The temp job file is the channel
    that works, and is the one fastbake already uses.)

CONVEX HULLS, WITH A BOX FALLBACK. (The first version of this file set
complex-as-simple; that was wrong for a reason neither lane had looked at -
the cursor trace ran with bTraceComplex=True against masses that carried no
complex geometry at all, so nothing could stop it. The instrument was the
fault, and the subject got changed first. Fixed in the driver; this file now
does what actually works.)

ONE HULL, NOT FOUR, AND THAT IS FINE. hull_count is a CEILING and the
decomposer returns 1 for these masses at every setting tried (4/16, 8/32,
16/32, 24/64). A convex hull cannot follow a setback inward - concavity is
what a step is - so one hull is the outer envelope. MEASURED in a trace, it
is NOT the AABB: on SM_WMass_w820_setback2 (bounds to z=4581) a downward
trace hits 4352 at the centre and 3533-3584 at the base edges, so the
envelope tapers from base to crown and claims measurably less air than a box
would. Above the base stage it still covers the setbacks' air to ~3530, which
is what a convex envelope must do and is the known cost.

WHAT THIS FILE USED TO SAY. The masses are STEPPED - setback1 has two
stages, setback2 three, tower two - so a single box claims the empty air above
every setback, and a click on sky beside a tower would select it. Complex-as-
simple uses the render triangles, which is the exact silhouette including the
steps, costs zero extra geometry, and is one property per asset. The two
things it gives up - physics simulation and cheap traces - are both irrelevant
here: these buildings never simulate, and a line trace against 264 triangles
is nothing.

WHAT THIS SCRIPT CANNOT PROVE. Setting the flag and reading it back proves the
property landed, not that a trace now stops on the mass. That is a different
question and it needs a real trace in PIE - the coordinator's instrument, not
this script's. The read-back below is a precondition, not the evidence, and it
is labelled that way so nobody reports it as the result.

THE REAL FIX IS ONE LINE IN SHARED CODE AND IS NOT MINE TO MAKE.
fastbake.py's GeometryScriptCreateNewStaticMeshAssetOptions carries
`enable_collision` and `collision_mode`, and it sets neither - only
enable_recompute_normals and enable_recompute_tangents (fastbake.py:207-208).
Setting them there would give every future bake collision and make this script
unnecessary. fastbake is shared with the flagship and carries the
byte-identical contract, and direction B does not edit it: named for the
owner, not changed.
"""
import json
import os
import sys
import tempfile
import unreal
import _path  # noqa: F401

FOLDER = '/Game/Stacktown/BakedWood'
JOB = os.path.join(tempfile.gettempdir(), 'stacktown_mass_collision.json')
ONE = 'SM_WMass_w820_setback2'


def _short(flag):
    return str(flag).split('.')[-1].split(':')[0]


def _prims(sm):
    agg = sm.get_editor_property('body_setup').get_editor_property('agg_geom')
    return (len(agg.get_editor_property('box_elems')),
            len(agg.get_editor_property('convex_elems')))


def apply_to(name):
    """Hulls first, box if the decomposition yields nothing. Verified from a
    RELOAD, because a count read off the live object proves the call ran and
    not that anything was written."""
    path = '%s/%s' % (FOLDER, name)
    sm = unreal.load_asset(path)
    if sm is None:
        return (name, 'MISSING', 0, 0, False)
    lib = unreal.EditorStaticMeshLibrary
    lib.remove_collisions(sm)
    lib.set_convex_decomposition_collisions(sm, 4, 16, 100000)
    how = 'hull'
    if _prims(sm)[1] == 0:
        lib.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.BOX)
        how = 'BOX (no hull)'
    bs = sm.get_editor_property('body_setup')
    bs.set_editor_property('collision_trace_flag',
                           unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    sm.set_editor_property('body_setup', bs)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    fresh = unreal.load_asset(path)
    b, c = _prims(fresh)
    return (name, how, b, c, (b + c) > 0)


def main():
    # HOW THIS SCRIPT TAKES AN ARGUMENT, after two channels that silently
    # did not: rung.sh takes the SCRIPT NAME as $1 and forwards nothing, so
    # sys.argv is empty in the editor; and an env var does not reach either,
    # because the script executes INSIDE THE EDITOR'S PROCESS with the
    # editor's environment, not the calling shell's. Both attempts ran,
    # printed a success line, and did 1 asset of 36 - a wrong scope wearing a
    # green tick. The project's own answer is a temp job file, which is how
    # fastbake takes its work, so this uses the same channel.
    want_all = '--all' in sys.argv
    try:
        with open(JOB) as fh:
            want_all = want_all or bool(json.load(fh).get('all'))
    except Exception:
        pass
    if want_all:
        names = sorted(
            p.split('.')[0].split('/')[-1]
            for p in unreal.EditorAssetLibrary.list_assets(FOLDER, recursive=False)
            if '/SM_WMass_' in p)
    else:
        names = [ONE]
    print('%-34s %-14s %s' % ('asset', 'how', 'box/convex'))
    bad = []
    for n in names:
        name, how, b, c, ok = apply_to(n)
        print('%-34s %-14s %d/%d %s' % (name, how, b, c, '' if ok else 'FAILED'))
        if not ok:
            bad.append(name)
    print()
    print('%d asset(s), %d with collision, %d FAILED' % (
        len(names), len(names) - len(bad), len(bad)))
    if bad:
        print('refused:', bad)
    print('PRECONDITION ONLY - prims exist and are saved. Whether a trace '
          'stops on them is a different question and needs a real trace.')


main()
