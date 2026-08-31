"""Street dressing for a SHOW frame only. Named HERO_/LAMP_ so it lifts out.

Run LOCALLY (python3 Content/Python/hero_dress.py), never through rung.sh:
this places geometry in live mode, which goes over MCP, and an MCP call from
inside a rung script waits on the thread it is running on.

WHY IT LIFTS OUT. street.py carries the Stage 2 constraint "no people,
vehicles or signage", and the street is gate evidence. Dressing it changes
what a capture of it means. So everything here is prefixed, the frame is taken
in SHOW mode (stamped, therefore inadmissible as judging evidence), and
hero_dress.py --clear removes it again. The level goes back to gate-valid.

VEHICLES: there are none. Searched every pack - AssetsvilleTown, Deko,
Mega_Street_Props, Uniblocks - and the only match for a car is SM_carSiren_01,
a siren. Street LAMPS do not exist either, which is why street_lamps.py
generates them from four boxes; that recipe (pole 26, height 780, arm 210) is
reused here rather than re-derived.
"""
import sys, os, math, random, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _path  # noqa: F401
import ue, json
import genbuild
from genbuild import mkactor, box, piece
import stagegeo

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'

# the street, as street.py built it - the DEFAULT, unchanged, so a run
# against Sandbox_Bench behaves exactly as it always has.
X0, RUN = 3000.0, 14483.0
Y_NORTH, STREET_W, PAVE = -22000.0, 1500.0, 260.0

# ...and an OVERRIDE, so the same proven dressing can be transplanted onto
# another street instead of a second copy being written for it. TestCity's
# arterial is a different geometry, not a different kind of thing.
_ovr = os.path.join(tempfile.gettempdir(), 'stacktown_dress.json')
if os.path.exists(_ovr):
    _o = json.load(open(_ovr))
    X0 = float(_o.get('x0', X0))
    RUN = float(_o.get('run', RUN))
    Y_NORTH = float(_o.get('y_north', Y_NORTH))
    STREET_W = float(_o.get('street_w', STREET_W))
    PAVE = float(_o.get('pave', PAVE))
    print('hero_dress: street override x0 %.0f run %.0f y_north %.0f'
          ' width %.0f pave %.0f' % (X0, RUN, Y_NORTH, STREET_W, PAVE))
Z = stagegeo.FLOOR_Z
if os.path.exists(_ovr):
    # the road surface differs per board; Sandbox's floor is not TestCity's
    # road top, and dressing placed at the wrong Z sinks into the carriageway.
    Z = float(json.load(open(_ovr)).get('z', Z))
PAVE_TOP = Z + 26.0
YB = Y_NORTH - PAVE / 2.0                 # north pavement centre line
YA = Y_NORTH - STREET_W + PAVE / 2.0      # south pavement centre line

POLE, HEIGHT, ARM, SPACING = 26.0, 780.0, 210.0, 1450.0
SP = '/Game/AssetsvilleTown/Meshes/StreetProps/'
# measured path, not assumed - the pack nests its meshes and the
# obvious guess was wrong; piece() said so loudly instead of
# silently placing nothing, which is the whole point of that fix.
POT = '/Game/Mega_Street_Props_Pack/Street_Props_Pack_V1/Mesh/SM_Flower_Pot'


def clear():
    """Remove by LABEL, via find_actors' own name filter.

    The first version matched '.HERO_' inside each actor's refPath and removed
    NOTHING while reporting success: an actor's refPath carries its internal
    NAME (Actor_23), not the label set afterwards. find_actors takes a `name`
    filter that matches the label, which is the thing we actually set.
    """
    n = 0
    # ONLY THIS SCRIPT'S OWN ACTORS. 'HERO_' also matches
    # hero_backdrop's HERO_End* buildings, so a broad prefix made the
    # two scripts clobber each other - dressing the street silently
    # deleted the row closing the vista, and the frame came back open.
    for pat in ('HERO_Props', 'HERO_Cars', 'LAMP_Hero'):
        r = ue.tool(S, 'find_actors',
                    {'name': pat, 'tag': '', 'collision_channels': []})
        try:
            found = json.loads(r)['returnValue']
        except Exception:
            continue
        for a in found:
            ue.tool(S, 'remove_from_scene', {'actor': a})
            n += 1
    return n


def lamp(name, x, y, reach):
    """Pole, arm and head - street_lamps.py's recipe, unchanged."""
    a = mkactor(name, (x, y, PAVE_TOP), (0.0, 0.0, 0.0))
    h = POLE / 2.0
    box(a, 'Frame_Base', -h - 8, h + 8, -h - 8, h + 8, 0, 34)
    box(a, 'Frame_Column', -h, h, -h, h, 34, HEIGHT)
    y0, y1 = (0, ARM) if reach > 0 else (-ARM, 0)
    box(a, 'Frame_Arm', -9, 9, y0, y1, HEIGHT - 22, HEIGHT)
    ty = ARM * reach
    box(a, 'Frame_Head', -26, 26,
        ty - 34 * abs(reach) if reach > 0 else ty,
        ty + 34 if reach > 0 else ty + 34 * abs(reach),
        HEIGHT - 52, HEIGHT - 20)
    return a


