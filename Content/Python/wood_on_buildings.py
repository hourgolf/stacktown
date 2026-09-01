#!/usr/bin/env python3
"""Put the seven timbers on REAL BAKED BUILDINGS and photograph them.

    python3 Content/Python/wood_on_buildings.py            place, capture, clean up
    python3 Content/Python/wood_on_buildings.py --keep     leave them standing

WHY THIS EXISTS. The first timber capture used seven CUBES. It proved the
import path and answered nothing the owner needed: "still can't see anything
built so hard to make an informed decision." Tone at building scale, grain
scale against a real facade, and whether 0.0005 tiling holds on a 1000 uu
mass are not judgeable from a 700 uu block - and the tiling was flagged in
fabrication.py's own comment as "a starting point to be trimmed on a
building", which a cube is not.

WHAT THESE ARE, AND ARE NOT. The subjects are FLAGSHIP models: they carry
windows, bands, cornices and glazing. Wood on an articulated facade is NOT
direction B's look, which is windowless carved mass (B1). These frames answer
the MATERIAL questions only - tone at scale, grain scale, figure legibility,
whether the ladder separates on real geometry. The massing question stays
open until the massing-only spec key lands. Frames are labelled so the two
can never be conflated.

STAGED FAR OFF THE BOARD at y=60000, the pattern bake_catalogue uses, and
removed afterwards with the removal VERIFIED by search rather than by
trusting return values. The level is asserted before every mutating step.
TestCity is never saved.
"""
import json
import os
import sys
import time
import base64

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'StacktownAlpha', 'Tools', 'measure'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '..', 'Tools', 'measure'))
import _path  # noqa: F401,E402
import ue  # noqa: E402

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
APP = 'EditorToolset.EditorAppToolset'
BAKED = '/Game/Stacktown/Baked'
MATD = '/Game/Stacktown/Materials'
LEVEL = '/Game/Maps/TestCity'
# PROJECT ROOT is two levels up from Content/Python, not three - the first
# version appended 'StacktownAlpha' to a path that already ended in it and
# wrote every frame into StacktownAlpha/StacktownAlpha/Saved/. Evidence in
# the wrong place is evidence nobody finds; Saved/ is the contract.
PROJECT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(PROJECT, 'Saved', 'DirectionB')

# One species per building, chosen from the PIN TABLE's own selection so the
# heights span the measured range (370 - 7490 uu) rather than being picked by
# eye. Pale timbers on small masses, dark on tall, so tone and scale are not
# confounded - if a dark building reads heavy it is the tone, not the size.
#
# THE TILING CHECK IS BUILT INTO THIS LIST, not run separately. tooth=0.0005
# is one tile per 2,000 uu, derived rather than eyeballed and labelled in
# fabrication.py as a starting point to trim ON A BUILDING. The list spans
# BOTH ENDS deliberately: vernacular8_t0 at 370 uu sees a fifth of a tile,
# tower_t6 at 7490 uu sees nearly four. If one tile per 2,000 uu is wrong the
# two ends fail in OPPOSITE directions - the shed reads as a smear and the
# tower as wallpaper - and one frame containing both is what makes that
# legible instead of a guess.
SUBJECTS = [
    ('maple',  'SM_Bld_vernacular8_t0_w820',    370),
    ('pine',   'SM_Bld_contemporary_t1_w1230',  829),
    ('ash',    'SM_Bld_modern8_t3_w1230',      1144),
    ('oak',    'SM_Bld_modern8_t5_w1640',      1729),
    ('cherry', 'SM_Bld_modern3_t3_w1230',      2314),
    ('sapele', 'SM_Bld_contemporary4_t4_w1230', 3286),
    ('walnut', 'SM_Bld_tower_t6_w1230',        7490),
]
BASE_Y = 60000.0
SPACING = 2600.0


def assert_level():
    lvl = json.loads(ue.tool(S, 'get_current_level', {}))['returnValue']
    assert lvl == LEVEL, 'level is %s, not %s - refusing to touch it' % (lvl, LEVEL)
    return lvl


