"""Generate M_FeedLayer + MI_FeedLayer: the monitor-flavor feed layer.

The owner-approved spec (Docs/CAMERA_DESIGN.md, "The feed layer"): the
player is the FEED, so a subtle analog-monitor layer - scanlines, slight
barrel curvature, chroma fringe, vignette - sells the signal between the
camera and the viewer. MONITOR flavor, not tape: modern superzoom on an
old studio monitor is coherent kit.

Design constraints honoured here:
  - ONE master Intensity scalar 0..1 multiplying everything; per-component
    scalars underneath (group "Feed").
  - Intensity 0 routes the UNTOUCHED centre SceneTexture sample through
    lerp(plain, fx, 0) - the identity path, so zero costs nothing visually.
  - Show-side only BY CONSTRUCTION: this material goes in its own volume
    (LOOK_Feed, made by mk_feedvolume.py), never in LOOK_Post.
  - No time-varying noise in v1 - we spent today killing temporal
    instability; the first read of this layer should be still-stable.

Generation script committed alongside the asset, per the fix-class ladder.
Rerunnable: deletes and rebuilds the graph if the material exists.
"""
import unreal

MEL = unreal.MaterialEditingLibrary
FOLDER = '/Game/Stacktown/Materials'
MAT = FOLDER + '/M_FeedLayer'
MI = FOLDER + '/MI_FeedLayer'

at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

# --- material asset ---------------------------------------------------------
if eal.does_asset_exist(MAT):
    mat = eal.load_asset(MAT)
    for e in list(MEL.get_material_expressions(mat) or []):
        MEL.delete_material_expression(mat, e)
    print('rebuilding existing M_FeedLayer graph')
else:
    mat = at.create_asset('M_FeedLayer', FOLDER, unreal.Material,
                          unreal.MaterialFactoryNew())
mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_POST_PROCESS)
mat.set_editor_property('blendable_location',
                        unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)


