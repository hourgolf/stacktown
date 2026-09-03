"""One-shot EDITOR-WORLD study dressing for the lighting study's chosen
subject: the play board. NEVER SAVED.

    python3 Content/Python/study_dress.py --dress   # wood-dress all 14 TC_Bld_* parcels to their PINNED tier, editor-world only
    python3 Content/Python/study_dress.py --clear   # revert all 14 to StaticMesh=None, exactly
    python3 Content/Python/study_dress.py --pose    # emit the play camera's default framing as JSON, no editor mutation at all

WHY THE 14 PARCELS SHOW StaticMesh=NONE IN THE EDITOR WORLD, CONFIRMED NOT
A BUG (asked for, not assumed): `BP_Parcel.ResolveMesh` only ever runs
from `EventBeginPlay`/`EventTick`, which the EDITOR WORLD never executes
- PIE runs a transient DUPLICATE world, and the editor's own copies of
these actors are otherwise-correct but inert. Same split already in
HANDOFF.md's `CaptureViewport`/`GetVisibleActors` entry; this is the
identical mechanism landing on a different symptom. From-scratch play is
correct: an unowned parcel IS meshless until bought. The lighting study
chose the play board as its subject anyway, so it needs something to
light regardless of what a fresh save would actually show - hence this
script, and hence it must never touch the save.

DO NOT SAVE THE LEVEL WHILE DRESSED. `--dress` sets real StaticMesh and
material references directly on the placed actors; saving the level in
that state would bake the eventual-city look into TestCity.umap and
silently break from-scratch play - every parcel would show its declared
tier's mesh instead of resolving fresh from citystate.json on the next
PIE start. That is exactly the "looks fine until someone actually plays
it" class of bug this project's own ledger exists to catch. Run --clear
before doing anything else in the editor, no exceptions, even if this
script itself is interrupted mid-`--dress`.

Runs LOCALLY over MCP (import ue) - never via remote exec. See HANDOFF's
"An MCP call from inside a rung script DEADLOCKS" trap: this script
calls MCP from outside the editor process, the only safe direction -
same reason mk_da_catalogue.py gives.
"""
import json
import math
import os
import sys

import _path  # noqa: F401
import testcity_pins
import woodmap
import ue

LEVEL = '/Game/Maps/TestCity'
WOOD_MI_PATH = '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s'
WOOD_MESH_PATH = '/Game/Stacktown/BakedWood/%s.%s'
POSE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'study_pose.json')
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
SCENE = 'editor_toolset.toolsets.scene.SceneTools'
PARCEL_CLASS = '/Game/Stacktown/Runtime/BP_Parcel.BP_Parcel_C'

# The boom's own EventBeginPlay defaults, BP_LensRig.uasset - Azimuth 250 /
# Reach 19000 / Height 9000 / Tilt -25 / Pan 0 / Focal 24, orbiting
# BoardCentre. Copied from the live Blueprint, not re-derived, so a study
# capture matches what a player actually sees on first boot. BoardCentre
# itself IS re-measured below (read live, not hardcoded here) since
# TESTCITY_PLAN.md is explicit that it's "measured, never authored."
DEFAULT_POSE = {'azimuth': 250.0, 'reach': 19000.0, 'height': 9000.0,
                 'tilt': -25.0, 'pan': 0.0, 'focal': 24.0}

LENSRIG_CLASS = '/Game/Stacktown/Runtime/BP_LensRig.BP_LensRig_C'


def call(toolset, name, args):
    """ue.tool() returns the raw MCP text content, which is the tool's
    JSON-serialised output ({"returnValue": ...}) as a string - unwrap it."""
    raw = ue.tool(toolset, name, args)
    return json.loads(raw)['returnValue']


def _assert_level():
    cur = call(SCENE, 'get_current_level', {})
    assert cur == LEVEL, \
        'wrong level open (%s) - refusing to touch parcels outside %s' % (
            cur, LEVEL)


def _parcel_actor(lot, rid, tier):
    """The one editor-world actor for a pinned lot, found by its exact
    genbuild-assigned label (confirmed live this session for tower lots:
    'TC_Bld_SW2_tower_t6' etc - rid and the PIN's declared tier are both
    baked into the label itself, so an exact match is unambiguous and
    identity never needs to be re-read off the meshless actor). NOT
    independently confirmed for the other 7 recipes in this pin table -
    returns None on anything but exactly one hit rather than crash the
    whole pass, so one unexpected label format costs one lot, not the
    run; caller reports it as unresolved same as a woodmap.resolve()
    failure."""
    label = 'TC_Bld_%s_%s_t%d' % (lot, rid, tier)
    hits = call(SCENE, 'find_actors', {
        'name': label, 'tag': '',
        'actor_type': {'refPath': PARCEL_CLASS}, 'collision_channels': []})
    if len(hits) != 1:
        return None
    return hits[0]


