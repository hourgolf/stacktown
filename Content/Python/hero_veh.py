"""Bind the TWO-SIDED card materials to the hero vehicles, and role-bind the
rest of the dressing.

The vehicles are open shells (the sedan has 12,004 open border edges against
6,064 triangles) because they were baked from skeletal meshes authored to be
seen from outside only. M_StacktownMaster is two_sided=False, so a normal card
material culls their backfaces and the road shows through the bodywork - Stage
2 audit defect 2. The *_2S siblings exist for exactly this.

Cars get card colours because at 1:87 a car IS a painted card shape; giving
them their own palette would be a second colour language on the same board.
"""
import unreal, _path, rolemap
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eal = unreal.EditorAssetLibrary

CARD_2S = ['MI_card_lift_2S', 'MI_card_ochre_2S', 'MI_card_rose_2S',
           'MI_card_sage_2S', 'MI_paint_cream_2S']
GLASS_2S = 'MI_glass_b_2S'


def M(n):
    return eal.load_asset('/Game/Stacktown/Materials/%s' % n)


cars = props = 0
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l == 'HERO_Cars':
        for i, c in enumerate(a.get_components_by_class(unreal.StaticMeshComponent)):
            sm = c.static_mesh
            if not sm:
                continue
            # THE MESHES CARRY NO MATERIALS AT ALL. Slot 0 holds
            # WorldGridMaterial and every other slot holds NONE, so there is
            # nothing recording which slot is glazing - which is also why
            # step_veh2s.py's "map whatever the slot holds to its _2S sibling"
            # had nothing to map. Binding one colour across every slot gave a
            # solid card lump with no windows.
            #
            # Slot ORDER is the only signal left, and the convention these
            # bakes follow is body / glass / trim / tyres. That is a
            # HYPOTHESIS confirmed by looking at the render, not a fact read
            # from the asset - if a vehicle ever comes through with a
            # different order it will be visible immediately as a car with
            # glass where its paint should be.
            body = M(CARD_2S[i % len(CARD_2S)])
            ORDER = [body, M(GLASS_2S), M('MI_dark_metal'), M('MI_dark_metal')]
            n = len(sm.get_editor_property('static_materials'))
            for si in range(n):
                c.set_material(si, ORDER[si] if si < len(ORDER) else body)
            cars += 1
    elif l in ('HERO_Props',) or l.startswith('LAMP_Hero'):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            n = c.get_name()
            base = rolemap.material_for(n, 'MI_dist_buff', 'MI_shingle_grey',
                                        'LAMP' if l.startswith('LAMP') else 'BLD2',
                                        'MI_paint_cream')
            if not base:
                continue
            sm = c.static_mesh
            slots = sm.get_editor_property('static_materials') if sm else []
            if len(slots) <= 1:
                c.set_material(0, M(base))
            else:
                for si, sl in enumerate(slots):
                    n2 = rolemap.material_for_slot(sl.material_slot_name, base)
                    c.set_material(si, M(n2 or base))
            props += 1
les.save_current_level()
print('HEROVEH bound %d vehicle bodies (2S) and %d dressing components' % (cars, props))
