"""Practicals for every generated building, placed procedurally.

Intensities are the TUNED values (the old ones clipped on the reveal box behind
the glass). They are absolute, not a scale factor, so re-running the build does
not dim the block further each time.

The new shopfronts rendered as flat black voids - MASTER_MATERIAL_SPEC's rule
that emptiness behind glass reads as a hole, not a room. Stage 1 only avoided it
because its practicals were hand-placed, which is exactly what cannot scale.

So this derives placement from the geometry: find each building's shop glass and
upper-floor interiors, and light a DELIBERATELY UNEVEN subset. Evenly lit floors
read as an office block at night; a model reads as occupied when some rooms are
lit and some are not.
"""
import unreal, random

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('LIGHT2_'):
        eas.destroy_actor(a)

def add_light(name, loc, intensity, temp, w, h, radius):
    act = eas.spawn_actor_from_class(unreal.RectLight, loc, unreal.Rotator(0, 90, 0))
    act.set_actor_label(name)
    c = act.get_components_by_class(unreal.RectLightComponent)[0]
    c.set_editor_property('intensity', intensity)
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', temp)
    c.set_editor_property('source_width', w)
    c.set_editor_property('source_height', h)
    c.set_editor_property('attenuation_radius', radius)
    c.set_editor_property('cast_shadows', False)
    return act

rnd = random.Random(918)
made = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith('BLD2_'):
        continue
    who = lbl.split('_')[1]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm = c.get_name()
        w = c.get_world_location()
        e = c.static_mesh.get_bounds().box_extent
        s = c.get_world_scale()
        if nm == 'Glass_Shop':
            n = 2 if e.x * s.x < 350 else 3
            for i in range(n):
                x = w.x + (i - (n - 1) / 2.0) * (e.x * s.x * 1.3 / max(1, n - 1) if n > 1 else 0)
                add_light('LIGHT2_%s_Shop%d' % (who, i),
                          unreal.Vector(x, w.y + 16, w.z),
                          rnd.uniform(1760, 2530), rnd.uniform(2700, 3000),
                          260, 180, 420)
                made += 1
        elif nm.startswith('Interior_B') and rnd.random() < 0.42:
            # sit the lamp just in FRONT of the interior box, not inside the
            # facade slab. At w.y-10 it was embedded in the wall depth and
            # washed the spandrel with a hard-edged band; the radius was also
            # 780 for a room 26 uu deep.
            add_light('LIGHT2_%s_%s' % (who, nm),
                      unreal.Vector(w.x, w.y - 4, w.z),
                      rnd.uniform(2310, 3960), rnd.uniform(2750, 3050),
                      150, 120, 300)
            made += 1
print('placed %d practicals' % made)
les.save_current_level()
