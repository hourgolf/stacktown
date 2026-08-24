import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

# CAM_Hero_B looks from X=+4893, so it saw past the right edge of the backdrop
# and picked up black void - gate D1. Widen and heighten the card, and widen
# the ground so nothing reads as emptiness from either approved camera.
def resize(actor_label, comp_name, x0, x1, y0, y1, z0, z1):
    a = acts[actor_label]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() != comp_name:
            continue
        c.set_editor_property('relative_scale3d', unreal.Vector(
            abs(x1 - x0) / 100.0, abs(y1 - y0) / 100.0, abs(z1 - z0) / 100.0))
        c.set_editor_property('relative_location', unreal.Vector(
            (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0))
        print('%s/%s -> %.0f x %.0f x %.0f' % (actor_label, comp_name,
              abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))
        return True
    return False


resize('STAGE_Backdrop', 'Card', -11000, 14000, 1100, 1130, -80, 7000)
resize('STAGE_Ground', 'Ground', -16000, 19000, -12000, 1120, -92, -80)
les.save_current_level()
print('saved')