def dress():
    _assert_level()
    missing = []
    dressed = 0
    for lot in sorted(testcity_pins.PINS):
        p = testcity_pins.PINS[lot]
        try:
            r = woodmap.resolve(p['rid'], p['tier'], p['w'], corner=p['corner'])
        except (KeyError, ValueError) as e:
            missing.append('%s: %s' % (lot, e))
            continue
        actor = _parcel_actor(lot, p['rid'], p['tier'])
        if actor is None:
            missing.append('%s: no editor-world actor matched the expected '
                            'label' % lot)
            continue
        comp = {'refPath': actor['refPath'] + '.Building'}
        mesh_ref = WOOD_MESH_PATH % (r['asset'], r['asset'])
        mi_ref = WOOD_MI_PATH % (r['species'], r['species'])
        # TWO SEPARATE calls, mesh then material, not one combined
        # set_properties - live-caught 2026-09-02: setting both in one call
        # silently dropped OverrideMaterials (StaticMesh alone landed fine),
        # almost certainly the mesh change resetting the material-slot array
        # after OverrideMaterials had already been applied in the same
        # request. Matches how ResolveMesh itself always did this in
        # Blueprint - SetStaticMesh then a separate SetMaterial node, never
        # combined - this script just hadn't matched it until now.
        ok = call(OBJ, 'set_properties', {
            'instance': comp, 'values': json.dumps({'StaticMesh': mesh_ref})})
        assert ok is True, (lot, ok)
        ok = call(OBJ, 'set_properties', {
            'instance': comp,
            'values': json.dumps({'OverrideMaterials': [mi_ref]})})
        assert ok is True, (lot, ok)
        back = json.loads(call(OBJ, 'get_properties', {
            'instance': comp, 'properties': ['StaticMesh', 'OverrideMaterials']}))
        assert back.get('StaticMesh', {}).get('refPath') == mesh_ref, (lot, back)
        mats = back.get('OverrideMaterials') or []
        assert mats and mats[0].get('refPath') == mi_ref, (lot, back)
        dressed += 1
        print('  dressed %-6s -> %s (%s, tier %d)' % (
            lot, r['asset'], r['species'], p['tier']))
    if missing:
        print('  UNRESOLVED, left meshless: %s' % '; '.join(missing))
    print('  %d/%d parcels dressed and read-back verified. DO NOT SAVE. '
          'Run --clear before leaving the editor.'
          % (dressed, len(testcity_pins.PINS)))


def _is_cleared(static_mesh_value):
    """True for whatever shape an unset object-reference property comes
    back as - seen different forms from this bridge for different
    properties this session (bare None, an empty-refPath dict), so this
    checks the meaning (no real asset referenced) rather than one exact
    shape."""
    if static_mesh_value is None:
        return True
    ref = static_mesh_value.get('refPath') if isinstance(
        static_mesh_value, dict) else static_mesh_value
    return not ref or ref == 'None'


def clear():
    _assert_level()
    cleared = 0
    unresolved = []
    for lot in sorted(testcity_pins.PINS):
        p = testcity_pins.PINS[lot]
        actor = _parcel_actor(lot, p['rid'], p['tier'])
        if actor is None:
            unresolved.append(lot)
            continue
        comp = {'refPath': actor['refPath'] + '.Building'}
        ok = call(OBJ, 'set_properties', {
            'instance': comp,
            'values': json.dumps({'StaticMesh': None, 'OverrideMaterials': []})})
        assert ok is True, (lot, ok)
        back = json.loads(call(OBJ, 'get_properties', {
            'instance': comp, 'properties': ['StaticMesh']}))
        assert _is_cleared(back.get('StaticMesh')), (lot, back)
        cleared += 1
    if unresolved:
        print('  NOT FOUND, left untouched: %s' % ', '.join(unresolved))
    print('  %d/%d parcels cleared to StaticMesh=None, read-back verified. '
          'Safe to save or close.' % (cleared, len(testcity_pins.PINS)))


def pose():
    _assert_level()
    rig = call(SCENE, 'find_actors', {
        'name': '', 'tag': '', 'actor_type': {'refPath': LENSRIG_CLASS},
        'collision_channels': []})
    assert len(rig) == 1, ('expected exactly one BP_LensRig', rig)
    bc = json.loads(call(OBJ, 'get_properties', {
        'instance': rig[0], 'properties': ['BoardCentre']}))['BoardCentre']

    d = DEFAULT_POSE
    az = math.radians(d['azimuth'])
    loc = {'x': bc['x'] + d['reach'] * math.cos(az),
           'y': bc['y'] + d['reach'] * math.sin(az),
           'z': bc['z'] + d['height']}
    rot = {'roll': 0.0, 'pitch': d['tilt'],
           'yaw': (d['azimuth'] + 180.0 + d['pan']) % 360.0}
    fov = 2.0 * math.degrees(math.atan(18.0 / d['focal']))
    out = {'location': loc, 'rotation': rot, 'fov_degrees': fov,
           'board_centre': bc, 'boom_params': d,
           'source': 'BP_LensRig EventBeginPlay defaults (Azimuth/Reach/'
                      'Height/Tilt/Pan/Focal) + BoardCentre read live off '
                      'the placed instance, 2026-09-02 - this is the '
                      'actual first-boot play framing, not a guess'}
    with open(POSE_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print('  wrote %s' % POSE_PATH)
    print('  location %.1f %.1f %.1f  rotation p=%.2f y=%.2f  fov=%.2f' % (
        loc['x'], loc['y'], loc['z'], rot['pitch'], rot['yaw'], fov))


if __name__ == '__main__':
    if '--dress' in sys.argv:
        dress()
    elif '--clear' in sys.argv:
        clear()
    elif '--pose' in sys.argv:
        pose()
    else:
        print(__doc__)
