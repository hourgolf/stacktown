"""Two named camera modes, switched by one call, VERIFIED by read-back.

    judge   the gate condition, unchanged doctrine: depth of field OFF, no
            grain, no fringe, manual exposure. Everything this project judges
            itself by - gate evidence, A-E lines, sweeps - is a judge frame,
            so weak geometry can never hide behind optics.

    show    the shipped claim: the hero look (f/2.8 on a 400 mm BACK, 8
            blades, 1/240, ISO 1568) plus the authored finishing set. A
            photograph of a real miniature has macro optics; their absence is
            itself a render-tell, so the cold reader sees this first.
            Stopped down from f/2 on 29 Aug after a reader read the brick as
            more convincing in judge - see dof.HERO for the ladder.

WHY THE BACK AND NOT THE APERTURE. Derived, and the derivation is already in
MASTER_MATERIAL_SPEC: at these subject distances aperture alone does nothing,
because the world is built 1:1 and the camera stands where a city photographer
would. The size of the camera BACK is the knob that asks the art-direction
question - 36 mm photographs a city, 400 mm photographs a model of one. Values
come from the 25 Aug contact sheet, not from taste applied today.

EVERY FRAME IS STAMPED. cap2.capture() writes a sidecar recording the mode
that took it, so a show frame can never quietly become judging evidence. That
stamp is what makes an easy toggle safe: the same reasoning as BakePath on a
baked mesh - a picture that cannot say how it was produced is weaker evidence
than it looks.

    python3 Tools/measure/lensrig.py judge
    python3 Tools/measure/lensrig.py show --focus 17500
"""
import os, sys, json, subprocess, tempfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = os.path.join(HERE, 'lens_mode.json')
sys.path.insert(0, HERE)
import dof                                   # noqa: E402  the settled hero look

# the authored finishing set, from filmlook.py - one source, not a second copy
FINISH_ON = {'film_grain_intensity': 1.05,
             'film_grain_intensity_shadows': 1.25,
             'film_grain_intensity_midtones': 1.0,
             'film_grain_intensity_highlights': 0.62,
             'vignette_intensity': 0.42,
             'scene_fringe_intensity': 0.30}
# OFF keeps the vignette: filmlook records it as a LENS property rather than a
# film one, costing nothing and holding the eye inside the board.
FINISH_OFF = dict(FINISH_ON, film_grain_intensity=0.0, scene_fringe_intensity=0.0)

CHECK = ['depth_of_field_focal_distance', 'depth_of_field_fstop',
         'depth_of_field_sensor_width', 'camera_shutter_speed', 'camera_iso',
         'film_grain_intensity', 'scene_fringe_intensity', 'vignette_intensity',
         'bloom_intensity']


def _post(body, marker='LENS'):
    src = ('import unreal, json\n'
           'eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n'
           'for a in eas.get_all_level_actors():\n'
           '    if a.get_actor_label() != "LOOK_Post":\n'
           '        continue\n'
           '    st = a.get_editor_property("settings")\n'
           + body +
           '    a.set_editor_property("settings", st)\n'
           '    out = {k: float(st.get_editor_property(k)) for k in %r}\n'
           '    print("%s " + json.dumps(out))\n' % (CHECK, marker))
    f = os.path.join(tempfile.gettempdir(), '_lensrig.py')
    open(f, 'w').write(src)
    r = subprocess.run(['python3', os.path.join(HERE, 'uepy.py'), f],
                       capture_output=True, text=True)
    line = next((l for l in r.stdout.splitlines() if marker in l), None)
    if not line:
        raise SystemExit('lensrig: LOOK_Post not reached\n' + r.stdout[-500:])
    return json.loads(line.split(marker, 1)[1].strip())


def _set(pairs):
    b = ''
    for k, v in pairs.items():
        b += '    st.set_editor_property("%s", %f)\n' % (k, v)
        b += '    st.set_editor_property("override_%s", True)\n' % k
    return b


