# Research: two Fab building generators (owner ask, 2026-08-31)

Research only — nothing purchased, downloaded, or imported. Sources:
the listings' own pages (description, limitations, reviews), read via
browser; documentation links noted.

## 1. Building Generator — erikcarter ($59.99 personal / $119.99 pro)

Spline-based Blueprint generator: user supplies wall/window meshes, the
tool assembles buildings along splines (HISM instancing, seed-
deterministic, four procedural roof types, curbs/cornices from curve
profiles, runtime or merge-tool bake, grid mode for "blocks or cities",
floors/stairs). **Actively maintained** (updated 2026-08-16; a 5-star
review 4 days ago), 4.5/5 over 17 reviews, praised for support and
terrain-following.

**Its own stated limitations are the disqualifiers for us**: procedural
meshes need triplanar texturing (per-face UVs), roofs cannot use custom
meshes, no smooth shading/bevels on roofs, and **no mesh distance
fields on procedural meshes → degraded Lumen** — our GI. Deeper:
everything it makes is gate-blind — BP-assembled HISM has no component
names (the role system cannot paint it), no stamps, no provenance, and
the coplanar census cannot see inside it. It is a parallel building
pipeline that bypasses every quality instrument this project runs on.

**VERDICT: NOT WORTH THE COST for this project.** It solves problems we
already solved with instruments it cannot pass. genbuild + fastbake +
the placer are our version of exactly this loop, with gates. The only
defensible use — throwaway massing studies in a scratch project — is
already served better by our own catalogue at our own fabrication tier.

## 2. [Free] Procedural Building Generator — Procedural World Lab

Assembles the USER'S modular meshes (none included — it is a funnel for
the seller's $99–$199 city packs) into buildings. 4.3/5 over 99
ratings, but the rating is legacy goodwill from its 2020 UE4 era:
**recent reviews are damning** — "crashed my project at start" (8 mo
ago), "barely works in UE 5.4, not performant" (1 yr), repeated
version-compatibility complaints. Tool version 3.4 dates to 2021;
documentation to March 2020; the 2026 "update" is a compatibility flag,
not development.

**VERDICT: NOT WORTH THE DOWNLOAD, even free.** Effectively abandoned
on modern UE, useless without the seller's paid mesh packs, and shares
every gate-blindness problem above.

## The pattern (same conclusion as the City Sample research)

Both are mesh-kit assemblers — the architecture this project
deliberately rejected in favour of gated generation at the fabrication
tier. What they do (splines → assembled buildings → baked merge,
deterministic seeds, grid placement) is a validation of our
genbuild/fastbake/placer shape, not a shortcut past it. Patterns were
already lifted where they mattered; the products cannot pass our gate,
match our tier, or carry our provenance. Money and disk both better
spent elsewhere — e.g., reference photography for the party-flank ask.
