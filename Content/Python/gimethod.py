"""Switch the sandbox PostProcess volume's GI/reflection method. Reversible.

Isolates Lumen as the flicker source. Our baked models are hundreds of very
thin boxes - 4 uu chamfers, 5-10 uu bands, thin glazing - and Lumen's software
tracing represents thin geometry with mesh distance fields, which is a known
source of unstable GI.

  reads: stacktown_gi.json {"gi": "LUMEN"|"NONE"|"SSGI", "refl": ...}
"""
import unreal
import _path  # noqa: F401
import json
import os
import tempfile

job = json.load(open(os.path.join(tempfile.gettempdir(), 'stacktown_gi.json')))
GI = {'LUMEN': unreal.DynamicGlobalIlluminationMethod.LUMEN,
      'NONE': unreal.DynamicGlobalIlluminationMethod.NONE,
      'SSGI': unreal.DynamicGlobalIlluminationMethod.SCREEN_SPACE}
RF = {'LUMEN': unreal.ReflectionMethod.LUMEN,
      'NONE': unreal.ReflectionMethod.NONE,
      'SSR': unreal.ReflectionMethod.SCREEN_SPACE}

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
n = 0
for a in eas.get_all_level_actors():
    if 'PostProcess' not in a.get_class().get_name():
        continue
    s = a.get_editor_property('settings')
    s.set_editor_property('override_dynamic_global_illumination_method', True)
    s.set_editor_property('dynamic_global_illumination_method', GI[job['gi']])
    s.set_editor_property('override_reflection_method', True)
    s.set_editor_property('reflection_method', RF[job['refl']])
    # LUMEN QUALITY / UPDATE SPEED. Measured: with Lumen on, a fixed camera
    # varied 1.55% frame to frame in a ~5-frame sawtooth; with Lumen off,
    # 0.000% across 20 frames. The slow stepping is Lumen's scene and final-
    # gather lighting refreshing on a cadence, so the update speeds are the
    # direct lever; detail and quality help it resolve our very thin parts.
    for k, v in (job.get('lumen') or {}).items():
        try:
            s.set_editor_property('override_%s' % k, True)
            s.set_editor_property(k, v)
        except Exception as e:
            print('    <%s: %s>' % (k, e))
    a.set_editor_property('settings', s)
    for k in (job.get('lumen') or {}):
        try:
            print('    %-46s %s' % (k, s.get_editor_property(k)))
        except Exception:
            pass
    got_gi = str(s.get_editor_property('dynamic_global_illumination_method'))
    got_rf = str(s.get_editor_property('reflection_method'))
    print('  %-12s GI -> %-28s  reflections -> %s'
          % (a.get_actor_label(), got_gi.split('.')[-1], got_rf.split('.')[-1]))
    n += 1
if not n:
    raise SystemExit('no PostProcess volume found')
les.save_current_level()
print('gimethod: %d volume(s)' % n)
