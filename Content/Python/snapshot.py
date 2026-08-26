"""Read the level into plain Python data, once.

Invariants are then pure functions over that data. Two reasons, both learned
the hard way. A pure function can be self-tested against a SYNTHETIC defect
without touching the level, so a rule can be proved able to detect the thing it
exists to detect. And reading the level once means every rule sees the same
world, so two rules cannot disagree about what is in it.
"""
import unreal, time
import _path
import labels

from qc import DEFAULT_MATS  # noqa: F401  - one definition, in qc.py


def _aabb(c):
    sm = c.static_mesh
    if not sm:
        return None
    b = sm.get_bounds()
    o, e = b.origin, b.box_extent
    t = c.get_world_transform()
    lo = [1e18]*3
    hi = [-1e18]*3
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                w = t.transform_location(unreal.Vector(o.x + sx*e.x,
                                                       o.y + sy*e.y,
                                                       o.z + sz*e.z))
                for i, v in enumerate((w.x, w.y, w.z)):
                    lo[i] = min(lo[i], v)
                    hi[i] = max(hi[i], v)
    return lo, hi


def take():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    t0 = time.time()
    actors, unread = [], 0
    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        rec = dict(label=lbl, family=labels.family(lbl), cls=type(a).__name__,
                   loc=(loc.x, loc.y, loc.z),
                   rot=(rot.pitch, rot.yaw, rot.roll), comps=[])
        try:
            comps = a.get_components_by_class(unreal.StaticMeshComponent)
        except Exception:
            comps = []
        for c in comps:
            if not c.is_visible():
                continue
            sm = c.static_mesh
            box = _aabb(c)
            mats = []
            try:
                n = len(sm.get_editor_property('static_materials')) if sm else 0
                for i in range(n):
                    m = c.get_material(i)
                    mats.append(m.get_name() if m else None)
            except Exception:
                unread += 1
            rec['comps'].append(dict(
                name=c.get_name(),
                mesh=sm.get_name() if sm else None,
                aabb=box, mats=mats))
        actors.append(rec)
    return dict(actors=actors, unread_material_slots=unread,
                seconds=round(time.time() - t0, 1))


def rect_of(comp):
    """World XY rectangle of a component, or None."""
    if not comp['aabb']:
        return None
    lo, hi = comp['aabb']
    return (lo[0], lo[1], hi[0], hi[1])


def mesh_actors(snap, pred):
    """[(actor, comp)] where pred(label, mesh) is true."""
    out = []
    for a in snap['actors']:
        for c in a['comps']:
            if pred(a['label'], c['mesh']):
                out.append((a, c))
    return out