def apply(mode, focus=None, grain=True):
    """Apply a mode and RETURN WHAT THE EDITOR ACTUALLY HOLDS afterwards.

    Read-back is not decoration. A restore that printed its intent rather than
    its result is exactly how t.MaxFPS stayed throttled while reporting it had
    been put back; this returns the editor's own numbers and refuses on a
    mismatch instead of announcing success.
    """
    if mode == 'judge':
        want = dict(FINISH_OFF)
        want.update({'depth_of_field_fstop': 4.0, 'camera_shutter_speed': 60.0,
                     'camera_iso': 800.0, 'bloom_intensity': 0.0,
                     'depth_of_field_focal_distance': 0.0})
        body = _set(want)
        body += '    st.set_editor_property("override_depth_of_field_focal_distance", False)\n'
    elif mode == 'show':
        if not focus:
            raise SystemExit('lensrig: show mode needs --focus <uu to subject>')
        # GRAIN IS OPT-OUT, and the default is under review. filmlook.py
        # turned grain OFF and recorded why: at 1.05 with shadows at 1.25 it
        # is visible as noise on every flat surface, and it FIGHTS DEPTH OF
        # FIELD - "blur plus grain reads as a bad scan rather than as a
        # photograph" - to be reconsidered once the DOF work is settled. Show
        # mode is that DOF work, so the two arrived together and the warning
        # applies to exactly this combination. The authored values live in
        # filmlook so they return exactly; that is not the same as approved.
        want = dict(FINISH_ON)
        if not grain:
            want['film_grain_intensity'] = 0.0
        # ISO COMES FROM HERO, NOT FROM A LITERAL. UE's post volume is a
        # physical camera: f-stop drives exposure as well as defocus, so a
        # stop change with ISO pinned at 800 darkens the frame by exactly the
        # amount it defocuses less. That coupling is what invalidated the
        # first f-stop sweep - it produced a brightness ladder wearing a
        # depth-of-field label. HERO['iso'] is 800*(N/2)^2, which holds the
        # exposure the shutter was chosen to match.
        want.update({'depth_of_field_fstop': dof.HERO['fstop'],
                     'depth_of_field_sensor_width': dof.HERO['sensor'],
                     'depth_of_field_focal_distance': float(focus),
                     'camera_shutter_speed': dof.HERO['shutter'],
                     'camera_iso': dof.HERO['iso'], 'bloom_intensity': 0.0})
        body = _set(want)
        body += ('    st.set_editor_property("depth_of_field_blade_count", %d)\n'
                 '    st.set_editor_property("override_depth_of_field_blade_count", True)\n'
                 % dof.HERO['blades'])
    else:
        raise SystemExit('lensrig: mode must be judge or show')

    got = _post(body)
    bad = [(k, want[k], got.get(k)) for k in want
           if k in got and abs(got[k] - want[k]) > 1e-3]
    if mode == 'judge':
        bad = [b for b in bad if b[0] != 'depth_of_field_focal_distance']
    if bad:
        raise SystemExit('lensrig: READ-BACK MISMATCH, mode NOT applied: %s'
                         % ['%s wanted %.3f got %s' % b for b in bad])
    rec = {'mode': mode, 'focus': focus, 'grain': bool(grain) if mode == 'show' else False,
           'applied': datetime.datetime.now().isoformat(timespec='seconds'),
           'readback': got}
    json.dump(rec, open(STAMP, 'w'), indent=1, sort_keys=True)
    return rec


def current():
    """The mode the editor was last put into, or None if never set."""
    try:
        return json.load(open(STAMP))
    except Exception:
        return None


if __name__ == '__main__':
    m = sys.argv[1] if len(sys.argv) > 1 else 'judge'
    f = None
    for i, a in enumerate(sys.argv):
        if a == '--focus' and i + 1 < len(sys.argv):
            f = float(sys.argv[i + 1])
    r = apply(m, f, grain=('--no-grain' not in sys.argv))
    print('LENS MODE = %s  grain=%s%s' % (r['mode'], r['grain'],
                                '  focus %.0f uu' % r['focus'] if r['focus'] else ''))
    for k in sorted(r['readback']):
        print('   %-34s %.3f' % (k, r['readback'][k]))