def place():
    made = []
    x = 0.0
    for sp, mesh, h in SUBJECTS:
        nm = 'WOODBLD_%s' % sp
        try:
            ref = json.loads(ue.tool(S, 'add_to_scene_from_asset', {
                'asset_path': '%s/%s' % (BAKED, mesh), 'name': nm,
                'xform': {'location': {'x': x, 'y': BASE_Y, 'z': 0.0}}}))['returnValue']
        except Exception as e:
            print('%-8s %-32s PLACE FAILED %s' % (sp, mesh, str(e)[:60]))
            x += SPACING
            continue
        ue.tool(A, 'set_label', {'actor': ref, 'label': nm})
        # override EVERY slot: a baked building is one mesh with N slots, and
        # leaving any unbound would show flagship paint beside the timber and
        # make the frame unreadable as a material test
        comps = json.loads(ue.tool(A, 'get_components', {'actor': ref}))['returnValue']
        smc = [c for c in comps if 'StaticMeshComponent' in c.get('refPath', '')
               or c.get('refPath', '').endswith('.StaticMeshComponent0')]
        mi = '%s/MI_wood_%s.MI_wood_%s' % (MATD, sp, sp)
        nslots = 0
        if smc:
            got = ue.tool(OBJ, 'get_properties',
                          {'instance': smc[0], 'properties': ['staticMesh']})
            nslots = 12   # over-provision; extra entries are ignored
            ue.tool(OBJ, 'set_properties', {'instance': smc[0], 'values': json.dumps(
                {'overrideMaterials': [{'refPath': mi}] * nslots})})
            back = ue.tool(OBJ, 'get_properties',
                           {'instance': smc[0], 'properties': ['overrideMaterials']})
            ok = 'MI_wood_%s' % sp in back
        else:
            ok = False
        print('%-8s %-32s h=%5d  %s' % (sp, mesh, h,
              'wood bound' if ok else 'BIND FAILED'))
        made.append({'sp': sp, 'ref': ref, 'x': x, 'h': h})
        x += SPACING
    return made


def capture(made, tag, cam, dwell=10, frames=4):
    ann = {'gridSpacing': 0.0, 'gridExtent': 0.0, 'gridHeight': 0.0,
           'maxLabelDistance': 0.0, 'classFilter': None, 'maxLabels': 0}
    ue.tool(APP, 'SetCameraTransform', {'transform': cam})
    time.sleep(dwell)
    os.makedirs(OUT, exist_ok=True)
    last = None
    for i in range(frames):
        r = json.loads(ue.tool(APP, 'CaptureViewport', {
            'captureTransform': cam, 'annotations': ann,
            'bShowUI': False}))['returnValue']
        last = os.path.join(OUT, '%s_%d.png' % (tag, i))
        open(last, 'wb').write(base64.b64decode(r['image']['data']))
        time.sleep(1.6)
    print('  %s -> %s' % (tag, last))
    return last


def cleanup(made):
    assert_level()
    for m in made:
        try:
            ue.tool(S, 'remove_from_scene', {'actor': m['ref']})
        except Exception as e:
            print('  remove failed %s: %s' % (m['sp'], str(e)[:50]))
    left = json.loads(ue.tool(S, 'find_actors', {
        'name': 'WOODBLD', 'tag': '', 'collision_channels': []}))['returnValue']
    print('WOODBLD left in level: %d' % len(left))
    assert not left, 'cleanup incomplete'
    print('level clean; %s NOT saved' % LEVEL)


README = """# Timber material test — 31 Aug 2026

## READ THIS BEFORE JUDGING THESE FRAMES

The buildings in these captures are **FLAGSHIP models**. They carry windows,
bands, cornices and glazing slots.

**This is NOT what direction B looks like.** Direction B's buildings are
WINDOWLESS CARVED MASSES (DIRECTION_B.md, B1) — windows exist only as light
at night. No such geometry exists yet; it waits on the massing-only spec key.

These frames were taken to answer the MATERIAL questions and only those:

  - does the tone ladder separate at building scale?
  - is the grain the right SIZE on a real facade?
  - is the figure legible at block-hero and at player zoom?
  - does 0.0005 tiling (one tile per 2,000 uu) hold at both ends of the
    height range — a 370 uu shed and a 7,490 uu tower are both in frame
    precisely so it can fail in opposite directions if it is wrong?

Any judgement about MASSING, silhouette, window treatment or how the city
reads is not supported by these images and must not be drawn from them.

Species, pale to dark: maple, pine, ash, oak, cherry, sapele, walnut.
Half A only — species tone plus grain-shaped ROUGHNESS. The colour figure
needs the approved master edit and is not in these frames.
"""


def main():
    print('level:', assert_level())
    made = place()
    if not made:
        return 1
    print()
    span = SPACING * (len(SUBJECTS) - 1)
    # BLOCK HERO: the whole row, tone ladder against real massing
    capture(made, 'wood_on_FLAGSHIP_massing_blockhero',
            {'location': {'x': span / 2.0, 'y': BASE_Y - 14000.0, 'z': 3200.0},
             'rotation': {'pitch': -9.0, 'yaw': 90.0, 'roll': 0.0},
             'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}})
    # PLAYER ZOOM: close on the mid three, where grain scale is judged
    capture(made, 'wood_on_FLAGSHIP_massing_playerzoom',
            {'location': {'x': SPACING * 3.0, 'y': BASE_Y - 3200.0, 'z': 900.0},
             'rotation': {'pitch': -6.0, 'yaw': 90.0, 'roll': 0.0},
             'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}})
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'README.md'), 'w').write(README)
    print('  caveat written to %s/README.md' % OUT)
    if '--keep' in sys.argv:
        print('\n--keep: actors left standing, REMOVE THEM before any bake')
        return 0
    print()
    cleanup(made)
    return 0


if __name__ == '__main__':
    sys.exit(main())
