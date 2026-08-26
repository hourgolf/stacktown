"""Assign every BLD2_/AV_ component by role prefix; wall colour comes from the
city table so a new block needs no edit here."""
import unreal, sys
import _path  # repo tool paths; replaces a dead scratchpad path
import labels
from city import BLOCKS
F='/Game/Stacktown/Materials'
# .get, not [] - an open zone has no wall colour and indexing it directly threw
# KeyError, which took the whole role sweep down and left 7000 components
# unassigned while every other step reported ok.
WALL={l['name']: l['wall'] for b in BLOCKS for l in b['lots'] if l.get('wall')}
# A pitched roof is the largest surface on a house and it was rendering on
# MI_concrete - the same pale grey as a flat commercial deck - so five houses
# read as five white wedges. Per lot, like the wall colour.
ROOF={l['name']: l.get('roofmat', 'MI_shingle_grey')
      for b in BLOCKS for l in b['lots']
      if l.get('style') in ('house', 'walkup') or l.get('roofmat')}
# Staging lots baked for the catalogue are not in the city table, so their
# colours arrive in a temp file. ONE role mapping, extended - not a second copy
# of it living in the bake script, which is how the two would drift.
import os, json, tempfile
_ov = os.path.join(tempfile.gettempdir(), 'stacktown_role_overrides.json')
if os.path.exists(_ov):
    for _n, _d in json.load(open(_ov)).items():
        if _d.get('wall'):    WALL[_n] = _d['wall']
        if _d.get('roofmat'): ROOF[_n] = _d['roofmat']
    print('role overrides for %s' % ', '.join(sorted(json.load(open(_ov)))))
# The table moved to rolemap.py so the FAST bake path can read it too - it
# runs without an editor and step_roles imports `unreal`. One table, two
# backends; a second copy is how a Timber_ ends up two different colours.
from rolemap import SHARED, FAMILY, MURAL  # noqa: E402
import rolemap
_bound = rolemap.BOUND
if _bound != set(labels.ROLES):
    raise SystemExit('role vocabulary disagrees with labels.ROLES\n'
                     '  bound here, not listed: %s\n'
                     '  listed, not bound here: %s'
                     % (sorted(_bound - set(labels.ROLES)),
                        sorted(set(labels.ROLES) - _bound)))
_m={}
def M(n):
    if n not in _m: _m[n]=unreal.EditorAssetLibrary.load_asset('%s/%s.%s'%(F,n,n))
    return _m[n]
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
done=0; unresolved=[]
for a in eas.get_all_level_actors():
    l=a.get_actor_label()
    # ELEV_ carries the flank elevations and uses the same role prefixes, so
    # it binds here for free - which is the whole point of role-in-the-name.
    # LAMP_ is here because lamps are built AFTER this sweep normally runs, so
    # nothing ever bound them: all 54 sat on WorldGridMaterial, which is gate
    # line B1, and no check had ever looked. The build now calls this a second
    # time once the lamps exist rather than growing a second binder.
    # CORE_ joined this list when cores stopped being bare StaticMeshActors
    # with a directly-assigned material and became Wall_ boxes like everything
    # else - one sweep, one vocabulary.
    if not l.startswith(('BLD2_', 'ELEV_', 'ZONE_', 'LAMP_', 'PLOT_', 'CORE_')): continue
    who=l.split('_')[1]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        nm=c.get_name()
        # ONE resolver, shared with the fast bake path. This loop used to
        # carry its own if/elif chain over the same tables, which is two
        # answers to "what material is a Timber_" waiting to drift - and it
        # did: rolemap grew SPECIAL (penthouse glazing is not window glazing)
        # and this sweep could not see it.
        mname = rolemap.material_for(nm, WALL.get(who), ROOF.get(who),
                                     labels.family(l))
        if mname:
            c.set_material(0, M(mname))
        elif l.startswith('CORE_'):
            # A CITY core is still a bare StaticMeshActor built by
            # step_cores3, which assigns its material directly - so its one
            # component is StaticMeshComponent0 and has no role to bind. The
            # catalogue's cores are Wall_ boxes and DO bind here. Skip rather
            # than report: it is not unresolved, it was never ours.
            continue
        else:
            unresolved.append(nm); continue
        done+=1
print('assigned %d slots; unresolved %s'%(done,sorted(set(unresolved))[:6]))
les.save_current_level()
