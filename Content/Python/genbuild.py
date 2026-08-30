"""Parameterised card-model building generator.

Stage 1 was hand-placed. That does not scale to a metropolis, so every building
from here is a PARAMETER SET, not a drawing. Component names carry their
material role as a prefix (Wall_, Glass_, Frame_, ...) so material assignment is
one sweep over the whole level rather than a per-building wiring job - the
pattern the Portland build got right and Stage 1 did not.

Sized against Saved/Stage2/STAGE2_BUDGET.md: at the block hero the 0.4%
threshold is 230 mm, so what earns its place here is MASS - height, plane
breaks, band offsets, canopies. Window furniture is built because it has to
hold at the 19 mm player-zoom threshold, not because it reads from 112 m.
"""
import _path  # noqa: F401 - puts Tools/measure (ue.py) on sys.path
import ue, json, math, random
import paths
import rolemap

S = 'editor_toolset.toolsets.scene.SceneTools'
P = 'editor_toolset.toolsets.primitive.PrimitiveTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
O = 'editor_toolset.toolsets.object.ObjectTools'


# --- the RECORDING SINK -----------------------------------------------------
# Every box in this file goes out as one MCP round trip, measured at ~0.2 s.
# A vernacular t5 with its elevations and core is ~900 boxes, so a single bake
# is twelve minutes - and an art loop that costs twelve minutes per look is not
# a loop, it is a batch job.
#
# bakegen.py exists for this and takes the other road: a SECOND implementation
# of the same geometry writing an OBJ. That is the "two scripts with separate
# ideas about the same ground" failure this codebase keeps finding, and it has
# already drifted - it knows nothing about cornices, stepped setbacks, roof
# gardens or penthouses.
#
# So: ONE generator, two backends. With the sink armed, mkactor and box and
# slab record instead of emitting, and the whole building comes back as plain
# data that fastbake.py turns into a mesh in one pass.
_SINK = None
_PIECE_FAILS = []   # donor placements the editor refused; see piece()


def record():
    """Arm the sink. Returns nothing; call drain() for the result."""
    global _SINK
    _SINK = []


def drain():
    """Disarm and return what was recorded."""
    global _SINK
    out = _SINK if _SINK is not None else []
    _SINK = None
    return out


def piece_failures(reset=False):
    """Donor placements the editor refused since the last reset.

    A caller that bakes should REFUSE on a non-empty list rather than stamp a
    model that is missing parts it thinks it has.
    """
    global _PIECE_FAILS
    out = list(_PIECE_FAILS)
    if reset:
        _PIECE_FAILS = []
    return out


def recording():
    return _SINK is not None


def mkactor(name, loc=(0, 0, 0), rot=None):
    if _SINK is not None:
        _SINK.append(dict(kind='actor', name=name, loc=list(loc),
                          rot=list(rot) if rot else [0.0, 0.0, 0.0]))
        return len(_SINK) - 1          # the ref is the record's index
    x = {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]}}
    if rot:
        x['rotation'] = {'pitch': rot[0], 'yaw': rot[1], 'roll': rot[2]}
    ref = json.loads(ue.tool(S, 'add_to_scene_from_class',
                             {'actor_type': {'refPath': '/Script/Engine.Actor'},
                              'name': name, 'xform': x}))['returnValue']
    ue.tool(A, 'set_label', {'actor': ref, 'label': name})
    return ref


# HAND TOLERANCE IS OFF, BY THE OWNER'S DECISION OF 29 Aug 2026.
#
# Shown a square building and a jittered one side by side - same seed, same
# spec, same light, exposure raised equally on both - the owner preferred the
# SQUARE one. That is the whole reason; it is a look call and it is theirs.
#
# The machinery below is CORRECT and stays. It was broken for the entire life
# of the feature - RelativeLocation/RelativeRotation were set on the Actor,
# which refuses them, and the refusal was discarded - and it now goes through
# ActorTools.set_actor_transform, which works. So this flag is a DECISION,
# not a workaround for something that does not function. Flip it to True and
# the jitter applies on the live and the recorded path alike.
#
# KNOWN COST, measured over the 548-model catalogue rather than assumed:
# 11,166 visible coplanar pairs with the jitter, 13,897 without. Nudging a
# floor off square is the cheapest way there is to stop two planes being
# exactly coincident, so square costs ~2,731 extra pairs of GATE-11 debt as
# the deliberate price of a deliberate look. ANY GATE-11 BUDGET MUST BE SET
# AGAINST THE SQUARE NUMBER - 13,897 is the real baseline, not 11,166.
HAND_TOLERANCE = False

DEGENERATE = []   # (name, dx, dy, dz) for boxes skipped as zero-sized
JITTER_APPLIED = []   # actors the hand tolerance actually moved


def box(actor, name, x0, x1, y0, y1, z0, z1):
    if _SINK is not None:
        _SINK.append(dict(kind='box', actor=actor, name=name,
                          c=[(x0 + x1)/2.0, (y0 + y1)/2.0, (z0 + z1)/2.0],
                          d=[abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)],
                          r=[0.0, 0.0, 0.0]))
        return
    # DEGENERATE BOXES ARE RECORDED, NOT CRASHED ON AND NOT HIDDEN.
    #
    # add_cube refuses a zero dimension. Until ue.tool started raising on
    # 29 Aug that refusal was DISCARDED - the box never appeared and the bake
    # reported success - so the catalogue has been missing geometry silently:
    # 128 boxes over 7 names, measured offline. Raising here instead would
    # kill a 548-model batch on the first bad one, which is not better.
    #
    # So: skip it, name it, count it, and let the caller report. The defect
    # stays exactly as visible as it is real.
    if min(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) <= 0.0:
        DEGENERATE.append((name, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))
        return
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': abs(x1 - x0), 'y': abs(y1 - y0), 'z': abs(z1 - z0)},
        'local_transform': {'location': {'x': (x0 + x1) / 2.0,
                                         'y': (y0 + y1) / 2.0,
                                         'z': (z0 + z1) / 2.0}}})



def _bx(a, nm, axis, p0, p1, u0, u1, z0, z1):
    """box() with the wall's plane axis abstracted, so one window routine can
    serve a front wall and a flank."""
    if axis == 'y':
        box(a, nm, u0, u1, min(p0, p1), max(p0, p1), z0, z1)
    else:
        box(a, nm, min(p0, p1), max(p0, p1), u0, u1, z0, z1)


def window(a, tag, axis, plane, outward, u0, u1, z0, z1, bars=(1, 1)):
    """A window built as an APPLIED unit, proud of the wall face.

    The first version recessed every part INTO the wall (d = -outward,
    glass 24 uu behind the plane) - correct thinking borrowed from the
    pier-and-gap facades, where the recess is open air, but every caller of
    THIS function builds one solid Wall_Body and passes its face: the whole
    unit was buried in opaque mass and rendered nothing. That is what "blank
    front and blank dormers after three rounds of detail" was - the detail
    existed, entombed. Found by the 2026-08-25 review; confirmed by the owner
    on block F.

    So the unit now mounts ON the face, the way a card modeller glues a
    glazing pane and frame to a facade: interior card flush (the dark void),
    glass just proud of it, frame proud of the glass by 6, sill proudest.
    The reveal hierarchy A1/A2 want is kept, just built outward. A true cut
    opening with an internal recess is the detailing-pass job for each
    draft recipe, not a change to make blind here.

    `outward` is +1 if the exterior face looks along +axis, -1 if it looks back.
    """
    d = outward                         # away from the wall
    _bx(a, 'Interior_%s' % tag, axis, plane + d*1, plane + d*3, u0, u1, z0, z1)
    _bx(a, 'Glass_%s' % tag, axis, plane + d*4, plane + d*6,
        u0 + 6, u1 - 6, z0 + 6, z1 - 6)
    _bx(a, 'Frame_%sL' % tag, axis, plane, plane + d*12, u0, u0 + 6, z0, z1)
    _bx(a, 'Frame_%sR' % tag, axis, plane, plane + d*12, u1 - 6, u1, z0, z1)
    _bx(a, 'Frame_%sT' % tag, axis, plane, plane + d*12, u0, u1, z1 - 6, z1)
    _bx(a, 'Frame_%sS' % tag, axis, plane, plane + d*16, u0 - 5, u1 + 5, z0 - 9, z0)
    n = 6
    for k in range(1, bars[0] + 1):
        m = u0 + (u1 - u0)*k/(bars[0] + 1.0)
        _bx(a, 'Mullion_%sV%d' % (tag, k), axis, plane + d*5, plane + d*11,
            m - 3, m + 3, z0, z1); n += 1
    for k in range(1, bars[1] + 1):
        mz = z0 + (z1 - z0)*k/(bars[1] + 1.0)
        _bx(a, 'Mullion_%sH%d' % (tag, k), axis, plane + d*5, plane + d*11,
            u0, u1, mz - 3, mz + 3); n += 1
    return n


def slab(actor, name, cx, cy, cz, sx, sy, sz, pitch=0.0, roll=0.0, yaw=0.0):
    """A box with a ROTATION. add_cube honours a rotation in its local
    transform - measured, the component reads back what it was given - which
    box() never passed, so every roof in this project was a stack of treads.
    Eleven risers over a 168 uu rise reads as terracing from the pavement."""
    if _SINK is not None:
        _SINK.append(dict(kind='box', actor=actor, name=name,
                          c=[cx, cy, cz], d=[sx, sy, sz],
                          r=[pitch, yaw, roll]))
        return
    ue.tool(P, 'add_cube', {
        'actor': actor, 'name': name,
        'dimensions': {'x': sx, 'y': sy, 'z': sz},
        'local_transform': {'location': {'x': cx, 'y': cy, 'z': cz},
                            'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': roll}}})


def piece(actor, name, asset, loc, rot=(0.0, 0.0, 0.0), scale=1.0, mat=None):
    """Place a DONOR MESH the way box() places a box.

    Boxes are all this generator could emit, which is why a planter was a pink
    cube: some things cannot be cut from card and a modelmaker does not try.
    A kit piece goes through the same sink, so the fast path carries it into a
    baked model exactly like a box.

    `mat` overrides the role lookup for pieces whose name carries no role -
    donor meshes are named by their maker, not by ours.

    `scale` is a float or an (x, y, z) triple. Non-uniform matters: a donor
    awning is 1402 uu long and a shop bay is 281, so fitting one to the other
    uniformly would also make it a fifth as deep and a fifth as tall. A
    modelmaker trims a length of stock to the opening; they do not shrink the
    whole part. Without this every donor had to already be our dimensions,
    which is most of why so few of them were usable.
    """
    sc = ([float(scale)] * 3 if isinstance(scale, (int, float))
          else [float(v) for v in scale])
    if _SINK is not None:
        _SINK.append(dict(kind='mesh', actor=actor, name=name, asset=asset,
                          c=list(loc), r=list(rot), s=sc, mat=mat))
        return
    # ADD_STATIC_MESH NEVER EXISTED. This branch called
    # ue.tool(S, 'add_static_mesh', ...) - a tool that is on no toolset at all
    # (not SceneTools, not PrimitiveTools, not StaticMeshTools) - and threw the
    # response away, so it failed silently for every donor on every live build
    # since it was written. Models baked through the LIVE path carry no roof
    # planting, no tanks, no drainpipes and no flowerbeds, and were stamped
    # Gate=PASS regardless; models baked through fastbake DO carry them,
    # because that path never comes through here. See POLISH_BACKLOG S11.
    #
    # The working sequence is a composite of two tools that do exist, and the
    # encoding is not guessable - it was probed:
    #   * StaticMesh takes the DOTTED object path ('/Game/x/SM_y.SM_y').
    #     A bare path string and an object-shaped {refPath:...} are both
    #     REJECTED. This is the one that would have been got wrong by guessing.
    #   * the transform structs accept either case.
    # Verified by bounds growth, not by a returnValue: placing the Assetsville
    # tank grew the actor's bounds to match its measured (288, 295, 877) from
    # Tools/measure/meshbounds.json, which proves the mesh actually resolved
    # rather than that a property string was accepted.
    global _PIECE_FAILS
    dotted = '%s.%s' % (asset, asset.rsplit('/', 1)[-1])
    try:
        comp = json.loads(ue.tool(A, 'add_component', {
            'owner': actor,
            'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'},
            'name': name}))['returnValue']
    except Exception as e:
        _PIECE_FAILS.append((name, asset, 'add_component: %s' % str(e)[:110]))
        if len(_PIECE_FAILS) <= 3:
            print('  PIECE FAILED %s <- %s : add_component %s'
                  % (name, asset, str(e)[:110]))
        return
    vals = {'StaticMesh': dotted,
            'RelativeLocation': {'X': loc[0], 'Y': loc[1], 'Z': loc[2]},
            'RelativeRotation': {'Pitch': rot[0], 'Yaw': rot[1], 'Roll': rot[2]},
            'RelativeScale3D': {'X': sc[0], 'Y': sc[1], 'Z': sc[2]}}
    resp = ue.tool(O, 'set_properties',
                   {'instance': comp, 'values': json.dumps(vals)})
    try:
        if json.loads(resp)['returnValue'] is not True:
            raise ValueError('returnValue not true')
    except Exception:
        _PIECE_FAILS.append((name, asset, str(resp)[:110]))
        if len(_PIECE_FAILS) <= 3:
            print('  PIECE FAILED %s <- %s : %s'
                  % (name, asset, str(resp)[:110].replace('\n', ' ')))


def _setprops(args):
    """ObjectTools.set_properties for HAND TOLERANCE - and a NO-OP while
    recording.

    These calls set a floor actor a percent or two off square, which is the
    deliberate maker's imperfection the look depends on. They were written
    straight against the editor with no `_SINK` branch, unlike every other
    emitter in this file - so they fired even in RECORD mode, where they are
    both useless and harmful:

      * `instance` is the sink's integer ref, not an actor path, so the call
        could only ever fail - and its return was discarded, so it failed
        silently, exactly like piece() did;
      * an offline sweep that should never touch the editor opened an MCP
        socket and made a blocking HTTP round trip PER FLOOR. With the editor
        busy those calls sit on a 180s timeout each, which is what stalled the
        ladder sweep at low CPU with an ESTABLISHED connection to port 8000.

    THE DIVERGENCE WAS THE OTHER WAY ROUND, and this docstring asserted it
    backwards until 29 Aug. It said the live path carried hand tolerance and
    the recorded path did not. The truth, tested directly rather than
    inferred: RelativeLocation and RelativeRotation live on the ROOT
    COMPONENT, not on the Actor, so ObjectTools.set_properties refused this
    call every single time it was ever made - and the refusal was discarded.
    The recorded path applies jitter (fixed for S14). The LIVE path never
    applied any. Every baked mesh in the catalogue is machine-square.

    That is not only a look bug. Measured over the 548-model catalogue on
    29 Aug: 11,166 visible coplanar pairs WITH the jitter, 13,897 without -
    the hand tolerance suppresses 2,731 of them, 24.5%, more than every
    generator fix of that week put together. Nudging a floor off square is
    the cheapest way there is to stop two planes being exactly coincident,
    which is most of what GATE-11 measures.

    So the live path now goes through ActorTools.set_actor_transform, which
    can actually move an actor, and adds the offsets the SAME way the sink
    does - world-space location delta, direct rotation delta - because the
    two paths agreeing matters more here than either being independently
    purer. They disagreed for the whole life of the feature and nobody could
    see it.
    """
    if not HAND_TOLERANCE:
        return None            # owner's call, see HAND_TOLERANCE
    if _SINK is not None:
        # RECORD IT, don't discard it. Jitter used to be applied to the LEVEL
        # only, so a live-baked mesh carried hand tolerance and a fastbaked one
        # did not - the two paths differed in the LOOK, not just in metadata
        # (POLISH_BACKLOG S14). Folding the offset into the ACTOR's recorded
        # transform is all it takes: fastbake already composes each part's
        # world transform from actor loc/rot, so it picks this up with no
        # change at its end and the live path is untouched.
        idx = args.get('instance')
        rec = _SINK[idx] if isinstance(idx, int) and 0 <= idx < len(_SINK) else None
        if rec is None or rec.get('kind') != 'actor':
            raise ValueError('hand tolerance aimed at %r, which is not an '
                             'actor record - jitter would be lost silently' % (idx,))
        vals = json.loads(args.get('values') or '{}')
        loc = vals.get('RelativeLocation') or {}
        rot = vals.get('RelativeRotation') or {}
        rec['loc'] = [rec['loc'][0] + float(loc.get('x', 0.0)),
                      rec['loc'][1] + float(loc.get('y', 0.0)),
                      rec['loc'][2] + float(loc.get('z', 0.0))]
        rec['rot'] = [rec['rot'][0] + float(rot.get('pitch', 0.0)),
                      rec['rot'][1] + float(rot.get('yaw', 0.0)),
                      rec['rot'][2] + float(rot.get('roll', 0.0))]
        return None
    # HAND TOLERANCE HAS NEVER BEEN APPLIED, and this records that rather
    # than crashing on it or going back to hiding it.
    #
    # RelativeLocation and RelativeRotation live on the ROOT COMPONENT, not
    # on the Actor, so this call has been refused every time it was ever
    # made. Until ue.tool started raising on 29 Aug the refusal was
    # discarded, so the jitter read as implemented and did nothing: every
    # building in the catalogue is machine-square. That is item 7 of what
    # makes a model read as physical - deliberate imperfection - absent for
    # the whole life of the feature.
    #
    # NOT FIXED HERE ON PURPOSE. Setting it on the root component would make
    # all 548 models slightly non-square, which is a visible change across
    # the entire catalogue and the owner's call, not a repair to slip into a
    # verification bake. Swallowing it silently again is not an option
    # either. So it is counted, and the bake behaves exactly as it always
    # has while the debt is on the books.
    ref = args.get('instance')
    vals = json.loads(args.get('values') or '{}')
    dl = vals.get('RelativeLocation') or {}
    dr = vals.get('RelativeRotation') or {}
    cur = json.loads(ue.tool(A, 'get_actor_transform',
                             {'actor': ref}))['returnValue']
    loc, rot = cur['location'], cur['rotation']
    ue.tool(A, 'set_actor_transform', {
        'actor': ref, 'worldspace': True,
        'xform': {'location': {'x': loc['x'] + float(dl.get('x', 0.0)),
                               'y': loc['y'] + float(dl.get('y', 0.0)),
                               'z': loc['z'] + float(dl.get('z', 0.0))},
                  'rotation': {'pitch': rot['pitch'] + float(dr.get('pitch', 0.0)),
                               'yaw': rot['yaw'] + float(dr.get('yaw', 0.0)),
                               'roll': rot['roll'] + float(dr.get('roll', 0.0))}}})
    JITTER_APPLIED.append(ref)
    return None


# HAND TOLERANCE MUST FIT INSIDE THE TOLERANCE THE PLOT ALLOWS.
#
# The jitter yaws a whole floor a fraction of a degree, which is right - a card
# model is not perfectly square. But a rotation grows the footprint in DEPTH by
# about W*sin(yaw), and W is up to 2460: half a degree costs ~21 uu of depth.
# Once S14 made the jitter real in the baked mesh, that pushed 30 marginal
# models past their parcel depth allowance (deco4 10, deco6 18, tower 2, worst
# 22.4 uu over) - a defect I introduced, and one GATE-05 cannot see because it
# measures component AABBs in ACTOR-LOCAL space and never applies the actor's
# own transform.
#
# So the yaw is bounded by its PROJECTED cost rather than by a flat number:
# wide buildings rotate less, which is also what a modelmaker's hand does -
# absolute misalignment does not grow with the size of the piece.
# 2.0, not 6.0. Measured: deco6 spans 867 uu against an allowed 870 - it
# oversails 127 of its permitted 130 BY DESIGN - so a 6 uu rotation budget was
# larger than the margin the recipe leaves and pushed all 18 of its
# combinations over. A budget only works if it is smaller than the tightest
# margin in the catalogue. Recorded as a design fragility in its own right:
# any recipe built to within 3 uu of its allowance has no room for the
# deliberate imperfection the look depends on.
JITTER_DEPTH_BUDGET = 2.0      # uu of depth a floor's rotation may cost


def jit_yaw(rnd, W, limit):
    """A yaw in +-limit degrees, clamped so W*sin(yaw) <= JITTER_DEPTH_BUDGET."""
    import math as _m
    w = max(float(W or 0.0), 1.0)
    cap = _m.degrees(_m.asin(min(1.0, JITTER_DEPTH_BUDGET / w)))
    lim = min(float(limit), cap)
    return rnd.uniform(-lim, lim)


def fit_scale(size, height, max_plan):
    """Uniform scale meeting a HEIGHT target without exceeding a PLAN budget.

    Scaling a donor by `height / size[2]` alone is only safe for a piece that
    is tall and narrow. SM_grassVerticalSingle is the opposite - a wide flat
    ground-cover card, 498 x 479 x 122 - so scaling it to 58 uu tall left a
    236 x 227 footprint, and the random yaw swung its diagonal to 328 uu. On a
    terrace whose planter bed is 22 uu deep, that one tuft pushed
    contemporary6 77 uu past its parcel depth and cost all 18 of its
    combinations at the gate. The mesh was never wrong; the axis chosen to
    scale it by was.
    """
    z = max(float(size[2]), 1e-6)
    s = float(height) / z
    plan = max(float(size[0]), float(size[1])) * s
    if max_plan and plan > max_plan:
        s = float(max_plan) / max(float(size[0]), float(size[1]))
    return s


def stair_head(actor, x0, W, D, ztop, rnd, back=True):
    """The bulkhead over the stair, on the back of the roof. Returns boxes made.

    Every building anyone can walk to the top of has one, and until now none of
    ours did: tiers 0-3 came out of the bake as bare slabs. From above - which
    is how a diorama is actually looked at - that reads as unfinished, and a
    roof is the one elevation a model shows the viewer for free.

    Placed at the BACK so it never competes with the cornice on the street
    front, and sized from the building rather than fixed, so a lock-up gets a
    hatch and a five-storey gets a proper stair house.
    """
    made = 0
    w = max(120.0, min(240.0, W * 0.18))
    d = max(110.0, min(200.0, D * 0.26))
    h = max(90.0, min(210.0, 60.0 + W * 0.10))
    hx = x0 + W * (0.60 if rnd.random() < 0.5 else 0.28) - w / 2.0
    hy = (D - d - 40.0) if back else 60.0
    box(actor, 'Wall_StairHead', hx, hx + w, hy, hy + d, ztop, ztop + h)
    made += 1
    box(actor, 'Band_StairCap', hx - 9, hx + w + 9, hy - 9, hy + d + 9,
        ztop + h, ztop + h + 11)
    made += 1
    # the door faces INTO the roof, not out over the street
    box(actor, 'Frame_StairDoor', hx + w * 0.26, hx + w * 0.74,
        hy - 4, hy + 2, ztop + 8, ztop + h * 0.78)
    made += 1
    return made


def roof_plant(actor, x0, W, ztop, n, rnd, ymin=180.0, yspread=90.0,
               D=None):
    """Rooftop plant, spread ACROSS the building and staying on it.

    Was `ux = x0 + W * (0.28 + 0.42 * u)`, which is fine for one or two units
    and puts the THIRD at 1.12 x width - off the end of the facade entirely,
    floating beside the building. Nothing had asked for three units until the
    tier ladders did. GATE-05 would have caught it at bake time as a model
    wider than its parcel, which is the gate earning its keep, but the fix
    belongs here.

    Units are spaced by their INDEX across the usable span, so any count from
    one upward lands on the roof.
    """
    import avkit
    made = 0
    n = max(0, int(n))
    # REAL PLANT. These were random boxes standing in for the huts, ducts and
    # aerials that CANON slot 5 shows on the top of every tower. Assetsville
    # has the actual objects at 112-960 triangles, which is our tier.
    # 'roof_stand' was here and it is a GIANT DONUT ADVERT on a stand - it
    # shipped on the crown of all three towers, where it read as a car tyre.
    # See avkit.REJECTED. Picked by name, never rendered, exactly the mistake
    # that put a concrete material on gravel earlier in this project.
    #
    # SIZED TO THE ROOF, and scattered rather than lined up. The kit was
    # cycled in a fixed order at a fixed y, so every building in a row wore
    # the same objects in the same place - and `vent_tank` is 512 uu long,
    # which is 40% of a 1230 roof. It read as one big dark pill repeated
    # down the street. Each unit is now scaled to a share of the roof and
    # placed on a jittered grid over the whole deck.
    KIT = ['ac_small', 'ac_large', 'antenna', 'vent_tank', 'water_tank',
           'chimney']
    # the biggest a single unit may be, as a fraction of the roof's short side
    CAP_F = 0.30
    span_y = max(200.0, (D if D else 700.0) - ymin - 60.0)
    order = list(KIT)
    rnd.shuffle(order)
    cols = max(1, int(math.ceil(math.sqrt(max(1, n) * max(0.4, W / max(1.0, span_y))))))
    rows = int(math.ceil(n / float(cols)))
    for u in range(n):
        key = order[u % len(order)]
        sx, sy, sz = avkit.size(key)
        cap = CAP_F * min(W, span_y)
        sc = min(1.0, cap / float(max(sx, sy)))
        cx_ = u % cols
        cy_ = u // cols
        ux = x0 + 70.0 + (max(0.0, W - 140.0) * (cx_ + 0.5) / cols) \
            + rnd.uniform(-40.0, 40.0)
        uy = ymin + (span_y * (cy_ + 0.5) / max(1, rows)) \
            + rnd.uniform(-30.0, 30.0)
        piece(actor, rolemap.donor_name(avkit.mat(key), 'RoofPlant%d' % u), avkit.path(key), (ux, uy, ztop),
              (0.0, rnd.choice((0.0, 90.0, 180.0, 270.0)), 0.0),
              scale=sc, mat=avkit.mat(key))
        made += 1
    return made


