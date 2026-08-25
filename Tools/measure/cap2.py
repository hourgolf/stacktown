"""Capture the viewport from a fixed transform, for MEASUREMENT only.

Not evidence. AGENTS.md forbids submitting an automated capture as visual
evidence for the gate; this exists to produce A/B numbers, and every claim it
supports is a number, not a look.
"""
import ue, json, base64, sys, os, subprocess, tempfile
E = 'EditorToolset.EditorAppToolset'

FOV = 28.84          # 70 mm on a 36x24 back - the project's camera
_HERE = os.path.dirname(os.path.abspath(__file__))


def set_fov(fov=FOV):
    """Pin the viewport FOV immediately before a capture.

    CaptureViewport renders at the VIEWPORT's field of view, not at any
    camera's, and saving the level resets that FOV - the trap prep_shot.py was
    written for and warns about in its own docstring. Any script that saves
    (practicals.py, step_roles.py, wipe_owned.py, ...) silently rescales every
    capture taken afterwards. Frames either side of a save are not comparable
    unless this runs, and for a long time in this session they were not.
    """
    # GAME VIEW too, not just FOV. bShowUI=False does not suppress the editor
    # axis widget, and AGENTS.md section 6 lists exactly that as one of the
    # evidenced failures inherited from the bakeoff: "the image the engine
    # decision rested on was an uncomposed viewport grab with the editor axis
    # gizmo still visible". It reappeared in this session's board capture.
    src = ('import unreal\n'
           'les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)\n'
           'ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)\n'
           'les.editor_set_game_view(True)\n'
           'k = les.get_active_viewport_config_key()\n'
           'les.set_level_viewport_fov(%f, k)\n'
           'unreal.SystemLibrary.execute_console_command(ues.get_editor_world(), "stat none")\n'
           'print("fov", round(les.get_level_viewport_fov(k), 3),'
           ' "gameview", les.editor_get_game_view())\n' % fov)
    f = os.path.join(tempfile.gettempdir(), '_capfov.py')
    open(f, 'w').write(src)
    subprocess.run(['python3', os.path.join(_HERE, 'uepy.py'), f],
                   capture_output=True, text=True)