def main():
    import genbuild as _gb; _gb.live()   # spawns into the OPEN level; see genbuild._LIVE
    if '--clear' in sys.argv:
        clear(); return
    clear()
    rnd = random.Random(20260827)
    made = {'lamps': 0, 'props': 0}

    # LAMPS, alternating sides so the arms interleave over the road
    x = X0 + 500.0
    i = 0
    while x < X0 + RUN - 400.0:
        north = (i % 2 == 0)
        lamp('LAMP_Hero%d' % i, x, YB if north else YA, -1 if north else 1)
        made['lamps'] += 1
        x += SPACING
        i += 1

    # DONOR FURNITURE on the pavements. Components carry existing roles so the
    # level's own role sweep binds them per SLOT - the props never ship their
    # pack's own materials.
    KIT = [(SP + 'SM_bench_02',    'Timber_Bench',  1.0, 0),
           (SP + 'SM_Bicycle_01',  'Rail_Bike',     1.0, 90),
           (SP + 'SM_bike_rack',   'Rail_Rack',     1.0, 0),
           (SP + 'SM_hydrant',     'Rail_Hydrant',  1.0, 0),
           (SP + 'SM_mailbox_1',   'Rail_Mailbox',  1.0, 0),
           (SP + 'SM_parking_meter', 'Rail_Meter',  1.0, 0),
           (SP + 'SM_public_phone', 'Rail_Phone',   1.0, 0),
           (POT, 'Planter_Pot', 1.0, 0)]
    props = mkactor('HERO_Props', (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    x = X0 + 900.0
    k = 0
    while x < X0 + RUN - 600.0:
        asset, base, sc, yaw = KIT[k % len(KIT)]
        north = (k % 2 == 1)
        y = (YB - 40.0) if north else (YA + 40.0)
        piece(props, '%s%d' % (base, k), asset,
              (x, y, PAVE_TOP), (0.0, yaw + (180.0 if north else 0.0), 0.0),
              scale=sc)
        made['props'] += 1
        x += 760.0 + rnd.uniform(-120.0, 220.0)
        k += 1

    # VEHICLES. They exist after all - SM_Baked_* in Content/Stacktown/Meshes,
    # baked by this project from the Assetsville physics assets and used in the
    # original city sandbox. My first search missed them because it anchored
    # the pattern to the start of the name.
    #
    # PEDESTRIANS ARE EXCLUDED. SM_Baked_Ped1/2/3 sit beside them, and Stage 2
    # says no people. Vehicles are the owner's explicit call for this frame;
    # people were not, so they stay out.
    #
    # They are OPEN SHELLS - the sedan carries 12,004 open border edges - so
    # they need the *_2S two-sided materials or the road shows through the
    # bodywork (step_veh2s.py, Stage 2 audit defect 2). Bound by hero_veh.py
    # after placement, since these slots are named Material_0 and carry no role.
    VEH = ['SM_Baked_Sedan', 'SM_Baked_Pickup', 'SM_Baked_Van',
           'SM_Baked_Muscle', 'SM_Baked_Truck', 'SM_Baked_Police',
           'SM_Baked_Sport', 'SM_Baked_Offroad']
    cars = mkactor('HERO_Cars', (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    x = X0 + 1250.0
    v = 0
    while x < X0 + RUN - 900.0:
        north = (v % 2 == 0)
        # parked against the kerb, nose alternating up and down the street
        y = (Y_NORTH - PAVE - 150.0) if north else (Y_NORTH - STREET_W + PAVE + 150.0)
        piece(cars, 'Car%d_%s' % (v, VEH[v % len(VEH)][9:]),
              '/Game/Stacktown/Meshes/' + VEH[v % len(VEH)],
              (x, y, Z + 2.0), (0.0, 0.0 if north else 180.0, 0.0))
        made['props'] += 1
        v += 1
        x += 1180.0 + rnd.uniform(-140.0, 260.0)
    print('hero_dress: %d vehicles parked' % v)

    fails = genbuild.piece_failures(reset=True)
    print('hero_dress: %d lamps, %d props' % (made['lamps'], made['props']))
    if fails:
        print('hero_dress: %d PLACEMENTS FAILED' % len(fails))
        for f in fails[:4]:
            print('   %s <- %s : %s' % f)


if __name__ == '__main__':
    main()
