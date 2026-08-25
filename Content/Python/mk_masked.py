"""Create M_StacktownMaster_Masked - the alpha-tested variant for foliage.

MASTER_MATERIAL_SPEC forbids a second master "just for this one thing", and
that rule is about ARCHITECTURE: variation between architectural surfaces must
come from instance parameters. Blend mode is not an instance parameter in
Unreal - it is baked into the material - so an alpha-tested surface cannot be
expressed as an instance of an opaque master no matter how it is authored.
M_StacktownMaster_2S exists for the same reason (two_sided is likewise not an
instance parameter). This is a third BLEND MODE of one material, not a second
look, and every card parameter stays shared.

Duplicated rather than authored fresh so the card band, the seam chain, the
triplanar paper and the curvature wear are identical by construction. If the
master changes, this must be re-duplicated or hand-matched - that is the cost,
and it is why there are three of these and not thirty.
"""
import unreal

SRC = '/Game/Stacktown/Materials/M_StacktownMaster'
DST = '/Game/Stacktown/Materials/M_StacktownMaster_Masked'

if unreal.EditorAssetLibrary.does_asset_exist(DST):
    print('already exists:', DST)
else:
    ok = unreal.EditorAssetLibrary.duplicate_asset(SRC, DST)
    print('duplicated ->', DST, bool(ok))

m = unreal.load_asset(DST)
m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
m.set_editor_property('two_sided', True)                # leaf cards are seen from both sides
m.set_editor_property('opacity_mask_clip_value', 0.33)
print('blend=%s twosided=%s clip=%s' % (
    m.get_editor_property('blend_mode'), m.get_editor_property('two_sided'),
    m.get_editor_property('opacity_mask_clip_value')))
unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
print('saved')
