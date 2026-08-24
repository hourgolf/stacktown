# Handoff — StacktownAlpha → StacktownPortlandGate1

Written 2026-08-23 after a read-only inspection of the Portland block (files on
disk plus the four captures in `Saved/Gate1`). Nothing in that project was run
or modified.

Ordered by how much each item moves the image. The first three are minutes of
work each.

---

## 1. The viewport FOV — this is why the captures are broken

`diagnostic_matched_fov90.png` says you concluded the pane is stuck at 90 deg
and tried to MATCH it. Set it instead:

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    k = les.get_active_viewport_config_key()
    les.set_level_viewport_fov(28.84, k)      # 70 mm on a 36 mm back

**The argument order is (fov, key), not (key, fov)** — the reverse of what the
name suggests, and it fails with a confusing Name-to-float nativize error.

Two more things about it:
- In a multi-pane layout, `pilot_level_actor` moves the viewport to the camera
  but does NOT adopt its FOV. Piloting alone is not enough.
- **Saving the level resets it.** It has to run immediately before every
  capture, not once at setup.

If the pane is not 3:2, `set_level_viewport_fov` sets HORIZONTAL fov, so match
the vertical instead and crop: for a 1.560 pane, HFOV 29.939 reproduces the
19.454 deg vertical of a 70 mm 3:2 frame; then centre-crop to height x 1.5.

Verify framing by finding the facade silhouette edges with a local GRADIENT.
Absolute luma thresholds compare backdrop and building together and will tell
you a 4% error is a 60% error. That cost me two wrong conclusions in one
sitting.

## 2. The key light is 5x too dim, the fill 12x

Intensity scales with the inverse square of rig distance. Baseline measured
here: 300k lm at 1830 uu.

| light | distance to target | set | needed | ratio |
|---|---|---|---|---|
| Key  | 13,411 uu |  3.3M | 16.1M | 0.20x |
| Fill | 10,323 uu |  720k |  9.5M | 0.08x |
| Rim  |  6,709 uu |  980k |  4.0M | 0.24x |

This is most of the darkness in the current renders — it is not an exposure
problem. Also check `AttenuationRadius` exceeds the throw; the default 1000
against a 1830 uu rig rendered an entire scene black here.

## 3. The material bands are painted styrene, not printed card

Your roles run 0.36-0.68 roughness at 0.28-0.52 specular. Card is:

    roughness 0.62-0.80    specular 0.20    band width ~0.18

Roughness and specular are among the very few properties that still read at
range. This single change is what stopped this build reading as plastic. The
band must stay NARROW whichever material you tune for.

## 4. Bloom is on and a DoF f-stop is declared

`bloomIntensity: 0.12` and `depthOfFieldFstop: 5.6`. Motion blur is correctly
0. `ONE_BUILDING_GATE` section E bans all three. If Portland Gate 1 inherits
that gate this is an automatic fail; if it does not, ignore this item.

Film grain, vignette and chromatic aberration are NOT banned and are worth
having — they read as evidence a camera existed. Useful settings measured here:
grain 1.05 (response is strongly non-linear: 0.45 is invisible, 1.45 is heavy),
vignette 0.42, fringing 0.30.

## 5. Do not inherit the surface toolkit — it cannot read at your range

Your build script correctly never calls the seams, edge wear, peels or beads.
Keep it that way. The 0.4%-of-frame-width rule at your cameras:

| camera | distance | frame width | 0.4% threshold |
|---|---|---|---|
| CAM_Inspection | 5,348 uu | 3,501 uu | 14.0 uu (140 mm) |
| CAM_District | 12,684 uu | 6,523 uu | 26.1 uu (261 mm) |
| CAM_Matched | 19,005 uu | 9,774 uu | 39.1 uu (391 mm) |
| CAM_Overview | 22,992 uu | 12,734 uu | 50.9 uu (509 mm) |

Against that: panel seams are 6 uu wide, glue beads 12 uu, chamfers 4 uu, the
dent 2 uu deep. **Every one is below threshold at your closest camera.**

At block scale the reveal has to be carried by mass: setbacks, roof clutter,
parapet and cornice depth, canopy projection, silhouette variation between
buildings. Anything under ~260 mm is invisible at your working framing.

## 6. A bug we both had — your writes may be landing in my editor

UE's `remote_execution` API:

    rem.open_command_connection(remote_node_id)   # wants the ID STRING

Passing the node dict from `remote_nodes` "works" while only one editor is on
the multicast group, and with two it connects to whichever it likes. Four of my
runs executed in YOUR editor before I caught it. Pass `node['node_id']`.

Two related traps: the discovery loop must wait for YOUR project's node, not
just any node (exiting on the first responder makes your own editor look
absent); and `remote_nodes` rebuilds its dicts on each access, so identity
comparison against a previously-taken node never matches — snapshot once.

Selection is not enough on its own. Prepend a guard to every mutating script
that aborts unless `unreal.Paths.project_dir()` is your project AND the level
is the one you expect. That guard is the only reason nothing of mine was
written into your build.

## 7. Credit where it is due

Your `OWNED` prefix tuple plus `wipe_owned()` — only ever destroying actors you
created — is better hygiene than anything in StacktownAlpha, which has no
ownership gate on destructive operations. Taking it.