def build(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """Dispatch on style. ONE generator with more parameters, never a second
    generator - "buildings are parameter sets" is the property HANDOFF.md 4.2
    calls the most important scaling behaviour in this codebase, and a
    genbuild2.py is how you lose it."""
    st = spec.get('style')
    if st == 'modern':
        return build_modern(spec, origin, yaw)
    if st == 'deco':
        return build_deco(spec, origin, yaw)
    if st == 'contemporary':
        return build_contemporary(spec, origin, yaw)
    if st == 'house':
        return build_house(spec, origin, yaw)
    if st == 'walkup':
        return build_walkup(spec, origin, yaw)
    if st == 'works':
        return build_works(spec, origin, yaw)
    return build_vernacular(spec, origin, yaw)


def build_vernacular(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """spec x0/width are BLOCK-LOCAL. The block's world placement lives on the
    actor transform, so a block can be dropped anywhere and rotated - which is
    what lets a second block face the first across a street without every
    coordinate being rewritten."""
    """spec keys: name x0 width depth floors gf_h fl_h parapet bays wall
                  canopy(None|projection) setback(None|uu) setback_floors
                  cornice(None|projection) roof_units glaze('large')
                  roof_garden(bool) penthouse(dict floors/inset/fl_h) seed"""
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    total = GF + F * FH + PAR
    made = 0

    # ---- ground floor -------------------------------------------------------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 6, x0 + W + 6, -12, D * 0.08, 0, 30); made += 1
    pier_w = 52.0
    box(g, 'Wall_PierL', x0, x0 + pier_w, 0, 60, 30, GF - 40); made += 1
    box(g, 'Wall_PierR', x0 + W - pier_w, x0 + W, 0, 60, 30, GF - 40); made += 1
    box(g, 'Wall_Bulkhead', x0 - 4, x0 + W + 4, -8, 60, GF - 40, GF); made += 1
    sx0, sx1 = x0 + pier_w, x0 + W - pier_w
    if spec.get('market'):
        # A MARKET HALL is one big room behind one big wall. The ground floor
        # is a run of tall ARCHED openings with almost no wall between them,
        # and there is a clerestory over: the building is a shed with a
        # dignified face, which is exactly what a market is.
        na = max(3, BAYS)
        for k in range(na):
            ax0 = sx0 + (sx1 - sx0) * k / float(na) + 16
            ax1 = sx0 + (sx1 - sx0) * (k + 1) / float(na) - 16
            if ax1 - ax0 < 60:
                continue
            ah = min(GF * 0.34, (ax1 - ax0) * 0.5)
            for j in range(5):
                t = (j + 1) / 5.0
                ins = (ax1 - ax0) * 0.5 * (1.0 - (1.0 - t * t) ** 0.5)
                # THE CROWN COURSE HAD ZERO WIDTH. At j=4, t is exactly 1.0
                # and the ellipse inset equals the half-width, so ax0+ins and
                # ax1-ins are the same point. add_cube refuses a zero
                # dimension and the refusal was discarded, so every market
                # arch in the catalogue has been missing its top course - 82
                # boxes, silently, for the whole life of the construct.
                # Capping the inset leaves a narrow keystone course, which is
                # what the top of a real arch looks like anyway.
                ins = min(ins, (ax1 - ax0) * 0.5 - 6.0)
                box(g, 'Wall_MktArch%d_%d' % (k, j), ax0 + ins, ax1 - ins,
                    -10, 56, GF - 40 - ah + ah * t * 0.98,
                    GF - 40 - ah + ah * (t + 0.24)); made += 1
            box(g, 'Glass_Mkt%d' % k, ax0 + 8, ax1 - 8, 40, 43,
                34, GF - 40 - ah * 0.12); made += 1
            box(g, 'Interior_Mkt%d' % k, ax0 + 2, ax1 - 2, 52, 58,
                34, GF - 40 - ah * 0.12); made += 1
            for m in range(1, 3):
                mx = ax0 + (ax1 - ax0) * m / 3.0
                box(g, 'Mullion_Mkt%d_%d' % (k, m), mx - 4, mx + 4, 36, 42,
                    34, GF - 40 - ah * 0.12); made += 1
    elif spec.get('chamfer'):
        # the corner cut away and the entrance put in it, at an angle to both
        # streets - four stepped returns standing in for a 45 degree face
        cl = spec.get('corner_side', 'left') == 'left'
        cd = float(spec['chamfer'])
        for k in range(4):
            t0, t1 = cd * k / 4.0, cd * (k + 1) / 4.0
            cx_0 = (x0 - 4 + t0) if cl else (x0 + W + 4 - t1)
            cx_1 = (x0 - 4 + t1) if cl else (x0 + W + 4 - t0)
            box(g, 'Wall_Chamf%d' % k, cx_0, cx_1, -14 + t1 * 0.9, 62,
                0, GF); made += 1
        ex = (x0 + cd * 0.42) if cl else (x0 + W - cd * 0.42)
        box(g, 'Timber_CornerDoor', ex - 52, ex + 52, cd * 0.30,
            cd * 0.30 + 9, 34, GF - 104); made += 1
        box(g, 'Frame_CornerCase', ex - 66, ex + 66, cd * 0.30 - 9,
            cd * 0.30 + 4, 30, GF - 88); made += 1
    if spec.get('civic'):
        # A CIVIC BUILDING - bank, library, institute. It does not sell
        # anything to the street, so it has no shopfront: it has a RUSTICATED
        # base of deep horizontal courses, a flight of steps to a central
        # doorway, and engaged columns above. The period's public face.
        nc = 5
        for k in range(nc):
            ch = (GF - 40.0) / nc
            o = 9.0 if k % 2 == 0 else 3.0
            box(g, 'Wall_Rustic%d' % k, x0 - o, x0 + W + o, -o, 60,
                30 + k * ch, 30 + (k + 1) * ch - 5); made += 1
        dm = x0 + W * 0.5
        dw = min(150.0, W * 0.16)
        for k in range(4):
            box(g, 'Kerbing_CivicStep%d' % k, dm - dw - 60 + k * 13,
                dm + dw + 60 - k * 13, -56 + k * 13, 8, 0, 14 + k * 12)
            made += 1
        box(g, 'Timber_CivicDoor', dm - dw, dm + dw, 26, 34, 62, GF - 96)
        made += 1
        box(g, 'Frame_CivicCase', dm - dw - 20, dm + dw + 20, 18, 30,
            62, GF - 76); made += 1
        # flanking windows, tall and narrow
        for side in (-1, 1):
            wx = dm + side * (dw + 90.0)
            if not (x0 + 60 < wx < x0 + W - 60):
                continue
            box(g, 'Glass_CivicW%d' % side, wx - 46, wx + 46, 38, 41,
                96, GF - 100); made += 1
            box(g, 'Frame_CivicW%d' % side, wx - 58, wx + 58, 28, 38,
                84, GF - 86); made += 1
    elif spec.get('terrace'):
        # A TERRACE MEETS THE STREET WITH FRONT DOORS, one per house, each up
        # its own flight of steps behind railings. No shopfront, no loading
        # bay: this is the residential building of the same era, and the
        # repeated stoop is the whole rhythm of it.
        nh = max(2, BAYS)
        for h in range(nh):
            hx0 = sx0 + (sx1 - sx0) * h / float(nh)
            hx1 = sx0 + (sx1 - sx0) * (h + 1) / float(nh)
            dw = min(96.0, (hx1 - hx0) * 0.36)
            dx = hx0 + (hx1 - hx0) * 0.18
            # steps down to the pavement
            for k in range(3):
                box(g, 'Kerbing_Step%d_%d' % (h, k), dx - 14, dx + dw + 14,
                    -34 + k * 11, 6, 0, 12 + k * 11); made += 1
            box(g, 'Timber_Door%d' % h, dx, dx + dw, 30, 38, 44, GF - 96)
            made += 1
            box(g, 'Frame_DoorCase%d' % h, dx - 13, dx + dw + 13, 24, 34,
                44, GF - 82); made += 1
            box(g, 'Glass_Fanlight%d' % h, dx + 6, dx + dw - 6, 32, 35,
                GF - 94, GF - 84); made += 1
            # area railings between the stoops
            for rk in range(4):
                rx = hx0 + (hx1 - hx0) * (0.56 + 0.11 * rk)
                box(g, 'Rail_Area%d_%d' % (h, rk), rx - 4, rx + 4, -26, -18,
                    12, 78); made += 1
            box(g, 'Rail_AreaTop%d' % h, hx0 + (hx1 - hx0) * 0.52,
                hx1 - 6, -28, -16, 78, 88); made += 1
            # the parlour window beside the door
            wx0 = hx0 + (hx1 - hx0) * 0.52
            if hx1 - 10 - wx0 > 50:
                box(g, 'Glass_Parlour%d' % h, wx0, hx1 - 10, 40, 43,
                    72, GF - 74); made += 1
                box(g, 'Interior_Parlour%d' % h, wx0 - 5, hx1 - 5, 52, 58,
                    66, GF - 70); made += 1
                box(g, 'Frame_ParlourCill%d' % h, wx0 - 8, hx1 - 2, 34, 46,
                    60, 74); made += 1
    elif spec.get('loft'):
        # A LOFT MEETS THE STREET WITH A LOADING BAY, not a shopfront. Cast
        # iron columns carrying the floor above, a raised loading platform,
        # and a pair of tall timber doors in the middle bay - the same era as
        # the shop & flat, a completely different building.
        nb = max(2, BAYS)
        box(g, 'Kerbing_LoadDock', x0 + 20, x0 + W - 20, -46, 10, 0, 34)
        made += 1
        for k in range(nb + 1):
            cx = sx0 + (sx1 - sx0) * k / float(nb)
            cx = min(max(cx, sx0), sx1)
            box(g, 'Frame_IronCol%d' % k, cx - 16, cx + 16, 6, 44, 34, GF - 44)
            made += 1
        dm = (sx0 + sx1) / 2.0
        dw = (sx1 - sx0) / float(nb) * 0.86
        box(g, 'Timber_LoadDoorL', dm - dw, dm - 4, 26, 34, 34, GF - 70)
        box(g, 'Timber_LoadDoorR', dm + 4, dm + dw, 26, 34, 34, GF - 70)
        made += 2
        for side in (-1, 1):
            box(g, 'Frame_DoorRail%d' % side, dm + side * 4 - 3,
                dm + side * dw, 22, 28, GF - 74, GF - 62); made += 1
        # the remaining bays are glazed in small panes behind the columns
        for k in range(nb):
            gx_0 = sx0 + (sx1 - sx0) * k / float(nb) + 18
            gx_1 = sx0 + (sx1 - sx0) * (k + 1) / float(nb) - 18
            if gx_1 - gx_0 < 40 or (gx_0 < dm < gx_1):
                continue
            box(g, 'Glass_Bay%d' % k, gx_0, gx_1, 30, 33, 46, GF - 56)
            box(g, 'Interior_Bay%d' % k, gx_0 - 4, gx_1 + 4, 44, 50, 40, GF - 52)
            made += 2
            for m in range(1, 3):
                mx = gx_0 + (gx_1 - gx_0) * m / 3.0
                box(g, 'Mullion_Bay%d_%d' % (k, m), mx - 3, mx + 3, 26, 32,
                    46, GF - 56); made += 1
    else:
        box(g, 'Glass_Shop', sx0, sx1, 40, 43, 40, GF - 48); made += 1
        box(g, 'Interior_Shop', sx0 - 6, sx1 + 6, 52, 58, 30, GF - 44); made += 1
        for k in range(1, 4):
            mx = sx0 + (sx1 - sx0) * k / 4.0
            box(g, 'Mullion_Shop%d' % k, mx - 3, mx + 3, 34, 41, 40, GF - 48); made += 1
        box(g, 'Frame_ShopSill', sx0, sx1, 34, 44, 30, 40); made += 1

    # ---- buttresses ----------------------------------------------------------
    if spec.get('buttress') and F >= 1:
        bt = mkactor('BLD2_%s_Butt' % n, origin, (0.0, yaw, 0.0))
        nbt = max(3, BAYS + 1)
        for k in range(nbt):
            bx = x0 + 30 + (W - 60) * k / float(nbt - 1)
            for st in range(3):
                bd = 62.0 - st * 18.0
                z_0 = GF + (GF + F * FH - GF) * st / 3.0
                z_1 = GF + (GF + F * FH - GF) * (st + 1) / 3.0
                box(bt, 'Wall_Butt%d_%d' % (k, st), bx - 27, bx + 27,
                    -bd, 10, z_0 - (14 if st else 0), z_1); made += 1
                box(bt, 'Band_ButtSet%d_%d' % (k, st), bx - 33, bx + 33,
                    -bd - 8, 12, z_1 - 16, z_1); made += 1

    # ---- engaged columns (civic) --------------------------------------------
    # A giant order standing on the rusticated base and carrying the cornice:
    # the one move that separates a public building from a commercial one of
    # the same date, and it costs three boxes a column.
    if spec.get('civic') and F >= 1:
        nc2 = max(3, BAYS + 1)
        col = mkactor('BLD2_%s_Order' % n, origin, (0.0, yaw, 0.0))
        czt = GF + max(1, F) * FH
        for k in range(nc2):
            cx = x0 + 40 + (W - 80) * k / float(nc2 - 1)
            cw2 = min(58.0, (W - 80) / float(nc2) * 0.52)
            box(col, 'Wall_Column%d' % k, cx - cw2 / 2, cx + cw2 / 2,
                -46, 8, GF, czt - 46); made += 1
            box(col, 'Band_Capital%d' % k, cx - cw2 / 2 - 11,
                cx + cw2 / 2 + 11, -58, 10, czt - 46, czt - 20); made += 1
            box(col, 'Band_Base%d' % k, cx - cw2 / 2 - 9, cx + cw2 / 2 + 9,
                -55, 10, GF, GF + 22); made += 1

    # ---- projecting bay windows ---------------------------------------------
    # A terrace's other signature, and the one that makes a whole row read as
    # houses rather than as flats: a canted bay standing proud of the wall on
    # the lower floors, one per house, stopping short of the top storey the
    # way a real terrace does.
    if spec.get('terrace') and F >= 1:
        nh = max(2, BAYS)
        nbf = min(F, int(spec.get('bay_floors', 1)))
        bpr = float(spec.get('bay_proud', 78.0))
        bw_ = mkactor('BLD2_%s_Bays' % n, origin, (0.0, yaw, 0.0))
        for h in range(nh):
            hx0 = (x0 + pier_w) + ((x0 + W - pier_w) - (x0 + pier_w)) * h / float(nh)
            hx1 = (x0 + pier_w) + ((x0 + W - pier_w) - (x0 + pier_w)) * (h + 1) / float(nh)
            bx0 = hx0 + (hx1 - hx0) * 0.10
            bx1 = hx0 + (hx1 - hx0) * 0.66
            if bx1 - bx0 < 70:
                continue
            for f in range(nbf):
                z0b, z1b = GF + f * FH, GF + (f + 1) * FH
                # the canted cheeks: two short returns instead of a curve
                box(bw_, 'Wall_BayL%d_%d' % (h, f), bx0, bx0 + 22,
                    -bpr * 0.62, 8, z0b + 8, z1b - 30); made += 1
                box(bw_, 'Wall_BayR%d_%d' % (h, f), bx1 - 22, bx1,
                    -bpr * 0.62, 8, z0b + 8, z1b - 30); made += 1
                box(bw_, 'Glass_BayFace%d_%d' % (h, f), bx0 + 22, bx1 - 22,
                    -bpr, -bpr + 3, z0b + 18, z1b - 40); made += 1
                box(bw_, 'Interior_BayFace%d_%d' % (h, f), bx0 + 18, bx1 - 18,
                    -bpr + 9, -bpr + 15, z0b + 18, z1b - 40); made += 1
                box(bw_, 'Frame_BayCill%d_%d' % (h, f), bx0 - 8, bx1 + 8,
                    -bpr - 9, 10, z0b + 4, z0b + 18); made += 1
                box(bw_, 'Band_BayCap%d_%d' % (h, f), bx0 - 10, bx1 + 10,
                    -bpr - 11, 10, z1b - 40, z1b - 26); made += 1
                mxb = (bx0 + bx1) / 2.0
                box(bw_, 'Mullion_Bay%d_%d' % (h, f), mxb - 4, mxb + 4,
                    -bpr - 4, -bpr + 1, z0b + 18, z1b - 40); made += 1

    # ---- upper floors -------------------------------------------------------
    for f in range(F):
        z0 = GF + f * FH
        z1 = z0 + FH
        # Upper-floor setback: a plane break, 900 mm, well over the 230 mm bar.
        # setback_floors lets the top N floors each step back a further notch,
        # so the crown changes as the building climbs instead of three tiers
        # differing only in how many identical floors are stacked.
        _sb = spec.get('setback') or 0.0
        # cores.setback_at is THE resolver - the same one the core bands on.
        # This formula used to be written out here, again lower down, again in
        # build_contemporary and again in cores; four copies of one rule is
        # how a floor steps back and its core does not (P12).
        import cores as _co
        fy = _co.setback_at(spec, f, F)
        a = mkactor('BLD2_%s_F%d' % (n, f), origin, (0.0, yaw, 0.0))
        if spec.get('coffer'):
            # A COFFERED GRID. The window is not a hole in a wall, it is the
            # bottom of a deep square box - so every opening carries a full
            # frame of shadow on all four sides and the facade reads as a
            # chequerboard from across the board. It is the most three-
            # dimensional facade in the catalogue and the most repetitive,
            # which is exactly the trade the era made.
            CF = 62.0
            for b in range(BAYS):
                px0 = x0 + W * b / float(BAYS)
                px1 = x0 + W * (b + 1) / float(BAYS)
                box(a, 'Wall_CofL%d_%d' % (f, b), px0, px0 + 26, fy - CF,
                    fy + 58, z0, z1); made += 1
                box(a, 'Wall_CofT%d_%d' % (f, b), px0, px1, fy - CF, fy + 58,
                    z1 - 26, z1); made += 1
                box(a, 'Wall_CofB%d_%d' % (f, b), px0, px1, fy - CF, fy + 58,
                    z0, z0 + 26); made += 1
                ox0, ox1 = px0 + 26, px1 - 26
                if ox1 - ox0 < 44:
                    continue
                box(a, 'Glass_Cof%d_%d' % (f, b), ox0, ox1, fy + 34,
                    fy + 37, z0 + 26, z1 - 26); made += 1
                box(a, 'Interior_Cof%d_%d' % (f, b), ox0, ox1, fy + 44,
                    fy + 50, z0 + 26, z1 - 26); made += 1
                mxc = (ox0 + ox1) / 2.0
                box(a, 'Mullion_Cof%d_%d' % (f, b), mxc - 4, mxc + 4,
                    fy + 30, fy + 35, z0 + 26, z1 - 26); made += 1
            box(a, 'Wall_CofR%d' % f, x0 + W - 26, x0 + W, fy - CF, fy + 58,
                z0, z1); made += 1
            _setprops({
                'instance': a, 'values': json.dumps({
                    'RelativeLocation': {'x': rnd.uniform(-1.4, 1.4) * (W / 100.0),
                                         'y': rnd.uniform(-1.0, 1.0), 'z': 0.0},
                    'RelativeRotation': {'pitch': 0.0, 'yaw': jit_yaw(rnd, W, 0.5),
                                         'roll': rnd.uniform(-0.4, 0.4)}})})
            continue
        if spec.get('deck_access'):
            # THE SLAB. Postwar housing: a continuous ACCESS DECK running the
            # full length of the building at every floor, with a solid
            # balustrade in front of it and the front doors and small windows
            # in shadow behind. The horizontal repeat is relentless on
            # purpose - that is what the building is.
            DK = 118.0
            box(a, 'Band_DeckSlab%d' % f, x0 - 8, x0 + W + 8, fy - DK,
                fy + 30, z0, z0 + 22); made += 1
            box(a, 'Wall_Balust%d' % f, x0 - 8, x0 + W + 8, fy - DK - 12,
                fy - DK + 6, z0 + 22, z0 + 92); made += 1
            box(a, 'Band_BalustCap%d' % f, x0 - 12, x0 + W + 12,
                fy - DK - 18, fy - DK + 12, z0 + 92, z0 + 106); made += 1
            # the wall behind the deck, with doors and small windows
            box(a, 'Wall_DeckWall%d' % f, x0, x0 + W, fy + 4, fy + 58,
                z0 + 22, z1); made += 1
            nu = max(3, int(round(W / 300.0)))
            for u in range(nu):
                ux0 = x0 + W * u / float(nu)
                ux1 = x0 + W * (u + 1) / float(nu)
                dx = ux0 + (ux1 - ux0) * 0.13
                dw = min(74.0, (ux1 - ux0) * 0.26)
                box(a, 'Timber_FlatDoor%d_%d' % (f, u), dx, dx + dw,
                    fy - 2, fy + 6, z0 + 26, z0 + 26 + FH * 0.62); made += 1
                wx0 = ux0 + (ux1 - ux0) * 0.48
                wx1 = ux1 - (ux1 - ux0) * 0.10
                if wx1 - wx0 > 46:
                    box(a, 'Glass_Flat%d_%d' % (f, u), wx0, wx1, fy + 2,
                        fy + 5, z0 + 44, z1 - 34); made += 1
                    box(a, 'Interior_Flat%d_%d' % (f, u), wx0, wx1, fy + 12,
                        fy + 18, z0 + 44, z1 - 34); made += 1
                    box(a, 'Frame_FlatCill%d_%d' % (f, u), wx0 - 6, wx1 + 6,
                        fy - 4, fy + 8, z0 + 36, z0 + 46); made += 1
            _setprops({
                'instance': a, 'values': json.dumps({
                    'RelativeLocation': {'x': rnd.uniform(-1.4, 1.4) * (W / 100.0),
                                         'y': rnd.uniform(-1.0, 1.0), 'z': 0.0},
                    'RelativeRotation': {'pitch': 0.0, 'yaw': jit_yaw(rnd, W, 0.5),
                                         'roll': rnd.uniform(-0.4, 0.4)}})})
            continue
        if spec.get('steel_frame'):
            # THE MIESIAN BOX. The third modern building: not ribbon glazing
            # behind a band (v1), not a precast frame with sunk windows (v2),
            # but floor-to-ceiling glass with the STEEL SHOWN - I-section
            # mullions standing proud of the glass the whole height of the
            # storey, and only a hairline slab edge between floors.
            #
            # It is the most restrained facade in the catalogue and the
            # hardest to get right: with nothing else on it, the mullion
            # rhythm and the slab edge ARE the building.
            box(a, 'Frame_SlabEdge%d' % f, x0 - 6, x0 + W + 6, fy - 20,
                fy + 62, z0, z0 + 26); made += 1
            box(a, 'Glass_Full%d' % f, x0 + 14, x0 + W - 14, fy + GLAZE_Y,
                fy + GLAZE_Y + 3, z0 + 26, z1); made += 1
            box(a, 'Interior_Full%d' % f, x0 + 14, x0 + W - 14,
                fy + GLAZE_Y + 9, fy + GLAZE_Y + 15, z0 + 26, z1); made += 1
            nmu = max(3, int(round(W / float(spec.get('mull_step', 118.0)))))
            for k in range(nmu + 1):
                mx = x0 + W * k / float(nmu)
                mx = min(max(mx, x0), x0 + W)
                # an I-section read as three boxes: web plus two flanges
                box(a, 'Frame_IbeamWeb%d_%d' % (f, k), mx - 4, mx + 4,
                    fy - 26, fy + GLAZE_Y + 2, z0 + 26, z1); made += 1
                for fl, dy in (('O', -26.0), ('I', GLAZE_Y - 4.0)):
                    box(a, 'Frame_IbeamFl%s%d_%d' % (fl, f, k),
                        mx - 14, mx + 14, fy + dy, fy + dy + 7,
                        z0 + 26, z1); made += 1
            _setprops({
                'instance': a, 'values': json.dumps({
                    'RelativeLocation': {'x': rnd.uniform(-1.2, 1.2) * (W / 100.0),
                                         'y': rnd.uniform(-0.9, 0.9), 'z': 0.0},
                    'RelativeRotation': {'pitch': 0.0, 'yaw': jit_yaw(rnd, W, 0.4),
                                         'roll': rnd.uniform(-0.3, 0.3)}})})
            continue
        if spec.get('precast'):
            # BRUTALIST PRECAST. The same decade as the ribbon block and its
            # opposite: instead of glass hung behind a proud band, a heavy
            # frame of precast units with the windows sunk deep inside it.
            # The shadow does all the work, which is why this reads at city
            # range where a curtain wall needs its mullions.
            REV = 46.0                      # how deep the window sits
            box(a, 'Wall_SlabBand%d' % f, x0 - 8, x0 + W + 8, fy - 18, fy + 62,
                z0, z0 + sp); made += 1
            for b in range(BAYS):
                px0 = x0 + W * b / float(BAYS)
                px1 = x0 + W * (b + 1) / float(BAYS)
                box(a, 'Wall_Mullion%d_%d' % (f, b), px0 - 15, px0 + 15,
                    fy - 18, fy + 62, z0 + sp, z1); made += 1
                ox0, ox1 = px0 + 15, px1 - 15
                if ox1 - ox0 < 50:
                    continue
                # the reveal: cheeks, head and cill cut back into the frame
                box(a, 'Wall_RevHead%d_%d' % (f, b), ox0, ox1,
                    fy - 18, fy + REV, z1 - 22, z1); made += 1
                box(a, 'Wall_RevCill%d_%d' % (f, b), ox0 - 6, ox1 + 6,
                    fy - 26, fy + REV, z0 + sp, z0 + sp + 20); made += 1
                box(a, 'Glass_Deep%d_%d' % (f, b), ox0 + 4, ox1 - 4,
                    fy + REV, fy + REV + 3, z0 + sp + 20, z1 - 22); made += 1
                box(a, 'Interior_Deep%d_%d' % (f, b), ox0, ox1,
                    fy + REV + 9, fy + REV + 15, z0 + sp + 20, z1 - 22); made += 1
                mx = (ox0 + ox1) / 2.0
                box(a, 'Mullion_Deep%d_%d' % (f, b), mx - 4, mx + 4,
                    fy + REV - 4, fy + REV + 1, z0 + sp + 20, z1 - 22); made += 1
            box(a, 'Wall_Mullion%d_end' % f, x0 + W - 15, x0 + W + 15,
                fy - 18, fy + 62, z0 + sp, z1); made += 1
            _setprops({
                'instance': a, 'values': json.dumps({
                    'RelativeLocation': {'x': rnd.uniform(-1.6, 1.6) * (W / 100.0),
                                         'y': rnd.uniform(-1.1, 1.1), 'z': 0.0},
                    'RelativeRotation': {'pitch': 0.0, 'yaw': jit_yaw(rnd, W, 0.6),
                                         'roll': rnd.uniform(-0.5, 0.5)}})})
            continue
        bw = (W - pier_w) / float(BAYS)
        for b in range(BAYS + 1):
            px = x0 + b * bw
            box(a, 'Wall_Pier%d' % b, px, px + pier_w, fy, fy + 60, z0, z1 - 34); made += 1
        # band course - primary depth carrier at range, 60 uu proud
        box(a, 'Band_Course', x0 - 8, x0 + W + 8, fy - 8, fy + 58, z1 - 34, z1); made += 1
        # QUOINS: alternating blocks at each corner, which is how a masonry
        # front turns a corner and what a narrow elevation has instead of bays.
        # INSIDE the lot. The first version ran the quoin 38 uu proud of the
        # lot edge, which put Narrow's left corner 68 uu into the Stage 1
        # building next door - check_block caught it. A quoin projects from the
        # WALL, not past the party line; it steps in Y, not in X.
        for qs, qx in (('L', x0), ('R', x0 + W)):
            for q in range(4):
                qw = 34.0 if q % 2 else 22.0
                qz = z0 + (z1 - z0)*q/4.0
                box(a, 'Wall_Quoin%s%d' % (qs, q),
                    qx if qs == 'L' else qx - qw,
                    qx + qw if qs == 'L' else qx,
                    fy - 14, fy + 26, qz + 4, qz + (z1 - z0)/4.0 - 4); made += 1
        # A RECLAIMED building keeps its holes and gets new glass. `glaze`
        # drops the cill and raises the head so the opening reads bigger in
        # the same wall, and strips the horizontal bar - which is exactly what
        # a heritage conversion does and why it reads as retrofit rather than
        # as a different building.
        big = spec.get('glaze') == 'large'
        for b in range(BAYS):
            wx0 = x0 + b * bw + pier_w
            wx1 = x0 + (b + 1) * bw
            wz0, wz1 = (z0 + 30, z1 - 34) if big else (z0 + 62, z1 - 66)
            gy = fy + 27                      # 250 mm recess (Stage 0 finding)
            box(a, 'Glass_B%d' % b, wx0 + 6, wx1 - 6, gy, gy + 2, wz0 + 6, wz1 - 6); made += 1
            box(a, 'Interior_B%d' % b, wx0, wx1, gy + 20, gy + 26, wz0, wz1); made += 1
            box(a, 'Frame_B%dL' % b, wx0, wx0 + 6, gy - 8, gy + 2, wz0, wz1); made += 1
            box(a, 'Frame_B%dR' % b, wx1 - 6, wx1, gy - 8, gy + 2, wz0, wz1); made += 1
            box(a, 'Frame_B%dT' % b, wx0, wx1, gy - 8, gy + 2, wz1 - 6, wz1); made += 1
            box(a, 'Frame_B%dS' % b, wx0 - 4, wx1 + 4, gy - 14, gy + 2, wz0 - 6, wz0); made += 1
            made += 0
            mx = (wx0 + wx1) / 2.0
            box(a, 'Mullion_B%dV' % b, mx - 3, mx + 3, gy - 6, gy + 1, wz0, wz1); made += 1
            if not big:
                mz = wz0 + (wz1 - wz0) * 0.62
                box(a, 'Mullion_B%dH' % b, wx0, wx1, gy - 6, gy + 1,
                    mz - 3, mz + 3); made += 1
            # CORBELS under the cill. A cill sits on something; DETAIL-01 found
            # Narrow at 0.65 parts per m2 and this is the detail a narrow
            # vernacular front is actually missing, not more mullions.
            for cb, cx_ in (('L', wx0 + 16), ('R', wx1 - 16)):
                box(a, 'Frame_B%dCorbel%s' % (b, cb), cx_ - 11, cx_ + 11,
                    gy - 12, gy + 2, wz0 - 20, wz0 - 6); made += 1
        # hand-made tolerance: model tolerances, 1-2% of width, not 0.15%
        _setprops({
            'instance': a, 'values': json.dumps({
                'RelativeLocation': {'x': rnd.uniform(-2.2, 2.2) * (W / 100.0),
                                     'y': rnd.uniform(-1.6, 1.6), 'z': 0.0},
                'RelativeRotation': {'pitch': 0.0, 'yaw': jit_yaw(rnd, W, 0.9),
                                     'roll': rnd.uniform(-0.7, 0.7)}})})

    # ---- roof ---------------------------------------------------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    ztop = GF + F * FH
    # THE PARAPET HAS TO FOLLOW THE SETBACK. It was pinned to the full front
    # plane while the top floors stepped back, so on a stepped tier it hung
    # 180 uu out in front of the wall it was supposed to cap - a floating
    # shelf, clearly visible the first time a stepped crown was rendered.
    SB = spec.get('setback') or 0.0
    SBF = max(1, int(spec.get('setback_floors', 1)))
    import cores as _co
    ty = _co.setback_top(spec, F)
    box(r, 'Wall_ParapetF', x0, x0 + W, ty - 4, ty + 30, ztop, ztop + PAR); made += 1
    box(r, 'Band_ParapetCap', x0 - 8, x0 + W + 8, ty - 14, ty + 40, ztop + PAR, ztop + PAR + 14); made += 1
    box(r, 'Wall_ParapetL', x0, x0 + 26, ty + 30, D, ztop, ztop + PAR - 20); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 26, x0 + W, ty + 30, D, ztop, ztop + PAR - 20); made += 1
    # A REAR PARAPET. There never was one: the core filled the roof void to
    # above the parapet, so the missing back wall could not be seen. With
    # `open_roof` the core stops at the roof line and the void is real, so the
    # roof has to be closed on all four sides like an actual parapet.
    # MITRED, not lapped. The back run used to span x0..x0+W while the flank
    # runs also reached the back wall, so both back corners were built TWICE -
    # 1,422 visible coplanar pairs across all 548 models, the third-largest
    # mechanism in the catalogue. Same material and same silhouette either
    # way, so cutting the back run to the flanks' inner faces is a no-op to
    # look at and removes the fight. It is also what a card builder does: you
    # cut four strips to length and butt them, you do not overlap them at the
    # corner and hope.
    box(r, 'Wall_ParapetB', x0 + 26, x0 + W - 26, D - 26, D, ztop, ztop + PAR - 20); made += 1
    # Tile_, not Roof_. `Roof_` is structure and binds to concrete; `Tile_` is
    # the roof SURFACE and binds to the recipe's `roofmat`, which vernacular
    # has declared as MI_shingle_grey since it was written and never once
    # shown - the core was covering this slab. A flat roof is felt or asphalt,
    # not fair-faced concrete.
    box(r, 'Tile_Deck', x0, x0 + W, ty + 20, D, ztop - 8, ztop); made += 1

    # A CORNICE, for the tiers that have earned one. Three courses - bed mould,
    # corona, cap - because a cornice that is one projecting slab reads as a
    # shelf. This is vernacular's grandeur lever: the traditional styles gain
    # ornament at the top as they grow, where modern gains a stepped crown and
    # rooftop plant. build_modern deliberately has no cornice and keeps its
    # flat coping over a shadow gap; that is its identity, not an omission.
    cp = spec.get('cornice') or 0.0
    if cp and spec.get('corbel'):
        # CORBELLED BRICK, not a moulded cornice. A warehouse crowns itself by
        # stepping courses out one at a time - the same material all the way
        # up, which is what a builder does when there is no budget for stone.
        zc = (GF + max(1, F - SBF) * FH) if SB else ztop
        for k in range(4):
            o = cp * (0.30 + 0.22 * k)
            box(r, 'Wall_Corbel%d' % k, x0 - o * 0.34, x0 + W + o * 0.34,
                -o, 30, zc - 44 + k * 13, zc - 44 + (k + 1) * 13); made += 1
        box(r, 'Band_CorbelCap', x0 - cp * 0.42, x0 + W + cp * 0.42,
            -cp * 1.02, 32, zc + 8, zc + 20); made += 1
    elif cp:
        # A cornice crowns the MAIN mass, with any set-back attic rising
        # BEHIND it. Placed at ztop it sat above the setbacks instead, which
        # is a cornice on the wrong building - the attic wore it as a hat.
        zc = (GF + max(1, F - SBF) * FH) if SB else ztop
        box(r, 'Band_CorniceBed', x0 - 10, x0 + W + 10, -cp*0.45, 30,
            zc - 34, zc - 16); made += 1
        box(r, 'Band_Cornice', x0 - 16, x0 + W + 16, -cp, 32,
            zc - 16, zc + 8); made += 1
        box(r, 'Band_CorniceCap', x0 - 12, x0 + W + 12, -cp*0.62, 30,
            zc + 8, zc + 18); made += 1

    made += roof_plant(r, x0, W, ztop, spec.get('roof_units', 1), rnd,
                       D=D)
    if spec.get('gable'):
        # A GABLE FRONT. A chapel or an institute: the roof turned end-on to
        # the street so the building shows its section. Stepped in five
        # courses like every other rake in this catalogue, because that is
        # what cut card does.
        gh = float(spec['gable'])
        gm = x0 + W * 0.5
        for k in range(6):
            t = k / 6.0
            hw = (W * 0.5 + 10) * (1.0 - t)
            box(r, 'Wall_Gable%d' % k, gm - hw, gm + hw, -18, 30,
                ztop + PAR + gh * t, ztop + PAR + gh * (t + 0.18)); made += 1
        # a rose window in the gable
        box(r, 'Glass_Rose', gm - 44, gm + 44, -22, -18,
            ztop + PAR + gh * 0.16, ztop + PAR + gh * 0.52); made += 1
        box(r, 'Frame_RoseSurround', gm - 56, gm + 56, -26, -18,
            ztop + PAR + gh * 0.10, ztop + PAR + gh * 0.58); made += 1
    if spec.get('cupola'):
        # A CORNER BUILDING ANNOUNCES ITSELF AT THE CORNER. The chamfer runs
        # the full height and the cupola sits on top of it - a pub or a
        # commercial hotel on a street corner, and the one vernacular that
        # is designed to be seen from two directions at once.
        ch = float(spec['cupola'])
        cxp = x0 + (28.0 if spec.get('corner_side', 'left') == 'left'
                    else W - 28.0)
        for k in range(3):
            o = 74.0 - k * 20.0
            box(r, 'Wall_Cupola%d' % k, cxp - o, cxp + o, 30 - o, 30 + o,
                ztop + PAR + k * ch * 0.30,
                ztop + PAR + (k + 1) * ch * 0.30); made += 1
            box(r, 'Band_CupolaCap%d' % k, cxp - o - 8, cxp + o + 8,
                22 - o, 38 + o, ztop + PAR + (k + 1) * ch * 0.30,
                ztop + PAR + (k + 1) * ch * 0.30 + 12); made += 1
        box(r, 'Frame_Finial', cxp - 7, cxp + 7, 23, 37,
            ztop + PAR + ch * 0.90 + 12, ztop + PAR + ch * 1.24); made += 1
    if spec.get('pediment'):
        # THE PEDIMENT, stepped rather than triangular - a card model cuts
        # steps, and at 1:87 a five-step rake reads as a pitch.
        pw = W * float(spec.get('pediment_w', 0.46))
        pm = x0 + W * 0.5
        ph = float(spec.get('pediment', 120.0))
        for k in range(5):
            t = k / 5.0
            hw = pw * 0.5 * (1.0 - t)
            box(r, 'Wall_Ped%d' % k, pm - hw, pm + hw, -30, 24,
                ztop + PAR + ph * t, ztop + PAR + ph * (t + 0.21)); made += 1
        box(r, 'Band_PedBase', pm - pw * 0.5 - 14, pm + pw * 0.5 + 14,
            -38, 28, ztop + PAR - 14, ztop + PAR + 8); made += 1
    if spec.get('stacks'):
        # CHIMNEY STACKS, one on each party wall. A terrace is a row of
        # houses and the stacks are where you can count them from the roof -
        # the only place the repetition is visible from above.
        ns = max(2, int(spec['stacks']))
        for k in range(ns):
            sx = x0 + W * (k + 0.5) / float(ns)
            sw = min(84.0, W / float(ns) * 0.34)
            box(r, 'Wall_Stack%d' % k, sx - sw / 2, sx + sw / 2, 140, 250,
                ztop, ztop + PAR + 108); made += 1
            box(r, 'Band_StackCap%d' % k, sx - sw / 2 - 9, sx + sw / 2 + 9,
                131, 259, ztop + PAR + 108, ztop + PAR + 122); made += 1
            for pk in range(2):
                px = sx - sw * 0.22 + sw * 0.44 * pk
                box(r, 'Frame_Pot%d_%d' % (k, pk), px - 11, px + 11,
                    176, 214, ztop + PAR + 122, ztop + PAR + 168); made += 1
    if spec.get('hoist'):
        # THE HOIST BEAM. A loading bay needs a way to get goods to the top
        # floor, and the gantry projecting over the street is the single
        # detail that says "warehouse" from across a block.
        hx = x0 + W * 0.5
        # SIZED TO THE READ THRESHOLD, not to a drawing. A feature must
        # subtend about 0.4% of frame width to register; at the hero framing
        # we actually ship (camera 18,083 uu out, 28.84 deg) the frame is
        # 9,299 uu wide, so that threshold is 37.2 uu. Every member here was
        # 18-30 uu - ALL of them under it - which is why a gantry that is
        # present in the model reads as a small box on the parapet (P1).
        #
        # The members grow; the OVERSAIL does not. GATE-05 allows 130 uu over
        # the pavement and the beam already reaches 118, so reach was never
        # the problem - mass was. At 1:87 a 56 uu baulk is a half-metre timber,
        # which is what a warehouse hoist actually is.
        box(r, 'Timber_HoistPost', hx - 28, hx + 28, 10, 62,
            ztop, ztop + PAR + 92); made += 1
        # 118, not 140: GATE-05 allows 130 uu of ornament over the pavement
        # and the beam was the deepest thing on the building. A gantry that
        # oversails further than the rule is a gantry that hits the model's
        # neighbour on a real street.
        box(r, 'Timber_HoistBeam', hx - 24, hx + 24, -118, 34,
            ztop + PAR + 52, ztop + PAR + 104); made += 1
        box(r, 'Frame_HoistBrace', hx - 19, hx + 19, -88, 22,
            ztop + PAR + 18, ztop + PAR + 66); made += 1
        # the block grows INWARD from its outer face: -112 stays put so the
        # oversail is untouched, and the mass arrives behind it.
        box(r, 'Frame_HoistBlock', hx - 22, hx + 22, -112, -68,
            ztop + PAR + 30, ztop + PAR + 62); made += 1
    # ROOF ACCESS. Skipped when a roof garden is built, because that lays its
    # own shed; skipped on a single-storey lock-up, which gets a hatch through
    # roof_plant instead of a stair house. Also skipped under a penthouse,
    # whose own core carries the stair.
    if (F >= 1 and not spec.get('roof_garden')
            and not spec.get('penthouse') and spec.get('stair_head', True)):
        made += stair_head(r, x0, W, D, ztop, rnd)

    # ---- the retrofit roof ------------------------------------------------
    # THE ROOF IS ZONED, front to back. The first version laid the garden over
    # the whole roof and then put the penthouse's own deck slab across it at
    # +94 - which buried every planter, bloom and bench under a floor. Only the
    # pergola showed, because it was tall enough to poke out.
    #
    # So the garden takes the FRONT of the roof, where it is seen from the
    # street, and the penthouse sits BEHIND it. Everything stays inside the
    # parapet line, so the footprint is untouched.
    rg = spec.get('roof_garden')
    ph = spec.get('penthouse')
    if rg or ph:
        gx0, gx1 = x0 + 46, x0 + W - 46
        gy0, gy1 = ty + 64, D - 44
        # A PENTHOUSE REPLACES THE GARDEN, it does not share the roof with
        # it. t4's roof IS the garden; t5 is the same building after somebody
        # bought the air rights, and what goes up there takes the roof. The
        # first version split them front/back, which read as a shed parked
        # beside a pergola rather than as an addition to the building.
        split = gy0 if ph else gy1

    if rg and not ph:
        box(r, 'Timber_Deck', gx0, gx1, gy0, split, ztop, ztop + 9); made += 1
        # planters along the front, against the parapet
        # REAL BEDS, from the Uniblocks garden kit. These were boxes: a
        # timber cube with a bloom cube sitting in it, which read as a pink
        # cushion on a stool however the numbers were tuned. Some things
        # cannot be cut from card and a modelmaker does not try - they buy a
        # moulded planter. ubkit lays the pieces out from their MEASURED
        # bounds; genbuild.piece carries them through the same sink as a box,
        # so the fast path bakes them into the model.
        import ubkit
        seg = max(1, int((gx1 - gx0 - 2*ubkit.CAP) / ubkit.SEG / 3.0))
        blen = ubkit.bed_length(seg)
        # MORE BEDS, AND A SECOND RANK. The garden was two troughs holding
        # fourteen plants between them on a roof with 42 bed parts on it -
        # the beds read, the planting did not. The Uniblocks bed is 50 uu
        # deep and that is what its parts are, so density comes from more
        # beds rather than from crowding these ones.
        npl = max(2, int((gx1 - gx0) / (blen + 30.0)))
        gap = ((gx1 - gx0) - npl * blen) / float(npl + 1)
        pys = [gy0 + ubkit.DEPTH + 18.0]
        back = split - ubkit.DEPTH - 40.0
        if back - pys[0] > ubkit.DEPTH * 2 + 150.0:
            pys.append(back)
        for i in range(npl * len(pys)):
            px = gx0 + gap + (i % npl) * (blen + gap)
            py = pys[i // npl]
            # bed_yaw, NOT yaw. This loop variable used to be called `yaw`,
            # which SHADOWED the function parameter of the same name - and
            # Python leaks a loop variable into the enclosing scope, so after
            # the last flowerbed piece `yaw` held ITS rotation for the rest of
            # the builder. The only mkactor after this point is the canopy, so
            # the canopy alone was created at yaw 180 and flipped whole about
            # the actor origin: local x 68..width became world x -(width-68)
            # ..-68, entirely off the parcel.
            #
            # That is the exact width-minus-68 signature the ladder sweep saw
            # - 752 / 1162 / 1572 uu over on parcels of 820 / 1230 / 1640 -
            # and it fired only on the two recipes that have BOTH a flowerbed
            # and a canopy (vernacular t4, vernacular5 t5). GATE-05 was right
            # every time it refused them.
            # ENUMERATED, like the downpipes: a bed returns BOTH end caps and
            # BOTH side walls, which share a short() name, so 'Bed%d_%s'
            # collided and UE auto-renamed the losers to StaticMesh1 - default
            # material, GATE-01/02/06 together. Five combos carried it.
            for _bi, (mesh, (mx, my, mz), bed_yaw) in enumerate(
                    ubkit.bed(seg, x=px, y=py, z=ztop + 9)):
                piece(r, rolemap.donor_name('MI_planter', 'Bed%d_%d_%s' % (i, _bi, ubkit.short(mesh))),
                      mesh, (mx, my, mz), (0.0, bed_yaw, 0.0),
                      mat='MI_planter')
                made += 1
            # REAL PLANTING, not a green box. A bed holds something growing;
            # an extruded cube never reads as that however it is coloured.
            # avkit sizes come from measurement so nothing pushes through a
            # wall, and the soil box stays underneath as the thing they sit in.
            import avkit
            x0b, y0b, x1b, y1b = ubkit.bed_extent(seg, px, py)
            box(r, 'Gravel_Soil%d' % i, x0b + 14, x1b - 14, y0b + 14, y1b - 14,
                ztop + 9 + 40, ztop + 9 + 62); made += 1
            for k, (key, (plx, ply, plz), pyaw) in enumerate(
                    avkit.bed_planting(x0b + 22, y0b + 18, x1b - 22, y1b - 18,
                                       ztop + 9 + 58, rnd)):
                piece(r, rolemap.donor_name(avkit.mat(key), 'Plant%d_%d' % (i, k)), avkit.path(key),
                      (plx, ply, plz), (0.0, pyaw, 0.0), mat=avkit.mat(key))
                made += 1
            # A SHRUB in every other bed, so the roof has height. This was a
            # trunk box under three stacked crown boxes - the last cube left
            # in the garden. avkit's bush is 614 uu across, so it is scaled to
            # the bed it stands in rather than dropped in at author size:
            # overhanging the rim a little is what a planted shrub does,
            # swallowing the bed is not.
            if i % 2 == 0:
                tx = (x0b + x1b) / 2.0
                ty = (y0b + y1b) / 2.0
                bw = avkit.size('bush')[0]
                sc = min(0.30, (y1b - y0b) * 2.6 / bw)
                piece(r, rolemap.donor_name(avkit.mat('bush'), 'Shrub%d' % i), avkit.path('bush'),
                      (tx, ty, ztop + 9 + 58), (0.0, rnd.uniform(0, 360), 0.0),
                      scale=sc, mat=avkit.mat('bush'))
                made += 1
        # ---- the roof PARK ------------------------------------------------
        # The pergola went. It was four posts, two beams, seven slats, a table
        # and two benches - eighteen boxes of timber over a strip of bare
        # deck, and it read as the frame of something rather than as a place.
        # A small rooftop park is the same footprint doing more: a flock lawn,
        # a gravel path across it, trees and shrubs, a bench, and a shed for
        # the stair that has to come up here anyway.
        pky0, pky1 = gy0 + 108, split - 26
        if pky1 > pky0 + 90:
            deck = ztop + 9
            # LAWN. Flock over card - 5 uu proud of the deck so its edge
            # catches light, which is the whole reason a model reads as made.
            # THICK, not a film. A 5 uu slab rendered as warm paper whatever
            # BaseColour said: the master's EdgeWearLift (1.42) brightens
            # toward the edge and on a slab that thin the edge is the whole
            # face. Measured RGB(142,124,100) on a material that is
            # (0.29,0.40,0.155) green. A roof lawn sits in a real build-up
            # anyway, so 30 uu is both the fix and the truer object.
            LAWN_T = 90.0
            box(r, 'Grass_Lawn', gx0 + 26, gx1 - 26, pky0, pky1,
                deck, deck + LAWN_T); made += 1

            # GRAVEL PATH, crossing the lawn from the shed to the parapet.
            # Laid as two runs meeting at a corner rather than one straight
            # strip: a path that goes somewhere reads as a park, a strip down
            # the middle reads as a divider.
            pmid = (pky0 + pky1) / 2.0
            pxj = gx0 + (gx1 - gx0) * 0.34
            box(r, 'Gravel_PathA', gx0 + 26, pxj + 34, pmid - 34, pmid + 34,
                deck, deck + LAWN_T + 2); made += 1
            box(r, 'Gravel_PathB', pxj - 34, pxj + 34, pky0, pmid + 34,
                deck, deck + LAWN_T + 2); made += 1

            # ROOF ACCESS SHED. Every roof anybody stands on has one, and it
            # is the piece that makes the rest read as reachable. Card box,
            # capped band, printed door - our own geometry, because this is
            # exactly what a modelmaker cuts.
            shw, shd, shh = 210.0, 168.0, 196.0
            shx = gx1 - 26 - shw - 40
            shy = pky1 - shd - 14
            box(r, 'Wall_Shed', shx, shx + shw, shy, shy + shd,
                deck, deck + shh); made += 1
            box(r, 'Gravel_ShedApron', shx - 30, shx + shw + 30, shy - 34,
                shy + shd + 12, deck, deck + LAWN_T + 1); made += 1
            box(r, 'Band_ShedCap', shx - 10, shx + shw + 10, shy - 10,
                shy + shd + 10, deck + shh, deck + shh + 13); made += 1
            box(r, 'Frame_ShedDoor', shx + shw * 0.28, shx + shw * 0.72,
                shy - 4, shy + 2, deck + 6, deck + shh * 0.76); made += 1
            box(r, 'Timber_ShedStep', shx + shw * 0.22, shx + shw * 0.78,
                shy - 26, shy - 2, deck, deck + 7); made += 1

            # REAL TREES. The earlier armature-and-flock trees were built
            # because donor foliage came through the merge as dark quads -
            # but that was fastbake binding ONE material across a mesh whose
            # leaf slots need the masked leaf materials. rolemap.SLOT fixes
            # it at the source, so the pack's own trees work here now, and
            # tuft clusters were never a good substitute for a tree.
            #
            # Two species at three sizes: a roof park is planted at once, so
            # the variation is in what was planted, not in age.
            TREES = (('tree_s', 0.22, 0.30, 430.0),
                     ('tree_t', 0.55, 0.68, 355.0),
                     ('tree_s', 0.80, 0.26, 300.0))
            for ti, (key, tx_f, ty_f, want_h) in enumerate(TREES):
                th = avkit.size(key)[2]
                tsc = want_h / th
                tw = avkit.size(key)[0] * tsc
                tx = gx0 + 50 + (gx1 - gx0 - 100) * tx_f
                ty = pky0 + (pky1 - pky0) * ty_f
                piece(r, rolemap.donor_name(avkit.mat(key), 'Tree%d' % ti), avkit.path(key),
                      (tx, ty, deck + LAWN_T),
                      (0.0, rnd.uniform(0, 360), 0.0), scale=tsc,
                      mat=avkit.mat(key))
                made += 1
                box(r, 'Gravel_TreePit%d' % ti, tx - tw * 0.26, tx + tw * 0.26,
                    ty - tw * 0.26, ty + tw * 0.26,
                    deck + LAWN_T - 16, deck + LAWN_T + 3); made += 1

            # SHRUBS along the back, and grass tufts breaking the lawn edge -
            # a lawn with a hard cut all the way round reads as a mat.
            # REAL SHRUBS, more of them. SM_bush_01 was failing for the same
            # reason the trees were - one material across every slot - so it
            # was kept small enough to hide the damage. It renders properly
            # now, so it can do the job the grass tufts were standing in for.
            SHRUBS = ((0.10, 0.82, 112.0), (0.26, 0.16, 92.0),
                      (0.42, 0.86, 128.0), (0.58, 0.22, 100.0),
                      (0.71, 0.80, 118.0), (0.88, 0.34, 96.0),
                      (0.95, 0.72, 108.0))
            for si, (sf_x, sf_y, sh) in enumerate(SHRUBS):
                sxp = gx0 + 70 + (gx1 - gx0 - 140) * sf_x
                syp = pky0 + (pky1 - pky0) * sf_y
                bsc = sh / avkit.size('bush')[2]
                piece(r, rolemap.donor_name(avkit.mat('bush'), 'ShrubP%d' % si), avkit.path('bush'),
                      (sxp, syp, deck + LAWN_T),
                      (0.0, rnd.uniform(0, 360), 0.0), scale=bsc,
                      mat=avkit.mat('bush'))
                made += 1
            # FLOCK IS SCATTERED FIBRE, not painted card. That is what a
            # modelmaker actually does - sifts flock over glue - and here it
            # is also the thing that WORKS: the lawn slab renders as warm
            # paper whatever material it carries (see the note below), while
            # these tufts carry MI_grass and come out green in the same
            # frame. So the green on this roof is the flock, and the slab
            # underneath is the glue bed it sits on.
            gsc = 52.0 / avkit.size('grass_tuft')[2]
            gstep = 118.0
            gnx = max(2, int((gx1 - gx0 - 120) // gstep))
            gny = max(2, int((pky1 - pky0 - 40) // gstep))
            gi = 0
            for gyi in range(gny):
                for gxi in range(gnx):
                    gxp = gx0 + 60 + gxi * gstep + rnd.uniform(-16, 16) \
                        + (gstep * 0.5 if gyi % 2 else 0.0)
                    gyp = pky0 + 20 + gyi * gstep + rnd.uniform(-14, 14)
                    if gxp > gx1 - 60 or gyp > pky1 - 14:
                        continue
                    # keep the gravel path and the shed apron clear
                    if abs(gyp - pmid) < 44 and gxp < pxj + 44:
                        continue
                    if abs(gxp - pxj) < 44 and gyp < pmid + 44:
                        continue
                    if gxp > shx - 40 and gyp > shy - 44:
                        continue
                    piece(r, rolemap.donor_name(avkit.mat('grass_tuft'), 'Tuft%d' % gi), avkit.path('grass_tuft'),
                          (gxp, gyp, deck + LAWN_T),
                          (0.0, rnd.uniform(0, 360), 0.0), scale=gsc,
                          mat=avkit.mat('grass_tuft'))
                    made += 1
                    gi += 1

            # A BENCH, facing the parapet and the street beyond it. Placed off
            # the path so it reads as somewhere to sit rather than an obstacle.
            bnl = avkit.size('bench')[1]
            piece(r, rolemap.donor_name(avkit.mat('bench'), 'Bench0'), avkit.path('bench'),
                  (gx0 + (gx1 - gx0) * 0.66, pky0 + 40, deck + LAWN_T),
                  (0.0, 90.0, 0.0), scale=1.0, mat=avkit.mat('bench'))
            made += 1

    # ---- a two-storey glass penthouse, set back ---------------------------
    # The shell below is UNCHANGED - that is the whole point of the tier.
    if ph:
        pfl = int(ph.get('floors', 2))
        ins = float(ph.get('inset', 150.0))
        pfh = float(ph.get('fl_h', 250.0))
        # MOST OF THE FOOTPRINT. It was inset 170 a side and squeezed into the
        # back 54% of the roof - about a third of the plan - which is why it
        # read as a rooftop hut. A penthouse floor is the building's floor,
        # set back just enough to leave a terrace round it.
        px0, px1 = x0 + ins, x0 + W - ins
        py0, py1 = gy0 + ins, gy1 - ins*0.6
        pz0 = ztop + 9
        # a plinth UNDER THE PENTHOUSE ONLY, not across the whole roof
        box(r, 'Timber_PentDeck', px0 - 34, px1 + 34, py0 - 40, py1 + 16,
            ztop, pz0); made += 1
        for f in range(pfl):
            z0p = pz0 + f * pfh
            z1p = z0p + pfh
            box(r, 'Glass_Pent%dF' % f, px0 + 6, px1 - 6, py0, py0 + 3,
                z0p + 8, z1p - 12); made += 1
            box(r, 'Glass_Pent%dB' % f, px0 + 6, px1 - 6, py1 - 3, py1,
                z0p + 8, z1p - 12); made += 1
            box(r, 'Glass_Pent%dL' % f, px0, px0 + 3, py0, py1,
                z0p + 8, z1p - 12); made += 1
            box(r, 'Glass_Pent%dR' % f, px1 - 3, px1, py0, py1,
                z0p + 8, z1p - 12); made += 1
            box(r, 'Interior_Pent%d' % f, px0 + 26, px1 - 26, py0 + 26, py1 - 26,
                z0p + 8, z1p - 12); made += 1
            for cx_, cy_ in ((px0, py0), (px1, py1), (px0, py1), (px1, py0)):
                box(r, 'Rail_PentP%d_%d_%d' % (f, int(cx_), int(cy_)),
                    cx_ - 7, cx_ + 7, cy_ - 7, cy_ + 7, z0p, z1p); made += 1
            box(r, 'Rail_PentBand%d' % f, px0 - 5, px1 + 5, py0 - 5, py1 + 5,
                z1p - 12, z1p); made += 1
            for k in range(1, 5):
                mx = px0 + (px1 - px0) * k / 5.0
                box(r, 'Mullion_PentF%d_%d' % (f, k), mx - 4, mx + 4,
                    py0 - 2, py0 + 5, z0p + 8, z1p - 12); made += 1
        # a DOOR onto the terrace, and a step down from it
        dx = (px0 + px1)/2.0
        box(r, 'Frame_PentDoorL', dx - 66, dx - 54, py0 - 4, py0 + 6,
            pz0 + 8, pz0 + 190); made += 1
        box(r, 'Frame_PentDoorR', dx + 54, dx + 66, py0 - 4, py0 + 6,
            pz0 + 8, pz0 + 190); made += 1
        box(r, 'Frame_PentDoorH', dx - 66, dx + 66, py0 - 4, py0 + 6,
            pz0 + 180, pz0 + 190); made += 1
        box(r, 'Timber_PentStep', dx - 90, dx + 90, py0 - 44, py0 - 6,
            ztop + 9, ztop + 22); made += 1
        # terrace furniture on the plinth in front of the door
        for k, ox_ in enumerate((-180.0, 180.0)):
            box(r, 'Timber_Lounger%d' % k, dx + ox_ - 52, dx + ox_ + 52,
                py0 - 40, py0 - 10, pz0, pz0 + 26); made += 1
        # planters flanking the terrace so it is not a bare shelf
        for k, ox_ in enumerate((px0 - 26, px1 - 42)):
            box(r, 'Timber_TerrPl%d' % k, ox_, ox_ + 68, py0 - 44, py0 - 4,
                pz0, pz0 + 44); made += 1
            box(r, 'Bloom_Terr%d' % k, ox_ + 8, ox_ + 60, py0 - 38, py0 - 10,
                pz0 + 38, pz0 + 74); made += 1
        # The cap was a 16-thick slab with a 12-thick 'fascia' stacked ON TOP
        # of it - 28 uu of solid white reading as a lid dropped on a box. A
        # fascia is the EDGE, not another layer. Slim roof, thin drip lip
        # projecting past it, and a shadow gap between the two so the lip
        # reads as a separate cut piece the way the parapet coping does.
        ptz = pz0 + pfl * pfh
        box(r, 'Roof_PentCap', px0 - 8, px1 + 8, py0 - 8, py1 + 8,
            ptz - 10, ptz - 2); made += 1
        box(r, 'Band_PentDrip', px0 - 20, px1 + 20, py0 - 20, py1 + 20,
            ptz, ptz + 7); made += 1
        # balustrade around the garden edge of the terrace only
        box(r, 'Rail_TerrEdge', gx0 + 20, gx1 - 20, split + 6, split + 16,
            ztop + 9, ztop + 62); made += 1

    # ---- downpipes, from the facade kit -----------------------------------
    # A rainwater pipe at each end of the frontage. This is the sort of part a
    # card builder cannot cut and a modelmaker buys as a length of rod, and it
    # is most of what makes an elevation look serviced rather than drawn.
    if spec.get('downpipes', True) and F >= 1:
        import avkit as _av
        for _sx in (x0 + 14.0, x0 + W - 14.0):
            # ENUMERATED. 'Pipe%d_%d' % (x, z) collides whenever two pipe
            # segments round to the same pair - measured, twice per model on
            # vernacular t1/t2 - and UE silently auto-renames the loser to
            # 'StaticMesh1', which lands on WorldGridMaterial and trips
            # GATE-01/02/06 together. Invisible until piece() started actually
            # placing donors; the gate caught it on the first bake that could.
            for _pi, (key, (dx, dy, dz), _dyaw) in enumerate(_av.downpipe(
                    36.0, ztop - 20.0, _sx, -18.0, rnd)):
                piece(r, rolemap.donor_name(_av.mat(key), 'Pipe%d_%d_%d' % (int(_sx), int(dz), _pi)), _av.path(key),
                      (dx, dy, dz), (0.0, 0.0, 0.0), mat=_av.mat(key))
                made += 1

    # ---- canopy -------------------------------------------------------------
    if spec.get('canopy'):
        proj = spec['canopy']
        c = mkactor('BLD2_%s_Canopy' % n, origin, (0.0, yaw, 0.0))
        # The head stays a box - it is structure, and a box is what a card
        # builder cuts for it. What was wrong was the AWNING being a box too:
        # one flat slab the full width of the shopfront, which is the one
        # thing a fabric awning is not.
        box(c, 'Wall_CanopySlab', x0 - 10, x0 + W + 10, -14, 8, GF - 26, GF - 10); made += 1
        # A CANOPY IS A BOX, and this is the right answer rather than a
        # concession. Two donor "awnings" were tried and both were rendered
        # before judging: SM_shopAwing_01 is a market STALL canopy on four
        # legs that reach the ground, and SM_shopCanopy_01 is a slatted
        # LOUVRE - at the size a shopfront wants it is a knife edge that
        # disappears, and blown up 3x it reads as dark blades throwing
        # striped shadows. Neither is fabric. A modelmaker cuts a canopy from
        # card and paints the fascia, which is exactly these two boxes, and
        # the fascia is where this building's accent colour lives.
        # 'Wall_CanopySlabU', not a second 'Wall_CanopySlab' - the head and
        # the underslab are two boxes and were given ONE name, so UE renamed
        # the second and the gate correctly refused it. Same role, so the
        # material is unchanged.
        box(c, 'Wall_CanopySlabU', x0 - 10, x0 + W + 10, -proj, 8, GF - 26, GF - 10); made += 1
        box(c, 'Accent_CanopyFascia', x0 - 10, x0 + W + 10, -proj - 8, -proj, GF - 40, GF - 4); made += 1
        made += 1
    print('%s: %d boxes, height %d uu' % (n, made, total))
    return total


# ---------------------------------------------------------------------------
# Late-60s / 70s late-modern.
#
# The difference from the vernacular style is RHYTHM AND PROPORTION, not more
# detail. Card wants flat planes and crisp cut edges, which is why this era is
# easier to fake convincingly in card than Main Street is: there is no
# ornament to approximate, only planes to place accurately.
#
#   vertical bay rhythm  ->  continuous horizontal ribbon
#   punched window       ->  glazing set 880 mm behind a proud spandrel band
#   masonry pier         ->  precast fin
#   projecting cornice   ->  flat coping over a shadow gap
#   shopfront in a frame ->  recessed arcade under an overhanging mass
#
# Everything still lands in y 0..60 with the core starting at 62, exactly as
# the vernacular style does, because step_cores3.py depends on that and a
# facade that drifts off it goes hollow.
# ---------------------------------------------------------------------------
ARCADE = 78.0        # ground floor set back under the overhang
SPAND_F = 0.34       # spandrel band as a fraction of floor height
BAND_PROUD = 40.0    # how far the spandrel stands off the facade line
GLAZE_Y = 44.0       # glazing plane: 84 uu / 840 mm of shadow behind the band
# THE DEPTH BUDGET IS 0..60. The core front is at FACADE_BACK+CLEAR = 62, so
# anything past it is inside solid mass: invisible if fully behind, z-FIGHTING
# if it straddles the face. Measured on Tower before this was fixed:
#   Glass_Shop      Y  78..80   INSIDE CORE      -> storefronts read blank
#   Interior_Shop   Y  94..100  INSIDE CORE
#   Interior_Ribbon Y  60..66   STRADDLES FACE   -> windows clipped at range
# The arcade is the one thing allowed past it, and only because step_cores3.py
# now steps the ground band back by ARCADE to make the recess real.
FIN_W = 34.0         # a precast fin, not a mullion: it has to be deep enough
FIN_PROUD = 46.0     # to cast a real shadow across the glass beside it


def build_modern(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    made = 0

    # ---- ground floor: an arcade, not a shopfront -------------------------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 4, x0 + W + 4, ARCADE - 10, D * 0.08, 0, 22); made += 1
    col_w = 64.0
    for b in range(BAYS + 1):
        px = min(x0 + b * (W / float(BAYS)), x0 + W - col_w)
        box(g, 'Wall_Col%d' % b, px, px + col_w, 0, 62, 0, GF); made += 1
    # the soffit is the whole point of an arcade - it is what casts the shadow
    box(g, 'Wall_Soffit', x0 - 4, x0 + W + 4, 0, ARCADE, GF - 14, GF); made += 1
    sx0, sx1 = x0 + col_w, x0 + W - col_w
    box(g, 'Glass_Shop', sx0, sx1, ARCADE, ARCADE + 2, 26, GF - 20); made += 1
    box(g, 'Interior_Shop', sx0 - 6, sx1 + 6, ARCADE + 16, ARCADE + 22, 22, GF - 16); made += 1
    for k in range(1, BAYS * 2):
        mx = sx0 + (sx1 - sx0) * k / float(BAYS * 2)
        box(g, 'Mullion_Shop%d' % k, mx - 3, mx + 3, ARCADE - 5, ARCADE + 1, 26, GF - 20); made += 1
    # AN ARCADE IS BUILT, NOT EXTRUDED. Column bases and caps, a coffer in the
    # soffit over each bay, a fascia at the head and a door in every other bay.
    # DETAIL-01 caught Annex at 8.2 parts per metre - a two-storey block gets
    # almost nothing from the upper-floor loop, so its ground floor has to
    # carry the elevation, and this one was twelve parts wide.
    for b in range(BAYS + 1):
        px = min(x0 + b * (W / float(BAYS)), x0 + W - col_w)
        box(g, 'Wall_ColBase%d' % b, px - 10, px + col_w + 10, -6, 70, 0, 40)
        box(g, 'Frame_ColCap%d' % b, px - 8, px + col_w + 8, -4, 68, GF - 46, GF - 26)
        made += 2
    for b in range(BAYS):
        bx0 = x0 + b * (W / float(BAYS)) + col_w
        bx1 = x0 + (b + 1) * (W / float(BAYS))
        if bx1 - bx0 < 60:
            continue
        box(g, 'Roof_Coffer%d' % b, bx0 + 8, bx1 - 8, 14, ARCADE - 14,
            GF - 30, GF - 14); made += 1
        box(g, 'Ground_Arcade%d' % b, bx0 - 6, bx1 + 6, 0, ARCADE, 0, 10); made += 1
        if b % 2 == 0:
            dcx = (bx0 + bx1)/2.0
            box(g, 'Frame_Door%d' % b, dcx - 52, dcx + 52, ARCADE - 6, ARCADE + 4,
                26, 26 + 190); made += 1
            box(g, 'Interior_Door%d' % b, dcx - 44, dcx + 44, ARCADE + 4,
                ARCADE + 12, 30, 26 + 178); made += 1
    box(g, 'Band_ShopFascia', x0 - 8, x0 + W + 8, ARCADE - 12, ARCADE + 8,
        GF - 20, GF - 4); made += 1

    # ---- upper floors: ribbon behind a proud band -------------------------
    for f in range(F):
        z0 = GF + f * FH
        z1 = z0 + FH
        sp = FH * SPAND_F
        # Only the TOP floor sets back, which is the rule step_cores3.py bands
        # the core on. build_modern ignored `setback` entirely at first, so the
        # core stepped back 140 uu and the facade did not: gap_check2 measured
        # a 142 uu void behind Tower F6. The spec said setback; the geometry
        # has to agree with it.
        _sb = spec.get('setback') or 0.0
        # cores.setback_at is THE resolver - the same one the core bands on.
        # This formula used to be written out here, again lower down, again in
        # build_contemporary and again in cores; four copies of one rule is
        # how a floor steps back and its core does not (P12).
        import cores as _co
        fy = _co.setback_at(spec, f, F)
        a = mkactor('BLD2_%s_F%d' % (n, f), origin, (0.0, yaw, 0.0))
        # spandrel: full width, standing proud. The primary horizontal.
        box(a, 'Band_Spandrel', x0 - 7, x0 + W + 7, fy - BAND_PROUD, fy + 20, z0 + 3, z0 + sp); made += 1
        # returns at each end so the band does not read as a floating slab.
        # They WRAP it - 4 uu proud in y, 4 wider in x, and the band lifted 3
        # off the floor line - because flush with it they shared the min-x,
        # min-y AND min-z planes with the band, all three at once. The outer
        # bound is unchanged: the return still holds x0-10, so the parcel
        # measurement GATE-05 makes is exactly what it was.
        box(a, 'Wall_EndL', x0 - 10, x0 + 16, fy - BAND_PROUD - 4, fy + 60, z0, z1); made += 1
        box(a, 'Wall_EndR', x0 + W - 16, x0 + W + 10, fy - BAND_PROUD - 4, fy + 60, z0, z1); made += 1
        gz0, gz1 = z0 + sp, z1
        gx0, gx1 = x0 + 16, x0 + W - 16
        box(a, 'Glass_Ribbon', gx0, gx1, fy + GLAZE_Y, fy + GLAZE_Y + 2, gz0 + 4, gz1 - 4); made += 1
        box(a, 'Interior_Ribbon', gx0, gx1, fy + GLAZE_Y + 8, fy + GLAZE_Y + 14, gz0, gz1); made += 1
        # OFF the floor and ceiling lines by 3: at gz0 and gz1 exactly these
        # shared a plane with every fin's end face.
        box(a, 'Frame_RibbonS', gx0 - 4, gx1 + 4, fy + GLAZE_Y - 8, fy + GLAZE_Y + 2, gz0 + 3, gz0 + 9); made += 1
        box(a, 'Frame_RibbonT', gx0 - 4, gx1 + 4, fy + GLAZE_Y - 8, fy + GLAZE_Y + 2, gz1 - 9, gz1 - 3); made += 1
        # A RIBBON IS NOT A SHEET OF GLASS. It is a run of lights divided by
        # mullions every metre or so, with a transom across it - and the
        # spandrel below is panels with joints between them, not one casting.
        # Without those the whole upper elevation was ten parts per floor
        # against the vernacular's twenty-four, which is the detail the F1
        # reader saw draining out of the later blocks.
        nmul = max(4, BAYS*3)
        for k in range(1, nmul):
            mx = gx0 + (gx1 - gx0)*k/float(nmul)
            # RUNS UNDER THE HEAD, and stops at its soffit. Ending at
            # gz1-4 put the mullion's top face on exactly the same plane as
            # Frame_MullHead's, over an 8x8 patch, on every vertical of every
            # ribbon floor - 21% of every coplanar pair in the catalogue, and
            # a piece of card cannot end flush with the piece laid across it.
            box(a, 'Mullion_R%dV%d' % (f, k), mx - 4, mx + 4,
                fy + GLAZE_Y - 7, fy + GLAZE_Y + 1, gz0 + 4, gz1 - 12); made += 1
        tz = gz0 + (gz1 - gz0)*0.62
        # PROUD OF THE VERTICALS, not in their plane. A transom crossing a
        # mullion at the same depth shares both faces where they cross; a
        # modelmaker laminates the horizontal over the verticals, which is
        # both buildable and the reveal the eye reads as thickness.
        box(a, 'Mullion_R%dT' % f, gx0, gx1, fy + GLAZE_Y - 10, fy + GLAZE_Y - 2,
            tz - 4, tz + 4); made += 1
        # spandrel panel joints, one per bay, and a reveal under the band
        for b in range(1, BAYS):
            jx = x0 + W*b/float(BAYS)
            box(a, 'Frame_Sp%dJ%d' % (f, b), jx - 4, jx + 4,
                fy - BAND_PROUD - 2, fy - BAND_PROUD + 14, z0 + 4, z0 + sp - 4)
            made += 1
        box(a, 'Frame_Sp%dReveal' % f, x0 - 4, x0 + W + 4,
            fy - BAND_PROUD - 3, fy - BAND_PROUD + 9, z0 + sp - 10, z0 + sp - 3)
        box(a, 'Frame_Sp%dCill' % f, x0 - 12, x0 + W + 12,
            fy - BAND_PROUD - 9, fy - BAND_PROUD + 6, z0 - 8, z0 + 4)
        made += 2
        # precast fins: the vertical rhythm, standing off the glass
        # FEWER fins, standing further off. At BAYS*2 they subdivided the
        # ribbon into six panes and read as window mullions - which is the
        # vernacular rhythm, the exact thing this style is not.
        fins = max(2, BAYS)
        for k in range(1, fins):
            fx = gx0 + (gx1 - gx0) * k / float(fins)
            box(a, 'Wall_Fin%d' % k, fx - FIN_W / 2, fx + FIN_W / 2,
                fy - FIN_PROUD, fy + GLAZE_Y + 7, gz0, gz1); made += 1
        mz = gz0 + (gz1 - gz0) * 0.58
        box(a, 'Mullion_RibbonH', gx0, gx1, fy + GLAZE_Y - 9, fy + GLAZE_Y - 3, mz - 3, mz + 3); made += 1
        # OPENING LIGHTS. A sealed ribbon is a curtain wall; a 60s office block
        # has top-hung vents, and every third light being proud of the plane is
        # what stops a run of glass reading as one sheet.
        for k in range(1, nmul, 3):
            ax0 = gx0 + (gx1 - gx0)*k/float(nmul)
            ax1 = gx0 + (gx1 - gx0)*(k + 1)/float(nmul)
            box(a, 'Frame_Vent%d_%d' % (f, k), ax0 + 5, ax1 - 5,
                fy + GLAZE_Y - 12, fy + GLAZE_Y - 2, mz + 8, gz1 - 10)
            box(a, 'Glass_Vent%d_%d' % (f, k), ax0 + 9, ax1 - 9,
                fy + GLAZE_Y - 10, fy + GLAZE_Y - 8, mz + 12, gz1 - 14)
            made += 2
        # SPANDREL PANELS. The band is panels bolted to a frame, not a casting:
        # each bay gets a face standing slightly proud between the joints.
        for b in range(BAYS):
            px0 = x0 + W*b/float(BAYS) + 10
            px1 = x0 + W*(b + 1)/float(BAYS) - 10
            # COLOURED SPANDREL. The 1960s curtain wall whose panels are a
            # colour, not a grey - the era's other facade, and a one-word
            # change here because the role vocabulary already carries an
            # accent. It is the cheapest distinct building in the catalogue.
            _pn = ('Accent_Panel%d_%d' if spec.get('spandrel_colour')
                   else 'Band_Panel%d_%d') % (f, b)
            box(a, _pn, px0, px1,
                fy - BAND_PROUD - 6, fy - BAND_PROUD + 10, z0 + 12, z0 + sp - 12)
            made += 1
        # heads and cills to the mullion run
        box(a, 'Frame_MullHead%d' % f, gx0 - 6, gx1 + 6, fy + GLAZE_Y - 9,
            fy + GLAZE_Y + 2, gz1 - 12, gz1 - 4)
        box(a, 'Frame_MullCill%d' % f, gx0 - 8, gx1 + 8, fy + GLAZE_Y - 13,
            fy + GLAZE_Y + 2, gz0 + 2, gz0 + 12)
        made += 2
        # hand tolerance: MODEL tolerances, 1-2%, not building tolerances
        _setprops({
            'instance': a, 'values': json.dumps({
                'RelativeLocation': {'x': rnd.uniform(-2.0, 2.0) * (W / 100.0),
                                     'y': rnd.uniform(-1.4, 1.4), 'z': 0.0},
                'RelativeRotation': {'pitch': 0.0, 'yaw': jit_yaw(rnd, W, 0.8),
                                     'roll': rnd.uniform(-0.6, 0.6)}})})

    # ---- canted supports ------------------------------------------------
    # GOOGIE. The roadside commercial building of the same fifteen years:
    # the mass lifted on splayed legs with a glazed void beneath, and the
    # slab cantilevering past them. Not one vertical on it, which is the
    # opposite of every other modern in the catalogue.
    if spec.get('canted'):
        cn = mkactor('BLD2_%s_Legs' % n, origin, (0.0, yaw, 0.0))
        nl = max(3, BAYS)
        for k in range(nl + 1):
            lx = x0 + W * k / float(nl)
            lx = min(max(lx, x0 + 8), x0 + W - 8)
            # splay: three stacked boxes walking outward as they go down
            for st in range(4):
                t = st / 4.0
                dx = 46.0 * t
                box(cn, 'Frame_Leg%d_%d' % (k, st), lx - 14 - dx, lx + 14 + dx,
                    -18 - 22 * t, 40, GF * (1.0 - (st + 1) / 4.0),
                    GF * (1.0 - t)); made += 1
        box(cn, 'Band_LiftSlab', x0 - 22, x0 + W + 22, -54, 66,
            GF - 34, GF + 6); made += 1
        box(cn, 'Accent_LiftFascia', x0 - 26, x0 + W + 26, -62, -50,
            GF - 40, GF + 10); made += 1

    # ---- roof: flat coping over a shadow gap, no cornice ------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    ztop = GF + F * FH
    # the gap is recessed BEHIND the facade line, so the coping reads as a
    # separate cut piece rather than a moulding
    box(r, 'Wall_ParapetF', x0, x0 + W, 12, 40, ztop, ztop + PAR - 12); made += 1
    box(r, 'Band_Coping', x0 - 6, x0 + W + 6, -6, 44, ztop + PAR - 12, ztop + PAR); made += 1
    # THE FRONT CORNERS, and this is the back-run bug again at the other end.
    # ParapetF occupies y 12..40; the flank runs started at 30, so they lapped
    # it by 10 uu while also sharing its x faces - two like-facing surfaces at
    # one depth on the roofline, which is where the owner saw it. Starting the
    # flanks at F's back face makes it a butt joint, which the rule allows and
    # a card builder cuts. I mitred ParapetB and never looked at ParapetF: a
    # fix applied to one instance of a mechanism is not a fix to the mechanism.
    box(r, 'Wall_ParapetL', x0, x0 + 24, 40, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 24, x0 + W, 40, D, ztop, ztop + PAR - 18); made += 1
    # REAR PARAPET, and the deck as a SURFACE. Both exist because the core no
    # longer fills the roof void: with `open_roof` it stops at the roof line,
    # so the back of the roof is a real hole and the deck is a real surface
    # instead of something buried inside the core. See cores.bands_for.
    # mitred to the flank runs - see the ParapetB note above
    box(r, 'Wall_ParapetB', x0 + 24, x0 + W - 24, D - 24, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Tile_Deck', x0, x0 + W, 20, D, ztop - 8, ztop); made += 1
    made += roof_plant(r, x0, W, ztop, spec.get('roof_units', 1), rnd,
                       ymin=200.0, yspread=100.0, D=D)
    if F >= 1 and spec.get('stair_head', True):
        made += stair_head(r, x0, W, D, ztop, rnd)
    # THE EXPRESSED SERVICE TOWER - a blind precast shaft running the full
    # height and standing proud of the mass, carrying the stair and the lift
    # past the parapet. It is the one thing that stops a brutalist block
    # reading as a box, and it belongs to the era as much as the reveals do.
    if spec.get('service_tower'):
        stw = W * 0.19
        stx = x0 + W * (0.08 if rnd.random() < 0.5 else 0.73)
        stx = max(x0 + 10, min(stx, x0 + W - stw - 10))
        # Band_, NOT Wall_. The role decides the material, and Wall_ resolves
        # to the lot's wall colour - which for modern2 is MI_concrete, the
        # same material as the wall the shaft stands against. A full-height
        # EXPRESSED core painted its background is not expressed at all, and
        # that is P3: the shaft has 34 uu of projection and no contrast, so it
        # disappears at any range where the shadow is soft.
        #
        # Band_ resolves to `trim`, whose documented purpose in rolemap is
        # exactly this - "the parts a real building picks out in a second
        # colour". An expressed service core is that part. The cap beside it
        # was already Band_ and already read; only the shaft body was wrong.
        box(r, 'Band_ServiceShaft', stx, stx + stw, -34, 74,
            0.0, ztop + PAR + 120.0); made += 1
        box(r, 'Band_ServiceCap', stx - 11, stx + stw + 11, -45, 85,
            ztop + PAR + 120.0, ztop + PAR + 138.0); made += 1
        for k in range(3):
            sy = -30 + 22 * k
            box(r, 'Frame_ServiceSlot%d' % k, stx + stw * 0.34,
                stx + stw * 0.66, -38, -30,
                ztop * (0.25 + 0.22 * k), ztop * (0.25 + 0.22 * k) + 60)
            made += 1

    print('%s [modern]: %d boxes, height %d uu' % (n, made, GF + F * FH + PAR))
    return GF + F * FH + PAR


# ---------------------------------------------------------------------------
# Art Deco / 1930s.
#
# Chosen because it is the OPPOSITE of the late-modern block, not a variation
# on it. Modern is horizontal - ribbon glazing behind a proud spandrel band.
# Deco is vertical: unbroken pilasters running from the base to the parapet,
# with the windows recessed into continuous channels between them, so the eye
# is pulled up rather than along. Set beside the vernacular bay rhythm the
# three read as three eras.
#
# It is also flat. Deco ornament is fluting, setbacks and stepped parapets -
# geometry, not moulding - which is exactly what cut card can do.
#
# Same depth budget as every other style: 0..60, core front at 62.
# ---------------------------------------------------------------------------
DECO_PIL_W = 76.0        # pilaster width
DECO_PROUD = 50.0        # how far it stands off the window plane
DECO_GLAZE = 40.0
DECO_FLUTE = 11.0


def build_deco(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    ztop = GF + F * FH
    bw = W / float(BAYS)
    made = 0
    # ONE jitter for the whole building. The other styles jitter each floor
    # independently, which is fine when every floor is a separate plane - but
    # a deco pilaster is a single piece running the full height, and floors
    # sliding under it would tear the shaft apart.
    # jit_yaw, not a bare uniform: build_deco precomputes its jitter into a
    # tuple rather than inline, so the width-bounded clamp has to be applied
    # HERE too. Missing this site is what left deco4 and deco6 20 uu over
    # their parcel depth after the first pass at bounding the yaw.
    jx, jy, jr = (rnd.uniform(-2.0, 2.0) * (W / 100.0),
                  rnd.uniform(-1.4, 1.4), jit_yaw(rnd, W, 0.8))

    def jitter(act):
        _setprops({
            'instance': act, 'values': json.dumps({
                'RelativeLocation': {'x': jx, 'y': jy, 'z': 0.0},
                'RelativeRotation': {'pitch': 0.0, 'yaw': jr, 'roll': 0.0}})})

    # ---- base: a heavy horizontal storefront the shaft stands on ----------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 8, x0 + W + 8, -22, D * 0.08, 0, 46); made += 1
    for b in range(BAYS + 1):
        px = min(x0 + b * bw, x0 + W - DECO_PIL_W)
        box(g, 'Wall_BasePier%d' % b, px - 8, px + DECO_PIL_W + 8,
            -DECO_PROUD - 8, 62, 46, GF - 46); made += 1
    box(g, 'Band_BaseCap', x0 - 16, x0 + W + 16, -DECO_PROUD - 16, 62,
        GF - 46, GF - 12); made += 1
    if spec.get('marquee'):
        # THE MARQUEE - a flat cantilevered canopy over the whole entrance
        # front, with a lit soffit and a banded fascia. Deco's one horizontal
        # gesture on a building that is otherwise all verticals, and the
        # thing that turns a frontage into a cinema.
        mq = float(spec['marquee'])
        box(g, 'Wall_Marquee', x0 - 14, x0 + W + 14, -mq, 10,
            GF - 122, GF - 78); made += 1
        box(g, 'Accent_MarqueeFascia', x0 - 18, x0 + W + 18, -mq - 12, -mq + 2,
            GF - 130, GF - 74); made += 1
        box(g, 'Interior_MarqueeSoffit', x0 - 8, x0 + W + 8, -mq + 8, 4,
            GF - 128, GF - 122); made += 1
        for k in range(6):
            hx = x0 + W * (k + 0.5) / 6.0
            box(g, 'Frame_MarqueeHang%d' % k, hx - 5, hx + 5, -mq * 0.5,
                -mq * 0.5 + 8, GF - 78, GF - 40); made += 1
    for b in range(BAYS):
        sx0, sx1 = x0 + b * bw + DECO_PIL_W, x0 + (b + 1) * bw
        if sx1 - sx0 < 80: continue
        box(g, 'Glass_Shop%d' % b, sx0, sx1, 34, 36, 58, GF - 52); made += 1
        box(g, 'Interior_Shop%d' % b, sx0 - 6, sx1 + 6, 48, 54, 50, GF - 48); made += 1
        for k in range(1, 3):
            mx = sx0 + (sx1 - sx0) * k / 3.0
            box(g, 'Mullion_Shop%d_%d' % (b, k), mx - 3, mx + 3, 28, 35,
                58, GF - 52); made += 1
    jitter(g)

    # ---- shaft ------------------------------------------------------------
    # STREAMLINE MODERNE is the same decade turned on its side. Deco proper
    # pulls the eye UP with unbroken pilasters; streamline drives it ALONG
    # with speed stripes, ribbon glazing and a rounded corner. Both are 1930s
    # and they look nothing like each other, which is the point of a v2.
    SL = bool(spec.get('streamline'))
    GO = bool(spec.get('giant_order'))
    BD = bool(spec.get('banded'))
    FLT = bool(spec.get('flats'))
    sh = mkactor('BLD2_%s_Shaft' % n, origin, (0.0, yaw, 0.0))
    if BD:
        # DECO VIII - BANDED. No pilasters at all. Three deco recipes were
        # reading as one building because all three were a row of fluted
        # verticals and only the crown differed; ornament level is not a
        # difference you can see from across a board. So this one drops the
        # vertical order entirely and becomes HORIZONTAL: a continuous cill
        # band and head band at every floor with punched openings between.
        # Same era, opposite axis, unmistakable at any distance.
        for f in range(max(1, F)):
            zb = GF + f * FH
            box(sh, 'Band_Course%d' % f, x0 - 12, x0 + W + 12, -26, 40,
                zb - 14, zb + 24); made += 1
        box(sh, 'Wall_EndL', x0, x0 + 34, -20, 58, GF - 12,
            ztop + PAR - 24); made += 1
        box(sh, 'Wall_EndR', x0 + W - 34, x0 + W, -20, 58, GF - 12,
            ztop + PAR - 24); made += 1
    elif GO:
        # DECO INDUSTRIAL - the giant order. A power station or pumping works
        # of the same decade: brick piers running the FULL height with one
        # enormous recessed bay between each pair, arched at the head. No
        # storeys expressed at all, which is what makes it read as industry
        # rather than as offices, and it is the cheapest facade in the
        # catalogue - a handful of very large boxes.
        pw = DECO_PIL_W * 1.35
        for b in range(BAYS + 1):
            px = min(x0 + b * bw, x0 + W - pw)
            box(sh, 'Wall_GiantPier%d' % b, px, px + pw, -DECO_PROUD * 0.55,
                60, 0.0, ztop + PAR - 20); made += 1
        for b in range(BAYS):
            rx0 = x0 + b * bw + pw
            rx1 = x0 + (b + 1) * bw
            if rx1 - rx0 < 70:
                continue
            # the ARCH, stepped: five courses narrowing to the crown, which is
            # how a card model makes a semicircle and how a bricklayer makes
            # a relieving arch anyway
            ah = min(FH * 0.9, (rx1 - rx0) * 0.5)
            for k in range(5):
                t = (k + 1) / 5.0
                ins = (rx1 - rx0) * 0.5 * (1.0 - (1.0 - t * t) ** 0.5)
                box(sh, 'Wall_Arch%d_%d' % (b, k), rx0 + ins, rx1 - ins,
                    -6, 54, ztop - 40 - ah + ah * t * 0.98,
                    ztop - 40 - ah + ah * (t + 0.22)); made += 1
            box(sh, 'Glass_Giant%d' % b, rx0 + 14, rx1 - 14, 36, 39,
                GF * 0.55, ztop - 40 - ah * 0.10); made += 1
            box(sh, 'Interior_Giant%d' % b, rx0 + 8, rx1 - 8, 48, 54,
                GF * 0.55, ztop - 40 - ah * 0.10); made += 1
            nmb = max(2, int((rx1 - rx0) / 120.0))
            for k in range(1, nmb):
                mx = rx0 + (rx1 - rx0) * k / float(nmb)
                box(sh, 'Mullion_Giant%d_%d' % (b, k), mx - 5, mx + 5, 32, 38,
                    GF * 0.55, ztop - 40 - ah * 0.10); made += 1
            for k in range(1, 5):
                tz = GF * 0.55 + (ztop - 40 - ah * 0.10 - GF * 0.55) * k / 5.0
                box(sh, 'Frame_GiantTrans%d_%d' % (b, k), rx0 + 14, rx1 - 14,
                    30, 40, tz - 5, tz + 5); made += 1
    elif SL:
        # the ROUNDED END, stepped in plan. A card model cannot bend, so the
        # curve is four returns of decreasing width - which is exactly how a
        # modelmaker fakes a radius, and it reads as one at this scale.
        rad = float(spec.get('corner_radius', 150.0))
        rl = spec.get('corner_side', 'left') == 'left'
        # EQUAL LAMINATIONS, not a sampled circle. Sampling a quarter-round at
        # even ANGLES puts nearly all the depth change in the first step: at
        # rad 150 the four returns sat at 50.8, 20.1, 4.8 and 0 uu, so the
        # steps BETWEEN them were 30.7, 15.3 and 4.8 - every one below the
        # 37.2 uu a feature needs to subtend at our hero framing to register.
        # The radius was present and unreadable, which is P5.
        #
        # A card modeller does not sample a curve; they laminate equal strips
        # and let the stack read as a radius. Three facets of rad/3 in BOTH
        # axes give steps of 50 uu - above the threshold in plan and in depth -
        # and the result is a faceted quarter-round, which is what the material
        # would actually produce. Fewer, bigger steps read as a curve; more,
        # smaller ones read as a smudge.
        NF = 3
        step = rad / NF
        for k in range(NF):
            t0 = step * k
            t1 = step * (k + 1)
            inset = step * (NF - 1 - k)
            cx_0 = (x0 - 6 + t0) if rl else (x0 + W + 6 - t1)
            cx_1 = (x0 - 6 + t1) if rl else (x0 + W + 6 - t0)
            box(sh, 'Wall_Round%d' % k, cx_0, cx_1,
                -DECO_PROUD + inset, 60, GF - 12, ztop + PAR - 26); made += 1
        # SPEED STRIPES: three continuous bands wrapping the whole frontage,
        # the accent one in the middle. Nothing interrupts them - an
        # interrupted stripe is a moulding, a continuous one is speed.
        for f in range(max(1, F)):
            zb = GF + f * FH
            for si, (dz, th, role) in enumerate(
                    ((0.30, 13.0, 'Band_'), (0.44, 9.0, 'Accent_'),
                     (0.58, 13.0, 'Band_'))):
                box(sh, '%sStripe%d_%d' % (role, f, si),
                    x0 - 10, x0 + W + 10, -DECO_PROUD - 10, 30,
                    zb + FH * dz, zb + FH * dz + th); made += 1
        made += 0
    else:
      for b in range(BAYS + 1):
        # DECO VI - FLATS uses SHALLOW piers and no fluting. A block of flats
        # of this date is not a commercial palace: the piers are a structural
        # rhythm, not an order, and the balcony is what you are meant to see.
        pilw = DECO_PIL_W * (0.55 if FLT else 1.0)
        prd = DECO_PROUD * (0.34 if FLT else 1.0)
        px = min(x0 + b * bw, x0 + W - pilw)
        box(sh, 'Wall_Pilaster%d' % b, px, px + pilw,
            -prd, 60, GF - 12, ztop + PAR - 26); made += 1
        if FLT:
            continue
        # Fluting reads as CARVED STONE, so it takes the wall colour (Band_)
        # rather than the saturated Accent_ role. Spandrels take Frame_, the
        # dark metal, which is what sat between deco windows.
        for k in (1, 2):
            fx = px + DECO_PIL_W * k / 3.0
            box(sh, 'Band_Flute%d_%d' % (b, k), fx - DECO_FLUTE/2, fx + DECO_FLUTE/2,
                -DECO_PROUD - 9, -DECO_PROUD + 4, GF - 4, ztop + PAR - 40); made += 1
      if spec.get('chevron'):
        # ZIGZAG DECO. A chevron band across each spandrel, built as a stepped
        # V from short boxes - the ornament that gives the style its other
        # name, and the only figurative thing in the whole catalogue. Cut
        # card does this beautifully and does curves badly, which is why deco
        # ornament suits this project so well.
        for f in range(max(1, F)):
            zb = GF + f * FH + FH * 0.06
            for b in range(BAYS):
                wx0 = x0 + b * bw + DECO_PIL_W
                wx1 = x0 + (b + 1) * bw
                if wx1 - wx0 < 90:
                    continue
                nz = 3
                seg = (wx1 - wx0) / float(nz * 2)
                for zi in range(nz * 2):
                    up = (zi % 2 == 0)
                    sx_ = wx0 + zi * seg
                    for st in range(3):
                        t = st / 3.0
                        zz = zb + (t if up else (1.0 - t)) * 26.0
                        box(sh, 'Accent_Chev%d_%d_%d_%d' % (f, b, zi, st),
                            sx_ + seg * t, sx_ + seg * (t + 0.40),
                            -DECO_PROUD - 6, -DECO_PROUD + 6,
                            zz, zz + 11); made += 1
    jitter(sh)

    # ---- floors -----------------------------------------------------------
    # `0 if GO else F` - the giant order draws its own full-height glazing in
    # the shaft and must NOT also get per-floor windows. This read
    # `0 if not GO else F` from the day the giant order was added, i.e. it
    # was inverted: every deco recipe EXCEPT the works ran zero floors and
    # therefore had no glazing whatsoever. The pale stripes between the
    # pilasters were the CORE showing through the gap where the windows
    # should have been. It is why deco bound only six materials, why the
    # ladders looked plain, and why three deco variants read as one building.
    for f in range(0 if GO else F):
        z0, z1 = GF + f * FH, GF + (f + 1) * FH
        a = mkactor('BLD2_%s_F%d' % (n, f), origin, (0.0, yaw, 0.0))
        if BD:
            # punched openings between the courses - squarer and further
            # apart than a deco channel, which is what an ordinary building
            # of the period actually had
            nw = max(2, int(round(W / 330.0)))
            for k in range(nw):
                wx0 = x0 + 48 + (W - 96) * k / float(nw)
                wx1 = x0 + 48 + (W - 96) * (k + 0.62) / float(nw)
                if wx1 - wx0 < 50:
                    continue
                wz0, wz1 = z0 + FH * 0.30, z1 - FH * 0.16
                box(a, 'Wall_Reveal%d_%d' % (f, k), wx0 - 12, wx1 + 12,
                    -8, 46, wz0 - 12, wz1 + 12); made += 1
                box(a, 'Glass_Punch%d_%d' % (f, k), wx0, wx1, 34, 37,
                    wz0, wz1); made += 1
                box(a, 'Interior_Punch%d_%d' % (f, k), wx0 - 4, wx1 + 4,
                    46, 52, wz0, wz1); made += 1
                mxb = (wx0 + wx1) / 2.0
                box(a, 'Mullion_Punch%d_%d' % (f, k), mxb - 4, mxb + 4,
                    30, 35, wz0, wz1); made += 1
                box(a, 'Frame_PunchCill%d_%d' % (f, k), wx0 - 16, wx1 + 16,
                    -14, 40, wz0 - 16, wz0 - 4); made += 1
            jitter(a)
            continue
        if SL:
            # RIBBON GLAZING, one run per floor, unbroken from end to end and
            # turning the rounded corner. The horizontal is the whole idea, so
            # nothing vertical is allowed to cut it except thin glazing bars.
            rad = float(spec.get('corner_radius', 150.0))
            rl = spec.get('corner_side', 'left') == 'left'
            rx0 = (x0 + rad * 0.55) if rl else (x0 + 26)
            rx1 = (x0 + W - 26) if rl else (x0 + W - rad * 0.55)
            gz0, gz1 = z0 + FH * 0.30, z0 + FH * 0.74
            box(a, 'Glass_Ribbon%d' % f, rx0, rx1, DECO_GLAZE,
                DECO_GLAZE + 3, gz0, gz1); made += 1
            box(a, 'Interior_Ribbon%d' % f, rx0, rx1, DECO_GLAZE + 10,
                DECO_GLAZE + 16, gz0, gz1); made += 1
            box(a, 'Frame_RibbonHead%d' % f, rx0 - 8, rx1 + 8,
                DECO_GLAZE - 8, DECO_GLAZE + 2, gz1 - 7, gz1 + 5); made += 1
            box(a, 'Frame_RibbonCill%d' % f, rx0 - 10, rx1 + 10,
                DECO_GLAZE - 12, DECO_GLAZE + 2, gz0 - 6, gz0 + 6); made += 1
            nb = max(3, int((rx1 - rx0) / 150.0))
            for k in range(1, nb):
                mx = rx0 + (rx1 - rx0) * k / float(nb)
                box(a, 'Mullion_Rib%d_%d' % (f, k), mx - 3, mx + 3,
                    DECO_GLAZE - 4, DECO_GLAZE + 1, gz0, gz1); made += 1
            jitter(a)
            continue
        for b in range(BAYS):
            wx0, wx1 = x0 + b * bw + DECO_PIL_W, x0 + (b + 1) * bw
            if wx1 - wx0 < 80: continue
            # spandrel panel between floors, set BACK from the pilaster face
            box(a, 'Frame_Spandrel%d' % b, wx0, wx1, 18, 30, z0, z0 + FH * 0.24); made += 1
            wz0, wz1 = z0 + FH * 0.24, z1
            box(a, 'Glass_B%d' % b, wx0 + 5, wx1 - 5, DECO_GLAZE, DECO_GLAZE + 2,
                wz0 + 5, wz1 - 5); made += 1
            box(a, 'Interior_B%d' % b, wx0, wx1, DECO_GLAZE + 10, DECO_GLAZE + 16,
                wz0, wz1); made += 1
            box(a, 'Frame_B%dL' % b, wx0, wx0 + 5, DECO_GLAZE - 6, DECO_GLAZE + 2,
                wz0, wz1); made += 1
            box(a, 'Frame_B%dR' % b, wx1 - 5, wx1, DECO_GLAZE - 6, DECO_GLAZE + 2,
                wz0, wz1); made += 1
            mx = (wx0 + wx1) / 2.0
            box(a, 'Mullion_B%dV' % b, mx - 3, mx + 3, DECO_GLAZE - 5, DECO_GLAZE + 1,
                wz0, wz1); made += 1
            if spec.get('deco_balcony') and f >= 1:
                # DECO APARTMENTS. The balcony IS the building - it was 66 uu
                # deep on every other bay and simply did not register next to
                # a 50 uu pilaster. Now it is 118 deep, runs the FULL bay, and
                # appears on every floor above the first: a continuous
                # sunbalcony, which is what the period actually built and
                # what makes this read as flats rather than as offices.
                bd_ = 100.0
                box(a, 'Band_DBalc%d_%d' % (f, b), wx0 - 10, wx1 + 10,
                    -bd_, 16, wz0 - 20, wz0 + 4); made += 1
                box(a, 'Wall_DBalcFront%d_%d' % (f, b), wx0 - 10, wx1 + 10,
                    -bd_ - 10, -bd_ + 8, wz0 + 4, wz0 + 74); made += 1
                box(a, 'Accent_DBalcRail%d_%d' % (f, b), wx0 - 15, wx1 + 15,
                    -bd_ - 17, -bd_ + 13, wz0 + 74, wz0 + 88); made += 1
                for _e in (wx0 - 10, wx1 - 4):
                    box(a, 'Wall_DBalcEnd%d_%d_%d' % (f, b, int(_e)),
                        _e, _e + 14, -bd_, 12, wz0 + 4, wz0 + 74); made += 1
        jitter(a)

    # ---- roof: STEPPED parapet, the deco silhouette -----------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    mid = BAYS // 2
    # THE CROWN IS THE TIER. Deco does not gain grandeur by setting floors
    # back - build_deco runs its pilasters unbroken from base to parapet, and
    # a setback would tear the shaft apart. It gains it at the TOP, so the
    # step is a per-tier parameter: a showroom gets a flat coping, a beacon
    # gets a ziggurat. That is the same lever the vernacular cornice pulls.
    cs = float(spec.get('crown_step', 1.9))
    for b in range(BAYS):
        px0, px1 = x0 + b * bw, x0 + (b + 1) * bw
        d = abs(b - mid)
        f = 1.0 + (cs - 1.0) * (1.0 if d == 0 else (0.55 if d == 1 else
                                                   (0.24 if d == 2 else 0.0)))
        step = PAR * f
        box(r, 'Wall_Parapet%d' % b, px0, px1, -18, 34, ztop, ztop + step); made += 1
        box(r, 'Band_Cap%d' % b, px0 - 8, px1 + 8, -28, 42,
            ztop + step, ztop + step + 16); made += 1
    box(r, 'Wall_ParapetL', x0, x0 + 26, 30, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 26, x0 + W, 30, D, ztop, ztop + PAR - 18); made += 1
    # mitred to the flank runs - see the ParapetB note above
    box(r, 'Wall_ParapetB', x0 + 26, x0 + W - 26, D - 26, D, ztop, ztop + PAR - 18); made += 1
    box(r, 'Tile_Deck', x0, x0 + W, 20, D, ztop - 8, ztop); made += 1
    # REAL PLANT, not boxes. These were `Roof_Unit` cubes - the same stand-in
    # the other styles carried until avkit arrived, and deco was simply never
    # revisited. roof_plant scales the kit to the roof and scatters it.
    made += roof_plant(r, x0, W, ztop, spec.get('roof_units', 1), rnd,
                       ymin=190.0, yspread=95.0, D=D)
    if F >= 1 and spec.get('stair_head', True):
        made += stair_head(r, x0, W, D, ztop, rnd)
    # THE ZIGGURAT. A single step per bay is a stepped parapet, not a deco
    # crown - the silhouette that makes the style is a STACK of setbacks
    # narrowing toward the centre. Built above the tallest bay so it reads as
    # one mass rising out of the parapet rather than an object placed on it.
    zt = ztop + PAR * cs + 16
    if spec.get('clock'):
        # A TERMINAL'S CLOCK TOWER. Square, set at one end, stepping in twice
        # before the clock stage - the civic timepiece that every station and
        # town hall of the period put on the skyline.
        kh = float(spec['clock'])
        kw = min(W * 0.20, 190.0)
        kx = x0 + W * float(spec.get('clock_at', 0.16))
        kx = max(x0 + 16, min(kx, x0 + W - kw - 16))
        for st in range(3):
            o = st * 13.0
            box(r, 'Wall_Clock%d' % st, kx + o, kx + kw - o, 30 + o,
                30 + kw - o, ztop + kh * st / 3.0, ztop + kh * (st + 1) / 3.0)
            made += 1
            box(r, 'Band_ClockSet%d' % st, kx + o - 10, kx + kw - o + 10,
                20 + o, 40 + kw - o, ztop + kh * (st + 1) / 3.0 - 16,
                ztop + kh * (st + 1) / 3.0); made += 1
        # the dial, on the street face
        cxm = kx + kw * 0.5
        box(r, 'Accent_Dial', cxm - 44, cxm + 44, 12, 20,
            ztop + kh * 0.70, ztop + kh * 0.92); made += 1
        box(r, 'Frame_DialRim', cxm - 52, cxm + 52, 6, 14,
            ztop + kh * 0.67, ztop + kh * 0.95); made += 1
    if spec.get('blade'):
        # THE BLADE. A cinema's vertical sign, standing clear of the parapet
        # at one end and running most of the way down the facade - the single
        # tallest thing on a low building, and the reason you can find the
        # picture house from the end of the street.
        bh = float(spec['blade'])
        bx = x0 + W * float(spec.get('blade_at', 0.14))
        bx = max(x0 + 40, min(bx, x0 + W - 40))
        box(r, 'Accent_Blade', bx - 34, bx + 34, -DECO_PROUD - 40,
            -DECO_PROUD + 6, ztop * 0.34, ztop + PAR + bh); made += 1
        box(r, 'Frame_BladeEdgeL', bx - 41, bx - 30, -DECO_PROUD - 47,
            -DECO_PROUD + 10, ztop * 0.34, ztop + PAR + bh); made += 1
        box(r, 'Frame_BladeEdgeR', bx + 30, bx + 41, -DECO_PROUD - 47,
            -DECO_PROUD + 10, ztop * 0.34, ztop + PAR + bh); made += 1
        for k in range(4):
            box(r, 'Band_BladeStep%d' % k, bx - 34 + k * 5, bx + 34 - k * 5,
                -DECO_PROUD - 44 + k * 4, -DECO_PROUD + 8,
                ztop + PAR + bh + k * 15, ztop + PAR + bh + (k + 1) * 15)
            made += 1
    if spec.get('stack'):
        # THE STACK. One tall brick chimney, square, with a corbelled cap -
        # the silhouette that says works from anywhere on the board, and the
        # thing canon slot 4 lists first in its rooftop kit.
        kh = float(spec['stack'])
        kw = min(W * 0.15, 150.0)
        kx = x0 + W * float(spec.get('stack_at', 0.80))
        kx = max(x0 + 20, min(kx, x0 + W - kw - 20))
        ky = 200.0
        box(r, 'Wall_Stack', kx, kx + kw, ky, ky + kw, 0.0, ztop + kh); made += 1
        for k in range(3):
            o = 7.0 + 6.0 * k
            box(r, 'Band_StackCap%d' % k, kx - o, kx + kw + o, ky - o,
                ky + kw + o, ztop + kh + k * 13, ztop + kh + (k + 1) * 13)
            made += 1
    if SL:
        # A streamline building does not step. It has a flat wrapped parapet
        # and, if it is showing off, one vertical fin - the single upright in
        # a building made of horizontals, which is what makes it read.
        if spec.get('fin'):
            fh = float(spec['fin'])
            fx = x0 + W * (0.16 if spec.get('corner_side', 'left') == 'left'
                           else 0.84)
            box(r, 'Accent_Fin', fx - 20, fx + 20, -DECO_PROUD - 12, 26,
                ztop, ztop + PAR + fh); made += 1
            box(r, 'Band_FinCap', fx - 27, fx + 27, -DECO_PROUD - 19, 32,
                ztop + PAR + fh, ztop + PAR + fh + 15); made += 1
            box(r, 'Frame_Flagpole', fx - 5, fx + 5, -14, -4,
                ztop + PAR + fh + 15, ztop + PAR + fh + 15 + fh * 0.55)
            made += 1
    elif cs > 1.4:
        LEVELS = [(0.58, 0.52), (0.34, 0.46)]
        if cs > 2.2:
            LEVELS.append((0.17, 0.40))
        cxm = x0 + W * 0.5
        for li, (frac, hf) in enumerate(LEVELS):
            hw = W * frac / 2.0
            hgt = PAR * hf
            box(r, 'Wall_Crown%d' % li, cxm - hw, cxm + hw, -10, 46,
                zt, zt + hgt); made += 1
            box(r, 'Band_CrownCap%d' % li, cxm - hw - 9, cxm + hw + 9,
                -19, 55, zt + hgt, zt + hgt + 13); made += 1
            # a fluted pilaster centred on each setback keeps the vertical
            # emphasis running all the way to the top
            for fx in (cxm - hw * 0.55, cxm + hw * 0.55):
                box(r, 'Band_CrownFlute%d_%d' % (li, int(fx)),
                    fx - DECO_FLUTE / 2, fx + DECO_FLUTE / 2, -14, -4,
                    zt + 6, zt + hgt - 6); made += 1
            zt += hgt + 13
    # A MAST on the tiers that have earned one - the deco beacon, and the one
    # piece of the silhouette that is not stone.
    if spec.get('mast'):
        mh = float(spec['mast'])
        mx = x0 + W * 0.5
        box(r, 'Frame_MastBase', mx - 34, mx + 34, 142, 210, zt, zt + 46); made += 1
        box(r, 'Frame_Mast', mx - 14, mx + 14, 162, 190,
            zt + 46, zt + 46 + mh); made += 1
        box(r, 'Frame_MastTip', mx - 6, mx + 6, 170, 182,
            zt + 46 + mh, zt + 46 + mh * 1.30); made += 1
    jitter(r)

    print('%s [deco]: %d boxes, height %d uu' % (n, made, ztop + PAR))
    return ztop + PAR


# ---------------------------------------------------------------------------
# Contemporary mixed-use, 2010-2025.
#
# The third era, and the one the city actually gets built out of. Our `modern`
# is 1960s: one extruded prism, a repeating grid, horizontal ribbon glazing
# behind a proud spandrel band. Deco is vertical. Vernacular is a bay rhythm.
# None of them is what a mid-rise built in the last fifteen years looks like.
#
# Contemporary is MASSING-LED rather than facade-led:
#   - stacked volumes that shift and step, not one prism
#   - two cladding systems meeting on a clean vertical line
#   - fenestration irregular WITHIN a rhythm, some bays solid
#   - recessed loggias and projecting balconies: shadow is the ornament
#   - a tall transparent ground floor behind exposed columns, deep soffit
#
# WHAT IS DELIBERATELY ABSENT. Mullion detail finer than ~6 uu, gaskets,
# spandrel texture - the things `modern` uses. At 1:87 they turn to mush, and
# the studio-director skill puts geometric reveal above all of it. Everything
# here is a real hole or a real step.
#
# Same depth budget as every other style: facade in y 0..60, core front at 62.
# ---------------------------------------------------------------------------
CONT_COL_W = 56.0        # exposed ground-floor column
CONT_SOFFIT = 44.0       # how far the ground-floor soffit projects
CONT_GLAZE = 42.0        # window plane, set back behind the cladding face


def build_contemporary(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    F, GF, FH, PAR = spec['floors'], spec['gf_h'], spec['fl_h'], spec['parapet']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    ztop = GF + F * FH
    bw = W / float(BAYS)
    made = 0

    # THE SPLIT is a vertical line, not a horizontal band. A contemporary
    # block changes cladding across the plan - a brick or fibre-cement volume
    # beside a metal one - which is what makes it read as two masses stuck
    # together rather than one wall wearing two paints.
    split_b = max(1, min(BAYS - 1, int(round(BAYS * spec.get('clad_split', 0.55)))))

    def clad(b):
        """Component prefix for bay `b`. `_B_` is picked up by panel_overrides."""
        return 'Wall_' if b < split_b else 'Wall_B_'

    # ---- ground floor: glass behind exposed columns, deep soffit ----------
    g = mkactor('BLD2_%s_GF' % n, origin, (0.0, yaw, 0.0))
    box(g, 'Wall_Plinth', x0 - 6, x0 + W + 6, -16, D * 0.08, 0, 26); made += 1
    sx0, sx1 = x0 + 40.0, x0 + W - 40.0
    # the shopfront is SET BACK, so the columns stand in front of it and the
    # soffit above throws a shadow down the glass - that recess is the whole
    # ground-floor idea and it costs four boxes
    box(g, 'Glass_Shop', sx0, sx1, 96, 99, 26, GF - 52); made += 1
    box(g, 'Interior_Shop', sx0 - 6, sx1 + 6, 108, 116, 26, GF - 48); made += 1
    for k in range(1, BAYS):
        mx = x0 + k * bw
        box(g, 'Mullion_Shop%d' % k, mx - 3, mx + 3, 90, 97, 26, GF - 52)
        made += 1
    for b in range(BAYS + 1):
        px = min(x0 + b * bw, x0 + W - CONT_COL_W)
        px = max(px, x0)
        box(g, 'Wall_Col%d' % b, px, px + CONT_COL_W, -8, 52, 0, GF - 46)
        made += 1
    # deep soffit over the whole frontage, projecting past the columns
    box(g, 'Band_Soffit', x0 - 10, x0 + W + 10, -CONT_SOFFIT, 60,
        GF - 46, GF - 10); made += 1
    box(g, 'Accent_SoffitEdge', x0 - 10, x0 + W + 10,
        -CONT_SOFFIT - 7, -CONT_SOFFIT, GF - 46, GF - 4); made += 1

    # ---- shaft: CURTAIN WALL ----------------------------------------------
    # CANON SLOT 5 (highrise), blessed for "silhouette and massing carrying
    # everything, printed-grid facades that are exactly enough at city range".
    # Its modern towers - the teal, the green, the black - are one idea: a
    # clean prism wearing an unbroken vertical grid, with a mechanical box on
    # the roof as the only crown.
    #
    # The first version of this style was punched windows between 26 uu piers
    # with loggias, balconies and stepped terraces. That is relief where the
    # canon asks for restraint, and at city range it reads as noise. The
    # owner's verdict was that it did not look modern at all, and it did not.
    #
    # MULLIONS RUN THE FULL HEIGHT as single boxes rather than per floor.
    # That is what makes a curtain wall read as one skin instead of stacked
    # storeys, and it is far cheaper too: about twenty boxes for a shaft.
    SH = float(spec.get('setback') or 0.0)
    SHF = max(0, int(spec.get('setback_floors', 0)))

    def back_at(f):
        import cores as _co
        return _co.setback_at(spec, f, F)

    if F >= 1 and spec.get('green_terrace'):
        # A PLANTED TERRACE AT EVERY FLOOR. The contemporary building that is
        # a hillside: each storey steps back from the one below and the slab
        # it leaves is planted. It is the only recipe where the greenery is
        # structural rather than decoration - take the planting away and the
        # building is just a ziggurat.
        sh = mkactor('BLD2_%s_Terr' % n, origin, (0.0, yaw, 0.0))
        stp = float(spec.get('terrace_step', 46.0))
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            bk = stp * f
            box(sh, 'Wall_TerrWall%d' % f, x0, x0 + W, bk, bk + 54,
                z0, z1); made += 1
            nb2 = max(3, int(round(W / 280.0)))
            for c in range(nb2):
                ox0 = x0 + W * c / float(nb2) + 20
                ox1 = x0 + W * (c + 1) / float(nb2) - 20
                if ox1 - ox0 < 46:
                    continue
                box(sh, 'Glass_Terr%d_%d' % (f, c), ox0, ox1, bk + 40,
                    bk + 43, z0 + FH * 0.18, z1 - FH * 0.10); made += 1
                box(sh, 'Interior_Terr%d_%d' % (f, c), ox0, ox1, bk + 50,
                    bk + 56, z0 + FH * 0.18, z1 - FH * 0.10); made += 1
            # the slab left by the step back, and the planter on it
            box(sh, 'Band_TerrSlab%d' % f, x0 - 8, x0 + W + 8, bk - stp - 8,
                bk + 8, z0 - 14, z0 + 6); made += 1
            box(sh, 'Wall_Planter%d' % f, x0 + 10, x0 + W - 10,
                bk - stp - 2, bk - stp + 30, z0 + 6, z0 + 46); made += 1
            box(sh, 'Grass_Bed%d' % f, x0 + 18, x0 + W - 18,
                bk - stp + 4, bk - stp + 26, z0 + 40, z0 + 52); made += 1
            box(sh, 'Rail_Terr%d' % f, x0 + 10, x0 + W - 10, bk - stp - 6,
                bk - stp + 2, z0 + 46, z0 + 96); made += 1
            # real planting on the wider terraces
            import avkit as _av2
            nt = max(2, int(W / 420.0))
            for t2 in range(nt):
                tx = x0 + 60 + (W - 120) * (t2 + 0.5) / nt
                # plant_s, NOT grass_tuft. A 22 uu planter bed wants a piece
                # that is tall and narrow; the grass card is 498 x 479 in plan
                # and no uniform scale makes it both visible and small enough.
                # plant_s is 39 x 39 x 101, so at 58 uu tall it occupies
                # 22 x 22 - the bed exactly. The plan budget is belt and
                # braces: a little overhang is natural for planting, a
                # 328 uu diagonal is not.
                _tk = 'plant_s'
                gsc = fit_scale(_av2.size(_tk), 58.0, 30.0)
                piece(sh, rolemap.donor_name(_av2.mat(_tk), 'TerrTuft%d_%d' % (f, t2)),
                      _av2.path(_tk), (tx, bk - stp + 14, z0 + 50),
                      (0.0, rnd.uniform(0, 360), 0.0), scale=gsc,
                      mat=_av2.mat(_tk)); made += 1

    elif F >= 1 and spec.get('brise'):
        # BRISE-SOLEIL. A continuous glass box behind a screen of vertical
        # fins standing well clear of it. The fins are the facade; the glass
        # behind them barely registers, which is the point - it is a
        # sunshade doing the architecture, and it throws a different shadow
        # every hour, which no printed grid does.
        sh = mkactor('BLD2_%s_Screen' % n, origin, (0.0, yaw, 0.0))
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            box(sh, 'Glass_Behind%d' % f, x0 + 12, x0 + W - 12, 44, 47,
                z0, z1); made += 1
            box(sh, 'Interior_Behind%d' % f, x0 + 12, x0 + W - 12, 54, 60,
                z0, z1); made += 1
            box(sh, 'Frame_SlabLine%d' % f, x0 - 4, x0 + W + 4, 30, 52,
                z0 - 6, z0 + 16); made += 1
        FIN = float(spec.get('fin_proj', 86.0))
        nf = max(6, int(round(W / float(spec.get('fin_step', 96.0)))))
        for k in range(nf + 1):
            fx = x0 + W * k / float(nf)
            fx = min(max(fx, x0), x0 + W)
            box(sh, 'Frame_Brise%d' % k, fx - 7, fx + 7, -FIN, 34,
                GF - 10, GF + F * FH + 10); made += 1
        # top and bottom rails tying the screen together
        for zz, tag in ((GF - 22.0, 'Lo'), (GF + F * FH + 10.0, 'Hi')):
            box(sh, 'Band_BriseRail%s' % tag, x0 - 10, x0 + W + 10,
                -FIN - 8, 38, zz, zz + 22); made += 1

    elif F >= 1 and spec.get('stacked'):
        # SHIFTED VOLUMES. The contemporary building that is composed rather
        # than clad: three or four blocks of floors, each one stepping the
        # opposite way from the last so the mass cantilevers over itself.
        # The whole read is the SHADOW under a cantilever, so the shifts have
        # to be big - 90 uu and up - and there must be very little else on
        # the elevation competing with them.
        sh = mkactor('BLD2_%s_Stack' % n, origin, (0.0, yaw, 0.0))
        blk = max(2, int(spec.get('stack_blocks', 3)))
        amp = float(spec.get('stack_shift', 105.0))
        per = max(1, F // blk)
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            bi = min(blk - 1, f // per)
            off = amp * (1.0 if bi % 2 else 0.0) - amp * 0.5
            first = (f == bi * per) and bi > 0
            if first:
                # the cantilever soffit - the shadow that is the whole idea
                box(sh, 'Band_Soffit%d' % f, x0 - 10, x0 + W + 10,
                    off - 16, off + 74, z0 - 20, z0 + 6); made += 1
            box(sh, 'Wall_Block%s%d' % ('B_' if bi % 2 else '', f),
                x0, x0 + W, off, off + 56, z0, z1); made += 1
            nb2 = max(3, int(round(W / 260.0)))
            for c in range(nb2):
                ox0 = x0 + W * c / float(nb2) + 22
                ox1 = x0 + W * (c + 1) / float(nb2) - 22
                if ox1 - ox0 < 46:
                    continue
                box(sh, 'Glass_Blk%d_%d' % (f, c), ox0, ox1, off + 40,
                    off + 43, z0 + FH * 0.24, z1 - FH * 0.12); made += 1
                box(sh, 'Interior_Blk%d_%d' % (f, c), ox0, ox1, off + 50,
                    off + 56, z0 + FH * 0.24, z1 - FH * 0.12); made += 1
                box(sh, 'Frame_BlkHead%d_%d' % (f, c), ox0 - 8, ox1 + 8,
                    off + 32, off + 45, z1 - FH * 0.12 - 8,
                    z1 - FH * 0.12 + 4); made += 1
        box(sh, 'Band_StackCap', x0 - 12, x0 + W + 12, -amp * 0.5 - 14,
            amp * 0.5 + 70, GF + F * FH - 14, GF + F * FH + 8); made += 1

    elif F >= 1 and spec.get('rainscreen'):
        # PANELISED METAL RAINSCREEN with syncopated openings - the third
        # contemporary building. v1 is a glass prism, v2 is an expressed
        # timber frame; this is a skin of flat panels with REVEAL JOINTS
        # between them and the windows placed in a rhythm that deliberately
        # refuses to line up into a grid.
        #
        # The irregularity is the whole point and it has to be a RULE, not a
        # random scatter: a facade that is random reads as broken, one that
        # is syncopated reads as designed. The pattern below walks by a
        # co-prime step so it never repeats within a normal building height.
        sh = mkactor('BLD2_%s_Skin' % n, origin, (0.0, yaw, 0.0))
        cols = max(4, int(round(W / 190.0)))
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            box(sh, 'Wall_Skin%d' % f, x0, x0 + W, 18, 56, z0, z1); made += 1
            # horizontal reveal joint at every floor line
            box(sh, 'Frame_JointH%d' % f, x0 - 2, x0 + W + 2, 12, 20,
                z1 - 7, z1); made += 1
            for c in range(cols):
                px0 = x0 + W * c / float(cols)
                px1 = x0 + W * (c + 1) / float(cols)
                # vertical reveal joint between panels
                box(sh, 'Frame_JointV%d_%d' % (f, c), px0 - 3, px0 + 3,
                    12, 20, z0, z1); made += 1
                # SYNCOPATION: 7 and 3 are co-prime with most column counts,
                # so the solid bays walk across the elevation instead of
                # stacking into a stripe
                # `regular` is contemporary V: same skin, no syncopation.
                # A quiet building needs the rhythm to line up, and the
                # difference between v3 and v5 is entirely this branch.
                if not spec.get('regular'):
                    if (c * 3 + f * 7) % 5 == 0:
                        continue                   # a blind panel
                wide = (not spec.get('regular')) and ((c + f) % 4 == 0)
                ox0 = px0 + 16
                ox1 = (px1 + (px1 - px0) * 0.72 - 16) if wide else (px1 - 16)
                ox1 = min(ox1, x0 + W - 10)
                if ox1 - ox0 < 44:
                    continue
                zz0 = z0 + FH * (0.20 if wide else 0.28)
                zz1 = z1 - FH * 0.14
                box(sh, 'Frame_Reveal%d_%d' % (f, c), ox0 - 9, ox1 + 9,
                    14, 52, zz0 - 9, zz1 + 9); made += 1
                box(sh, 'Glass_Panel%d_%d' % (f, c), ox0, ox1, 44, 47,
                    zz0, zz1); made += 1
                box(sh, 'Interior_Panel%d_%d' % (f, c), ox0, ox1, 54, 60,
                    zz0, zz1); made += 1
        box(sh, 'Band_SkinCap', x0 - 9, x0 + W + 9, 8, 62,
            GF + F * FH - 14, GF + F * FH + 6); made += 1

    elif F >= 1 and spec.get('timber'):
        # MASS TIMBER. The other contemporary building, and the Portland one:
        # a CLT frame with its glulam columns and beams SHOWN on the elevation
        # instead of a curtain wall hiding everything behind glass. Same
        # decade as the glass tower, opposite structural idea - one is a skin,
        # this is a frame you can count the members of.
        #
        # It is also why this ladder stops low: CLT builds six to eight
        # storeys, not seventeen, and a mass-timber tower would be a lie about
        # the material.
        sh = mkactor('BLD2_%s_Frame' % n, origin, (0.0, yaw, 0.0))
        cols = max(2, BAYS)
        cw = 30.0
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            # the glulam BEAM at every floor line, proud of the cladding
            box(sh, 'Timber_Beam%d' % f, x0 - 8, x0 + W + 8, -26, 30,
                z0 - 16, z0 + 16); made += 1
            for b in range(cols):
                bx0 = x0 + W * b / float(cols)
                bx1 = x0 + W * (b + 1) / float(cols)
                # infill panel, set back behind the frame
                box(sh, 'Wall_B_Infill%d_%d' % (f, b), bx0 + cw, bx1 - cw,
                    18, 54, z0 + 16, z1 - 16); made += 1
                ox0, ox1 = bx0 + cw + 20, bx1 - cw - 20
                if ox1 - ox0 > 50:
                    # a punched opening with a DEEP timber reveal - the
                    # shadow a frame building gets instead of a mullion grid
                    # THE REVEAL STANDS PROUD OF THE INFILL, and the head
                    # runs BETWEEN the jambs. Both were coplanar faults and
                    # together they are contemporary2's whole tail - the
                    # recipe the owner put ahead of the general pair list
                    # because excluding it the catalogue max falls 208 -> 115.
                    #
                    # PROUD: the lining sat at y 18, the same front plane as
                    # Wall_B_Infill, so a strip of timber glued around an
                    # opening was flush with the panel it is glued to. 4 uu
                    # forward gives it the edge the comment above already
                    # claims it has - the shadow a frame building gets - and
                    # removes the shared plane.
                    #
                    # BETWEEN: the head ran ox0-14..ox1+14, which is exactly
                    # the jambs' outer faces, so it double-covered both of
                    # them. Same mechanism as the parapet ring and the coping
                    # ring before it: four strips cut to length and butted,
                    # not lapped at the corner. The jambs already span the
                    # head's full height, so the union is unchanged.
                    box(sh, 'Timber_RevL%d_%d' % (f, b), ox0 - 14, ox0,
                        14, 62, z0 + 34, z1 - 34); made += 1
                    box(sh, 'Timber_RevR%d_%d' % (f, b), ox1, ox1 + 14,
                        14, 62, z0 + 34, z1 - 34); made += 1
                    box(sh, 'Timber_RevHead%d_%d' % (f, b), ox0, ox1,
                        14, 62, z1 - 46, z1 - 34); made += 1
                    box(sh, 'Glass_Punch%d_%d' % (f, b), ox0, ox1, 56, 59,
                        z0 + 34, z1 - 34); made += 1
                    box(sh, 'Interior_Punch%d_%d' % (f, b), ox0, ox1, 64, 70,
                        z0 + 34, z1 - 34); made += 1
                    mx = (ox0 + ox1) / 2.0
                    box(sh, 'Mullion_Punch%d_%d' % (f, b), mx - 4, mx + 4,
                        52, 57, z0 + 34, z1 - 34); made += 1
                # SLAT BALCONY on a staggered share of the bays - timber
                # balustrades read as slats at this scale, which no metal
                # rail does
                if f >= 1 and ((b + f) % 3 == 1):
                    box(sh, 'Timber_BalcSlab%d_%d' % (f, b), bx0 + 6, bx1 - 6,
                        -104, 8, z0 - 2, z0 + 14); made += 1
                    for sk in range(5):
                        sz = z0 + 18 + sk * 11
                        box(sh, 'Timber_Slat%d_%d_%d' % (f, b, sk),
                            bx0 + 6, bx1 - 6, -104, -96, sz, sz + 6); made += 1
                    for ex in (bx0 + 6, bx1 - 12):
                        box(sh, 'Timber_BalcEnd%d_%d_%d' % (f, b, int(ex)),
                            ex, ex + 6, -104, 8, z0 + 14, z0 + 76); made += 1
        # the glulam COLUMNS, full height, in front of everything
        for b in range(cols + 1):
            bx = x0 + W * b / float(cols)
            bx = min(max(bx, x0), x0 + W)
            box(sh, 'Timber_Col%d' % b, bx - cw / 2, bx + cw / 2, -30, 34,
                GF - 20, GF + F * FH + 18); made += 1
        box(sh, 'Band_FrameCap', x0 - 12, x0 + W + 12, -36, 40,
            GF + F * FH + 18, GF + F * FH + 34); made += 1

    elif F >= 1:
        # THE EXPRESSED CORE - one solid clad strip beside the glass, the
        # service core shown on the elevation. It gives the second cladding a
        # job and it matches the canon's solid towers standing beside its
        # glass ones, without breaking the prism.
        core_w = bw * float(spec.get('core_bays', 1))
        core_left = spec.get('core_side', 'right') == 'left'
        cx0 = x0 if core_left else (x0 + W - core_w)
        cx1 = cx0 + core_w
        gx0 = cx1 if core_left else x0
        gx1 = (x0 + W) if core_left else cx0

        sh = mkactor('BLD2_%s_Shaft' % n, origin, (0.0, yaw, 0.0))
        for f in range(F):
            z0, z1 = GF + f * FH, GF + (f + 1) * FH
            bk = back_at(f)
            box(sh, 'Glass_Curtain%d' % f, gx0 + 8, gx1 - 8,
                bk + CONT_GLAZE, bk + CONT_GLAZE + 3, z0, z1); made += 1
            box(sh, 'Interior_Curtain%d' % f, gx0 + 8, gx1 - 8,
                bk + CONT_GLAZE + 9, bk + CONT_GLAZE + 15, z0, z1); made += 1
            # a SLIM spandrel at each floor line, set BACK behind the mullion
            # face so the vertical always wins over the horizontal
            box(sh, 'Frame_Spandrel%d' % f, gx0 + 8, gx1 - 8,
                bk + CONT_GLAZE - 4, bk + CONT_GLAZE + 4,
                z0 - 5, z0 + 20); made += 1
            box(sh, 'Wall_B_Core%d' % f, cx0, cx1, bk, bk + 54, z0, z1); made += 1
            box(sh, 'Glass_CoreSlot%d' % f, cx0 + core_w * 0.36,
                cx0 + core_w * 0.64, bk + 40, bk + 43,
                z0 + FH * 0.30, z1 - FH * 0.22); made += 1

        bands = []
        if SHF:
            bands.append((0, F - SHF))
            for k in range(SHF):
                bands.append((F - SHF + k, F - SHF + k + 1))
        else:
            bands = [(0, F)]
        MULL = float(spec.get('mullion_step', 88.0))
        for bi, (f0, f1) in enumerate(bands):
            if f1 <= f0:
                continue
            bk = back_at(f0)
            zA, zB = GF + f0 * FH, GF + f1 * FH
            nm = max(2, int(round((gx1 - gx0) / MULL)))
            for k in range(nm + 1):
                mx = gx0 + (gx1 - gx0) * k / float(nm)
                mw = 11.0 if (k == 0 or k == nm) else 7.0
                box(sh, 'Mullion_V%d_%d' % (bi, k), mx - mw / 2, mx + mw / 2,
                    bk + CONT_GLAZE - 13, bk + CONT_GLAZE + 2, zA, zB)
                made += 1
            for cxp, tag in ((gx0, 'L'), (gx1, 'R')):
                # STOPS UNDER THE CAP, not level with it. The post used to
                # run to zB and the cap covered its top 12 uu, so both tops
                # sat on one plane - the white stripe meeting the brick
                # corner the owner reported on 29 Aug. 78 visible pairs.
                #
                # THIS IS NOT A SILHOUETTE NO-OP, and I first wrote here that
                # it was. The claim was that the cap is wider than the post in
                # both axes so the removed 12 uu was already inside it. In y,
                # yes. In X IT IS NOT: the cap spans 72..656.8 and the posts
                # sit at 65..91 and 637.8..663.8, so the cap is 7 uu SHORT of
                # each post's outer face. Shortening the post therefore cuts a
                # 7 x 12 uu notch at each end of every band - measured at 168
                # cells per band in front elevation, on all five test models.
                #
                # Kept because it was LOOKED AT: at inspection range the notch
                # reads as a stepped capital where the band dies into the
                # corner, which is a detail a card builder would cut, not a
                # fault. If it ever reads wrong, the no-op alternative is to
                # widen the cap to the posts' outer faces instead of
                # shortening the posts - that also clears the fight and gains
                # rather than loses material.
                box(sh, 'Wall_Corner%d%s' % (bi, tag), cxp - 13, cxp + 13,
                    bk - 4, bk + 58, zA, zB - 12); made += 1
            box(sh, 'Band_BandCap%d' % bi, gx0 - 6, gx1 + 6,
                bk - 8, bk + 60, zB - 12, zB); made += 1

        for f in range(1, F):
            bk, pk = back_at(f), back_at(f - 1)
            if bk > pk:
                a2 = mkactor('BLD2_%s_T%d' % (n, f), origin, (0.0, yaw, 0.0))
                box(a2, 'Band_TerraceSlab%d' % f, x0, x0 + W, pk - 6, bk + 16,
                    GF + f * FH - 12, GF + f * FH + 4); made += 1
                box(a2, 'Rail_Terrace%d' % f, x0 + 10, x0 + W - 10,
                    pk - 2, pk + 4, GF + f * FH + 4, GF + f * FH + 54); made += 1


    # ---- roof -------------------------------------------------------------
    r = mkactor('BLD2_%s_Roof' % n, origin, (0.0, yaw, 0.0))
    import cores as _co
    ty = _co.setback_top(spec, F)
    box(r, 'Wall_ParapetF', x0, x0 + W, ty - 4, ty + 26, ztop, ztop + PAR); made += 1
    box(r, 'Band_Coping', x0 - 7, x0 + W + 7, ty - 12, ty + 34,
        ztop + PAR, ztop + PAR + 12); made += 1
    box(r, 'Wall_ParapetL', x0, x0 + 24, ty + 26, D, ztop, ztop + PAR - 16); made += 1
    box(r, 'Wall_ParapetR', x0 + W - 24, x0 + W, ty + 26, D, ztop, ztop + PAR - 16); made += 1
    # mitred to the flank runs - see the ParapetB note above
    box(r, 'Wall_ParapetB', x0 + 24, x0 + W - 24, D - 24, D, ztop, ztop + PAR - 16); made += 1
    box(r, 'Tile_Deck', x0, x0 + W, ty + 20, D, ztop - 8, ztop); made += 1
    made += roof_plant(r, x0, W, ztop, spec.get('roof_units', 1), rnd,
                       ymin=ty + 190.0, yspread=95.0, D=D)
    if F >= 1 and spec.get('stair_head', True):
        made += stair_head(r, x0, W, D, ztop, rnd)

    # THE MECHANICAL PENTHOUSE. Canon slot 5's towers all carry one, and it is
    # the ONLY crown a modern prism gets - no setback, no ornament, no mast.
    # Smaller footprint than the roof, offset rather than centred, clad in the
    # core material so it reads as the shaft arriving at the top.
    mp = spec.get('mech')
    if mp:
        mw = W * float(mp.get('w', 0.34))
        md = min(D * 0.42, 280.0)
        mh = float(mp.get('h', 150.0))
        mx = x0 + W * float(mp.get('at', 0.30))
        mx = max(x0 + 20, min(mx, x0 + W - mw - 20))
        my = ty + 120.0
        box(r, 'Wall_B_Mech', mx, mx + mw, my, my + md,
            ztop + PAR - 10, ztop + PAR - 10 + mh); made += 1
        box(r, 'Band_MechCap', mx - 9, mx + mw + 9, my - 9, my + md + 9,
            ztop + PAR - 10 + mh, ztop + PAR - 10 + mh + 13); made += 1
        # louvre slots, the one piece of detail on it
        for k in range(3):
            ly = my + md * (0.22 + 0.26 * k)
            box(r, 'Frame_MechLouvre%d' % k, mx - 3, mx + 3, ly, ly + md * 0.16,
                ztop + PAR - 10 + mh * 0.30, ztop + PAR - 10 + mh * 0.78)
            made += 1

    print('%s [contemporary]: %d boxes, height %d uu' % (n, made, ztop + PAR))
    return ztop + PAR


def build_house(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A house, which is not a small office block.

    Three things make it read as residential rather than as a shrunk commercial
    block, and none of them is the massing. A SETBACK, so the street line is
    garden and fence instead of shopfront. A PITCHED roof, stepped rather than
    sloped because box() is axis-aligned and a card model folds anyway. And the
    GAP: these are detached, so the lot is wider than the house and the space
    between them is the point.

    Detached also means it is self-contained - all four walls are built here, so
    it needs no core behind it and no flank elevation added later.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    GF, FH = spec['gf_h'], spec['fl_h']
    F = spec['floors']                     # storeys ABOVE the ground floor
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))

    # VARIANTS. Five houses from one generator were five colours of the same
    # house, which is the thing "buildings are parameter sets" is supposed to
    # avoid. These are the differences that actually read from the street: what
    # the roof does at the top, what the front door does at the bottom, and
    # whether the elevation is flat or broken.
    roof_kind = spec.get('roof', rnd.choice(('gable', 'crossgable', 'gable')))
    entry = spec.get('entry', rnd.choice(('porch', 'stoop')))
    dormers = spec.get('dormers', rnd.choice((0, 0, 2)))
    bay = spec.get('bay', rnd.random() < 0.45)
    garage = spec.get('garage', rnd.random() < 0.4)

    GARDEN = 250.0 + rnd.uniform(-20, 20)  # street line to the front wall
    SIDE = 100.0                           # gap to the lot edge, each side
    hx0, hx1 = x0 + SIDE, x0 + W - SIDE
    hy0 = GARDEN
    hy1 = min(D - 60.0, GARDEN + 430.0)
    HW, HD = hx1 - hx0, hy1 - hy0
    eaves = GF + F*FH
    made = 0

    a = mkactor('BLD2_%s_H' % n, origin, (0.0, yaw, 0.0))
    # THE PLOT IS NOT THE BUILDING. Gardens, fences, drives and sheds went onto
    # the building actor, so check_block - which takes a building's extent from
    # all of its components - measured the fences and reported eight overlaps
    # between houses that do not touch. Side fences on a shared boundary SHOULD
    # meet. Separate actor, exactly as an open lot already gets ZONE_.
    pl = mkactor('PLOT_%s' % n, origin, (0.0, yaw, 0.0))

    # ---- gardens, fences, front walk, drive ---------------------------------
    # which side the drive takes is decided first, because the shed goes in the
    # back corner the drive does not use
    # The PLOT has its own random stream. Drawing it from the building's
    # stream meant a tier change shifted every later draw, so upgrading a house
    # moved its drive and swapped its swing set for a putting green - the
    # opposite of the identity the recipe tiers exist to preserve.
    grnd = random.Random(spec.get('seed', 0)*7 + 13)
    dside = 1 if grnd.random() < 0.5 else -1
    dx = x0 + (W - 150.0) if dside > 0 else x0 + 26.0
    box(pl, 'Grass_Yard', x0 + 12, x0 + W - 12, 8, GARDEN - 4, 0, 10); made += 1
    # THE BACK GARDEN. A house with nothing behind it is a facade with a roof;
    # from any camera that is not square to the street the rear reads, and
    # these had bare walls and bare ground.
    by0, by1 = hy1 + 10.0, D - 12.0
    if by1 - by0 > 200.0:
        box(pl, 'Grass_Back', x0 + 12, x0 + W - 12, by0, by1, 0, 10); made += 1
        box(pl, 'Ground_Patio', hx0 + 30, hx1 - 30, by0, by0 + 130, 0, 13); made += 1
        for sgn, fx in ((-1.0, x0 + 8), (1.0, x0 + W - 8)):
            box(pl, 'Kerbing_SideFence%d' % (int(sgn) + 1), fx - 7, fx + 7,
                GARDEN - 20, by1, 8, 78); made += 1
        box(pl, 'Kerbing_BackFence', x0 + 8, x0 + W - 8, by1 - 10, by1, 8, 84)
        made += 2
        # THINGS PEOPLE PUT IN A GARDEN, laid out so they do not stand in
        # each other. The first version put the washing line at the garden's
        # centre and the bed along a fence and let them overlap - the frames
        # showed a line running into a raised bed - and the bed was on
        # MI_grass, so it was a raised bed of grass.
        #
        # The garden is divided ONCE, into three bands, and each thing gets
        # one. Bed against the fence the drive does not use, lawn feature in
        # the middle, drying area at the back.
        bed_x0 = x0 + 30.0 if dside > 0 else x0 + W - 250.0
        bed_x1 = bed_x0 + 220.0
        lawn_x0 = bed_x1 + 60.0 if dside > 0 else x0 + 30.0
        lawn_x1 = x0 + W - 30.0 if dside > 0 else bed_x0 - 60.0
        lcx = (lawn_x0 + lawn_x1)/2.0

        box(pl, 'Kerbing_Bed', bed_x0, bed_x1, by0 + 60, by1 - 300, 10, 46)
        box(pl, 'Bloom_Bed', bed_x0 + 14, bed_x1 - 14, by0 + 74, by1 - 314, 10, 58)
        made += 2

        if grnd.random() < 0.62:
            # a swing set: two A-frames and a beam, not a pile of uprights
            sw = lcx
            legs = 172.0
            for sgn2 in (-1.0, 1.0):
                for lean in (-1.0, 1.0):
                    slab(pl, 'Frame_SwingLeg%d%d' % (int(sgn2) + 1, int(lean) + 1),
                         sw + sgn2*95.0, by0 + 190.0 + lean*38.0, legs/2.0,
                         14.0, 16.0, legs + 26.0, roll=lean*13.0)
                    made += 1
            box(pl, 'Frame_SwingBeam', sw - 118, sw + 118,
                by0 + 182, by0 + 198, legs, legs + 16)
            for k in (-1, 1):
                sx2 = sw + k*54.0
                for cs in (-1, 1):
                    box(pl, 'Frame_SwingChain%d%d' % (k + 1, cs + 1),
                        sx2 + cs*22 - 3, sx2 + cs*22 + 3,
                        by0 + 187, by0 + 193, 62, legs)
                box(pl, 'Frame_SwingSeat%d' % (k + 1), sx2 - 30, sx2 + 30,
                    by0 + 180, by0 + 200, 54, 62)
            made += 7
        else:
            box(pl, 'Grass_Putt', lcx - 150, lcx + 150, by0 + 120, by0 + 360, 10, 16)
            box(pl, 'Frame_PuttFlag', lcx + 86, lcx + 94, by0 + 234, by0 + 242, 16, 120)
            box(pl, 'Accent_PuttFlag', lcx + 94, lcx + 150, by0 + 236, by0 + 240, 96, 120)
            made += 3

        # the drying area is at the BACK, clear of both
        for sgn2 in (-1, 1):
            px2 = lcx + sgn2*(min(180.0, (lawn_x1 - lawn_x0)/2.0 - 30.0))
            box(pl, 'Frame_LinePost%d' % (sgn2 + 1), px2 - 7, px2 + 7,
                by1 - 200, by1 - 186, 10, 170); made += 1
        box(pl, 'Frame_Line', lcx - 180, lcx + 180, by1 - 195, by1 - 191, 160, 164)
        made += 1

        # a shed in the corner the drive does not use
        sx_ = lawn_x1 - 200.0 if dside > 0 else lawn_x0 + 10.0
        box(pl, 'Wall_Shed', sx_, sx_ + 190, by1 - 190, by1 - 24, 0, 150); made += 1
        box(pl, 'Tile_Shed', sx_ - 12, sx_ + 202, by1 - 202, by1 - 12, 150, 166)
        box(pl, 'Frame_ShedDoor', sx_ + 40, sx_ + 150, by1 - 196, by1 - 188, 8, 128)
        made += 2
        for k in range(3):
            px = x0 + 120.0 + (W - 240.0)*k/2.0
            box(pl, 'Frame_BackPost%d' % k, px - 6, px + 6, by1 - 12, by1 + 2,
                8, 96); made += 1
    box(pl, 'Kerbing_FenceL', x0 + 8, x0 + W*0.34, 0, 10, 10, 76); made += 1
    box(pl, 'Kerbing_FenceR', x0 + W*0.66, x0 + W - 8, 0, 10, 10, 76); made += 1
    for k in range(4):
        px = x0 + 26 + (W - 52)*k/3.0
        box(pl, 'Frame_FencePost%d' % k, px - 7, px + 7, -2, 12, 10, 92); made += 1

    # the front walk is a PATH - a centreline and a width - so the porch and the
    # gate are derived from it rather than from three more hand-typed numbers
    cx = (hx0 + hx1)/2.0
    walk = paths.Path((cx, 0.0), (cx, GARDEN + 6.0), 96.0, 'walk')
    wr = walk.rect()
    box(pl, 'Ground_Walk', wr[0], wr[2], wr[1], wr[3], 0, 12); made += 1
    box(pl, 'Ground_Drive', dx, dx + 124, 0, GARDEN + 40, 0, 11); made += 1

    # ---- body ---------------------------------------------------------------
    box(a, 'Wall_Plinth', hx0 - 10, hx1 + 10, hy0 - 10, hy1 + 10, 0, 26); made += 1
    box(a, 'Wall_Body', hx0, hx1, hy0, hy1, 26, eaves); made += 1

    # ---- the way the front door meets the ground ----------------------------
    if entry == 'porch':
        pw = 210.0
        box(a, 'Roof_Porch', cx - pw/2 - 20, cx + pw/2 + 20, hy0 - 96, hy0 + 6,
            GF - 34, GF - 16); made += 1
        for sgn in (-1, 1):
            px = cx + sgn*(pw/2 - 8)
            box(a, 'Frame_PorchPost%d' % (sgn + 1), px - 9, px + 9,
                hy0 - 88, hy0 - 70, 26, GF - 34); made += 1
        box(a, 'Ground_PorchDeck', cx - pw/2 - 14, cx + pw/2 + 14,
            hy0 - 92, hy0, 14, 26); made += 1
    else:
        # a stoop: three steps up to the door and a small hood over it
        for i in range(3):
            box(a, 'Ground_Stoop%d' % i, cx - 78 + i*6, cx + 78 - i*6,
                hy0 - 72 + i*22, hy0, 0, 10 + i*8); made += 1
        box(a, 'Roof_Hood', cx - 76, cx + 76, hy0 - 54, hy0 + 4,
            26 + 158, 26 + 178); made += 1
    box(a, 'Frame_Door', cx - 44, cx + 44, hy0 - 4, hy0 + 5, 26, 26 + 150); made += 1
    box(a, 'Interior_Hall', cx - 38, cx + 38, hy0 + 5, hy0 + 12, 30, 26 + 140); made += 1

    # ---- windows: front, and both flanks, because a house is seen from three
    # sides at once and a blank gable is what gave the first block away -------
    # front elevation: door bay in the middle, windows either side
    for b in range(BAYS):
        bx = hx0 + 40 + (HW - 80)*(b + 0.5)/BAYS
        if abs(bx - cx) > 70:
            made += window(a, 'GF%d' % b, 'y', hy0, -1.0, bx - 62, bx + 62,
                           26 + 62, GF - 34, bars=(1, 1))
        # A SINGLE-STOREY COTTAGE had two street windows and nothing else,
        # because the upper-floor loop does not run when floors is 0. The gable
        # above the eaves is elevation too: it takes a window.
        if F == 0 and abs(bx - cx) <= 70 and GF - 34 - (26 + 168) >= 44:
            # only when there is real wall between the door hood and the
            # eaves - on a low cabin (gf_h ~200) this range is INVERTED and
            # abs() in box() was emitting a 28 uu sliver over the door
            made += window(a, 'GFd', 'y', hy0, -1.0, bx - 46, bx + 46,
                           26 + 168, GF - 34, bars=(1, 0))
        for f in range(F):
            z0 = GF + f*FH + 44
            made += window(a, 'U%d_%d' % (f, b), 'y', hy0, -1.0,
                           bx - 56, bx + 56, z0, z0 + FH - 96, bars=(1, 1))
    # flanks
    for sgn, side in ((-1.0, hx0), (1.0, hx1)):
        for k in range(2):
            wy = hy0 + HD*(0.3 + 0.4*k)
            # F==0: eaves == GF, so the upper-floor range floats above the
            # roofline - drop the flank windows into the ground floor instead
            wz = (GF + 44, GF + FH - 52) if F else (26 + 62, GF - 34)
            made += window(a, 'S%d_%d' % (int(sgn) + 1, k), 'x', side, sgn,
                           wy - 58, wy + 58, wz[0], wz[1], bars=(1, 0))

    # ---- rear elevation ------------------------------------------------------
    for b in range(2):
        rx = hx0 + 40 + (HW - 80)*(b + 0.5)/2.0
        made += window(a, 'R0_%d' % b, 'y', hy1, 1.0, rx - 58, rx + 58,
                       26 + 66, GF - 40, bars=(1, 1))
        for f in range(F):
            z0 = GF + f*FH + 44
            made += window(a, 'R%d_%d' % (f + 1, b), 'y', hy1, 1.0,
                           rx - 52, rx + 52, z0, z0 + FH - 96, bars=(1, 1))
    bd = (hx0 + hx1)/2.0
    box(a, 'Frame_BackDoor', bd - 40, bd + 40, hy1 - 5, hy1 + 4, 26, 26 + 146)
    box(a, 'Roof_BackHood', bd - 62, bd + 62, hy1 - 4, hy1 + 54,
        26 + 150, 26 + 166)
    made += 2

    # ---- trim: the small parts that separate a model from a massing study ---
    # A fascia is a BAND round the eaves. This was a solid box spanning the
    # whole plan at eaves height - a flat slab under the pitched roof, which is
    # what made the roofs read as inverted and as "a flat roof laid on top of a
    # pitched one". Four thin bands, not a lid.
    for tag, fx0, fy0, fx1, fy1 in (
            ('F', hx0 - 30, hy0 - 30, hx1 + 30, hy0 - 12),
            ('B', hx0 - 30, hy1 + 12, hx1 + 30, hy1 + 30),
            ('L', hx0 - 30, hy0 - 30, hx0 - 12, hy1 + 30),
            ('R', hx1 + 12, hy0 - 30, hx1 + 30, hy1 + 30)):
        box(a, 'Frame_Fascia%s' % tag, fx0, fx1, fy0, fy1,
            eaves - 16, eaves + 4); made += 1
    box(a, 'Frame_Gutter', hx0 - 34, hx1 + 34, hy0 - 34, hy0 - 22,
        eaves - 14, eaves - 2); made += 1
    box(a, 'Frame_Downpipe', hx1 - 22, hx1 - 8, hy0 - 20, hy0 - 6,
        26, eaves - 12); made += 1
    for cxn, cx_ in (('L', hx0), ('R', hx1)):
        box(a, 'Frame_Corner%sF' % cxn, cx_ - 9, cx_ + 9, hy0 - 6, hy0 + 4,
            26, eaves); made += 1
        box(a, 'Frame_Corner%sB' % cxn, cx_ - 9, cx_ + 9, hy1 - 4, hy1 + 6,
            26, eaves); made += 1
    box(a, 'Frame_Threshold', cx - 52, cx + 52, hy0 - 16, hy0 + 4, 20, 30); made += 1
    box(a, 'Glass_Fanlight', cx - 36, cx + 36, hy0 + 2, hy0 + 6,
        26 + 152, 26 + 172); made += 1
    made += 4

    # ---- a bay window, which is what breaks a flat cottage elevation --------
    if bay:
        bside = -1 if entry == 'porch' else 1
        bx = cx + bside*(HW*0.28)
        box(a, 'Wall_Bay', bx - 96, bx + 96, hy0 - 86, hy0 + 6, 20, GF - 30); made += 1
        box(a, 'Glass_Bay', bx - 82, bx + 82, hy0 - 90, hy0 - 84, 26 + 60, GF - 52); made += 1
        for sgn in (-1, 1):
            box(a, 'Glass_BayS%d' % (sgn + 1), bx + sgn*90, bx + sgn*96,
                hy0 - 80, hy0 - 10, 26 + 60, GF - 52); made += 1
        box(a, 'Roof_Bay', bx - 104, bx + 104, hy0 - 94, hy0 + 6,
            GF - 30, GF - 14); made += 1
        made += 4

    # ---- a garage, set back from the house front so it does not lead --------
    if garage:
        gw = 190.0
        gx = dx + 62.0 - gw/2.0
        # CLAMP to the lot. The garage roof oversails 16 uu either side, and
        # unclamped that put the extended cottage at 842 uu inside an 820 uu
        # parcel - 22 uu into the neighbour it would be placed beside. In the
        # city the overhang landed in a garden and nothing complained; baked
        # into a catalogue mesh it is a parcel that does not fit its own
        # declared width. GATE-05 caught it on the gate's first working run.
        OS = 16.0
        gx = max(x0 + OS, min(gx, x0 + W - gw - OS))
        box(pl, 'Wall_Garage', gx, gx + gw, hy0 + 40, hy0 + 230, 0, 190); made += 1
        box(pl, 'Frame_GarageDoor', gx + 14, gx + gw - 14, hy0 + 34, hy0 + 42,
            8, 168); made += 1
        box(pl, 'Roof_Garage', gx - 16, gx + gw + 16, hy0 + 26, hy0 + 240,
            190, 210); made += 1

    # ---- pitched roof, actually pitched --------------------------------------
    # Two rotated slabs meeting at a ridge. The HIP that used to live here was
    # wrong: a hip's main slopes are trapezoids and its ends are triangles, and
    # a box is neither, so it came out as four full-size slabs overlapping in
    # the middle - which is the "flat roof laid on top of a pitched roof" in
    # the frames. Variety comes from which way the RIDGE runs instead, which is
    # a real difference a street reads: gable to the side, or gable to the
    # street.
    OV = 34.0
    rise = 168.0 + rnd.uniform(-16, 16)
    ey0, ey1 = hy0 - OV, hy1 + OV
    ex0, ex1 = hx0 - OV, hx1 + OV
    street_gable = (roof_kind == 'crossgable')

    if street_gable:
        ridge = (ex0 + ex1)/2.0
        run = ridge - ex0
        ang = math.degrees(math.atan2(rise, run))
        for sgn in (-1.0, 1.0):
            slab(a, 'Tile_Slope%d' % (int(sgn) + 1), ridge + sgn*run/2.0,
                 (ey0 + ey1)/2.0, eaves + rise/2.0,
                 # sign mirrors the roll used for a ridge along X; the first
                 # version had it the other way and the roof came out as a
                 # valley - two slopes meeting in a V instead of at a ridge
                 math.hypot(run, rise), ey1 - ey0, 18.0, pitch=-sgn*ang)
            made += 1
        for sgn, ey_ in ((-1.0, hy0), (1.0, hy1)):
            for i in range(7):
                t0, t1 = i/7.0, (i + 1)/7.0
                box(a, 'Wall_Gable%d_%d' % (int(sgn) + 1, i),
                    ex0 + run*t1, ex1 - run*t1, ey_ - 10, ey_ + 10,
                    eaves + rise*t0, eaves + rise*t1)
                made += 1
    else:
        ridge = (ey0 + ey1)/2.0
        run = ridge - ey0
        ang = math.degrees(math.atan2(rise, run))
        for sgn, tag in ((-1.0, 'F'), (1.0, 'B')):
            slab(a, 'Tile_Slope%s' % tag, (hx0 + hx1)/2.0, ridge + sgn*run/2.0,
                 eaves + rise/2.0, (hx1 - hx0) + 2*OV,
                 # MEASURED, not reasoned: a positive roll takes +Y DOWN, so
                 # the slope whose +Y end is the ridge needs a NEGATIVE roll.
                 # This was -sgn*ang and every side-gabled roof was a valley.
                 math.hypot(run, rise), 18.0, roll=sgn*ang)
            made += 1
        for sgn, hx_ in ((-1.0, hx0), (1.0, hx1)):
            for i in range(7):
                t0, t1 = i/7.0, (i + 1)/7.0
                # the step's top must land ON the slope, not above it: take
                # the NEXT station's footprint, or each corner pokes through
                # and the ridge shows as a dashed line
                box(a, 'Wall_Gable%d_%d' % (int(sgn) + 1, i),
                    hx_ - 10, hx_ + 10, ey0 + run*t1, ey1 - run*t1,
                    eaves + rise*t0, eaves + rise*t1)
                made += 1

    # Dormers: SHED dormers, with their own sloped cap. The old ones were a
    # box with a flat plate on top, sitting on a pitched slope - which is
    # exactly the "flat roof on a pitched roof" that reads as broken. Only on a
    # side-gabled roof: a street-facing gable has no front slope to sit in.
    if dormers and not street_gable:
        dh = rise*0.52
        dd = run*0.46
        dang = math.degrees(math.atan2(dh*0.34, dd))
        for d in range(dormers):
            dxc = hx0 + HW*(0.3 + 0.4*d)
            dz = eaves + rise*0.10
            box(a, 'Wall_DormerC%dL' % d, dxc - 66, dxc - 52,
                hy0 - 8, hy0 - 8 + dd, dz, dz + dh); made += 1
            box(a, 'Wall_DormerC%dR' % d, dxc + 52, dxc + 66,
                hy0 - 8, hy0 - 8 + dd, dz, dz + dh); made += 1
            box(a, 'Wall_DormerF%d' % d, dxc - 66, dxc + 66,
                hy0 - 12, hy0 - 4, dz, dz + dh); made += 1
            # the dormer's FRONT face is hy0-12 (Wall_DormerF spans -12..-4);
            # passing its mid-plane put the glass inside the roof
            made += window(a, 'Dm%d' % d, 'y', hy0 - 12, -1.0,
                           dxc - 48, dxc + 48, dz + 26, dz + dh - 22, bars=(1, 0))
            slab(a, 'Tile_Dormer%d' % d, dxc, hy0 - 14 + dd/2.0,
                 dz + dh + dh*0.17, 148.0, math.hypot(dd, dh*0.34), 12.0,
                 roll=-dang)
            made += 1

    box(a, 'Wall_Chimney', hx1 - 120, hx1 - 62, hy0 + HD*0.62, hy0 + HD*0.62 + 58,
        eaves, eaves + rise + 86); made += 1

    print('%s [house %s/%s%s%s%s]: %d boxes'
          % (n, roof_kind, entry, ' bay' if bay else '',
             ' %ddormer' % dormers if dormers else '',
             ' garage' if garage else '', made))
    return made


def build_walkup(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A small walk-up apartment block: the step between a house and a block.

    It is not a short office block and it is not a wide house. What makes it
    read as apartments is REPETITION with a single front door - the same window
    and the same balcony stacked three high, one stoop on the street, and a
    forecourt too small to be a garden. Setback is shallower than a house's,
    because a walk-up sits closer to the pavement than a cottage does.

    Detached like the houses, so it builds all four of its own walls.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    GF, FH, PAR = spec['gf_h'], spec['fl_h'], spec['parapet']
    F = spec['floors']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))

    FORE = 130.0 + rnd.uniform(-14, 14)
    SIDE = 70.0
    hx0, hx1 = x0 + SIDE, x0 + W - SIDE
    hy0 = FORE
    hy1 = min(D - 60.0, FORE + 520.0)
    HW = hx1 - hx0
    top = GF + F*FH
    made = 0

    a = mkactor('BLD2_%s_A' % n, origin, (0.0, yaw, 0.0))
    pl = mkactor('PLOT_%s' % n, origin, (0.0, yaw, 0.0))
    cx = (hx0 + hx1)/2.0

    # ---- forecourt: a low wall and a path, not a garden ---------------------
    box(pl, 'Ground_Fore', x0 + 10, x0 + W - 10, 8, FORE - 4, 0, 12); made += 1
    box(pl, 'Kerbing_Wall', x0 + 8, x0 + W - 8, 0, 16, 12, 62); made += 1
    walk = paths.Path((cx, 0.0), (cx, FORE + 6.0), 130.0, 'walk')
    wr = walk.rect()
    box(pl, 'Ground_Walk', wr[0], wr[2], wr[1], wr[3], 0, 14); made += 1

    # ---- body ---------------------------------------------------------------
    box(a, 'Wall_Plinth', hx0 - 12, hx1 + 12, hy0 - 12, hy1 + 12, 0, 34); made += 1
    box(a, 'Wall_Body', hx0, hx1, hy0, hy1, 34, top); made += 1
    box(a, 'Wall_Parapet', hx0 - 10, hx1 + 10, hy0 - 10, hy1 + 10,
        top, top + PAR); made += 1
    box(a, 'Roof_Cap', hx0 - 14, hx1 + 14, hy0 - 14, hy1 + 14,
        top + PAR, top + PAR + 10); made += 1

    # ---- one front door, on a stoop -----------------------------------------
    for i in range(3):
        box(a, 'Ground_Stoop%d' % i, cx - 96 + i*8, cx + 96 - i*8,
            hy0 - 78 + i*24, hy0, 0, 12 + i*8); made += 1
    box(a, 'Frame_Door', cx - 62, cx + 62, hy0 - 6, hy0 + 6, 34, 34 + 170); made += 1
    box(a, 'Interior_Lobby', cx - 54, cx + 54, hy0 + 6, hy0 + 14, 40, 34 + 158); made += 1
    box(a, 'Roof_Canopy', cx - 108, cx + 108, hy0 - 84, hy0 + 6,
        34 + 178, 34 + 200); made += 1

    # ---- the stack: same window, same balcony, three high -------------------
    for f in range(F + 1):
        z0 = 34 + (GF - 34 if f else 0) + max(0, f - 1)*FH
        z0 = GF + (f - 1)*FH if f else 34
        h = (GF - 34) if f == 0 else FH
        for b in range(BAYS):
            bx = hx0 + 44 + (HW - 88)*(b + 0.5)/BAYS
            if f == 0 and abs(bx - cx) < 96:
                continue                       # the door takes the middle bay
            wz0 = z0 + (54 if f else 62)
            wz1 = z0 + h - (46 if f else 40)
            made += window(a, 'W%d_%d' % (f, b), 'y', hy0, -1.0,
                           bx - 62, bx + 62, wz0, wz1, bars=(1, 1))
            if f > 0 and b % 2 == 0:
                # A BALCONY, not a shelf. The old one was a slab with a solid
                # panel in front of it, which from any distance reads as a
                # canopy. What says balcony is the RAILING: a top rail with
                # light showing between uprights, and a door behind it.
                bw2, bp = 96.0, 104.0
                box(a, 'Ground_Balc%d_%d' % (f, b), bx - bw2, bx + bw2,
                    hy0 - bp, hy0 + 2, wz0 - 26, wz0 - 12); made += 1
                for e2, ex2 in (('L', bx - bw2), ('R', bx + bw2)):
                    box(a, 'Frame_BalcEnd%d_%d%s' % (f, b, e2), ex2 - 7, ex2 + 7,
                        hy0 - bp, hy0 + 2, wz0 - 12, wz0 + 84); made += 1
                box(a, 'Frame_BalcRail%d_%d' % (f, b), bx - bw2 - 4, bx + bw2 + 4,
                    hy0 - bp - 4, hy0 - bp + 8, wz0 + 72, wz0 + 84); made += 1
                for u in range(5):
                    ux = bx - bw2 + 2*bw2*(u + 0.5)/5.0
                    box(a, 'Mullion_Balust%d_%d_%d' % (f, b, u), ux - 4, ux + 4,
                        hy0 - bp - 1, hy0 - bp + 6, wz0 - 12, wz0 + 74); made += 1
                box(a, 'Frame_BalcDoor%d_%d' % (f, b), bx - 40, bx + 40,
                    hy0 - 6, hy0 + 3, wz0 - 12, wz0 + 118); made += 1
    # flank windows, because a detached block is seen from three sides
    for sgn, side in ((-1, hx0), (1, hx1)):
        for f in range(F + 1):
            z0 = GF + (f - 1)*FH if f else 34
            h = (GF - 34) if f == 0 else FH
            for k in range(2):
                wy = hy0 + (hy1 - hy0)*(0.32 + 0.36*k)
                made += window(a, 'S%d_%d_%d' % (sgn + 1, f, k), 'x', side,
                               float(sgn), wy - 54, wy + 54,
                               z0 + 58, z0 + h - 46, bars=(1, 0))

    # ---- trim: a cornice, a string course at each floor, a downpipe ---------
    box(a, 'Band_Cornice', hx0 - 16, hx1 + 16, hy0 - 16, hy1 + 16,
        top - 26, top); made += 1
    for f in range(1, F + 1):
        zc = GF + (f - 1)*FH
        box(a, 'Band_String%d' % f, hx0 - 9, hx1 + 9, hy0 - 9, hy0 + 4,
            zc - 12, zc); made += 1
    box(a, 'Frame_Downpipe', hx1 - 26, hx1 - 10, hy0 - 22, hy0 - 6,
        34, top - 20); made += 1
    for cxn, cx_ in (('L', hx0), ('R', hx1)):
        box(a, 'Frame_Corner%s' % cxn, cx_ - 10, cx_ + 10, hy0 - 6, hy0 + 4,
            34, top); made += 1
    box(a, 'Frame_Threshold', cx - 70, cx + 70, hy0 - 18, hy0 + 4, 26, 38); made += 1
    made += 3

    # ---- rear yard and rear elevation ---------------------------------------
    by0, by1 = hy1 + 10.0, D - 12.0
    if by1 - by0 > 200.0:
        box(pl, 'Ground_Yard', x0 + 10, x0 + W - 10, by0, by1, 0, 12); made += 1
        box(pl, 'Kerbing_YardWall', x0 + 8, x0 + W - 8, by1 - 12, by1, 12, 96)
        for sgn, fx in ((-1.0, x0 + 8), (1.0, x0 + W - 8)):
            box(pl, 'Kerbing_YardSide%d' % (int(sgn) + 1), fx - 7, fx + 7,
                by0 - 40, by1, 12, 96); made += 1
        # bin store: every block of flats has one and it is always by the back
        box(pl, 'Wall_BinStore', x0 + 70, x0 + 350, by1 - 200, by1 - 30, 0, 130)
        box(pl, 'Roof_BinStore', x0 + 58, x0 + 362, by1 - 212, by1 - 18, 130, 144)
        box(pl, 'Ground_Bins', x0 + 400, x0 + 640, by1 - 150, by1 - 40, 0, 96)
        # a yard people use: a drying area, a bench, a strip of planting and a
        # couple of parking bays off the back lane
        for sgn2 in (-1, 1):
            px2 = (x0 + W)/2.0 + sgn2*220.0
            box(pl, 'Frame_LinePost%d' % (sgn2 + 1), px2 - 7, px2 + 7,
                by0 + 150, by0 + 164, 12, 180); made += 1
        box(pl, 'Frame_Line', (x0 + W)/2.0 - 220, (x0 + W)/2.0 + 220,
            by0 + 155, by0 + 159, 170, 174)
        box(pl, 'Kerbing_YardBed', x0 + W - 330, x0 + W - 40, by0 + 40, by1 - 260, 12, 48)
        box(pl, 'Grass_YardBed', x0 + W - 316, x0 + W - 54, by0 + 54, by1 - 274, 12, 56)
        for k in range(2):
            bxp = x0 + 700.0 + k*260.0
            box(pl, 'Ground_Bay%d' % k, bxp, bxp + 230, by1 - 300, by1 - 40, 12, 15)
            made += 1
        made += 7
    for f in range(F + 1):
        z0 = GF + (f - 1)*FH if f else 34
        h = (GF - 34) if f == 0 else FH
        for b in range(2):
            rx = hx0 + 60 + (HW - 120)*(b + 0.5)/2.0
            made += window(a, 'RR%d_%d' % (f, b), 'y', hy1, 1.0,
                           rx - 58, rx + 58, z0 + 58, z0 + h - 46, bars=(1, 1))
    box(a, 'Frame_RearStair', hx1 - 150, hx1 - 30, hy1 - 4, hy1 + 120, 34, top)
    box(a, 'Frame_BackDoor', cx - 44, cx + 44, hy1 - 5, hy1 + 5, 34, 34 + 160)
    made += 2

    box(a, 'Roof_Stair', cx - 110, cx + 110, hy1 - 210, hy1 - 40,
        top + PAR, top + PAR + 120); made += 1

    print('%s [walkup %dst]: %d boxes' % (n, F + 1, made))
    return made


def build_works(spec, origin=(0.0, 0.0, 0.0), yaw=0.0):
    """A works: long, low, and lit from the roof rather than the wall.

    Nothing on this board had this texture. A city has an edge where things are
    made, and it does not look like a smaller office block - it looks like a
    SHED. What says shed is the sawtooth: a run of asymmetric roof bays, each
    with a steep glazed face turned away from the sun so the light inside never
    moves. That is why a factory roof looks the way it does, and it is only
    possible here because add_cube honours a rotation.

    Ground floor is doors, not windows: roller shutters and a dock, because
    what a works does at street level is take things in and send them out.
    """
    n = spec['name']
    x0, W, D = spec['x0'], spec['width'], spec['depth']
    GF, PAR = spec['gf_h'], spec['parapet']
    F = spec['floors']
    BAYS = spec['bays']
    rnd = random.Random(spec.get('seed', 0))
    SIDE, FRONT = 40.0, 90.0
    hx0, hx1 = x0 + SIDE, x0 + W - SIDE
    hy0, hy1 = FRONT, D - 60.0
    HW, HD = hx1 - hx0, hy1 - hy0
    eaves = GF + F*spec['fl_h']
    made = 0

    a = mkactor('BLD2_%s_W' % n, origin, (0.0, yaw, 0.0))
    pl = mkactor('PLOT_%s' % n, origin, (0.0, yaw, 0.0))

    # ---- the yard in front: hard standing, a kerb and a gate ---------------
    box(pl, 'Ground_Apron', x0 + 10, x0 + W - 10, 10, hy0 - 6, 0, 12); made += 1
    box(pl, 'Kerbing_Kerb', x0 + 6, x0 + W - 6, 0, 14, 12, 30); made += 1
    for k in range(5):
        px = x0 + 60.0 + (W - 120.0)*k/4.0
        box(pl, 'Frame_Bollard%d' % k, px - 12, px + 12, 40, 64, 12, 96); made += 1

    # ---- body ---------------------------------------------------------------
    box(a, 'Wall_Plinth', hx0 - 12, hx1 + 12, hy0 - 12, hy1 + 12, 0, 34); made += 1
    box(a, 'Wall_Body', hx0, hx1, hy0, hy1, 34, eaves); made += 1
    box(a, 'Band_Eaves', hx0 - 14, hx1 + 14, hy0 - 14, hy1 + 14,
        eaves - 22, eaves + PAR*0.4); made += 1

    # ---- ground floor: shutters and a dock, not shopfronts ------------------
    bw = HW/float(BAYS)
    for b in range(BAYS):
        bx0 = hx0 + b*bw + 26
        bx1 = hx0 + (b + 1)*bw - 26
        if b % 3 == 1:                       # a loading dock
            box(a, 'Frame_Dock%d' % b, bx0, bx1, hy0 - 8, hy0 + 4, 34, 34 + 300)
            box(a, 'Interior_Dock%d' % b, bx0 + 12, bx1 - 12, hy0 + 4, hy0 + 16,
                46, 34 + 286)
            box(pl, 'Ground_Ramp%d' % b, bx0 - 10, bx1 + 10, hy0 - 130, hy0,
                0, 32)
            box(a, 'Roof_DockHood%d' % b, bx0 - 22, bx1 + 22, hy0 - 120, hy0 + 6,
                34 + 306, 34 + 330)
            made += 4
        else:                                # a roller shutter
            box(a, 'Frame_Shutter%d' % b, bx0, bx1, hy0 - 6, hy0 + 4, 34, 34 + 250)
            for r in range(6):
                rz = 34 + 26 + r*36.0
                box(a, 'Mullion_Slat%d_%d' % (b, r), bx0 + 8, bx1 - 8,
                    hy0 - 9, hy0 - 3, rz, rz + 22)
            made += 7
        # a clerestory over every bay - the high strip windows a shed has
        made += window(a, 'Cl%d' % b, 'y', hy0, -1.0, bx0 + 10, bx1 - 10,
                       eaves - 150, eaves - 46, bars=(2, 0))

    # ---- flanks and rear ----------------------------------------------------
    for sgn, side in ((-1.0, hx0), (1.0, hx1)):
        for k in range(3):
            wy = hy0 + HD*(0.22 + 0.28*k)
            made += window(a, 'S%d_%d' % (int(sgn) + 1, k), 'x', side, sgn,
                           wy - 70, wy + 70, eaves - 190, eaves - 60, bars=(1, 0))
    for k in range(3):
        rx = hx0 + HW*(0.2 + 0.3*k)
        made += window(a, 'R%d' % k, 'y', hy1, 1.0, rx - 80, rx + 80,
                       eaves - 190, eaves - 60, bars=(2, 0))

    # ---- SAWTOOTH ROOF ------------------------------------------------------
    # Each tooth: a shallow slope facing the street and a steep glazed face
    # turned away from the sun, so the light inside never moves.
    teeth = max(3, int(round(HD/300.0)))
    td = HD/float(teeth)
    rise = 190.0
    ang = math.degrees(math.atan2(rise, td*0.78))
    slope_len = math.hypot(td*0.78, rise)
    for t in range(teeth):
        ty = hy0 + td*(t + 0.5)
        slab(a, 'Tile_Tooth%d' % t, (hx0 + hx1)/2.0, ty - td*0.11,
             eaves + rise/2.0, HW + 24.0, slope_len, 16.0, roll=-ang)
        made += 1
        gz = eaves + rise
        gy = ty + td*0.39
        box(a, 'Frame_ToothF%d' % t, hx0 - 10, hx1 + 10, gy - 9, gy + 9,
            eaves, gz); made += 1
        box(a, 'Glass_Tooth%d' % t, hx0 + 16, hx1 - 16, gy - 4, gy + 3,
            eaves + 16, gz - 14); made += 1
        for k in range(1, 6):
            mx = hx0 + (hx1 - hx0)*k/6.0
            box(a, 'Mullion_Tooth%d_%d' % (t, k), mx - 5, mx + 5,
                gy - 7, gy + 2, eaves + 16, gz - 14); made += 1
    box(a, 'Wall_ParapetF', hx0 - 6, hx1 + 6, hy0 - 6, hy0 + 14,
        eaves, eaves + PAR); made += 1
    box(a, 'Band_Coping', hx0 - 14, hx1 + 14, hy0 - 14, hy0 + 18,
        eaves + PAR, eaves + PAR + 12); made += 1

    if spec.get('chimney'):
        cx_ = hx1 - 220.0
        cy_ = hy1 - 200.0
        for k in range(4):
            w2 = 92.0 - k*12.0
            box(a, 'Wall_Stack%d' % k, cx_ - w2, cx_ + w2, cy_ - w2, cy_ + w2,
                eaves + k*260.0, eaves + (k + 1)*260.0); made += 1
        box(a, 'Frame_StackCap', cx_ - 96, cx_ + 96, cy_ - 96, cy_ + 96,
            eaves + 1040, eaves + 1076); made += 1

    print('%s [works %d teeth%s]: %d boxes'
          % (n, teeth, ' + stack' if spec.get('chimney') else '', made))
    return made
