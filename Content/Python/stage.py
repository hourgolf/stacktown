"""Fit the stage to the board, derived rather than authored.

The board has grown four times - east for the avenue, south twice for the
houses, north for the works - and the stage was authored once for 11,360 x
10,700. It is 11,360 x 14,300 now. Every time the board grows, a stage that
was authored once is wrong again, so this derives everything from
citygeom.board_rect().

THE BACKDROP MUST NOT CAST SHADOW. It is a photographic element - a wall that
catches light behind the subject - and a 14,300 uu wall with the sun at 52
degrees throws a shadow across everything behind the board. That is the hard
diagonal edge in the last board capture, and it is why the surround read as a
void at mean 60 while the city itself was correctly lit.
"""
import unreal
import _path  # noqa: F401
import citygeom as G

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

x0, y0, x1, y1 = G.board_rect()
W, D = x1 - x0, y1 - y0
cx, cy = (x0 + x1)/2.0, (y0 + y1)/2.0
BIG = max(W, D)

# the room: floor a comfortable margin past the board, backdrop standing behind
# Big enough to FILL THE FRAME at the board camera, which stands about 30,000
# out. At board + 0.9x the model floated in a void from there, and the gate
# asks for a room "so the building is lit by a place rather than floating in a
# void". In day mode the sun lights a large plane as evenly as a small one -
# the earlier darkness was the floor sitting ABOVE the board, not its size.
GROUND = (W + BIG*3.4, D + BIG*3.4)
# The backdrop must be sized off the GROUND, not the board, or its edge cuts a
# visible diagonal across the surround - the floor kept going where the wall
# stopped. Same fault as the floor itself: sized against the wrong thing.
BACK_W, BACK_H = GROUND[0]*1.05, BIG*0.85
BACK_Y = y1 + BIG*0.30

found = {}
for a in eas.get_all_level_actors():
    found[a.get_actor_label()] = a


def fit(label, loc, want, shadow):
    """Set a stage plane's world position and SIZE, then MEASURE the result.

    Four bugs have hidden in this function, and every one of them survived
    because it printed what it asked for instead of what it got:

      1. the ground was built at 4.5x the board and never grew with it;
      2. the meshes were assumed to be 100 uu cubes - they are not, and the
         ground came out 8,480,500 uu wide, at z -27, ABOVE the board top
         at -30, so the floor was covering the city;
      3. the COMPONENT carries its own relative scale on top of the actor's,
         so resetting only the actor still left it 8,480,500 uu wide;
      4. the component also carries a relative LOCATION, and a relative offset
         is MULTIPLIED by the root's scale. The ground mesh sat at
         (1500, -5440) relative; at 600x that put it 900,000 uu from the city.
         Enlarging the ground threw it FURTHER AWAY, which is why the surround
         got blacker the bigger I made it.

    STAGE_ModelBoard never had any of these because its root is at the origin
    with scale 1 and its mesh components carry both location and scale. So the
    rule is: the root holds the transform, the components hold nothing.
    """
    a = found.get(label)
    if not a:
        print('  %-18s MISSING' % label); return
    a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    base = None
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        c.set_editor_property('relative_scale3d', unreal.Vector(1.0, 1.0, 1.0))
        c.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 0.0))
        if c.static_mesh and base is None:
            b = c.static_mesh.get_bounds().box_extent
            base = (max(b.x*2, 1.0), max(b.y*2, 1.0), max(b.z*2, 1.0))
    if not base:
        print('  %-18s no mesh' % label); return
    scale = tuple(max(w/bs, 0.001) for w, bs in zip(want, base))
    a.set_actor_location(unreal.Vector(*loc), False, False)
    a.set_actor_scale3d(unreal.Vector(*scale))
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        c.set_editor_property('cast_shadow', shadow)

    # MEASURE. get_actor_bounds is the engine's own answer, the same one the
    # renderer culls against - which is what made the plane invisible rather
    # than dark. Report the measured numbers; assert against the asked-for.
    org, ext = a.get_actor_bounds(False)
    got_loc = (org.x, org.y, org.z)
    got_sz = (ext.x*2, ext.y*2, ext.z*2)
    tol = max(want[0], want[1]) * 0.02 + 50.0
    bad = [i for i in range(3) if abs(got_loc[i] - loc[i]) > tol]
    # Only police axes big enough to matter. get_actor_bounds includes the
    # editor BillboardComponent, which swamps a thin axis - the backdrop is
    # 60 uu deep and measures 256 because of the sprite. A billboard can only
    # inflate bounds, never shrink them, so a thin axis proves nothing.
    bad += [i+3 for i in (0, 1, 2)
            if want[i] > 1000.0 and abs(got_sz[i] - want[i]) > want[i]*0.05]
    print('  %-18s at (%7.0f,%8.0f,%7.0f)  size (%8.0f,%8.0f)  shadow=%s%s'
          % (label, got_loc[0], got_loc[1], got_loc[2], got_sz[0], got_sz[1],
             shadow, '' if not bad else '   <-- MEASURED != ASKED'))
    if bad:
        print('      asked  at (%7.0f,%8.0f,%7.0f)  size (%8.0f,%8.0f)'
              % (loc[0], loc[1], loc[2], want[0], want[1]))
        raise AssertionError('%s did not land where it was put' % label)


# a 100 uu cube is the unit these were built from, hence /100
# The board slab reads from -80 to 0, so the room floor goes BELOW it at -140
# and the board sits on the floor rather than in it.
fit('STAGE_Ground', (cx, cy, -140.0), (GROUND[0], GROUND[1], 24.0), True)
fit('STAGE_Backdrop', (cx, BACK_Y, BACK_H/2.0 - 140.0),
    (BACK_W, 60.0, BACK_H), False)
print('board %.0f x %.0f   ground %.0f x %.0f   backdrop %.0f wide %.0f tall at Y %.0f'
      % (W, D, GROUND[0], GROUND[1], BACK_W, BACK_H, BACK_Y))
les.save_current_level()
