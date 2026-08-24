"""Restore the pack's own materials on foliage.

Their trees use alpha-tested leaf cards (M_AlphaTest / M_Plants). Our card
material is opaque, so binding it over the foliage slots filled in every gap
between the leaves and turned a canopy into a solid cone. The card treatment
cannot be blanket-applied to anything alpha-cut - foliage needs either its own
masked variant of the master, or the pack's original material.

Original materials here, so the screenshot shows the honest state.
"""
import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
n=0
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    if not (l.startswith('SUR_tree') or l=='SUR_prop4'):
        continue
    c=a.static_mesh_component
    sm=c.static_mesh
    for i,s in enumerate(sm.get_editor_property('static_materials')):
        if s.material_interface:
            c.set_material(i, s.material_interface)
    n+=1
print('restored original materials on %d foliage actors'%n)
les.save_current_level()
