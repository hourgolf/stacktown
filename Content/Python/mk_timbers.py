#!/usr/bin/env python3
"""Import direction B's seven timbers and build their material instances.

    python3 Content/Python/mk_timbers.py            import, build, verify
    python3 Content/Python/mk_timbers.py --dry      print the plan, touch nothing

RUNS LOCALLY OVER MCP, never through rung.sh or remote exec. An MCP call
issued from inside a remote-exec script waits on the thread it is running on
and DEADLOCKS - documented in CATALOGUE_PIPELINE and walked into anyway on
2026-08-27. mk_da_catalogue.py is the precedent this follows.

IDEMPOTENT. Re-running re-imports and re-applies rather than duplicating, so
a half-finished window can simply be run again.

WHAT IT MAKES
  14 textures  T_<species>_N        the species nor_dx normal
               T_grain_<species>    the luminance-only grain mask (D8)
   7 instances MI_wood_<species>    of M_StacktownMaster

HALF A ONLY. Each instance's existing PaperDetail parameter is pointed at its
own grain mask, which gives grain-shaped ROUGHNESS with no master change -
PaperDetail is the roughness Lerp's alpha (traced from wire_paper.py). The
COLOUR figure needs a multiply inserted into the master's base-colour chain,
which is a shared-master edit with its own window and its own split proof.
This script deliberately cannot do it.

sRGB IS OFF ON ALL FOURTEEN, and that is not boilerplate. T_WoodFloor039 in
the donor packs is imported as a colour texture - sRGB on, DXT1, World group -
and is a normal map by name only. The fault is live in this project today,
so every setting here is WRITTEN AND THEN READ BACK, and a mismatch fails
loudly. State changes prove themselves by read-back, never by printing intent.

flip_green_channel is NOT set and MUST NOT BE. These are nor_dx - DirectX
convention, which is what UE samples. Setting a flip here would reinstate the
inverted-brick fault the DirectX choice exists to make impossible.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _path  # noqa: F401,E402
import fabrication as F  # noqa: E402
import ue  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, 'Tools', 'textures', 'source', 'polyhaven')
MASKS = os.path.join(ROOT, 'Tools', 'textures', 'grain_masks')
TEX_DIR = '/Game/Stacktown/Textures'
MAT_DIR = '/Game/Stacktown/Materials'
MASTER = '%s/M_StacktownMaster.M_StacktownMaster' % MAT_DIR

TT = 'editor_toolset.toolsets.texture.TextureTools'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

# species -> (nor_dx source basename, sRGB hex tone)
#
# PALETTE COMPRESSED AND WARMED, owner 2026-08-31, from the first board frame:
# "you can compress the palette and make it tighter and warmer". The original
# ladder spanned 58 L* (30..88) with saturation to 0.72, and on a board that
# read as PAINTED BLOCKS - adjacent pieces fought each other and the city
# stopped looking like one material cut many ways, which is the whole read.
# The reference photograph's blocks sit in a narrow warm band. Now 43 L*
# (37..80), saturation ceiling 0.51, every hue warm brown. Cherry and sapele
# lose the terracotta that made them read as brick.
TIMBERS = {
    'maple':  ('white_maple_veneer',     '#DCC49F'),
    'pine':   ('coated_pine',            '#CDB088'),
    'ash':    ('ash_veneer',             '#C2A278'),
    'oak':    ('white_oak_veneer',       '#B18E62'),
    'cherry': ('cherry_veneer',          '#9C7A54'),
    'sapele': ('sapele_veneer',          '#8A6844'),
    'walnut': ('american_walnut_veneer', '#6E5236'),
}


def call(toolset, name, args):
    raw = ue.tool(toolset, name, args)
    try:
        return json.loads(raw)['returnValue']
    except Exception:
        return raw


def srgb_to_linear(hexstr):
    """UE material vector parameters are LINEAR. A hex picked off a palette is
    sRGB, and writing it straight in makes every timber render too dark - the
    kind of silent constant error that survives a look because everything is
    wrong together. Converted here, once, with the standard transfer."""
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def import_texture(asset_name, source_file, normal_map):
    """Import and force the settings, then READ THEM BACK."""
    if not os.path.exists(source_file):
        return None, 'source missing: %s' % source_file
    call(TT, 'import_file', {'folder_path': TEX_DIR,
                             'asset_name': asset_name,
                             'source_file': source_file})
    ref = {'refPath': '%s/%s.%s' % (TEX_DIR, asset_name, asset_name)}
    want = {'sRGB': False,
            'compressionSettings': ('TC_Normalmap' if normal_map
                                    else 'TC_Grayscale'),
            'lODGroup': ('TEXTUREGROUP_WorldNormalMap' if normal_map
                         else 'TEXTUREGROUP_World')}
    call(OBJ, 'set_properties', {'instance': ref, 'values': json.dumps(want)})
    got = call(OBJ, 'get_properties',
               {'instance': ref, 'properties': list(want)})
    try:
        got = json.loads(got) if isinstance(got, str) else got
    except Exception:
        pass
    bad = [k for k in want
           if str(got.get(k, '')).lower() != str(want[k]).lower()]
    return ref, ('settings did not take: %s (got %s)' % (bad, got)) if bad else None


def main():
    dry = '--dry' in sys.argv
    print('%-9s %-34s %s' % ('species', 'asset', 'note'))
    problems = []
    for sp in F.TIMBERS:
        asset, tone = TIMBERS[sp]
        # PREFER THE DIRECTION-NORMALISED NORMAL. mk_grain_masks rotates a
        # species whose grain runs the wrong way and, since the crossing was
        # measured, emits the matching normal too - rotated AND with its R/G
        # channels turned, because those encode tangent-space x and y. Five
        # species were shipping a figure running one way and a donor normal
        # running the other: two directional patterns at 90 degrees, which
        # renders as a weave. Falls back to the donor for the species that
        # never needed turning, so the two paths cannot disagree.
        rot = os.path.join(MASKS, 'T_%s_N.png' % sp)
        nor = rot if os.path.exists(rot) else os.path.join(
            SRC, '%s_nor_dx_2k.png' % asset)
        msk = os.path.join(MASKS, 'T_grain_%s.png' % sp)
        plan = [('T_%s_N' % sp, nor, True), ('T_grain_%s' % sp, msk, False)]
        if dry:
            for n, src, isnor in plan:
                print('%-9s %-34s %s %s%s' % (sp, n,
                      'normal' if isnor else 'mask',
                      'OK' if os.path.exists(src) else 'SOURCE MISSING',
                      '  [direction-normalised]'
                      if isnor and src == rot else ''))
            continue
        for n, src, isnor in plan:
            ref, err = import_texture(n, src, isnor)
            print('%-9s %-34s %s' % (sp, n, err or 'imported, settings verified'))
            if err:
                problems.append('%s: %s' % (n, err))

    if dry:
        print('\n--dry: nothing was touched')
        return 0

    print()
    for sp in F.TIMBERS:
        name = 'MI_wood_%s' % sp
        call(MI, 'create', {'folder_path': MAT_DIR, 'asset_name': name,
                            'parent': {'refPath': MASTER}})
        ref = {'refPath': '%s/%s.%s' % (MAT_DIR, name, name)}
        p = F.params_for(name)
        for k, v in p.items():
            call(MI, 'set_scalar_parameter',
                 {'instance': ref, 'name': k, 'value': float(v)})
        r, g, b = srgb_to_linear(TIMBERS[sp][1])
        call(MI, 'set_vector_parameter',
             {'instance': ref, 'name': 'BaseColour',
              'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
        call(MI, 'set_texture_parameter',
             {'instance': ref, 'name': 'PaperNormal',
              'value': {'refPath': '%s/T_%s_N.T_%s_N' % (TEX_DIR, sp, sp)}})
        # HALF A: the grain mask drives ROUGHNESS through the existing
        # PaperDetail parameter. No master change.
        call(MI, 'set_texture_parameter',
             {'instance': ref, 'name': 'PaperDetail',
              'value': {'refPath': '%s/T_grain_%s.T_grain_%s'
                                   % (TEX_DIR, sp, sp)}})
        # READ BACK, do not trust the writes
        back = call(MI, 'get_texture_parameter',
                    {'instance': ref, 'name': 'PaperDetail'})
        ok = 'T_grain_%s' % sp in str(back)
        if not ok:
            problems.append('%s: PaperDetail did not take (%s)' % (name, back))
        print('%-9s %-34s tile %.4f amt %.1f rough %.2f-%.2f  %s'
              % (sp, name, p['PaperTiling'], p['PaperNormalAmount'],
                 p['RoughMin'], p['RoughMax'],
                 'grain wired' if ok else 'GRAIN NOT WIRED'))

    if problems:
        print('\n%d PROBLEM(S) - nothing here is verified art until these '
              'are clear:' % len(problems))
        for p in problems:
            print('  ' + p)
        return 1
    print('\nseven timbers imported and wired; Half A only, master untouched')
    return 0


if __name__ == '__main__':
    sys.exit(main())
