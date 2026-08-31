"""Hang a light under each lamp head.

Separate from street_lamps.py because a light is an ACTOR and the lamp geometry
is components placed over MCP. Own prefix so practicals.py - which wipes every
LIGHT2_ actor it finds - cannot take these with it.
"""
import unreal, random
import _path  # noqa: F401
import labels

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 'LAMPLIGHT_s1F_0'.startswith('LAMP_') is TRUE, so the build loop counted the
# lights it had just made as lamps and hung a second light on each: 46 lamps
# produced 88 lights. Collect the lamps BEFORE wiping, and discriminate by
# FAMILY rather than by prefix string - which is the whole reason labels.py
# exists.
LAMPS = [a for a in eas.get_all_level_actors()
         if labels.family(a.get_actor_label()) == 'LAMP']
for a in list(eas.get_all_level_actors()):
    if labels.family(a.get_actor_label()) == 'LAMPLIGHT':
        eas.destroy_actor(a)

HEIGHT, ARM = 780.0, 210.0
rnd = random.Random(90210)
n = 0
for a in LAMPS:
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    # The head sits at the arm's far end; which way is encoded in the label's
    # side letter, the same way the geometry decided it. street_lamps.py
    # builds F with reach +1 (over the road at k_far) and N with -1; the old
    # decode here had BOTH signs inverted, so every light hung 420 uu over
    # the pavement instead of under its own head. Avenues lean along X.
    side = lbl.split('_')[1][-1]
    dx, dy = {'F': (0.0, 1.0), 'N': (0.0, -1.0),
              'W': (1.0, 0.0), 'E': (-1.0, 0.0)}[side]
    lt = eas.spawn_actor_from_class(
        unreal.RectLight,
        unreal.Vector(loc.x + ARM*dx, loc.y + ARM*dy, HEIGHT - 56.0),
        unreal.Rotator(0.0, -90.0, 0.0))          # face straight DOWN
    lt.set_actor_label('LAMPLIGHT_' + lbl[5:])
    c = lt.get_components_by_class(unreal.RectLightComponent)[0]
    c.set_editor_property('intensity', rnd.uniform(2600.0, 3400.0))
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', rnd.uniform(2100.0, 2400.0))   # sodium
    c.set_editor_property('source_width', 46.0)
    c.set_editor_property('source_height', 46.0)
    c.set_editor_property('attenuation_radius', 900.0)
    c.set_editor_property('cast_shadows', False)
    n += 1
print('lamp lights: %d' % n)