def expr(cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def scalar(name, default, x, y):
    p = expr(unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property('parameter_name', name)
    p.set_editor_property('default_value', default)
    p.set_editor_property('group', 'Feed')
    return p


def const(v, x, y):
    c = expr(unreal.MaterialExpressionConstant, x, y)
    c.set_editor_property('r', v)
    return c


def wire(a, aout, b, bin):
    ok = MEL.connect_material_expressions(a, aout, b, bin)
    assert ok, 'wire failed: %s.%s -> %s.%s' % (a.get_name(), aout,
                                                b.get_name(), bin)

# --- parameters -------------------------------------------------------------
pIntensity = scalar('Intensity', 0.35, -2200, -600)
pLines = scalar('LineCount', 400.0, -2200, -400)
pScan = scalar('ScanAmt', 0.35, -2200, -200)
pChroma = scalar('ChromaPx', 0.8, -2200, 0)
pCurv = scalar('CurvAmt', 0.06, -2200, 200)
pVign = scalar('VignAmt', 0.25, -2200, 400)

# --- viewport uv and curvature ---------------------------------------------
uv = expr(unreal.MaterialExpressionScreenPosition, -2000, -100)
half = expr(unreal.MaterialExpressionConstant2Vector, -2000, 60)
half.set_editor_property('r', 0.5)
half.set_editor_property('g', 0.5)
c = expr(unreal.MaterialExpressionSubtract, -1840, -40)     # uv - 0.5
wire(uv, '', c, 'A')
wire(half, '', c, 'B')
r2 = expr(unreal.MaterialExpressionDotProduct, -1700, 40)    # |c|^2
wire(c, '', r2, 'A')
wire(c, '', r2, 'B')
curvTerm = expr(unreal.MaterialExpressionMultiply, -1560, 120)
wire(r2, '', curvTerm, 'A')
wire(pCurv, '', curvTerm, 'B')
one = const(1.0, -1560, 220)
curvScale = expr(unreal.MaterialExpressionAdd, -1420, 160)   # 1 + curv*r2
wire(one, '', curvScale, 'A')
wire(curvTerm, '', curvScale, 'B')
cScaled = expr(unreal.MaterialExpressionMultiply, -1280, 40)
wire(c, '', cScaled, 'A')
wire(curvScale, '', cScaled, 'B')
uvD = expr(unreal.MaterialExpressionAdd, -1140, 0)           # distorted uv
wire(cScaled, '', uvD, 'A')
wire(half, '', uvD, 'B')

# --- chroma fringe: r/b sampled a hair left/right of the green --------------
vsz = expr(unreal.MaterialExpressionViewSize, -1420, 320)
vszX = expr(unreal.MaterialExpressionComponentMask, -1280, 320)
vszX.set_editor_property('r', True)
vszX.set_editor_property('g', False)
wire(vsz, '', vszX, '')
px = expr(unreal.MaterialExpressionDivide, -1140, 300)       # ChromaPx / width
wire(pChroma, '', px, 'A')
wire(vszX, '', px, 'B')
zero = const(0.0, -1140, 420)
off = expr(unreal.MaterialExpressionAppendVector, -1000, 340)
wire(px, '', off, 'A')
wire(zero, '', off, 'B')
uvL = expr(unreal.MaterialExpressionSubtract, -860, 120)
wire(uvD, '', uvL, 'A')
wire(off, '', uvL, 'B')
uvR = expr(unreal.MaterialExpressionAdd, -860, 260)
wire(uvD, '', uvR, 'A')
wire(off, '', uvR, 'B')


def scene(x, y, uv_expr=None):
    s = expr(unreal.MaterialExpressionSceneTexture, x, y)
    s.set_editor_property('scene_texture_id',
                          unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    if uv_expr is not None:
        wire(uv_expr, '', s, 'UVs')
    return s


def mask(src, x, y, rr=False, gg=False, bb=False):
    m = expr(unreal.MaterialExpressionComponentMask, x, y)
    m.set_editor_property('r', rr)
    m.set_editor_property('g', gg)
    m.set_editor_property('b', bb)
    wire(src, 'Color', m, '')
    return m

sL = scene(-700, 60, uvL)
sC = scene(-700, 200, uvD)
sR = scene(-700, 340, uvR)
chR = mask(sL, -540, 60, rr=True)
chG = mask(sC, -540, 200, gg=True)
chB = mask(sR, -540, 340, bb=True)
rg = expr(unreal.MaterialExpressionAppendVector, -400, 120)
wire(chR, '', rg, 'A')
wire(chG, '', rg, 'B')
rgb = expr(unreal.MaterialExpressionAppendVector, -260, 200)
wire(rg, '', rgb, 'A')
wire(chB, '', rgb, 'B')

# --- scanlines: 1 - ScanAmt * (0.5 + 0.5*sin(uv.y * LineCount)) -------------
uvY = expr(unreal.MaterialExpressionComponentMask, -1000, -300)
uvY.set_editor_property('r', False)
uvY.set_editor_property('g', True)
wire(uv, '', uvY, '')
lineArg = expr(unreal.MaterialExpressionMultiply, -860, -300)
wire(uvY, '', lineArg, 'A')
wire(pLines, '', lineArg, 'B')
sn = expr(unreal.MaterialExpressionSine, -720, -300)
wire(lineArg, '', sn, '')
halfC = const(0.5, -720, -200)
snHalf = expr(unreal.MaterialExpressionMultiply, -580, -300)
wire(sn, '', snHalf, 'A')
wire(halfC, '', snHalf, 'B')
snPos = expr(unreal.MaterialExpressionAdd, -440, -300)       # 0..1
wire(snHalf, '', snPos, 'A')
wire(halfC, '', snPos, 'B')
snAmt = expr(unreal.MaterialExpressionMultiply, -300, -300)
wire(snPos, '', snAmt, 'A')
wire(pScan, '', snAmt, 'B')
oneB = const(1.0, -300, -200)
scanF = expr(unreal.MaterialExpressionSubtract, -160, -300)  # 1 - amt
wire(oneB, '', scanF, 'A')
wire(snAmt, '', scanF, 'B')

# --- vignette: 1 - VignAmt * 2 * r2 -----------------------------------------
two = const(2.0, -1000, 500)
v2 = expr(unreal.MaterialExpressionMultiply, -860, 500)
wire(r2, '', v2, 'A')
wire(two, '', v2, 'B')
vAmt = expr(unreal.MaterialExpressionMultiply, -720, 500)
wire(v2, '', vAmt, 'A')
wire(pVign, '', vAmt, 'B')
oneC = const(1.0, -720, 600)
vignF = expr(unreal.MaterialExpressionSubtract, -580, 500)
wire(oneC, '', vignF, 'A')
wire(vAmt, '', vignF, 'B')

# --- combine: fx = rgb * scan * vign; out = lerp(plain, fx, Intensity) ------
m1 = expr(unreal.MaterialExpressionMultiply, -120, 200)
wire(rgb, '', m1, 'A')
wire(scanF, '', m1, 'B')
fx = expr(unreal.MaterialExpressionMultiply, 20, 240)
wire(m1, '', fx, 'A')
wire(vignF, '', fx, 'B')
plain = scene(-120, -80)                                    # untouched centre
plainRGB = mask(plain, 20, -80, True, True, True)
out = expr(unreal.MaterialExpressionLinearInterpolate, 180, 60)
wire(plainRGB, '', out, 'A')
wire(fx, '', out, 'B')
wire(pIntensity, '', out, 'Alpha')
ok = MEL.connect_material_property(out, '',
                                   unreal.MaterialProperty.MP_EMISSIVE_COLOR)
assert ok, 'emissive hookup failed'

MEL.layout_material_expressions(mat)
MEL.recompile_material(mat)
print('M_FeedLayer compiled:', mat.get_path_name())

# --- instance ---------------------------------------------------------------
if eal.does_asset_exist(MI):
    mi = eal.load_asset(MI)
else:
    f = unreal.MaterialInstanceConstantFactoryNew()
    mi = at.create_asset('MI_FeedLayer', FOLDER,
                         unreal.MaterialInstanceConstant, f)
MEL.set_material_instance_parent(mi, mat)
MEL.set_material_instance_scalar_parameter_value(mi, 'Intensity', 0.35)
MEL.update_material_instance(mi)
print('MI_FeedLayer ready:', mi.get_path_name())
for p in (MAT, MI):
    eal.save_asset(p, only_if_is_dirty=False)
print('feedlayer: assets saved')
