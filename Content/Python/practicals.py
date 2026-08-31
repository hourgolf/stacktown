"""Practicals for every generated building and every exposed flank.

THE BUG THIS REPLACES. Every practical in the project was spawned with
`unreal.Rotator(0, 90, 0)`, intended as "yaw 90". Rotator takes
(roll, PITCH, yaw), so it set pitch instead: measured on the level, all 43
lights had forward = (0, 0, 1) and were aimed at the ceiling. Seen from the
street that is a bright horizontal bar with a wash up the underside of the
window head, which is exactly what it looked like. The trap is written down in
HANDOFF.md section 5 and the code did it anyway.

WHAT A LIT WINDOW SHOULD BE. Not a visible lamp. In a card model a lit window is
a diffusing panel behind the glazing, so the read is an evenly glowing rectangle
with no source in view. So the practical now sits BETWEEN the glass and the
interior card, aimed INWARD at the card, with a source sized to the opening.
The card is what you see; the lamp is edge-on and behind the glass.

AIM IS DERIVED, NOT TABULATED. Each interior card is paired with its own glass
by name suffix - Interior_B0 with Glass_B0, Interior_L2B1 with Glass_L2B1 - and
the light points along the vector between them. That is why this works
unchanged on block B, which faces the other way, and on the flank elevations,
whose windows face +/-X. A table of facing directions would have needed an edit
for every one of them.

Intensities are absolute, not a scale factor, so re-running does not dim the
block further each time.
"""
import unreal, random

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith('LIGHT2_'):
        eas.destroy_actor(a)


def world_extent(c):
    e = c.static_mesh.get_bounds().box_extent
    s = c.get_world_scale()
    return unreal.Vector(abs(e.x * s.x), abs(e.y * s.y), abs(e.z * s.z))


def add_light(name, loc, aim, intensity, temp, w, h, radius):
    """aim is the direction the light faces; a RectLight emits along local +X."""
    rot = unreal.MathLibrary.make_rot_from_x(aim)
    act = eas.spawn_actor_from_class(unreal.RectLight, loc, rot)
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
made = skipped = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith(('BLD2_', 'ELEV_')):
        continue
    # the FULL label after the family, not just the building name: a facade
    # actor BLD2_Bank_F0 and elevation ELEV_Bank_W both reduced to 'Bank',
    # so two Interior_B1 components on different actors produced two light
    # actors sharing one label - NAME-03's standing failure
    who = lbl.split('_', 1)[1]
    comps = {c.get_name(): c for c in a.get_components_by_class(unreal.StaticMeshComponent)}
    for nm, c in comps.items():
        if not nm.startswith('Interior_'):
            continue
        glass = comps.get('Glass_' + nm[len('Interior_'):])
        if glass is None:
            skipped += 1
            continue
        shop = nm == 'Interior_Shop'
        if not shop and rnd.random() >= 0.42:
            continue            # a model reads as occupied when only SOME rooms are lit
        gi, gl = c.get_world_location(), glass.get_world_location()
        d = unreal.Vector(gi.x - gl.x, gi.y - gl.y, gi.z - gl.z)
        gap = d.length()
        if gap < 1e-3:
            skipped += 1
            continue
        aim = unreal.Vector(d.x / gap, d.y / gap, d.z / gap)     # glass -> card
        # sit in the void between glazing and card, looking at the card
        loc = unreal.Vector(gl.x + aim.x * gap * 0.55,
                            gl.y + aim.y * gap * 0.55,
                            gl.z + aim.z * gap * 0.55)
        ge = world_extent(glass)
        # source sized to the OPENING so the card lights evenly instead of
        # taking a hot spot. The thin axis of the glass box is its depth.
        horiz = max(ge.x, ge.y) * 2.0
        vert = ge.z * 2.0
        if shop:
            add_light('LIGHT2_%s_%s' % (who, nm), loc, aim,
                      rnd.uniform(1760, 2530), rnd.uniform(2700, 3000),
                      max(120.0, horiz * 0.9), max(90.0, vert * 0.9), 420)
        else:
            add_light('LIGHT2_%s_%s' % (who, nm), loc, aim,
                      rnd.uniform(2310, 3960), rnd.uniform(2750, 3050),
                      max(80.0, horiz * 0.9), max(60.0, vert * 0.9), 300)
        made += 1

print('placed %d practicals (%d skipped: no paired glass)' % (made, skipped))
les.save_current_level()