VIEWS = {
    'zoom':   ({'x':934,'y':-830,'z':1044}, {'pitch':-6,'yaw':68,'roll':0}),
    'hero':   ({'x':540,'y':-9272,'z':2946},{'pitch':-12,'yaw':90,'roll':0}),
    'block':  ({'x':2140,'y':-10924,'z':3422},{'pitch':-12,'yaw':90,'roll':0}),
    'corner': ({'x':-361,'y':-843,'z':645}, {'pitch':-10,'yaw':51.8,'roll':0}),
    # SUR_tree0 sits at (560,-300,0) and stands ~690 uu; frame it from the
    # street side at ~1900 uu so the canopy fills the frame vertically.
    'tree':   ({'x':560,'y':-2100,'z':780},  {'pitch':-4,'yaw':90,'roll':0}),
    # BAKED_veh0, a parked car at (600,-690,0). Kerb-height, close.
    'veh':    ({'x':600,'y':-1420,'z':170},  {'pitch':-3,'yaw':90,'roll':0}),
    # BLD_Roof/RoofDeck: a 1080 x 800 Z-facing deck at z=1859. Looked at from
    # straight above, screen-X is world X and screen-Y is world Y, so a
    # projection missing one of them shows as pure directional streaking.
    'roof':   ({'x':542,'y':388,'z':3300},   {'pitch':-89,'yaw':0,'roll':0}),
    'ped':    ({'x':1250,'y':-900,'z':150},  {'pitch':-2,'yaw':90,'roll':0}),
    # Oblique on BAKED_veh0 from the street side. See-through bodywork shows
    # from an angle and hides itself dead-on, which is why the Stage 2 audit
    # missed it in the hero.
    'veh34':  ({'x':1180,'y':-1520,'z':255},  {'pitch':-5,'yaw':124,'roll':0}),
    # --- block-hero candidates for a street with TWO facing rows -------------
    'city':     ({'x':-3830,'y':-912,'z':2185},  {'pitch':-13,'yaw':1,'roll':0}),
    'corner':   ({'x':6333,'y':-1624,'z':1262},  {'pitch':-8,'yaw':148,'roll':0}),
    'junction': ({'x':3767,'y':-3502,'z':1463},  {'pitch':-9,'yaw':100,'roll':0}),
    'blockb':   ({'x':7310,'y':-10146,'z':3263}, {'pitch':-11,'yaw':117,'roll':0}),
    # Tilting DOWN pushes the uncovered end of the board up out of frame and
    # brings the road and pavements in, which is what makes it read as a model
    # on a table rather than a street with a hole at the end of it.
    'heroA':    ({'x':-2600,'y':-800,'z':2600},  {'pitch':-20,'yaw':2,'roll':0}),
    'heroB':    ({'x':-1800,'y':-700,'z':2200},  {'pitch':-16,'yaw':4,'roll':0}),
    'heroC':    ({'x':-3200,'y':-860,'z':3400},  {'pitch':-26,'yaw':2,'roll':0}),
    # The four street trees sit on block A's pavement at y -300 and stack into a
    # wall when viewed end-on from the centreline. Standing on the block B side
    # throws them to the far side of the canyon instead of down the middle.
    'heroD':    ({'x':-3200,'y':-1250,'z':3400}, {'pitch':-26,'yaw':5,'roll':0}),
    'heroE':    ({'x':-2400,'y':-1350,'z':2900}, {'pitch':-22,'yaw':8,'roll':0}),
    # Mid's east flank at world x 4158, viewed from off the east end of the block
    # Mid's east flank is at world x 4158 and spans y 62..750 - BEHIND the
    # street line, so it is only visible from off the east end of the block.
    'flankMid': ({'x':7600,'y':430,'z':1450},    {'pitch':-9,'yaw':180,'roll':0}),
    # ModernTest sits at x 4400..5420 on block A's facade line, so this frames
    # it beside the vernacular Mid building under identical light.
    # At 28.84 deg the frame is 0.514 x distance, so a 1020-wide building plus
    # its vernacular neighbour needs ~5000 uu of standoff, not 2350.
    'modern':   ({'x':4050,'y':-5000,'z':1900},  {'pitch':-9,'yaw':82,'roll':0}),
    # street 2 canyon: block C's north row on the left, block B's rear on the right
    'streetC':  ({'x':-2600,'y':-3250,'z':2600},  {'pitch':-20,'yaw':2,'roll':0}),
    # oblique on the island's east end, showing both rows meeting at a corner
    # frame width is 0.514 x distance, so a 4150-wide island needs ~6000 uu
    'islandC':  ({'x':9600,'y':-3050,'z':3100},   {'pitch':-15,'yaw':196,'roll':0}),
    # street 3, block C's south row
    'streetD':  ({'x':-2200,'y':-5800,'z':1900},  {'pitch':-14,'yaw':3,'roll':0}),
    # whole board, oblique. Board diagonal is ~9000 uu and frame width is
    # 0.514 x distance, so this needs ~18000 uu of standoff.
    'city':     ({'x':15000,'y':-16000,'z':11000}, {'pitch':-31,'yaw':134,'roll':0}),
    # block C south row's arcade, from the service street pavement
    'arcadeC':  ({'x':1750,'y':-6450,'z':330},   {'pitch':-3,'yaw':90,'roll':0}),
    # the intersection of street 1 and the avenue, from the north-west
    # stay INSIDE the board footprint: at y +1900 the camera sat behind the
    # studio backdrop and every frame came back pure black, mean 0.000
    'junction': ({'x':1800,'y':880,'z':4600},    {'pitch':-49,'yaw':-27,'roll':0}),
    # block D, the deco row, from across street 1
    'deco':     ({'x':5000,'y':-780,'z':1150},   {'pitch':-7,'yaw':-19,'roll':0}),
    # whole board now that it is 10700 x 7600
    'board':    ({'x':19000,'y':-19000,'z':14000},{'pitch':-30,'yaw':129,'roll':0}),
}

def capture(path, view='zoom', fov=True):
    if fov:
        set_fov()
    loc, rot = VIEWS[view]
    xf = {'location':loc,'rotation':rot,'scale':{'x':1,'y':1,'z':1}}
    # 'annotations' is REQUIRED and there is no bShowActorLabels key - passing
    # one is accepted and silently ignored, and the capture comes back with
    # white label boxes over the exact surfaces being measured. The off switch
    # is maxLabelDistance=0 and maxLabels=0.
    r = ue.tool(E,'CaptureViewport',{'captureTransform':xf,'bShowUI':False,
        'annotations':{'gridSpacing':0,'gridExtent':0,'gridHeight':0,
                       'maxLabelDistance':0,'classFilter':None,'maxLabels':0}})
    try:
        d = json.loads(r)['returnValue']['image']['data']
    except Exception:
        raise SystemExit('capture failed: %s' % r[:300])
    open(path,'wb').write(base64.b64decode(d))
    return os.path.getsize(path)

if __name__ == '__main__':
    p = sys.argv[1]; v = sys.argv[2] if len(sys.argv)>2 else 'zoom'
    print('wrote %s (%s) %d bytes' % (p, v, capture(p, v)))
