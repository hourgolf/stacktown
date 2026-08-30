"""Shoot a candidate normal map on the STANDARD ACCEPTANCE BUILDING.

RUN LOCALLY. The survey harness: bind a texture to the active normal
samplers, capture both standoffs settled in judge mode, measure, write the
frames out to be LOOKED AT. Numbers rank; only the frames accept.

WHY THE ACTIVE SAMPLERS ARE THE COARSE THREE. With the octave work parked,
PaperFineWeight is 0 and the fine chain contributes nothing, so the coarse
triplanar samplers are the whole normal. Swapping their Texture swaps the
material's micro-relief and nothing else - which is exactly the admitted
scope of the rule: their micro-relief, our colour and sheen. Albedo, colour
and weathering are untouched because this never goes near them.

SETTLES. Switching texture forces a shader rebuild and invalidates Lumen's
surface cache; comparing a settled state against an unsettled one is how a
recompile once got reported as a 4.27 finding.
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'StacktownAlpha', 'Content', 'Python'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'Content', 'Python'))
import ue, cap2, img, live, lensrig, matlib as ml

E = 'EditorToolset.EditorAppToolset'
MAT = ml.mat('/Game/Stacktown/Materials/M_StacktownMaster.M_StacktownMaster')
MPATH = '/Game/Stacktown/Materials/M_StacktownMaster'
ACTIVE = ('TextureSampleParameter2D_2', 'TextureSampleParameter2D_3',
          'TextureSampleParameter2D_4')
FAR, NEAR = 3189.0, 800.0
# WHOLE-BUILDING standoff. The gate's player zoom fills the frame
# HORIZONTALLY (0.5143 x distance), and this building is 2258 tall against
# 1640 wide, so 3189 crops it to four bays with no roofline and no ground.
# Frame height is 0.2881 x distance, so 2258 plus margin needs ~9000. This is
# an ADDITIONAL standoff, not a replacement: the gate's definition still
# governs acceptance, this one governs silhouette and how the surface reads
# across a whole mass.
WHOLE = 9000.0
LABEL = 'ACCEPT_Vernacular'


def building():
    import subprocess, tempfile
    src = ('import unreal, json\n'
           'eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n'
           'for a in eas.get_all_level_actors():\n'
           '    if a.get_actor_label() != "%s":\n'
           '        continue\n'
           '    o, e = a.get_actor_bounds(False)\n'
           '    print("ACC " + json.dumps([o.x,o.y,o.z,e.x,e.y,e.z]))\n' % LABEL)
    f = os.path.join(tempfile.gettempdir(), '_acc.py')
    open(f, 'w').write(src)
    r = subprocess.run(['python3', os.path.join(HERE, 'uepy.py'), f],
                       capture_output=True, text=True)
    line = next((l for l in r.stdout.splitlines() if 'ACC ' in l), None)
    if not line:
        raise SystemExit('%s not found - run accept_building.py first' % LABEL)
    return json.loads(line.split('ACC', 1)[1].strip())


def bind(tex):
    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    for n in ACTIVE:
        ml.setp(by['MaterialExpression' + n], {'Texture': {'refPath': tex}})
    ml.finish(MAT, MPATH, save=True)
    by = {e['refPath'].split('.')[-1].split(':')[-1]: e for e in ml.exprs(MAT)}
    got = ml.props(by['MaterialExpression' + ACTIVE[0]], ['Texture']).get('Texture')
    got = (got.get('refPath') if isinstance(got, dict) else got) or 'NULL'
    if tex.split('.')[-1] not in str(got):
        raise SystemExit('bind failed, sampler holds %s' % got)
    return str(got).split('.')[-1]


def _shoot(out, loc, rot, reps=3):
    cap2.set_fov()
    for _ in range(6):
        ue.tool(E, 'SetCameraTransform', {'transform': {
            'location': loc, 'rotation': rot, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
        g = json.loads(ue.tool(E, 'GetCameraTransform', {}))['returnValue']['location']
        if all(abs(g[k] - loc[k]) < 2 for k in 'xyz'):
            break
    cap2.VIEWS['_a'] = (loc, rot)
    for _ in range(reps):
        cap2.capture(out, '_a')
    return img.load(out)


def settled(out, loc, rot, eps=0.6, tries=22):
    """eps widened from 0.35 and the cap raised from 14. On flat panels 0.35
    converged; on a FACADE it did not - three of four datum runs hit the cap
    and returned an unconverged frame while reporting a number. Glazing and
    grazing shadow keep a facade moving frame to frame, so the criterion has
    to suit the surface being judged, not the one it was tuned on."""
    prev = None; quiet = 0
    for i in range(tries):
        cur = _shoot(out, loc, rot)
        if prev is not None:
            quiet = quiet + 1 if img.mean_abs_diff(prev, cur) < eps else 0
            if quiet >= 2:
                return cur, i + 1
        prev = cur
    return prev, tries


def run(tag, tex, outdir):
    name = bind(tex)
    o = building()
    face_y = o[1] - o[4]
    rot = {'pitch': 0.0, 'yaw': 90.0, 'roll': 0.0}
    row = {}
    for nm, d, z in (('whole', WHOLE, o[2]), ('far', FAR, o[2]),
                     ('near', NEAR, o[2] - o[5] * 0.45)):
        p = os.path.join(outdir, 'ACC_%s_%s.png' % (tag, nm))
        im, n = settled(p, {'x': o[0], 'y': face_y - d, 'z': z}, rot)
        dx, dy, r = img.anisotropy(im, int(im.w*.35), int(im.h*.35),
                                   int(im.w*.65), int(im.h*.65))
        s = live.stats(p)
        row[nm] = dict(mean=round(s['mean'], 3), detail=round((dx+dy)/2.0, 4),
                       aniso=round(r, 3), settled=n)
        print('  %-14s %-5s mean %7.2f detail %7.4f aniso %5.2f settled@%d'
              % (tag, nm, s['mean'], (dx+dy)/2.0, r, n))
    return name, row


if __name__ == '__main__':
    outdir = sys.argv[1]
    lensrig.apply('judge')
    res = {}
    for tag, tex in (('datum', '/Game/Stacktown/Textures/T_PaperNormal.T_PaperNormal'),
                     ('grunge', '/Game/Deko_MatrixDemo/Shared/Textures/T_Grunge_Dirt_01_N.T_Grunge_Dirt_01_N')):
        nm, row = run(tag, tex, outdir)
        res[tag] = dict(texture=nm, **row)
    bind('/Game/Stacktown/Textures/T_PaperNormal.T_PaperNormal')
    print('master returned to the parked datum texture')
    json.dump(res, open(os.path.join(outdir, 'accept_datum.json'), 'w'),
              indent=1, sort_keys=True)
