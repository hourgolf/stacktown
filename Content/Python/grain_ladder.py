#!/usr/bin/env python3
"""A GRAIN-SCALE LADDER: one block, one light, four values of PaperTiling.

    python3 Content/Python/grain_ladder.py

WHY. The owner's standing note across three boards is that the timber reads
like VENEER rather than sawn stock. wood_board.py sets PaperTiling to 0.0025
and calls it "five times coarser" than fabrication's 0.0005. That comment is
backwards, and the arithmetic is in fabrication's own table: card_prop
measures 0.006 as SACKING and 0.080 as NEARLY SMOOTH on the same object, so a
LOWER PaperTiling makes features BIGGER. 0.0025 is therefore five times FINER
than the shipped timber value, not coarser - which is exactly the veneer read.

That is an argument, and an argument is not evidence. This shoots the ladder.

ONE VARIABLE. Same block, same camera, same key, same material instance -
only PaperTiling moves between frames, so a difference in the frames is a
difference in grain scale and nothing else. Exposure cannot drift underneath
it: ue.tool() now refuses a capture whose lens state is off the gate
condition, which is the guard written after the f/22 incident.
"""
import base64
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'Tools', 'measure'))
import _path  # noqa: F401,E402
import ue  # noqa: E402
import wood_board as wb  # noqa: E402

S, A, OBJ, MIT = wb.S, wb.A, wb.OBJ, wb.MIT
APP, MATD, LEVEL, OUT = wb.APP, wb.MATD, wb.LEVEL, wb.OUT
BAKED = '/Game/Stacktown/BakedWood'

# 0.0025 is what the boards have been shot at; 0.0005 is fabrication's shipped
# timber value; the outer two bracket it so the answer is not pinned to an end
LADDER = [0.0025, 0.0010, 0.0005, 0.00025]

# SECOND LADDER, and it asks a different question. The first ladder showed
# directionality rising only from 1.24 to 1.42 as features grew - present, but
# nothing like sawn timber, which should be strongly directional. The suspect
# is the master's CARD WEAVE normal: _timber sets PaperNormalAmount 1.8, so
# every wooden block wears a card model's paper tooth at nearly twice unit
# amplitude, competing with its own grain. fabrication's table documents this
# exact failure once already - flock "inherited the master's card weave at
# triple amplitude" and read as green felt. This measures whether timber is
# the second instance.
NORMAL_LADDER = [1.8, 0.9, 0.3, 0.0]

# THIRD LADDER: how hard the figure drives colour. GrainGain is live (2.7-3.1,
# normalised per species by sd) but the B1 reference carries far stronger
# dark/light banding than anything this rig has produced - a lit timber face
# there measures sd 67 across its own width. This asks how far the gain has to
# go. Absolute highpass_sd is not comparable across frames at different
# scales, so the ladder is read RELATIVELY: same block, same camera, only the
# gain moves, and the eye picks from the frames.
GAIN_LADDER = [1.0, 2.0, 3.0, 5.0, 8.0]
BLOCK, SPECIES = 'low', 'ash'      # ash is open-grained: the figure is legible


def _species():
    """--species=oak overrides, for the crossed-vs-consistent known-answer cell."""
    for a in sys.argv[1:]:
        if a.startswith('--species='):
            return a.split('=', 1)[1]
    return SPECIES


