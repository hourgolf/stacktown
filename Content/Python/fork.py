#!/usr/bin/env python3
"""Fork M_WoodMaster off the shared master, and move direction B onto it.

    python3 Content/Python/fork.py --plan     read-only: what WOULD happen
    python3 Content/Python/fork.py --fork     duplicate + re-parent
    python3 Content/Python/fork.py --verify   prove the shared master is untouched

Owner, 2026-09-02: the wooden city and the flagship are SEPARATE PROJECTS,
and nothing direction B does may affect flagship models or the teams working
on them. So direction B stops sharing M_StacktownMaster and takes a copy.

WHAT --plan EXISTS TO ANSWER, and why it runs before anything is re-parented.
The seven MI_wood_* are unambiguously this lane's. The board and studio
instances - MI_board_plot, MI_board_road, MI_model_board, MI_studio_grey -
are NOT obviously ours: they dress the plate and the room, and whether the
flagship also renders them is a referencer question. Re-parenting one the
flagship uses would change the flagship's look, which is the exact thing the
owner just forbade. So --plan reports each candidate's referencers and
re-parents NOTHING; a human decides, then --fork acts on the settled list.

The shared master is duplicated, never modified. --verify re-asserts its
expression count and its two original drivers afterwards, because "I only
copied it" is a claim about intent, not about state.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path            # noqa: F401,E402
import ue               # noqa: E402
import woodmaster as WM  # noqa: E402

AT = 'editor_toolset.toolsets.asset.AssetTools'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
M = 'editor_toolset.toolsets.material.MaterialTools'
APP = 'EditorToolset.EditorAppToolset'
SHARED_ASSET = WM.SHARED.split('.')[0]
FORK_ASSET = WM.FORK.split('.')[0]


def _pie_guard():
    assert not json.loads(ue.tool(APP, 'IsPIERunning', {}))['returnValue'], \
        'PIE active - refusing'


def _refs(path):
    return json.loads(ue.tool(AT, 'get_referencers',
                              {'asset_path': path}))['returnValue']


# THE BOUNDARY RULE, coordinator 2026-09-02. An MI is direction B's to
# re-parent IF AND ONLY IF every referencer lives in TestCity or in a
# direction-B-owned asset. One flagship referencer and it stays shared -
# re-parenting a material the flagship also renders would change the
# flagship's look in the act of complying with the instruction not to.
# Referencers on BOTH sides mean DUPLICATE, not re-parent: the flagship keeps
# its instance untouched and TestCity's actors point at the wood copy.
B_ROOTS = ('/Game/Maps/TestCity', '/Game/Stacktown/BakedWood',
           '/Game/Stacktown/LookStudy', '/Game/Stacktown/Materials/MI_wood_',
           '/Game/Stacktown/Materials/M_WoodMaster')
FLAGSHIP_MARKS = ('Sandbox_Bench', 'Stage2_', 'OneBuildingTest', 'Stage1_')


def side(ref):
    """B, FLAGSHIP, or UNKNOWN. Unknown counts AS flagship when deciding -
    the conservative direction, because the cost of a false 'ours' is
    changing the flagship's look and the cost of a false 'theirs' is one
    duplicated material."""
    if any(m in ref for m in FLAGSHIP_MARKS):
        return 'FLAGSHIP'
    if any(ref.startswith(r) for r in B_ROOTS):
        return 'B'
    return 'UNKNOWN'


def verdict(refs):
    sides = {side(r) for r in refs}
    if not refs:
        return 'UNREFERENCED - safe to re-parent, but check it is still used'
    if sides == {'B'}:
        return 'RE-PARENT - every referencer is direction B'
    if 'B' in sides:
        return 'DUPLICATE - referenced by both sides'
    return 'LEAVE SHARED - no direction-B referencer'


def plan():
    """Read-only. Nothing is created, nothing is re-parented."""
    print('shared master :', SHARED_ASSET)
    print('fork would be :', FORK_ASSET)
    ex = json.loads(ue.tool(AT, 'exists', {'path': FORK_ASSET}))['returnValue']
    print('fork exists already:', ex)
    dirty = json.loads(ue.tool(AT, 'is_dirty',
                               {'asset_path': SHARED_ASSET}))['returnValue']
    print('shared master dirty (unsaved edits present):', dirty)
    print('\nMIs this lane owns outright - will be re-parented:')
    for p in WM.WOOD_MIS:
        print('   ', p.split('.')[0])
    print('\nCANDIDATES - referencer evidence, nothing touched:')
    for nm in WM.CANDIDATE_SHARED:
        p = '%s/%s' % (WM.MATD, nm)
        if not json.loads(ue.tool(AT, 'exists', {'path': p}))['returnValue']:
            print('  %-16s (does not exist)' % nm)
            continue
        r = _refs(p)
        print('  %-16s %2d referencers -> %s' % (nm, len(r), verdict(r)))
        for x in r[:8]:
            print('        [%-8s] %s' % (side(x), x))
        if len(r) > 8:
            print('        ... %d more' % (len(r) - 8))


# THE SETTLED LIST, decided 2026-09-02 from referencer evidence plus
# provenance, and recorded here so the next run does not re-litigate it.
#
#   MI_wood_* (7)   RE-PARENT     this lane's outright
#   MI_board_plot   RE-PARENT     0 referencers, but PROVENANCE overrides the
#   MI_board_road   RE-PARENT     snapshot: wood_set.py BOARD_STOCKS declares
#                                 both and ensure_board_mis() creates them,
#                                 applied to ZONE_SetBRoad / ZONE_SetBPlots.
#                                 Zero referencers because the rig is DOWN,
#                                 not because they are dead. Verified in the
#                                 source, not taken on the relay's word.
#   MI_model_board  LEAVE SHARED  5 flagship referencers, no direction B
#   MI_studio_grey  LEAVE SHARED  referenced by both sides - and USING an
#                                 unchanged shared material changes nothing
#                                 for the flagship, so the separation rule
#                                 does not require acting. A per-session
#                                 repoint was considered and REJECTED: the
#                                 studio room's actors are persistent SAVED
#                                 content, and reapplying a repoint to
#                                 persistent actors every session is
#                                 "looks done but isn't" wearing a script.
#                                 When D19's room work actually needs to edit
#                                 that material: duplicate to the fork and
#                                 repoint ONCE, saved on the owner's word.
ALSO = ('%s/MI_board_plot.MI_board_plot' % WM.MATD,
        '%s/MI_board_road.MI_board_road' % WM.MATD)


def fork(also=ALSO):
    """Duplicate the master and re-parent. `also` = extra MIs, decided by a
    human from --plan's referencer report, never guessed here."""
    _pie_guard()
    if not json.loads(ue.tool(AT, 'exists', {'path': FORK_ASSET}))['returnValue']:
        ok = json.loads(ue.tool(AT, 'duplicate', {
            'path': SHARED_ASSET, 'new_path': FORK_ASSET}))['returnValue']
        assert ok, 'duplicate refused'
        print('duplicated ->', FORK_ASSET)
    else:
        print('fork already exists, not re-duplicating')
    parent = {'refPath': WM.FORK}
    for p in tuple(WM.WOOD_MIS) + tuple(also):
        inst = {'refPath': p}
        ue.tool(MIT, 'set_parent', {'instance': inst, 'parent': parent})
        print('  re-parented', p.split('/')[-1].split('.')[0])
    verify()


