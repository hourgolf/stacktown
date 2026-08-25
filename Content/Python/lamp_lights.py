"""Hang a light under each lamp head.

Separate from street_lamps.py because a light is an ACTOR and the lamp geometry
is components placed over MCP. Own prefix so practicals.py - which wipes every
LIGHT2_ actor it finds - cannot take these with it.
"""
import unreal, random

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('LAMPLIGHT_'):
        eas.destroy_actor(a)

HEIGHT, ARM = 780.0, 210.0
rnd = random.Random(90210)
n = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith('LAMP_'):
        continue
    loc = a.get_actor_location()
    # the arm leans along Y; the head sits at its far end. Which way is encoded
    # in the label's side letter, the same way the geometry decided it.
    reach = -1.0 if ('sF' in lbl or lbl.split('_')[1].endswith('F')) else 1.0
    lt = eas.spawn_actor_from_class(
        unreal.RectLight,
        unreal.Vector(loc.x, loc.y + ARM*reach, HEIGHT - 56.0),
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
