"""Widen the board and street for four lots, and re-derive the light rig.

The backdrop (half-X 12500) and ground (17500) are already wide enough; only the
board and street were sized for one building.

Lights are scaled from what MEASURABLY worked at Stage 1, not from the recipe's
nominal figure: the key sat 5128 uu from the subject at 1.58M lm. Moving the rig
to 9000 uu is a 1.755x distance, so 1.58M x 1.755^2 = 4.87M. Deriving from the
formula instead would have given 7.26M and blown the highlights.
"""
import unreal, math

TARGET_HALF_X = 2440.0          # board/street span X -300 .. 4580
BLOCK_CX, BLOCK_CZ = 2140.0, 1100.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

for lbl, names in (('STAGE_ModelBoard', ('BoardTop', 'BoardPlinth')),
                   ('STAGE_Street', ('Sidewalk', 'Road', 'CurbFace'))):
    for c in acts[lbl].get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() not in names:
            continue
        s = c.get_world_scale()
        half = c.static_mesh.get_bounds().box_extent.x * s.x
        # board top is fractionally larger than its plinth - keep that relation
        want = TARGET_HALF_X + (half - 1450.0 if half > 1440 else 0.0) * 0.0
        f = want / half
        loc = c.get_world_location()
        c.set_world_scale3d(unreal.Vector(s.x * f, s.y, s.z))
        c.set_world_location(unreal.Vector(BLOCK_CX, loc.y, loc.z), False, False)
        print('%-12s half %6.0f -> %6.0f  (x%.3f)' % (c.get_name(), half, want, f))

def relight(lbl, new_dist, subject):
    a = acts[lbl]
    lc = a.get_components_by_class(unreal.RectLightComponent)[0]
    pos = a.get_actor_location()
    off = unreal.Vector(pos.x - subject[0], pos.y - subject[1], pos.z - subject[2])
    d = math.sqrt(off.x ** 2 + off.y ** 2 + off.z ** 2)
    k = new_dist / d
    a.set_actor_location(unreal.Vector(subject[0] + off.x * k,
                                       subject[1] + off.y * k,
                                       subject[2] + off.z * k), False, False)
    I = lc.get_editor_property('intensity')
    lc.set_editor_property('intensity', I * k * k)
    for p in ('source_width', 'source_height'):
        try:
            lc.set_editor_property(p, lc.get_editor_property(p) * k)
        except Exception:
            pass
    lc.set_editor_property('attenuation_radius',
                           max(lc.get_editor_property('attenuation_radius'), new_dist * 2.4))
    print('%-11s d %6.0f -> %6.0f   %9.0f -> %9.0f lm' % (lbl, d, new_dist, I, I * k * k))

subj = (BLOCK_CX, 0.0, BLOCK_CZ)
relight('LIGHT_Key', 9000.0, subj)
relight('LIGHT_Fill', 7400.0, subj)
les.save_current_level()
print('stage extended and relit')