def main():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s' % lvl
    assert json.loads(ue.tool(S, 'find_actors', {
        'name': 'LIGHT_BoardKey', 'tag': '',
        'collision_channels': []}))['returnValue'], 'run board_light.py first'

    # NOTHING ELSE MAY BE STANDING ON THE STAGE. Every rig in this lane
    # stages at the same point near the key's aim, and several take --keep, so
    # a leftover town or carving row sits exactly where this block goes. That
    # is not cosmetic: the measurement patch is a fixed rectangle in frame, so
    # a stale actor is silently measured INSTEAD of the subject, and the
    # ladder reports numbers for the wrong object. It did - a gain ladder was
    # read off a carving comparison left over from the previous run, and the
    # parameter looked inert because the frame never contained it.
    #
    # Refusing is right rather than auto-clearing: another lane's actors are
    # not mine to delete, and a rig that quietly tidies the level is how you
    # lose someone else's work.
    intruders = []
    for pat in ('SETB_', 'ZONE_SetB', 'CARVE_', 'BLD2_', 'ZONE_Board'):
        intruders += [a for a in json.loads(ue.tool(S, 'find_actors', {
            'name': pat, 'tag': '',
            'collision_channels': []}))['returnValue']]
    assert not intruders, (
        '%d rig actors are standing on the stage (%s...). This ladder '
        'measures a fixed rectangle in frame and would measure them instead '
        'of the subject. Clear them and re-run.'
        % (len(intruders),
           ', '.join(a['refPath'].rsplit('.', 1)[-1] for a in intruders[:4])))

    for stale in ('GRAIN_',):
        for a in json.loads(ue.tool(S, 'find_actors', {
                'name': stale, 'tag': '',
                'collision_channels': []}))['returnValue']:
            ue.tool(S, 'remove_from_scene', {'actor': a})

    ox, oy = wb.BASE_X + 3400.0, wb.BASE_Y + 2440.0
    r = json.loads(ue.tool(S, 'add_to_scene_from_asset', {
        'asset_path': '%s/SM_Mass_%s' % (BAKED, BLOCK), 'name': 'GRAIN_Block',
        'xform': {'location': {'x': ox, 'y': oy, 'z': 0.0},
                  'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                  'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}))['returnValue']
    ue.tool(A, 'set_label', {'actor': r, 'label': 'GRAIN_Block'})

    # ONE INSTANCE PER SPECIES. This was 'MI_grainladder' for every species,
    # and create() refuses to overwrite an existing asset - an error this code
    # swallows as benign, because a re-run is normal. So --species=oak kept
    # ASH as its parent and produced ash frames under an oak name. The tell
    # was two species agreeing to three decimals; the instrument was wrong,
    # not the hypothesis it appeared to refute. Per-species name AND an
    # unconditional set_parent, so neither a stale asset nor a swallowed
    # error can serve the wrong wood again.
    sp = _species()
    name = 'MI_grainladder_%s' % sp
    ref = {'refPath': '%s/%s.%s' % (MATD, name, name)}
    src = {'refPath': '%s/MI_wood_%s.MI_wood_%s' % (MATD, sp, sp)}
    try:
        ue.tool(MIT, 'create', {'folder_path': MATD, 'asset_name': name,
                                'parent': src})
    except Exception as e:
        if 'already exists' not in str(e):
            raise
    ue.tool(MIT, 'set_parent', {'instance': ref, 'parent': src})
    ue.tool(MIT, 'set_scalar_parameter',
            {'instance': ref, 'name': 'PaperRotate', 'value': 0.0})
    for c in json.loads(ue.tool(A, 'get_components', {
            'actor': r}))['returnValue']:
        if 'StaticMeshComponent' in c.get('refPath', ''):
            ue.tool(OBJ, 'set_properties', {'instance': c, 'values':
                    json.dumps({'overrideMaterials': [ref]})})

    # close enough that the figure is countable, not a texture impression
    cam = {'location': {'x': ox - 1500.0, 'y': oy - 950.0, 'z': 430.0},
           'rotation': {'pitch': -7.0, 'yaw': 30.0, 'roll': 0.0},
           'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}
    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    os.makedirs(OUT, exist_ok=True)
    ue.tool(APP, 'SetCameraTransform', {'transform': cam})
    time.sleep(8)
    normals = '--normal' in sys.argv
    gains = '--gain' in sys.argv
    if normals:
        # hold tiling at the value the first ladder chose, vary only amplitude
        ue.tool(MIT, 'set_scalar_parameter',
                {'instance': ref, 'name': 'PaperTiling', 'value': 0.0005})
        time.sleep(2)
    if gains:
        ue.tool(MIT, 'set_scalar_parameter',
                {'instance': ref, 'name': 'PaperTiling', 'value': 0.0005})
        time.sleep(2)
    ladder = GAIN_LADDER if gains else (NORMAL_LADDER if normals else LADDER)
    pname = ('GrainGain' if gains else
             ('PaperNormalAmount' if normals else 'PaperTiling'))
    for t in ladder:
        ue.tool(MIT, 'set_scalar_parameter',
                {'instance': ref, 'name': pname, 'value': float(t)})
        time.sleep(4)
        got = json.loads(ue.tool(APP, 'CaptureViewport', {
            'captureTransform': cam, 'annotations': ann,
            'bShowUI': False}))['returnValue']
        tag = '%s%s_%s' % ('GAIN' if gains else ('NRM' if normals else 'GRAIN'),
                           '' if sp == SPECIES else '_' + sp,
                           ('%g' % t).replace('.', 'p'))
        open(os.path.join(OUT, '%s.png' % tag), 'wb').write(
            base64.b64decode(got['image']['data']))
        print('captured %-14s %s %g' % (tag, pname, t))

    for a in json.loads(ue.tool(S, 'find_actors', {
            'name': 'GRAIN_', 'tag': '',
            'collision_channels': []}))['returnValue']:
        ue.tool(S, 'remove_from_scene', {'actor': a})
    print('cleaned; %s NOT saved' % LEVEL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
