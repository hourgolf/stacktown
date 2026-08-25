# Portland production pass 0.4

## Outcome

The project now has a procedural intake lane instead of another hand-built mockup.
`/Game/Maps/PortlandAssetZoo_01` uses Epic's PCG asset-grid utility to turn an
array of source meshes into a generated, editable comparison map. The first run
generated sixteen real Static Mesh Actors from the installed City Street Props
pack. This proves the production mechanism; it is not a visual-quality pass.

## What this pass deliberately does not claim

- The existing prop pack does not supply a coherent Portland city.
- Camera blur, depth of field, and warm lighting cannot normalize incompatible
  architecture.
- A procedural scatter does not make an asset photorealistic or miniature-like.
- No additional city block should be hand-assembled from these inputs.

## Production architecture

1. **Source intake** — new assets enter an isolated asset-zoo map first.
2. **Normalization** — scale, texel density, roughness range, glass, and naming
   are corrected in reusable parent materials and data assets.
3. **Kit assembly** — buildings are made from a compact facade grammar:
   structural bay, window bay, corner, roofline, storefront, entrance, service
   wall, and rooftop set. We author the grammar once rather than sculpting each
   building.
4. **City generation** — splines and PCG generate roads, lots, facades, trees,
   signs, and prop sockets from seeds and style profiles.
5. **Hero dressing** — manual work is limited to the camera-visible 10–15% that
   distinguishes a district.
6. **Visual gate** — one finished intersection must pass the reference test at
   the hero camera and both movement endpoints before the city expands.

## Next executable gate

Build `PortlandHeroIntersection_01` from:

- one editable road intersection;
- four lot envelopes;
- two procedural facade variants sharing one normalized material family;
- twelve curated City Street Props pieces;
- one Portland vegetation family;
- one 70–100 mm camera with bounded pan, orbit, and zoom endpoints.

The gate passes only if the three captures read as a photographed physical
miniature without explanation and a second seed produces a credible variation.
If it fails, revise the kit or material language; do not add another block.

## Current technical evidence

- PCG graph: `/PCGPrimitives/Examples/Utilities/Asset_grid_with_Frame`
- Test map: `/Game/Maps/PortlandAssetZoo_01`
- Generated assets: 16 Static Mesh Actors in a 4 × 4 PCG grid
- Existing prop source: `/Game/Deko_MatrixDemo/City/Meshes`
- Platform: Unreal Engine 5.8.1 on Apple Silicon
