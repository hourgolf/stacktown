"""Assign the card foliage materials by MATERIAL SLOT NAME.

Imported assets carry role in the slot name, not the component name - that is
what makes the Assetsville tileset usable and its four complete buildings not.
The tree slots are testleaf_01, testleaf_02 and testtrunk_01, so the role
vocabulary keys off "leaf" and "trunk" and a new tree from the same pack costs
nothing.

Reversible: pass restore=True to put the pack's own materials back. Nothing
here saves the level.
"""
import unreal, json
import _path  # noqa: F401
import rolemap

# ONE VOCABULARY. These lived here as local dicts, so the bake path could not
# see them and bound a single material across every slot of a donor tree.
LEAF = {k: '/Game/Stacktown/Materials/%s' % v
        for k, v in rolemap.SLOT.items()}
TRUNK = '/Game/Stacktown/Materials/MI_wood'

def apply(restore=False):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m: continue
            for i, sm in enumerate(m.get_editor_property('static_materials')):
                slot = str(sm.material_slot_name)
                tgt = None
                if slot in LEAF: tgt = LEAF[slot]
                elif 'trunk' in slot.lower(): tgt = TRUNK
                if not tgt: continue
                if restore:
                    c.set_material(i, sm.material_interface)   # the asset's own
                else:
                    c.set_material(i, unreal.load_asset(tgt))
                n += 1
    print('%s %d slots' % ('restored' if restore else 'assigned', n))

if __name__ == '__main__':
    apply(restore=bool(json.loads(ARGS).get('restore')) if 'ARGS' in dir() else False)
