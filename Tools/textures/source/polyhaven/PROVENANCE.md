# Poly Haven source textures — provenance

Downloaded 2026-08-28 at the owner's explicit word, for the brick_sheet
stock's normal map (replacing the unverifiable pack-authored brick).

| file | asset | license | source |
|---|---|---|---|
| brick_wall_001_nor_gl_2k.png | Brick Wall 001 | CC0 (https://polyhaven.com/license) | https://polyhaven.com/a/brick_wall_001 |
| brick_wall_02_nor_gl_2k.png | Brick Wall 02 | CC0 (https://polyhaven.com/license) | https://polyhaven.com/a/brick_wall_02 |

Both are **nor_gl** — OpenGL green convention (green = up). UE expects
DirectX (green = down): the admission gate's green-convention check
applies AT IMPORT, deliberately — the same class of defect as the
backwards brick this replaces. Import settings: TC_NORMALMAP, sRGB off,
flip green (or import as DirectX) — and verify by LOOKING at lit
coursing, not by the numbers, which are direction-blind.

---

## The seven timbers — downloaded 2026-08-31 at the owner's word

For direction B's wooden city: one species stock per timber (D6), each
lending a normal AND a luminance-only grain mask (D8, "their pattern, our
palette"). All CC0 — verified at https://polyhaven.com/license: commercial
use, redistribution, no attribution required.

**These are `nor_dx`, NOT `nor_gl`.** The note above says "flip green (*or
import as DirectX*)" and nobody had taken up the second option. Taking the
DirectX maps means `flip_green_channel` is not set, not needed, and cannot
be forgotten on a fresh clone — the inverted-brick fault class is closed by
construction here rather than guarded.

**LFS:** `.gitattributes` gained `Tools/textures/source/**` patterns on
2026-08-31 BEFORE these were staged. The brick pair above predates that and
sits in git proper as raw blobs; that is not fixable without a history
rewrite, which is a hard stop.

| file | stock | asset | source | sha256 (16) |
|---|---|---|---|---|
| american_walnut_veneer_diffuse_2k.jpg | `walnut` | American Walnut Veneer | https://polyhaven.com/a/american_walnut_veneer | `278ed3382b3a28a9` |
| american_walnut_veneer_nor_dx_2k.png | `walnut` | American Walnut Veneer | https://polyhaven.com/a/american_walnut_veneer | `11138fd1769ace1f` |
| ash_veneer_diffuse_2k.jpg | `ash` | Ash Veneer | https://polyhaven.com/a/ash_veneer | `00abb70f86bdfe49` |
| ash_veneer_nor_dx_2k.png | `ash` | Ash Veneer | https://polyhaven.com/a/ash_veneer | `b04444a16278c0f7` |
| cherry_veneer_diffuse_2k.jpg | `cherry` | Cherry Veneer | https://polyhaven.com/a/cherry_veneer | `dc572a16d860d56f` |
| cherry_veneer_nor_dx_2k.png | `cherry` | Cherry Veneer | https://polyhaven.com/a/cherry_veneer | `0f057f9ff3d0feaf` |
| coated_pine_diffuse_2k.jpg | `pine` | Coated Pine | https://polyhaven.com/a/coated_pine | `377fa07523a1d2a5` |
| coated_pine_nor_dx_2k.png | `pine` | Coated Pine | https://polyhaven.com/a/coated_pine | `cae43a999b2f2ba7` |
| sapele_veneer_diffuse_2k.jpg | `sapele` | Sapele Veneer | https://polyhaven.com/a/sapele_veneer | `677f56c6e70f04ca` |
| sapele_veneer_nor_dx_2k.png | `sapele` | Sapele Veneer | https://polyhaven.com/a/sapele_veneer | `997715c973ecdda9` |
| white_maple_veneer_diffuse_2k.jpg | `maple` | White Maple Veneer | https://polyhaven.com/a/white_maple_veneer | `45ee4e8def749bdb` |
| white_maple_veneer_nor_dx_2k.png | `maple` | White Maple Veneer | https://polyhaven.com/a/white_maple_veneer | `d080923fff0be6a7` |
| white_oak_veneer_diffuse_2k.jpg | `oak` | White Oak Veneer | https://polyhaven.com/a/white_oak_veneer | `00e09e2f901fb76c` |
| white_oak_veneer_nor_dx_2k.png | `oak` | White Oak Veneer | https://polyhaven.com/a/white_oak_veneer | `de4da71ed2e09c3a` |

The diffuse maps are kept as the SOURCE of the grain masks, which are
derived by `Tools/textures/mk_grain_masks.py` and deliberately NOT committed
— they are regenerable by construction, and the asset that ships is the
imported `.uasset`. **No donor colour enters `Content/`:** the greyscale
conversion happens in that script, so "our palette" is a property of the
asset rather than a promise about the material graph.
