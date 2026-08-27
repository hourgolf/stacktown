"""Resize STAGE_Ground to cover a requested rectangle. Sandbox only.

P14: the shelf outgrew the stage. 32 recipe ladders at one row each ran to
y = -70,518 while the ground stopped near -12,000, so most of the catalogue
sat unlit in the void and no capture of it was usable.

This is stage.py's `fit` for one plane, and it carries the same four hard-won
rules, because every one of them cost a debugging session:

  1. the meshes are NOT 100 uu cubes - measure the mesh, do not assume;
  2. the COMPONENT carries its own relative scale on top of the actor's, so
     resetting only the actor leaves it at the old size;
  3. the component also carries a relative LOCATION, and a relative offset is
     MULTIPLIED by the root's scale - at 600x that threw the ground 900,000
     uu away, which is why enlarging it used to make the surround blacker;
  4. MEASURE the result with get_actor_bounds and assert against what was
     asked, because printing what you asked for proves nothing.

  reads: stacktown_ground.json {x0, y0, x1, y1, margin}
"""
import unreal
import _path  # noqa: F401
import stagegeo
import json
import os
import tempfile

SANDBOX = 'Sandbox_Bench'
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if SANDBOX not in eus.get_editor_world().get_path_name():
    raise SystemExit('refusing to resize the ground outside the sandbox')

job = json.load(open(os.path.join(tempfile.gettempdir(),
                                  'stacktown_ground.json')))
m = float(job.get('margin', 2500.0))
x0, y0 = float(job['x0']) - m, float(job['y0']) - m
x1, y1 = float(job['x1']) + m, float(job['y1']) + m
want = (x1 - x0, y1 - y0, 24.0)
loc = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, stagegeo.FLOOR_Z - 12.0)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
a = next((x for x in eas.get_all_level_actors()
          if x.get_actor_label() == 'STAGE_Ground'), None)
if not a:
    raise SystemExit('STAGE_Ground not found')

a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
base = None
for c in a.get_components_by_class(unreal.StaticMeshComponent):
    c.set_editor_property('relative_scale3d', unreal.Vector(1.0, 1.0, 1.0))
    c.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 0.0))
    if c.static_mesh and base is None:
        b = c.static_mesh.get_bounds().box_extent
        base = (max(b.x * 2, 1.0), max(b.y * 2, 1.0), max(b.z * 2, 1.0))
if not base:
    raise SystemExit('STAGE_Ground has no mesh')

a.set_actor_location(unreal.Vector(*loc), False, False)
a.set_actor_scale3d(unreal.Vector(*[max(w / bs, 0.001)
                                    for w, bs in zip(want, base)]))
org, ext = a.get_actor_bounds(False)
got = (ext.x * 2, ext.y * 2)
ok = all(abs(got[i] - want[i]) <= want[i] * 0.05 for i in (0, 1))
print('  STAGE_Ground -> centre (%.0f, %.0f)  size %.0f x %.0f  (asked %.0f x %.0f)  %s'
      % (org.x, org.y, got[0], got[1], want[0], want[1],
         'ok' if ok else '*** MEASURED != ASKED ***'))
assert ok, 'the ground did not take the size it was given'
# THE TOP SURFACE, computed - not measured. get_actor_bounds includes the
# editor BillboardComponent, which swamps a THIN axis: the plane is 24 uu deep
# and the sprite made it measure a top of -12 instead of -128. stage.py
# documents exactly this trap ("a billboard can only inflate bounds, never
# shrink them, so a thin axis proves nothing") and the first version of this
# file asserted on it anyway. The assertion was right to fail; the measurement
# was the thing that was wrong.
#
# So: police the axes that are big enough to measure (x and y, above), and for
# z assert on the LOCATION, which is what we actually set.
got_z = a.get_actor_location().z
top = got_z + want[2] / 2.0
print('  top surface z = %.1f (location %.1f + half of %.0f)  stagegeo.FLOOR_Z = %.1f'
      % (top, got_z, want[2], stagegeo.FLOOR_Z))
assert abs(got_z - loc[2]) < 2.0, (
    'ground sits at z %.1f, was put at %.1f' % (got_z, loc[2]))
assert abs(top - stagegeo.FLOOR_Z) < 6.0, (
    'ground top at %.1f but stagegeo.FLOOR_Z says %.1f - everything placed by '
    'floor_z_at would float or sink' % (top, stagegeo.FLOOR_Z))
les.save_current_level()
print('groundfit: done')
