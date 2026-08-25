"""Do any street lamps stand inside a parked vehicle?

The far-side lamps were once placed 62 uu INSIDE the carriageway and speared
the parked cars. That was fixed for the streets; this asks the same question of
every lamp on the board, including the avenue, so the answer is measured rather
than assumed. Self-check first: a deliberately overlapping pair must be caught,
or the test is asking the wrong question.
"""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def rect(a):
    o, e = a.get_actor_bounds(False)
    return (o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y)

def overlap(p, q):
    return not (p[1] <= q[0] or q[1] <= p[0] or p[3] <= q[2] or q[3] <= p[2])

# known answer: two rects that plainly overlap, and two that plainly do not
assert overlap((0, 10, 0, 10), (5, 15, 5, 15)), 'overlap() misses a real overlap'
assert not overlap((0, 10, 0, 10), (20, 30, 20, 30)), 'overlap() invents one'

lamps, cars = [], []
for a in eas.get_all_level_actors():
    n = a.get_actor_label()
    if n.startswith('LAMP_') and not n.startswith('LAMPLIGHT'):
        lamps.append((n, a))
    elif n.startswith('BAKED_veh'):
        cars.append((n, a))
print('lamps %d   vehicles %d' % (len(lamps), len(cars)))

# a lamp POLE is thin; its actor bounds include the arm reaching over the road,
# so testing the whole bounds would flag every lamp near a kerb. Test the pole
# footprint only: 40 uu square about the actor origin.
hits = []
for ln, la in lamps:
    p = la.get_actor_location()
    pole = (p.x - 20, p.x + 20, p.y - 20, p.y + 20)
    for cn, ca in cars:
        if overlap(pole, rect(ca)):
            hits.append((ln, cn, p.x, p.y))
for h in hits:
    print('  SPEARED %-22s through %-22s at (%.0f, %.0f)' % h)
print('lamp/vehicle intersections: %d' % len(hits))
