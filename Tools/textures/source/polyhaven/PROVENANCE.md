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