def verify():
    """Cold read of BOTH masters. This is also the POST-RESTART check.

    A save reporting is_dirty=False proves the write landed, not that what
    landed is right - so after an editor relaunch the fork is read back from
    scratch here rather than trusted. Everything below comes off the loaded
    assets; nothing is remembered.
    """
    rows = []
    n = len(json.loads(ue.tool(M, 'get_expressions', {
        'material_or_function': {'refPath': WM.SHARED}}))['returnValue'])
    rows.append(('shared master expressions', n == 195, n))
    rows.append(('fork present', json.loads(ue.tool(AT, 'exists', {
        'path': FORK_ASSET}))['returnValue'], FORK_ASSET.split('/')[-1]))

    import wear as W  # noqa: E402  - imported here so --plan stays light
    fn = len(json.loads(ue.tool(M, 'get_expressions', {
        'material_or_function': {'refPath': WM.FORK}}))['returnValue'])
    rows.append(('fork expressions', fn == 210, fn))

    for name, idx in WM.__dict__.get('WEAR_CHANNELS', ()) or (
            ('Age', 0), ('Attention', 4), ('Failure', 5), ('Scorch', 6)):
        e = W.find_param(name)
        if e is None:
            rows.append(('%s present' % name, False, 'MISSING'))
            continue
        p = W._props(e, ['PrimitiveDataIndex', 'bUseCustomPrimitiveData',
                         'DefaultValue'])
        good = (p.get('PrimitiveDataIndex') == idx
                and p.get('bUseCustomPrimitiveData') is True
                and p.get('DefaultValue') == 0.0)
        rows.append(('%s ch%d, cpd, default 0' % (name, idx), good,
                     'ch%s' % p.get('PrimitiveDataIndex')))

    # the Age chain and the normals correction, neither covered by cpdmap
    tint = any('VectorParameter' in e['refPath'] for e in
               json.loads(ue.tool(M, 'get_expressions', {
                   'material_or_function': {'refPath': WM.FORK}}))['returnValue'])
    rows.append(('AgedTint vector param on the fork', tint, tint))
    ins = json.loads(ue.tool(M, 'get_expression_inputs', {
        'material_or_function': {'refPath': WM.FORK},
        'expression': {'refPath': WM.FORK + ':MaterialExpressionAbs_0'}}))['returnValue']
    if isinstance(ins, str):
        ins = json.loads(ins)
    src = ''
    for i in ins:
        if isinstance(i, dict):
            x = i.get('expression')
            src = (x.get('refPath') if isinstance(x, dict) else x) or ''
    rows.append(('curvature proxy reads VertexNormalWS',
                 'VertexNormalWS' in src, src.rsplit(':', 1)[-1] or 'NOTHING'))

    print('%-42s %-6s %s' % ('check', 'pass', 'value'))
    for label, ok, val in rows:
        print('%-42s %-6s %s' % (label, 'YES' if ok else 'NO', val))
    allok = all(r[1] for r in rows)
    print('\n%s' % ('ALL PASS' if allok else 'FAILURES - do not build on this'))
    return allok


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else '--plan'
    {'--plan': plan, '--fork': fork, '--verify': verify}[cmd]()
